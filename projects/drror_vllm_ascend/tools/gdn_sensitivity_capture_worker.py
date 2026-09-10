"""Opt-in dense GDN observer for non-evaluation sensitivity calibration.

The historic two-prompt teacher worker remains unchanged.  This adapter reuses
its pass-through tensor hooks while binding sixteen raw-token calibration
sequences and recording its own source identity.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import time

import torch

try:
    import gdn_teacher_capture_worker as base
except ModuleNotFoundError:  # Imported as tools.* by the software test suite.
    from tools import gdn_teacher_capture_worker as base


SCHEMA = "gdn-sensitivity-calibration-v1"
SEQUENCE_COUNT = 16


def validate_manifest(document):
    base.require(
        isinstance(document, dict) and document.get("schema") == SCHEMA,
        "sensitivity manifest schema",
    )
    expected = {
        "model": base.MODEL,
        "tp_size": 4,
        "input_tokens": 128,
        "decode_steps": 8,
        "output_tokens": 9,
        "no_thinking": True,
        "raw_token_prompts": True,
        "add_special_tokens": False,
    }
    for name, value in expected.items():
        base.require(document.get(name) == value, "sensitivity manifest " + name)
    base.validate_layers(document.get("layers"))
    source = document.get("source_calibration", {})
    base.require(
        isinstance(source, dict)
        and source.get("rows") == SEQUENCE_COUNT
        and isinstance(source.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", source["sha256"]),
        "source calibration binding",
    )
    sequences = document.get("sequences")
    base.require(
        isinstance(sequences, list) and len(sequences) == SEQUENCE_COUNT,
        "sixteen sensitivity sequences required",
    )
    hashes = set()
    for index, sequence in enumerate(sequences):
        ids = sequence.get("input_ids")
        base.require(
            sequence.get("id") == f"calibration-{index:02d}"
            and sequence.get("source_index") == index
            and isinstance(ids, list)
            and len(ids) == 128
            and all(type(token) is int and token >= 0 for token in ids)
            and sequence.get("input_ids_sha256") == base.ids_sha256(ids)
            and isinstance(sequence.get("source_input_ids_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", sequence["source_input_ids_sha256"])
            and sequence["input_ids_sha256"] not in hashes,
            "sensitivity sequence identity",
        )
        hashes.add(sequence["input_ids_sha256"])
    return document


def validate_step(sequence, step, ids, positions):
    base.require(type(step) is int and 0 <= step <= 8, "step outside sensitivity budget")
    base.require(
        isinstance(ids, list) and all(type(token) is int and token >= 0 for token in ids),
        "sensitivity step token IDs",
    )
    expected_positions = list(range(128)) if step == 0 else [127 + step]
    if (
        isinstance(positions, list)
        and len(positions) == 3
        and all(isinstance(item, list) for item in positions)
    ):
        base.require(
            positions[0] == positions[1] == positions[2],
            "non-text MRoPE positions",
        )
        positions = positions[0]
    base.require(positions == expected_positions, "positions/chunked prefill mismatch")
    base.require(
        ids == sequence["input_ids"] if step == 0 else len(ids) == 1,
        "sensitivity prompt/decode token mismatch",
    )


# The inherited methods resolve these globals from the base module at runtime.
# Mutation is process-local to this explicitly selected worker class.
base.SCHEMA = SCHEMA
base.validate_manifest = validate_manifest
base.validate_step = validate_step


class GdnSensitivityCaptureWorker(base.GdnTeacherCaptureWorker):
    def load_model(self):
        super().load_model()
        base.write_json(
            self._teacher_dir / f"rank{self.rank}.sensitivity-wrapper.json",
            {
                "schema": SCHEMA,
                "rank": self.rank,
                "adapter": base.file_identity(__file__),
                "base_worker": base.file_identity(base.__file__),
                "manifest_sha256": self._manifest_hash,
                "claim": "Opt-in pass-through observer; no candidate math or performance.",
            },
        )

    def _model_before(self, module, args, kwargs):
        base.require(
            self._frame is None and self._current is None and not self._pending,
            "nested/stale forward",
        )
        arm_path = self._teacher_dir / "armed.json"
        if not arm_path.exists():
            return None
        arm = json.loads(arm_path.read_text())
        base.require(arm.get("schema") == SCHEMA, "arm schema")
        sid = arm.get("sequence_id")
        lookup = {item["id"]: item for item in self._manifest["sequences"]}
        base.require(sid in lookup, "arm sequence")
        sequence = lookup[sid]
        index = sequence["source_index"]
        base.require(
            all(self._steps.get(f"calibration-{prior:02d}") == 9 for prior in range(index)),
            "sensitivity sequence ordering",
        )
        base.require(
            arm.get("input_ids_sha256") == sequence["input_ids_sha256"],
            "arm token binding",
        )
        nonce = arm.get("nonce")
        base.require(
            isinstance(nonce, str) and re.fullmatch(r"[a-zA-Z0-9-]{16,64}", nonce),
            "arm nonce",
        )
        if sid in self._nonces:
            base.require(nonce == self._nonces[sid], "nonce changed within sequence")
        else:
            self._nonces[sid] = nonce
        step = self._steps.get(sid, 0)
        base.require(
            not args and kwargs.get("positions") is not None,
            "root forward input interface",
        )
        positions = base.snapshot(kwargs["positions"]).tolist()
        token_count = kwargs["positions"].shape[-1]
        tokens = kwargs.get("input_ids")
        token_source = "root_input_ids"
        if tokens is None:
            base.require(
                kwargs.get("inputs_embeds") is not None
                and kwargs["inputs_embeds"].shape[0] == token_count,
                "embedding token interface",
            )
            tokens = self.model_runner.input_ids.gpu[:token_count]
            token_source = "frozen_runner_input_ids_buffer_with_text_embeddings"
        ids = base.snapshot(tokens).tolist()
        validate_step(sequence, step, ids, positions)
        self._frame = {
            "sequence_id": sid,
            "nonce": nonce,
            "step": step,
            "input_ids": ids,
            "positions": positions,
            "input_ids_source": token_source,
            "layers": [],
            "records": [],
        }
        return None
