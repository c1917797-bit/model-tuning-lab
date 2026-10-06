"""Default-OFF selected-slot native reference seam; no framework import at module load.

This is a test-harness adapter, not production cache or performance evidence.
MAIN owns source admission, loaded-library proof, physical mapping and execution.
"""
import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import traceback

REGIONS = ("high", "low", "scales")
FIELDS = ("original_output_bf16", "native_output_reordered_bf16",
          "restored_fp32_after_native_bf16_cast", "native_updated_selected_fp32",
          "transformed_value_bf16")
BASE_PATH = "projects/damp-ascend/tools/independent_allT_dispatch_v1/reference_seam.py"
FROZEN_PATH = "projects/damp-ascend/tests/native_compressed_golden.py"
HERE = Path(__file__).resolve().parent

class Pending(RuntimeError):
    pass

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_bindings(repo_root, manifest_sha256):
    root = Path(repo_root).resolve()
    path = HERE / "SOURCE_MANIFEST.json"
    if sha(path) != manifest_sha256:
        raise Pending("NEW source manifest identity differs")
    manifest = json.loads(path.read_text())
    if (manifest.get("schema") != "damp-selected-row-reference-source/v1" or
            manifest.get("default_enabled") is not False or
            manifest.get("npu_executed") is not False):
        raise Pending("prepared source manifest is not NPU authority")
    checked = {}
    for relative, expected in {**manifest["sources"], **manifest["dependencies"]}.items():
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or sha(target) != expected:
            raise Pending("source drift: " + relative)
        checked[relative] = expected
    return {"path": str(path), "sha256": manifest_sha256, "sources": checked,
            "npu_executed": False, "serving_ready": False}

def equivalence_plan(batches):
    batches = tuple(batches)
    if not batches or len(set(batches)) != len(batches) or any(
            type(t) is not int or not 1 <= t <= 16 for t in batches):
        raise Pending("explicit distinct true T1..16 required")
    return [{"batch": t, "slots": t+3, "variant": variant, "fixture_index": index,
             "original_slot": slot, "local_slots": 1, "local_index": 0}
            for t in batches for variant in (0, 1) for index in (0, 7, 159)
            for slot in (0, t+2)]

def _put_failure(gate, record, primary):
    # Record the same raised exception BEFORE secondary retention. No retry.
    record["primary_error"] = {"type": type(primary).__name__, "error": repr(primary),
                               "traceback": traceback.format_exc()}
    try:
        if record is not gate.fixture:
            gate.fixture["selected_row_last"] = record
        gate.retain()
    except BaseException as secondary:
        record["retention_error"] = repr(secondary)
        try:
            primary.add_note("secondary selected-row retention error: " + repr(secondary))
        except BaseException:
            pass

def _packed_exact(p, left, right):
    return all(p.exact(getattr(left, n), getattr(right, n)) for n in REGIONS)

def _selected(packed, index, packed_type):
    return packed_type(*(getattr(packed, n).index_select(0, index).clone()
                         for n in REGIONS))

def _merge(working, row_before, local_before, local_after, original_index, p):
    if any(getattr(local_after, n).shape != getattr(local_before, n).shape
           or getattr(local_after, n).dtype != getattr(local_before, n).dtype
           for n in REGIONS):
        raise AssertionError("local packed result ABI differs")
    for n in REGIONS:
        getattr(working, n).index_copy_(0, original_index, getattr(local_after, n))
    slot = int(original_index.tolist()[0])
    untouched = [s for s in range(working.high.shape[0]) if s != slot]
    guards = {
        "original_CPU_other_slots_bitwise": all(p.exact(getattr(working, n)[untouched],
                                        getattr(row_before, n)[untouched]) for n in REGIONS),
        "original_CPU_selected_equals_local": all(p.exact(
            getattr(working, n).index_select(0, original_index), getattr(local_after, n))
            for n in REGIONS)}
    if not all(guards.values()):
        raise AssertionError("selected-slot CPU merge changed original address mapping")
    return guards

def selected_compose(reference, before, layout, q, k, v, g, beta, ids, native, device):
    """OWN CPU feedback; actual native receives ONLY selected state/INT32[0].

    The full-pool CPU validation is retained once per call. Frozen helper math,
    quantizer and actual native function are unchanged. No candidate result is
    read or used as oracle input. Empty local untouched != observed full NPU pool.
    """
    p, torch, frozen, gate = reference.protocols, reference.torch, reference.frozen, reference.gate
    batch, slots = q.shape[0], before.high.shape[0]
    if (type(batch) is not int or not 1 <= batch <= 16 or ids.device.type != "cpu" or
            ids.shape != (batch,) or ids.dtype not in (torch.int32, torch.int64)):
        raise ValueError("CPU true-T inputs and integer slot vector required")
    original_ids = ids.long()
    values = original_ids.tolist()
    if len(set(values)) != batch or any(s < 0 or s >= slots for s in values):
        raise ValueError("all original slots unique/in-range BEFORE native calls")
    # Preserve old rejection of invalid UNSELECTED hi/scales/-128, not merely
    # selected-state checks. This function is independent frozen oracle code.
    validated = frozen.unpack_value_major(before, layout)
    if validated.shape != (slots, 12, 128, 128):
        raise ValueError("full CPU state ABI differs")
    del validated
    full_before = before.clone()
    working = before.clone()
    rows, summaries = [], []
    for row, slot in enumerate(values):
        original_index = torch.tensor([slot], dtype=torch.long)
        row_before = working.clone()
        local = _selected(working, original_index, frozen.ValueMajorPacked)
        local_before = local.clone()
        local_ids = torch.tensor([0], dtype=torch.int32)
        record = {"row": row, "original_slot": slot, "original_slots": slots,
                  "local_slots": 1, "local_ids": local_ids.clone(),
                  "original_row_before": p.packed_dict(row_before),
                  "local_before": p.packed_dict(local_before),
                  "local_untouched_count": 0,
                  "local_untouched_scope": "empty local allocation; NOT full original NPU pool"}
        # CPU clones are in-memory until original Gate.retain/anchor torch.save.
        # A process kill can lose the current row; no per-row durable promise.
        gate.fixture["selected_row_last"] = record
        try:
            evidence = frozen.step(local, layout, q[row:row+1], k[row:row+1],
                v[row:row+1], g[row:row+1], beta[row:row+1], local_ids,
                reference._native(native), device)
            record["local_after"] = p.packed_dict(evidence["packed"])
            record["native_evidence"] = {n: evidence[n] for n in FIELDS}
            if not _packed_exact(p, local, local_before):
                raise AssertionError("frozen helper changed its readonly local CPU input")
            guards = _merge(working, row_before, local_before, evidence["packed"], original_index, p)
            if any(evidence[n] is not True for n in (
                    "value_cast_exact", "restored_cast_exact", "native_fp32_untouched_exact")):
                raise AssertionError("frozen local numerical/cast guard failed")
            record.update(original_row_after=p.packed_dict(working), guards=guards)
            rows.append(evidence)
            summaries.append({"row": row, "original_slot": slot, "local_index": 0,
                "local_untouched_count": 0, "guards": guards})
        except BaseException as primary:
            # Preserve the exact exception propagated by the frozen helper and
            # any raw fields it retained. Its internal secondary-copy limitation
            # is unchanged; this adapter cannot reconstruct a hidden exception.
            _put_failure(gate, record, primary)
            raise
    if not _packed_exact(p, before, full_before):
        raise AssertionError("source full CPU before trajectory was mutated")
    result = {"packed": working}
    for name in FIELDS:
        result[name] = torch.cat([r[name] for r in rows], dim=0)
    for name in ("value_cast_exact", "restored_cast_exact"):
        result[name] = all(r[name] is True for r in rows)
    # Backward-compatible logical unchanged flag, with explicit stronger scope:
    # local actual native unchanged check + original complete CPU merge proof.
    # This does not claim original unselected pool was an NPU input.
    result["native_fp32_untouched_exact"] = all(
        r["native_fp32_untouched_exact"] is True for r in rows) and all(
        all(s["guards"].values()) for s in summaries)
    result["selected_row_reference"] = {
        "schema": "damp-selected-row-reference/v1",
        "full_CPU_before_validation": True, "source_before_CPU_immutable": True,
        "original_CPU_all_other_slots_bitwise": True, "rows": summaries,
        "native_untouched_observation": "S1 empty set; full original pool remains CPU",
        "general_sr_supported": False, "production_cache_supported": False}
    result["scope"] = "restricted native local-S1 own-feedback; full CPU slot merge"
    gate.fixture["selected_row_reference"] = result["selected_row_reference"]
    return result

def build_reference(gate, protocols, frozen_native, torch, torch_npu,
                    repo_root, manifest_sha256, *, enabled=False):
    if enabled is not True:
        raise Pending("default OFF; MAIN must explicitly inject reviewed reference")
    identity = source_bindings(repo_root, manifest_sha256)
    root = Path(repo_root).resolve()
    if Path(inspect.getsourcefile(frozen_native.step) or "").resolve() != root/FROZEN_PATH:
        raise Pending("frozen native helper actual source differs")
    expected_protocols = root / "projects/damp-ascend/operator/production_integer_compaction_v1/tests/protocols.py"
    if Path(getattr(protocols, "__file__", "")).resolve() != expected_protocols:
        raise Pending("actual protocols module source differs")
    base_path = root/BASE_PATH
    spec = importlib.util.spec_from_file_location("_damp_selected_row_frozen_base", base_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # Frozen seam imports ONLY stdlib types.
    base = module.NativeRows
    if base._rows.__module__ != module.__name__:
        raise Pending("frozen _rows owner differs")
    class SelectedRows(base):
        def __init__(self, *args):
            super().__init__(*args)
            self.selected_row_identity = identity
            self.local_equivalence_passed = False
            self.equivalence_batches = ()
        def assert_sources(self):
            if source_bindings(repo_root, manifest_sha256) != identity:
                raise Pending("source identity changed during selected-row gate")
        def _rows(self, *args):
            return selected_compose(self, *args)
        def step(self, *args):
            if not self.local_equivalence_passed or args[2].shape[0] not in self.equivalence_batches:
                raise Pending("actual full-S/local-S1 gate for this true T remains pending")
            return super().step(*args)
        def run_equivalence(self, native, batches, device="npu:0"):
            return run_equivalence(self, native, batches, device)
    return SelectedRows(gate, protocols, frozen_native, torch, torch_npu)

def run_equivalence(reference, native, batches, device="npu:0"):
    """192 full-S B1/local-S1 pairs (48/shard), BEFORE original six anchors.

    MAIN must already prove actual native schema/library/maps/SoC/resource/route.
    No SO is loaded or device acquired by this module. Whole-call failures abort.
    """
    batches = tuple(batches)
    plan = equivalence_plan(batches)
    reference.assert_sources()
    reference.local_equivalence_passed = False
    reference.equivalence_batches = ()
    torch, p, gate = reference.torch, reference.protocols, reference.gate
    records = []
    # same generator order per T/variant; actual B1 operands, not PAD16.
    for batch in batches:
        for variant in (0, 1):
            layout, initial, generator = p.restricted.layouts(batch, variant)
            for index in (0, 7, 159):
                for slot in (0, batch+2):
                    fixture = list(p.restricted.turn(1, batch+3, index, generator))
                    fixture[5] = torch.tensor([slot], dtype=torch.int32)
                    before = initial.clone()
                    gate.fixture = {"stage": "full_S_B1_vs_local_S1", "batch_geometry": batch,
                        "variant": variant, "fixture_index": index, "original_slot": slot,
                        "before": p.packed_dict(before),
                        "fixture_cpu": [x.clone() for x in fixture], "layout": p.layout_dict(layout)}
                    path = gate.out / ("selected-row-before-T%d-v%d-i%d-s%d.pt" %
                                        (batch, variant, index, slot))
                    if path.exists():
                        raise ValueError("never overwrite equivalence raw-before")
                    torch.save(gate.fixture, path)  # Durable BEFORE either native call.
                    raw_before = {"path": str(path), "sha256": sha(path)}
                    reference.guard_records = []
                    try:
                        full = reference.frozen.step(before.clone(), layout, *fixture,
                            reference._native(native), device)
                        local = selected_compose(reference, before.clone(), layout, *fixture, native, device)
                        full_fp32 = reference.frozen.unpack_value_major(before, layout)
                        local_fp32 = full_fp32.clone()
                        full_fp32.index_copy_(0, fixture[5].long(), full["native_updated_selected_fp32"])
                        local_fp32.index_copy_(0, fixture[5].long(), local["native_updated_selected_fp32"])
                        guards = {"complete_FP32_state_bitwise": p.exact(full_fp32, local_fp32),
                            "complete_packed_bitwise": _packed_exact(p, full["packed"], local["packed"]),
                            "selected_FP32_bitwise": p.exact(full["native_updated_selected_fp32"],
                                                           local["native_updated_selected_fp32"]),
                            "original_BF16_bitwise": p.exact(full["original_output_bf16"],
                                                          local["original_output_bf16"]),
                            "all_native_calls_guards": len(reference.guard_records) == 2 and
                                all(all(g.values()) for g in reference.guard_records),
                            "full_native_untouched_bitwise": full["native_fp32_untouched_exact"] is True,
                            "original_CPU_merge_bitwise": local["selected_row_reference"][
                                "original_CPU_all_other_slots_bitwise"] is True}
                        guards.update({n+"_bitwise": p.exact(full[n], local[n]) for n in FIELDS})
                        record = {"batch": batch, "slots": batch+3, "variant": variant,
                            "fixture_index": index, "original_slot": slot, "local_index": 0,
                            "passed": all(guards.values()), "guards": guards, "raw_before": raw_before}
                        gate.fixture.update(full_result=full, local_result=local,
                            complete_FP32_full=full_fp32, complete_FP32_local=local_fp32, guards=guards)
                        records.append(record)
                        gate.require("selected_row_equivalence_%d_%d_%d_%d" %
                                     (batch, variant, index, slot), record["passed"], record)
                    except BaseException as primary:
                        _put_failure(gate, gate.fixture, primary)
                        raise
    if len(records) != len(plan) or not all(r["passed"] for r in records):
        raise AssertionError("full-S/local-S1 numerical gate incomplete")
    reference.assert_sources()
    gate.report["selected_row_equivalence"] = {"schema": "damp-selected-row-equivalence/v1",
        "status": "restricted_fullS_localS1_bitwise_pass", "pair_count": len(records),
        "batches": list(batches), "cases": records, "source_identity": reference.selected_row_identity,
        "npu_executed": True, "general_sr_supported": False, "serving_ready": False,
        "performance_measurement_admitted": False}
    try:
        gate.save()
    except BaseException as primary:
        _put_failure(gate, gate.fixture, primary)
        raise
    reference.equivalence_batches = batches
    reference.local_equivalence_passed = True
    return gate.report["selected_row_equivalence"]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--batches", nargs="+", type=int, required=True)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--gate-plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if args.execute:
        raise Pending("NPU CLI consumer/proof bridge must be reviewed by MAIN; this module never self-dispatches")
    if not args.audit_only and not args.gate_plan:
        raise Pending("default OFF; request source audit or exact gate plan")
    bound = source_bindings(args.repo_root, args.source_manifest_sha256)
    plan = equivalence_plan(args.batches)
    print(json.dumps({"schema": "damp-selected-row-preparation/v1",
        "source_identity": bound, "pair_count": len(plan), "pairs": plan,
        "npu_executed": False, "serving_ready": False, "launchable": False}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
