"""Exclusive per-TP-rank CPU output; bounded streaming statistics."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
from .contract import canonical, digest, require, STATE_BYTES
from .timeline import decay_weights


class Writer:
    def __init__(self, root, rank, manifest, source):
        require(rank in range(4), "invalid TP rank")
        root = Path(root).resolve()
        require(root.is_dir() and (root / "RUN.json").is_file(), "run must be explicitly created")
        run = json.loads((root / "RUN.json").read_text())
        require(run["manifest_sha256"] == digest(manifest) and run["capture_enabled"] is True,
                "run/manifest capture mismatch")
        self.path = root / ("rank-" + str(rank))
        self.path.mkdir(exist_ok=False)
        self.rank, self.manifest = rank, manifest
        self.audit = (self.path / "events.jsonl").open("x", encoding="utf-8")
        self.rms_sum, self.rms_anchors = {}, {}
        self.event("worker_started", manifest_sha256=digest(manifest), source=source,
                   native_state_layout="Hv,Dv,Dk", paper_state_layout="Dk,Dv",
                   group_axis="native Dv", state_dtype="float32")

    def event(self, kind, **fields):
        record = dict(event=kind, rank=self.rank, pid=os.getpid(), **fields)
        self.audit.write(canonical(record).decode() + "\n")
        self.audit.flush()

    def binary(self, relative, payload):
        path = self.path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
        return dict(path=relative, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))

    def anchor(self, row, layer, step, state):
        import torch
        require(sys.byteorder == "little" and state.device.type == "cpu" and
                state.dtype == torch.float32 and tuple(state.shape) == (12, 128, 128),
                "anchor must be CPU little-endian FP32 [Hv,Dv,Dk]")
        require(bool(torch.isfinite(state).all()), "nonfinite captured anchor")
        payload = state.contiguous().numpy().tobytes(order="C")
        require(len(payload) == STATE_BYTES, "state binary size mismatch")
        artifact = self.binary(f'{row["id"]}/layer-{layer}/anchor-{step}.f32', payload)
        self.event("anchor", logical_id=row["id"], layer=layer, update=step, artifact=artifact,
                   state_shape=[12, 128, 128], split=row.get("split", "smoke"))
        if row.get("split") == "fit":
            # RMS over paper key dimension Dk, equal weighting of each fit anchor.
            contribution = state.double().square().mean(dim=-1)
            self.rms_sum[layer] = self.rms_sum.get(layer, torch.zeros_like(contribution)) + contribution
            self.rms_anchors[layer] = self.rms_anchors.get(layer, 0) + 1
            self.flush_rms(layer)

    def flush_rms(self, layer):
        stats = dict(layer=layer, count=self.rms_anchors[layer],
                     sum_mean_key_square=self.rms_sum[layer].tolist(),
                     meaning="sqrt(sum/count) gives per-value-channel fit RMS",
                     shape=[12, 128], accumulation_dtype="float64",
                     equal_weight="anchor; balanced manifest supplies sequence/window/domain weights")
        # Append immutable snapshots; never rewrite earlier evidence.
        self.event("fit_rms_snapshot", **stats)

    def future(self, row, layer, anchor, rows):
        from array import array
        require(len(rows) == self.manifest["horizon"], "incomplete future horizon")
        floats = array("f", (x for values in rows for x in values))
        artifact = self.binary(f'{row["id"]}/layer-{layer}/future-{anchor}.f32', floats.tobytes())
        self.event("future", logical_id=row["id"], layer=layer, update=anchor, artifact=artifact,
                   shape=[self.manifest["horizon"], 12], log_decay=True,
                   decay_weight_including_anchor=decay_weights(rows))

    def complete(self, row, layer, timeline):
        self.event("layer_complete", logical_id=row["id"], layer=layer,
                   anchors=list(self.manifest["anchors"]), update=timeline.step)
