#!/usr/bin/env python3
"""Actual-NPU native anchor, then independent general-SR compressed feedback.

Prepared only. Parent owns all Docker/build/NPU execution. No production
helpers, candidate traces or CPU mv/sum recurrence are imported as a golden.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

import torch

from independent_oracle import (OracleLayout, ValueMajorPacked, errors,
                                pack_value_major, restore_state,
                                transform_state, unpack_value_major)
from native_call_contract import validate_native_schema
from general_sr_contract import (ANCHOR_VARIANTS, GENERAL_VARIANTS, LIMITS,
                                 NATIVE_COMMIT, NATIVE_HEADER_SHA, STEPS,
                                 PREPARE_INPUT_NAMES,
                                 assert_matrix_order, validate_device_proof,
                                 validate_source_manifest)

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT.parents[1]
SEED = 260827513
GDN_SHA = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
REFERENCE_HASHES = {
    "CMakeLists.txt": "f921cc3580e5a3ec3f0fb02130108249626ac918b5275ec5b857e6ac11a3deba",
    "LICENSE-APACHE": "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    "LICENSE-CANN": "5ee30bd08e3c47a51591e380d04cfc4cf90692c18a1b439abd85cf2f105dee8d",
    "README.md": "c139d70a3622a0a37329570c2668ee152ecc28740f0b959c9e54c35944874c1e",
    "check_source_contract.py": "5e4a09325b73729c96309cfb13867358d9ce725e8f3b083265556acb6337223a",
    "op_extension/native_sr_reference_torch.cpp": "71c69bae01a6e15e3f4b9f9cac80bcab08916acf83ec08412eb06653b8f4b9ba",
    "op_extension/ops.h": "1b4b34b3588d3d4d6325221ad702e43f082c4940f6575ab927e2cc4d5a6e2282",
    "op_extension/register.cpp": "fa485af95d0a55f009226db77f6af7294d018e1d8b6a5fd08f27aaca2f34845a",
    "op_kernel/native_sr_reference.h": "8816198563deaa460aa50dfd993e94b1e8483173fdfa65ed4af83104f9474896",
    "op_kernel/native_sr_reference_kernel.asc": "296f2cd699ab228d347cba1783b614c990d9affcc2188debe82b606cf78d6c3c",
}
CANDIDATE_HASHES = {
    "op_kernel/qwen36_gdn_damp_decode.h": "ecc24fada002dafbca962de5265f1bddc27a03d1e723070d9b317b415e3ca856",
    "op_extension/qwen36_gdn_damp_decode_torch.cpp": "0329433adda1821600026df9b8449b64aa9b3d48c4bdcfec82ad07b8f3a94ed4",
}
REGIONS = ("high", "low", "scales")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(x):
    if isinstance(x, float) and not math.isfinite(x):
        return "nonfinite:" + repr(x)
    if isinstance(x, dict):
        return {str(k): safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [safe(v) for v in x]
    return x


def cpu_clone(x):
    if isinstance(x, torch.Tensor):
        return x.detach().cpu().clone()
    if isinstance(x, dict):
        return {k: cpu_clone(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [cpu_clone(v) for v in x]
    return x


def exact(a, b):
    a, b = a.detach().cpu().contiguous(), b.detach().cpu().contiguous()
    return (a.dtype == b.dtype and a.shape == b.shape and
            torch.equal(a.view(torch.uint8), b.view(torch.uint8)))


def tensor_digest(items):
    digest = hashlib.sha256()
    for x in items:
        value = x.detach().cpu().contiguous()
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def verify_loaded_binding(rows, manifest, libraries):
    loaded = {row["path"]: row["sha256"] for row in rows}
    for path, expected in libraries:
        if loaded.get(str(path.resolve())) != expected:
            raise RuntimeError("explicit registration SO not loaded under frozen identity")
    native_path = str(Path(manifest["native_runtime_library_path"]).resolve())
    if loaded.get(native_path) != manifest["native_runtime_library_sha256"]:
        raise RuntimeError("frozen actual native runtime library not visible in process maps")


def packed_dict(p):
    return {name: getattr(p, name) for name in REGIONS}


def layout_dict(layout):
    return {"c": layout.c, "pk": layout.pk, "pv": layout.pv,
            "inv_pv": layout.pv.argsort(1).int(), "khi": 16, "group": 32}


def loaded_libraries(paths):
    wanted = {str(Path(p).resolve()) for p in paths}
    found = {}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split()
        if len(fields) < 6:
            continue
        raw = fields[-1]
        if not raw.startswith("/") or not Path(raw).is_file():
            continue
        path = str(Path(raw).resolve())
        if path in wanted or any(s in path.lower() for s in
                ("cust_opapi", "custopapi", "libopapi", "vllm_ascend",
                 "libtorch_npu", "qwen36_damp")):
            found[path] = sha(path)
    return [{"path": p, "sha256": h} for p, h in sorted(found.items())]


def make_layout(batch, variant, stage):
    generator = torch.Generator().manual_seed(
        SEED + batch * 100 + variant * 13 + (10000 if stage == "general" else 0))
    identity = torch.arange(128, dtype=torch.int32).repeat(12, 1)
    if stage == "anchor" and variant == 0:
        pk, pv = identity.clone(), identity.clone()
    else:
        pk = torch.stack([torch.randperm(128, generator=generator) for _ in range(12)]).int()
        pv = torch.stack([torch.randperm(128, generator=generator) for _ in range(12)]).int()
    if stage == "anchor":
        c = (torch.pow(torch.tensor(2.0), torch.randint(-2, 3, (12, 128),
              generator=generator).float()) if variant == 2 else torch.ones(12, 128))
    else:
        # Synthetic positive non-power2 FP32 c; not calibrated final model plans.
        c = torch.exp((torch.rand(12, 128, generator=generator) - 0.5) * 1.4).float()
    layout = OracleLayout(c.contiguous(), pv.contiguous(), pk.contiguous())
    state = torch.randn(batch + 3, 12, 128, 128, generator=generator) * 0.005
    transformed = transform_state(state, layout).contiguous()
    if stage == "general" and variant == 1:
        # Same fixed data on both paths: near-half-cell/cancellation stress.
        # This is not a claim that these cells remain half ties after recurrence.
        low = transformed[..., 16:].reshape(batch + 3, 12, 4, 32, 112)
        values = torch.arange(32, dtype=torch.float32).reshape(1, 1, 1, 32, 1) - 15.5
        center = values * torch.tensor(2.0 ** -12, dtype=torch.float32)
        below = torch.nextafter(center, torch.full_like(center, -math.inf))
        above = torch.nextafter(center, torch.full_like(center, math.inf))
        low[..., 0::3] = center
        low[..., 1::3] = below
        low[..., 2::3] = above
        low[..., 0, :] = 127 * torch.tensor(2.0 ** -12, dtype=torch.float32)
    return layout, transformed, generator


def turn(batch, slots, index, generator, anchor):
    q = torch.randn(batch, 4, 128, generator=generator)
    k = torch.randn(batch, 4, 128, generator=generator)
    q = (q / q.norm(dim=-1, keepdim=True)).bfloat16()
    k = (k / k.norm(dim=-1, keepdim=True)).bfloat16()
    v = ((torch.randint(-256, 257, (batch, 12, 128), generator=generator).float()
          / 1024).bfloat16() if anchor else
         (torch.randn(batch, 12, 128, generator=generator) * 0.2).bfloat16())
    g = (-0.002 - torch.rand(batch, 12, generator=generator) * 0.18).float()
    beta = torch.sigmoid(torch.randn(batch, 12, generator=generator)).bfloat16()
    ids = ((torch.arange(batch, dtype=torch.int32) + index) % slots).int()
    return q, k, v, g, beta, ids


def audit_cast(v, layout):
    scaled = (v.float() / layout.c.unsqueeze(0)).gather(
        2, layout.pv.long().unsqueeze(0).expand(v.shape[0], -1, -1)).contiguous()
    return exact(scaled.bfloat16().float(), scaled), scaled


def half_cell_evidence(updated, packed, layout):
    tail = updated[..., 16:].reshape(updated.shape[0], 12, 4, 32, 112)
    quotient = tail / packed.scales.unsqueeze(3)
    distance = (quotient - (torch.floor(quotient) + 0.5)).abs()
    flat = int(distance.reshape(-1).argmin())
    return {"minimum_distance_to_half": float(distance.reshape(-1)[flat]),
            "flat_group_cell": flat, "quotient_at_cell": float(quotient.reshape(-1)[flat]),
            "ties_count": int((distance == 0).sum()),
            "quotient_fp32": quotient.contiguous()}


def schema_contract():
    candidate = torch.ops.qwen36_damp.decode.default._schema
    prepare = torch.ops.qwen36_damp.prepare.default._schema
    reference = torch.ops.qwen36_damp_reference.decode.default._schema
    if len(candidate.arguments) != 14 or len(candidate.returns) != 1:
        raise RuntimeError("candidate schema arity mismatch")
    for i, arg in enumerate(candidate.arguments):
        alias = arg.alias_info
        if i in (5, 6, 7):
            if alias is None or not alias.is_write:
                raise RuntimeError("candidate packed regions must be mutable aliases")
        elif alias is not None:
            raise RuntimeError("candidate non-state schema alias unexpected")
    if candidate.returns[0].alias_info is not None:
        raise RuntimeError("candidate output schema must be fresh")
    if len(prepare.arguments) != 6 or prepare.returns or any(
            a.alias_info is not None for a in prepare.arguments):
        raise RuntimeError("prepare must have six immutable inputs and no returns")
    names = [a.name for a in reference.arguments]
    if names != ["q", "k", "v", "g", "beta", "state_selected", "pk", "pv", "inv_pv", "sr"]:
        raise RuntimeError("reference frozen argument names/order mismatch: " + repr(names))
    if len(reference.returns) != 3 or any(a.alias_info is not None for a in
            list(reference.arguments) + list(reference.returns)):
        raise RuntimeError("reference must have three fresh nonalias outputs")
    # Meta proves shape/schema only. No graph or NPU dispatch inference.
    for b in (1, 16):
        q = torch.empty(b, 4, 128, dtype=torch.bfloat16, device="meta")
        hi = torch.empty(b+3, 12, 128, 16, dtype=torch.float16, device="meta")
        lo = torch.empty(b+3, 12, 128, 112, dtype=torch.int8, device="meta")
        sc = torch.empty(b+3, 12, 4, 112, device="meta")
        pk, pv, inv = [torch.empty(12, 128, dtype=torch.int32, device="meta") for _ in range(3)]
        sr = torch.empty(12, 128, device="meta")
        k, v = q.clone(), torch.empty(b, 12, 128, dtype=torch.bfloat16, device="meta")
        g, beta = torch.empty(b, 12, device="meta"), torch.empty(b, 12, dtype=torch.bfloat16, device="meta")
        lens, ids = torch.empty(b+1, dtype=torch.int32, device="meta"), torch.empty(b, dtype=torch.int32, device="meta")
        if torch.ops.qwen36_damp.prepare(q, hi, pk, pv, inv, sr) is not None:
            raise RuntimeError("prepare Meta unexpectedly returned a value")
        out = torch.ops.qwen36_damp.decode(q, k, v, g, beta, hi, lo, sc, pk, pv, inv, sr, lens, ids)
        results = torch.ops.qwen36_damp_reference.decode(
            q, k, v, g, beta, torch.empty(b, 12, 128, 128, device="meta"), pk, pv, inv, sr)
        expected = [((b, 12, 128, 128), torch.float32),
                    ((b, 12, 128), torch.float32), ((b, 12, 128), torch.bfloat16)]
        if out.shape != (b, 12, 128) or out.dtype != torch.bfloat16:
            raise RuntimeError("candidate Meta output mismatch")
        if len(results) != 3 or any(x.device.type != "meta" or tuple(x.shape) != shape or
                                  x.dtype != dtype for x, (shape, dtype) in zip(results, expected)):
            raise RuntimeError("reference Meta output mismatch")
    return {"candidate": str(candidate), "prepare": str(prepare), "reference": str(reference)}


class Gate:
    def __init__(self, out, report):
        self.out, self.report = out, report
        self.fixture = {"stage": "preflight"}
        self.case = None

    def save(self):
        (self.out / "report.json").write_text(json.dumps(safe(self.report), indent=2,
                                                      allow_nan=False) + "\n")

    def retain(self):
        path = self.out / "first_failure.pt"
        if path.exists():
            return
        try:
            torch.save(cpu_clone(self.fixture), path)
            self.report["first_failure_fixture"] = {"path": str(path), "sha256": sha(path)}
        except BaseException as error:
            self.report["fixture_save_error"] = repr(error)

    def require(self, name, passed, details=None):
        self.report["checks"].append({"name": name, "passed": bool(passed), **(details or {})})
        self.save()
        if not passed:
            raise AssertionError(name)

    def start_case(self, stage, batch, variant):
        self.case = {"stage": stage, "batch": batch, "slots": batch+3,
                     "variant": (ANCHOR_VARIANTS if stage == "anchor" else GENERAL_VARIANTS)[variant],
                     "status": "running", "steps": []}
        self.report["cases"].append(self.case)
        self.save()

    def step(self, row):
        self.case["steps"].append(row)
        self.save()
        if not row["passed"]:
            self.case.update(status="failed", failed_step=row["step"])
            raise AssertionError(self.case["stage"] + " numerical/guard gate failed")

    def end_case(self):
        self.case["status"] = "passed"
        self.save()


def storage_disjoint(a, b):
    """Compare complete contiguous byte intervals, not only equal pointers."""
    if a.device != b.device:
        return True
    ab, bb = a.data_ptr(), b.data_ptr()
    ae, be = ab + a.numel()*a.element_size(), bb + b.numel()*b.element_size()
    return ae <= bb or be <= ab


def invoke_reference(gate, ref, inputs, selected, plans, sr, nd):
    tensors = list(inputs) + [nd(selected)] + list(plans) + [sr]
    before = [x.cpu().clone() for x in tensors]
    pointers = [x.data_ptr() for x in tensors]
    gate.fixture.update(reference_inputs_before=before,
                        reference_input_pointers_before=pointers)
    results = ref(*tensors)
    torch.npu.synchronize()
    # Retain actual returns and input-after BEFORE any format/finite/ABI gate.
    # A malformed or nonfinite return must not erase its original evidence.
    gate.fixture.update(reference_raw_outputs=cpu_clone(results),
                        reference_inputs_after=[x.cpu().clone() for x in tensors],
                        reference_input_pointers_after=[x.data_ptr() for x in tensors])
    b = selected.shape[0]
    expected = [((b, 12, 128, 128), torch.float32),
                ((b, 12, 128), torch.float32), ((b, 12, 128), torch.bfloat16)]
    if not isinstance(results, (tuple, list)) or len(results) != 3:
        raise RuntimeError("reference must return three tensors")
    from torch_npu import get_npu_format
    for output, (shape, dtype) in zip(results, expected):
        if get_npu_format(output) != 2:
            raise RuntimeError("reference output must use physical ND(2)")
        if tuple(output.shape) != shape or output.dtype != dtype:
            raise RuntimeError("reference output shape/dtype mismatch")
        if not bool(torch.isfinite(output.cpu()).all()):
            raise RuntimeError("reference output is nonfinite")
        if any(not storage_disjoint(output, x) for x in tensors):
            raise RuntimeError("reference output aliases input")
    if any(not storage_disjoint(results[i], results[j])
           for i in range(3) for j in range(i)):
        raise RuntimeError("reference output storage aliases other output")
    if pointers != [x.data_ptr() for x in tensors]:
        raise RuntimeError("reference input storage pointer changed")
    if not all(exact(x, y) for x, y in zip(tensors, before)):
        raise RuntimeError("reference mutated an input")
    if not exact(results[1].cpu().bfloat16(), results[2]):
        raise RuntimeError("reference output violates sole final BF16 cast")
    return [x.cpu().clone() for x in results]


def anchor_case(gate, native, ref, nd, torch_npu, batch, variant, steps):
    layout, original_transformed, generator = make_layout(batch, variant, "anchor")
    native_state = nd(original_transformed)
    reference_state = original_transformed.clone()  # Test-only uncompressed anchor.
    state_ptr = native_state.data_ptr()
    plans = [nd(x.int()) for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
    sr, lens = nd(layout.c), nd(torch.tensor([0]+[1]*batch, dtype=torch.int32))
    static, static_cpu = plans+[sr, lens], [x.cpu().clone() for x in plans+[sr, lens]]
    static_ptrs = [x.data_ptr() for x in static]
    gate.start_case("anchor", batch, variant)
    gate.case["initial_fixture_sha256"] = tensor_digest(
        [original_transformed, layout.c, layout.pk, layout.pv])
    gate.save()
    for index in range(steps):
        q, k, v, g, beta, ids = turn(batch, batch+3, index, generator, True)
        cast_ok, reordered_v = audit_cast(v, layout)
        native_before, reference_before = native_state.cpu().clone(), reference_state.clone()
        gate.fixture = {"stage": "native_reference_anchor", "batch": batch, "variant": variant,
                        "step": index+1, "layout": layout_dict(layout), "q": q, "k": k,
                        "v": v, "g": g, "beta": beta, "indices": ids,
                        "native_before": native_before, "reference_before": reference_before}
        gate.require("anchor_scaledV_BF16_exact", cast_ok)
        inputs = [nd(x) for x in (q, k, v, g, beta)]
        input_before = [x.cpu().clone() for x in inputs]
        input_ptrs = [x.data_ptr() for x in inputs]
        # Native NK=12 is a test-only expansion enabling arbitrary per-Hv Pk.
        # Model/production ABI stays HQ=4; every value head takes source h//3.
        expanded_q = q.repeat_interleave(3, 1).gather(
            2, layout.pk.long().unsqueeze(0).expand(batch, -1, -1))
        expanded_k = k.repeat_interleave(3, 1).gather(
            2, layout.pk.long().unsqueeze(0).expand(batch, -1, -1))
        nq, nk, nv, nids = [nd(x.contiguous()) for x in
                            (expanded_q, expanded_k, reordered_v.bfloat16(), ids)]
        native_inputs = [nq, nk, nv, inputs[3], inputs[4], lens, nids]
        native_inputs_before = [x.cpu().clone() for x in native_inputs]
        native_input_ptrs = [x.data_ptr() for x in native_inputs]
        native_out = native(nq, nk, nv, native_state, beta=inputs[4], scale=128**-0.5,
                            actual_seq_lengths=lens, ssm_state_indices=nids,
                            num_accepted_tokens=None, g=inputs[3], gk=None)
        torch.npu.synchronize()
        native_after = native_state.cpu().clone()
        gate.fixture.update(native_after=native_after, native_output_reordered=cpu_clone(native_out),
                            native_inputs_after=[x.cpu().clone() for x in native_inputs],
                            static_inputs_after=[x.cpu().clone() for x in static])
        updated, output_fp32, output_bf16 = invoke_reference(
            gate, ref, inputs, reference_state.index_select(0, ids.long()).contiguous(), plans, sr, nd)
        reference_state.index_copy_(0, ids.long(), updated)
        native_after = native_state.cpu().clone()
        # FP32-before-cast native readout is unavailable. Only power2 permits
        # this exact BF16-rounding commutation anchor, checked explicitly.
        inv = layout.pv.argsort(1).long().unsqueeze(0).expand(batch, -1, -1)
        restored_native = native_out.cpu().float().gather(2, inv) * layout.c.unsqueeze(0)
        restored_exact = exact(restored_native.bfloat16().float(), restored_native)
        untouched = [s for s in range(batch+3) if s not in ids.tolist()]
        state_metric = errors(native_after, reference_state)
        output_metric = errors(restored_native.bfloat16(), output_bf16)
        guards = {
            "native_untouched_bitwise": exact(native_after[untouched], native_before[untouched]),
            "reference_untouched_bitwise": exact(reference_state[untouched], reference_before[untouched]),
            "native_storage_stable": native_state.data_ptr() == state_ptr,
            "static_inputs_bitwise": all(exact(x, y) for x, y in zip(static, static_cpu)),
            "static_input_pointers_stable": static_ptrs == [x.data_ptr() for x in static],
            "reference_turn_inputs_bitwise": all(exact(x, y) for x, y in zip(inputs, input_before)),
            "reference_turn_input_pointers_stable": input_ptrs == [x.data_ptr() for x in inputs],
            "native_turn_inputs_bitwise": all(exact(x, y) for x, y in zip(native_inputs, native_inputs_before)),
            "native_turn_input_pointers_stable": native_input_ptrs == [x.data_ptr() for x in native_inputs],
            "native_restored_cast_exact": restored_exact,
            "native_output_ABI": native_out.shape == (batch, 12, 128) and native_out.dtype == torch.bfloat16,
            "native_output_ND": torch_npu.get_npu_format(native_out) == 2,
            "native_output_nonalias": all(storage_disjoint(native_out, x) for x in native_inputs+[native_state]),
            "complete_state_bitwise": exact(native_after, reference_state),
            "original_output_bitwise": exact(restored_native.bfloat16(), output_bf16),
        }
        gate.fixture.update(native_after=native_after, reference_after=reference_state,
                            native_output_reordered=native_out, native_output_restored=restored_native,
                            reference_updated_fp32=updated, reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=output_bf16)
        gate.step({"step": index+1, "indices": ids.tolist(),
                   "passed": all(guards.values()) and state_metric["finite"] and output_metric["finite"],
                   "turn_fixture_sha256": tensor_digest([q, k, v, g, beta, ids]),
                   "complete_transformed_state": state_metric, "original_output": output_metric,
                   "guards": guards})
    gate.end_case()


def invoke_prepare_guard(gate, prepare, inputs, arena):
    """Eager only: every prepare input plus all packed buffers stays bitwise."""
    if len(inputs) != len(PREPARE_INPUT_NAMES) or len(arena) != 3:
        raise RuntimeError("prepare guard expects six inputs and three packed regions")
    input_before = [x.cpu().clone() for x in inputs]
    arena_before = [x.cpu().clone() for x in arena]
    input_ptrs = [x.data_ptr() for x in inputs]
    arena_ptrs = [x.data_ptr() for x in arena]
    gate.fixture.update(prepare_inputs_before=dict(zip(PREPARE_INPUT_NAMES, input_before)),
                        prepare_arena_before=dict(zip(REGIONS, arena_before)))
    prepared = prepare(*inputs)
    torch.npu.synchronize()
    input_after = [x.cpu().clone() for x in inputs]
    arena_after = [x.cpu().clone() for x in arena]
    guards = {
        "prepare_returns_none": prepared is None,
        "all_six_prepare_inputs_bitwise": all(exact(x, y)
                                             for x, y in zip(input_after, input_before)),
        "all_three_packed_regions_bitwise": all(exact(x, y)
                                               for x, y in zip(arena_after, arena_before)),
        "all_six_prepare_input_pointers_stable": input_ptrs == [x.data_ptr() for x in inputs],
        "all_three_packed_storage_pointers_stable": arena_ptrs == [x.data_ptr() for x in arena],
    }
    gate.fixture.update(prepare_inputs_after=dict(zip(PREPARE_INPUT_NAMES, input_after)),
                        prepare_arena_after=dict(zip(REGIONS, arena_after)))
    gate.require("eager_prepare_all_inputs_immutable", all(guards.values()), {"guards": guards})


def general_case(gate, ref, nd, torch_npu, batch, variant, steps):
    layout, transformed, generator = make_layout(batch, variant, "general")
    golden = pack_value_major(transformed, layout)
    arena = [nd(x) for x in (golden.high, golden.low, golden.scales)]
    plans = [nd(x.int()) for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
    sr, lens = nd(layout.c), nd(torch.tensor([0]+[1]*batch, dtype=torch.int32))
    static, static_before = plans+[sr, lens], [x.cpu().clone() for x in plans+[sr, lens]]
    static_ptrs = [x.data_ptr() for x in static]
    pointers = [x.data_ptr() for x in arena]
    q0 = nd(torch.zeros(batch, 4, 128, dtype=torch.bfloat16))
    gate.start_case("general", batch, variant)
    gate.case["initial_fixture_sha256"] = tensor_digest(
        [golden.high, golden.low, golden.scales, layout.c, layout.pk, layout.pv])
    gate.save()
    gate.fixture = {"stage": "eager_prepare", "batch": batch, "variant": variant,
                    "layout": layout_dict(layout)}
    invoke_prepare_guard(gate, torch.ops.qwen36_damp.prepare,
                         [q0, arena[0], *plans, sr], arena)
    # No persistent FP32 candidate sidecar; drop initialization now.
    del transformed
    for index in range(steps):
        q, k, v, g, beta, ids = turn(batch, batch+3, index, generator, False)
        before = ValueMajorPacked(*[x.cpu().clone() for x in arena])
        golden_before = golden.clone()
        gate.fixture = {"stage": "general_sr_compressed_feedback", "batch": batch,
                        "variant": variant, "step": index+1, "layout": layout_dict(layout),
                        "q": q, "k": k, "v": v, "g": g, "beta": beta, "indices": ids,
                        "candidate_before": packed_dict(before), "reference_before": packed_dict(golden_before)}
        inputs, nids = [nd(x) for x in (q, k, v, g, beta)], nd(ids)
        input_before = [x.cpu().clone() for x in inputs]
        input_ptrs = [x.data_ptr() for x in inputs] + [nids.data_ptr()]
        # Reference starts ONLY from its own independently quantized feedback.
        selected = unpack_value_major(golden, layout).index_select(0, ids.long()).contiguous()
        updated, output_fp32, expected_output = invoke_reference(gate, ref, inputs, selected, plans, sr, nd)
        selected_packed = pack_value_major(updated, layout)
        boundary = half_cell_evidence(updated, selected_packed, layout)
        for name in REGIONS:
            getattr(golden, name).index_copy_(0, ids.long(), getattr(selected_packed, name))
        output = torch.ops.qwen36_damp.decode(*inputs, *arena, *plans, sr, lens, nids)
        torch.npu.synchronize()
        actual = ValueMajorPacked(*[x.cpu().clone() for x in arena])
        # Save raw packed-after/output BEFORE unpack/restore can reject corrupt
        # scales or codes. The first failure must preserve the candidate bytes.
        gate.fixture.update(candidate_after=packed_dict(actual), candidate_output=cpu_clone(output),
                            reference_after=packed_dict(golden), reference_updated_fp32=updated,
                            reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=expected_output,
                            candidate_inputs_after=[x.cpu().clone() for x in inputs]+[nids.cpu().clone()],
                            static_inputs_after=[x.cpu().clone() for x in static],
                            reference_pre_RINT=boundary)
        untouched = [s for s in range(batch+3) if s not in ids.tolist()]
        actual_dense = restore_state(unpack_value_major(actual, layout), layout)
        expected_dense = restore_state(unpack_value_major(golden, layout), layout)
        selected_state_metric = errors(actual_dense.index_select(0, ids.long()),
                                       expected_dense.index_select(0, ids.long()))
        complete_state_metric = errors(actual_dense, expected_dense)
        output_metric = errors(output, expected_output)
        guards = {
            "candidate_untouched_bitwise": all(exact(getattr(actual, n)[untouched],
                                    getattr(before, n)[untouched]) for n in REGIONS),
            "reference_untouched_bitwise": all(exact(getattr(golden, n)[untouched],
                                    getattr(golden_before, n)[untouched]) for n in REGIONS),
            "storage_pointers_stable": pointers == [x.data_ptr() for x in arena],
            "static_inputs_bitwise": all(exact(x, y) for x, y in zip(static, static_before)),
            "static_input_pointers_stable": static_ptrs == [x.data_ptr() for x in static],
            "turn_inputs_bitwise": all(exact(x, y) for x, y in zip(inputs, input_before)),
            "turn_input_pointers_stable": input_ptrs == [x.data_ptr() for x in inputs]+[nids.data_ptr()],
            "indices_bitwise": exact(nids, ids),
            "output_ABI": output.shape == (batch, 12, 128) and output.dtype == torch.bfloat16,
            "output_ND": torch_npu.get_npu_format(output) == 2,
            "output_nonalias": all(storage_disjoint(output, x) for x in arena+inputs+static+[nids]),
            "reference_SR_general": bool((layout.c > 0).all()) and bool(torch.isfinite(layout.c).all()),
        }
        passed = (all(guards.values()) and selected_state_metric["finite"] and
                  complete_state_metric["finite"] and output_metric["finite"] and
                  selected_state_metric["max_head_relative_l2"] <= LIMITS["state"] and
                  complete_state_metric["max_head_relative_l2"] <= LIMITS["state"] and
                  output_metric["max_head_relative_l2"] <= LIMITS["output"])
        gate.fixture.update(candidate_after=packed_dict(actual), reference_after=packed_dict(golden),
                            reference_updated_fp32=updated, reference_original_output_fp32=output_fp32,
                            reference_original_output_bf16=expected_output, candidate_output=output,
                            reference_pre_RINT=boundary)
        gate.step({"step": index+1, "indices": ids.tolist(), "passed": passed,
                   "turn_fixture_sha256": tensor_digest([q, k, v, g, beta, ids]),
                   "selected_original_state": selected_state_metric,
                   "complete_original_state": complete_state_metric, "output": output_metric,
                   "guards": guards,
                   "reference_half_cell": {k: x for k, x in boundary.items() if k != "quotient_fp32"},
                   "packed_bitwise_diagnostic": {n: exact(getattr(actual, n), getattr(golden, n))
                                                for n in REGIONS}})
        # selected/update/restore tensors are temporary test diagnostics, never feedback.
        del selected, updated, actual_dense, expected_dense
    gate.end_case()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--audit-only", action="store_true", help="CPU fixture software audit; no NPU imports/loads")
    parser.add_argument("--anchor-only", action="store_true",
                        help="NEW native/reference anchors only; never dispatch compressed candidate")
    parser.add_argument("--steps", type=int, default=STEPS)
    parser.add_argument("--operator-library", type=Path)
    parser.add_argument("--operator-sha256")
    parser.add_argument("--reference-library", type=Path)
    parser.add_argument("--reference-sha256")
    parser.add_argument("--device-proof", type=Path)
    parser.add_argument("--native-source-manifest", type=Path)
    parser.add_argument("--native-source-manifest-sha256")
    parser.add_argument("--native-gdn-source", type=Path,
                        default=Path("/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"))
    parser.add_argument("--native-gdn-source-sha256", default=GDN_SHA)
    args = parser.parse_args()
    if args.audit_only and args.anchor_only:
        parser.error("--audit-only and --anchor-only are separate evidence stages")
    out = args.output_dir.resolve()
    if out.exists() or out == REPO or REPO in out.parents:
        parser.error("require a NEW output root outside repository")
    if not 1 <= args.steps <= STEPS:
        parser.error("steps must be 1..160; <160 is smoke-only")
    if not args.audit_only:
        if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
            parser.error("logical0 only; parent must freshly prove physical4 binding")
        if os.environ.get("DAMP_ENABLE_NATIVE_REFERENCE") != "1":
            parser.error("explicit DAMP_ENABLE_NATIVE_REFERENCE=1 required")
        for name in ("operator_library", "reference_library", "device_proof", "native_source_manifest"):
            value = getattr(args, name)
            if value is None or not value.is_file():
                parser.error("require existing --" + name.replace("_", "-"))
        for name in ("operator_sha256", "reference_sha256", "native_source_manifest_sha256"):
            value = getattr(args, name)
            if value is None or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                parser.error("require lowercase SHA256 --" + name.replace("_", "-"))
    out.mkdir(parents=True, exist_ok=False)
    report = {"schema": "damp-general-sr-native-derived/v1", "status": "running",
              "created_ns": time.time_ns(), "artifact_root": str(out), "seed": SEED,
              "steps": args.steps, "matrix_class": "full-160" if args.steps == STEPS else "smoke-only",
              "mode": "fixture-audit-only" if args.audit_only else "actual-npu",
              "anchor_only": args.anchor_only, "compressed_candidate_dispatched": False,
              "anchor_gate": "NEW strict bitwise complete transformed FP32 state and restored BF16 output",
              "limits": LIMITS, "checks": [], "cases": [], "versions": {"torch": torch.__version__},
              "source_hashes": {p.name: sha(p) for p in
                (Path(__file__), HERE/"general_sr_contract.py", HERE/"independent_oracle.py", HERE/"native_call_contract.py")},
              "scope": "synthetic general positive FP32 SR, eager single-token B1/B16, independent "
                "compressed feedback; NOT calibrated192plans, graph, mixed turns, allocator, TP4 "
                "serving, performance or GSM8K/LongBench-v2 accuracy",
              "calibrated_plan_count": 0,
              "precision": "original BF16 V -> FP32 Div(V,c) -> Pv; native source arithmetic; "
                "FP32 readout -> inversePv * original c -> sole BF16 cast; pack updated FP32 afterwards",
              "feedback": "own independent packed reference / own mutable candidate packed arena; no step resync",
              "source_provenance_authority": "pinned parent source/build manifest + actual loaded ELF paths/hashes"}
    gate = Gate(out, report)
    gate.save()
    try:
        torch.set_num_threads(1)
        audited = 0
        for b in (1, 16):
            for variant in range(len(ANCHOR_VARIANTS)):
                layout, _, generator = make_layout(b, variant, "anchor")
                for index in range(args.steps):
                    v = turn(b, b+3, index, generator, True)[2]
                    gate.fixture = {"stage": "fixture_audit", "batch": b, "variant": variant,
                                    "step": index+1, "layout": layout_dict(layout), "v": v}
                    valid, _ = audit_cast(v, layout)
                    gate.require("anchor_fixture_scaledV_BF16_exact", valid)
                    audited += 1
        report["fixture_audit"] = {"anchor_turns": audited, "exact_scaledV_BF16": True}
        if args.audit_only:
            report["status"] = "fixture_software_audit_pass"
            return
        gate.fixture = {"stage": "runtime_preflight"}
        for path, expected in ((args.operator_library, args.operator_sha256),
                               (args.reference_library, args.reference_sha256),
                               (args.native_source_manifest, args.native_source_manifest_sha256),
                               (args.native_gdn_source, args.native_gdn_source_sha256)):
            gate.require("pinned_hash_" + path.name, sha(path) == expected)
        manifest = json.loads(args.native_source_manifest.read_text())
        validate_source_manifest(manifest, REFERENCE_HASHES, CANDIDATE_HASHES)
        for name, expected in REFERENCE_HASHES.items():
            gate.require("reference_source_" + name, sha(PROJECT/"operator/reference"/name) == expected)
        for name, expected in CANDIDATE_HASHES.items():
            gate.require("candidate_source_" + name, sha(PROJECT/"operator"/name) == expected)
        device = json.loads(args.device_proof.read_text())
        validate_device_proof(device, time.time_ns())
        report["device_proof"] = {"path": str(args.device_proof), "sha256": sha(args.device_proof),
                                  "content": device, "authority": "external launcher, not independent host proof"}
        report["native_source_manifest"] = {"path": str(args.native_source_manifest),
            "sha256": sha(args.native_source_manifest), "content": manifest}
        report["libraries"] = {"candidate": {"path": str(args.operator_library.resolve()),
              "sha256": sha(args.operator_library)}, "reference": {"path": str(args.reference_library.resolve()),
              "sha256": sha(args.reference_library)}}
        import torch_npu
        from vllm_ascend.utils import enable_custom_op
        torch_npu.npu.set_compile_mode(jit_compile=False)
        if not enable_custom_op():
            raise RuntimeError("native bootstrap unavailable")
        torch.npu.set_device(0)
        torch.ops.load_library(str(args.operator_library.resolve()))
        torch.ops.load_library(str(args.reference_library.resolve()))
        report["schemas"] = schema_contract()
        native = torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        report["native_schema"] = str(native.default._schema)
        report["native_call_contract"] = validate_native_schema(native.default._schema)
        report["versions"]["torch_npu"] = torch_npu.__version__
        report["CANN_files"] = [{"path": str(p), "sha256": sha(p),
              "content": p.read_text(errors="replace")[:4096]} for p in
            (Path("/usr/local/Ascend/cann-9.1.0/version.cfg"),
             Path("/usr/local/Ascend/ascend-toolkit/latest/version.cfg"),
             Path("/usr/local/Ascend/ascend-toolkit/latest/opp/version.info")) if p.is_file()]
        libraries = [args.operator_library, args.reference_library]
        report["loaded_libraries_before"] = loaded_libraries(libraries)
        gate.save()
        def nd(x):
            result = torch_npu.npu_format_cast(x.to("npu:0").contiguous(), 2)
            if torch_npu.get_npu_format(result) != 2:
                raise RuntimeError("physical ND(2) required")
            return result
        ref = torch.ops.qwen36_damp_reference.decode
        # ALL anchors finish before ANY compressed candidate recurrence.
        for b in (1, 16):
            for variant in range(len(ANCHOR_VARIANTS)):
                anchor_case(gate, native, ref, nd, torch_npu, b, variant, args.steps)
                report["loaded_libraries_after_anchor"] = loaded_libraries(libraries)
                verify_loaded_binding(report["loaded_libraries_after_anchor"], manifest,
                    [(args.operator_library, args.operator_sha256),
                     (args.reference_library, args.reference_sha256)])
        assert_matrix_order(report["cases"], require_complete_anchor=True)
        gate.require("all_native_reference_anchors_passed", all(
            c["status"] == "passed" for c in report["cases"]))
        if args.anchor_only:
            report["status"] = ("native_reference_anchors_pass" if args.steps == STEPS
                                else "native_reference_anchors_smoke_pass")
            return
        report["compressed_candidate_dispatched"] = True
        for b in (1, 16):
            for variant in range(len(GENERAL_VARIANTS)):
                general_case(gate, ref, nd, torch_npu, b, variant, args.steps)
        assert_matrix_order(report["cases"], require_complete_anchor=True)
        report["status"] = "synthetic_general_sr_numerical_pass" if args.steps == STEPS else "synthetic_general_sr_smoke_pass"
    except BaseException as error:
        if gate.case is not None and gate.case["status"] == "running":
            gate.case.update(status="failed", error=repr(error))
        report.update(status="failed", error=repr(error), error_type=type(error).__name__,
                      traceback=traceback.format_exc())
        gate.retain()
        raise
    finally:
        report["completed_ns"] = time.time_ns()
        if not args.audit_only and args.operator_library is not None and args.reference_library is not None:
            try:
                report["loaded_libraries_final"] = loaded_libraries(
                    [args.operator_library, args.reference_library])
            except BaseException as error:
                report["library_snapshot_error"] = repr(error)
        try:
            gate.save()
        except BaseException as error:
            print("secondary report-save error: " + repr(error), file=sys.stderr)
        if report["status"] != "failed":
            print(json.dumps({"status": report["status"], "report": str(out/"report.json")}))


if __name__ == "__main__":
    main()
