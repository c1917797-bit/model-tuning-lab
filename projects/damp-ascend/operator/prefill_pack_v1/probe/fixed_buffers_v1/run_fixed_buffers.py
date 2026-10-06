"""NEW default-dry eager fixed-address changing-input gate; MAIN alone runs NPU."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

BASE = Path(__file__).resolve().parent
PROBE = BASE.parent
REPO = BASE.parents[5]
PROJECT = REPO / "projects/damp-ascend"
NAMESPACE = "qwen36_damp_prefill_float_probe"
COUNTS = (64, 896)
TURNS = 20
REPEATS = 8
OWN_NAMES = ("run_fixed_buffers.py", "test_fixed_buffers.py", "READY.md")
FROZEN = {
    "projects/damp-ascend/operator/prefill_pack_v1/exact_float_div_bits.h": "bca2ab982ac57ebed71efa4145281b5ee37faa5ec46cc0beccddf9d83eb2ae04",
    "projects/damp-ascend/operator/prefill_pack_v1/independent_float_div.py": "5d0e489be5936adf2adac537c8a204d02851116f7d2d34a31b06a56b8cc88df4",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/CMakeLists.txt": "9f8ca19fbac4f959a910aafc89001a161ad1858a1a8607d1fec74dda53a76c86",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/README.md": "ed3b9ce83b066df402e232ab48eb6d6cb6c291486166bd88d5d77f643474ef54",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/cases.py": "b87aceacdef1ed99674fdef16dd83f45d164181f20a0c08b8163ace53a626c9b",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_extension/float_div_torch.cpp": "b3445859b0f6bb4ce122d345e8dad9287588f547897d1b1a0103e3eb8159fffc",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_extension/ops.h": "73d79931312ad87b7f8128f544a5a8dc67f539457133fde639d471d23740643a",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_extension/register.cpp": "3c88b9ce99649b1fae7a96b5e979118ede8e5ef0846aba53f50916a9d9591c8a",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_kernel/float_div_probe.h": "771286de9da81c4bae193b43d6add505d2008f2ee6d7c30bacd83bfa09d06e03",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_kernel/float_div_probe_kernel.asc": "7e8c7c49f4752b0f67f2d9c0a52c1f0ba20f0bd7dc25feac29dffc2cadbbc22e",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/op_kernel/probe_plan.h": "2e73d7499a13325baa64b9161a8e60df5321fa8843908c95bfe69ed134b2bd0c",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/run_float_gate.py": "41d2fe741e27718f40207e560d3d1d1415cef3f5db49fc19fe2e0fb09338c702",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/test_software_contract.py": "311cc2215858d2b693913bb96c0441b7d7a790300fc0953ec09c2e5a7e5b0ff9",
    "projects/damp-ascend/operator/quantizer/exact_quantizer_bits.h": "f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169",
    "projects/damp-ascend/tests/all_batch_gate_v1/contract.py": "f42a42ce36dc18cb65381f00ac3a4737cb8b50dbf50b22bf90a719dd800d87fd",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/source_manifest.json": "e8e1bd5f29b219b68351834da02c5385925ce51d86edfd27be304c1ef140817c",
    "projects/damp-ascend/operator/prefill_pack_v1/probe/runtime_manifest.json": "bfc7d359ad444ad22dc99915f9372b543beef8d3ac568c2e96bb48c22554f1f1"
}
SCHEMA = "damp-prefill-fixed-buffers-runtime/v1"
MANIFEST = BASE / "runtime_manifest.json"
OLD_SOURCE = PROBE / "source_manifest.json"
OLD_RUNTIME = PROBE / "runtime_manifest.json"

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def row_fingerprints(rows):
    return tuple(hashlib.sha256(json.dumps([r[key] for r in rows],
                 separators=(",", ":")).encode()).hexdigest()
                 for key in ("x", "c", "proposal"))

def validate_rows(rows, count, gold):
    require(type(count) is int and count in COUNTS and len(rows) == count, "exact fixture N")
    for row in rows:
        require(isinstance(row, dict), "fixture row object")
        for key in ("x", "c", "proposal"):
            require(type(row.get(key)) is int and 0 <= row[key] <= 0xffffffff,
                    "raw fixture UINT32 " + key)
        valid, finite, bits = gold.oracle(row["x"], row["c"])
        accepted = gold.oracle_certificate(row["x"], row["c"], row["proposal"])
        expected = dict(valid=int(valid), finite=int(finite), bits=bits, accepted=int(accepted))
        require(all(type(row.get(k)) is int and row[k] == value
                    for k, value in expected.items()), "incorrect independent fixture golden")
        require(isinstance(row.get("label"), str), "fixture label")
    return row_fingerprints(rows)

def changing_fixture(count, turn, cases, gold):
    require(type(turn) is int and 0 <= turn < TURNS, "registered turn")
    rows = cases.changing_rows(count, turn)
    # Every turn also exercises un-clipped overflow, signed zero, subnormal,
    # binade/normal boundary and invalid input flags in the SAME buffers.
    edges = ((0, 0x3f800000), (0x80000000, 0x3f800000),
             (1, 0x40000000), (0x80000001, 0x40000000),
             (0x007fffff, 0x3f800001), (0x00800000, 0x3f8ccccd),
             (0x3f800001, 0x3f8ccccd), (0xbf800001, 0x3f8ccccd),
             (0x7f7fffff, 1), (0xff7fffff, 1),
             (0x7f7fffff, 0x7f7fffff), (0x7f800000, 0x3f800000),
             (0x7fc00001, 0x3f800000), (1, 0), (1, 0x80000000),
             (1, 0x7fc00000))
    for lane in range(len(edges)):
        x, c = edges[(lane + turn) % len(edges)]
        valid, finite, bits = gold.oracle(x, c)
        magnitude = bits & 0x7fffffff
        proposal = magnitude if (lane + turn) % 3 else min(gold.INF, magnitude + 1)
        rows[lane] = dict(x=x, c=c, proposal=proposal, valid=int(valid),
                         finite=int(finite), bits=bits,
                         accepted=int(gold.oracle_certificate(x, c, proposal)),
                         label="fixed-buffer-edge-" + str((lane + turn) % len(edges)))
    return rows

def source_snapshot(args):
    """Best-effort immutable-file observation, including failed admission."""
    table = dict(FROZEN)
    manifest_error = None
    try:
        document = json.loads(MANIFEST.read_text())
        names = {str(BASE.relative_to(REPO) / name) for name in OWN_NAMES}
        own = document.get("sources", {})
        require(isinstance(own, dict) and set(own) == names, "exact NEW source3")
        for name, digest in own.items():
            require(isinstance(digest, str) and len(digest) == 64, "NEW source digest")
            table[name] = digest
    except BaseException as error:
        manifest_error = repr(error)
        for name in OWN_NAMES:
            table[str(BASE.relative_to(REPO) / name)] = None
    table[str(MANIFEST.relative_to(REPO))] = args.fixed_manifest_sha256
    observations = []
    for name, expected in sorted(table.items()):
        path = REPO / name
        record = dict(path=str(path), expected_sha256=expected, actual_sha256=None,
                      matched=False, error=None)
        try:
            record.update(actual_sha256=sha(path), size_bytes=path.stat().st_size)
            record["matched"] = bool(expected and record["actual_sha256"] == expected)
        except BaseException as error:
            record["error"] = repr(error)
        observations.append(record)
    return dict(schema="damp-prefill-fixed-source-observation/v1",
                observed_at_ns=time.time_ns(), manifest_error=manifest_error,
                files=observations, all_match=manifest_error is None and
                all(r["matched"] for r in observations))

def snapshot_identity(snapshot):
    return [(r["path"], r["actual_sha256"]) for r in snapshot["files"]]

def bind_sources(args, before):
    require(before["all_match"], "source-before admission failed")
    manifest = json.loads(MANIFEST.read_text())
    require(manifest.get("schema") == SCHEMA and manifest.get("namespace") == NAMESPACE and
            manifest.get("frozen_dependencies") == FROZEN and
            manifest.get("counts") == list(COUNTS) and manifest.get("turns") == TURNS and
            manifest.get("identical_repeats") == REPEATS and
            manifest.get("default_execute") is False and manifest.get("npu_executed") is False and
            manifest.get("graph_supported") is False and manifest.get("packing_supported") is False,
            "exact fixed-buffer preregistration")
    require(Path(args.source_manifest).resolve() == OLD_SOURCE.resolve() and
            Path(args.runtime_manifest).resolve() == OLD_RUNTIME.resolve() and
            args.source_manifest_sha256 == FROZEN[str(OLD_SOURCE.relative_to(REPO))] and
            args.runtime_manifest_sha256 == FROZEN[str(OLD_RUNTIME.relative_to(REPO))],
            "frozen old compiled/runtime manifests only")
    original = load_module("damp_fixed_buffers_original_gate", PROBE / "run_float_gate.py")
    binding = original.source_bindings(args)
    compiled = json.loads(OLD_SOURCE.read_text())["compiled_sources"]
    require(len(compiled) == 9 and all(FROZEN.get(k) == v for k, v in compiled.items()),
            "unchanged actual compiled9")
    return binding

def check_schema(op):
    expected = ("x_bits", "sr_bits", "proposal_bits", "use_candidate")
    schemas = {}
    for name, returns in (("prepare", 0), ("divide_bits", 4)):
        schema = getattr(op, name).default._schema
        require(tuple(a.name for a in schema.arguments) == expected and
                tuple(str(a.type) for a in schema.arguments) == ("Tensor", "Tensor", "Tensor", "bool") and
                all(not a.kwarg_only and a.alias_info is None for a in schema.arguments) and
                len(schema.returns) == returns and
                all(str(r.type) == "Tensor" and r.alias_info is None for r in schema.returns),
                "actual frozen readonly operator schema " + name)
        schemas[name] = str(schema)
    return schemas

def pointer_records(tensors):
    records = []
    for t in tensors:
        base = int(t.untyped_storage().data_ptr())
        width = int(t.element_size())
        pointer = int(t.data_ptr())
        nbytes = int(t.untyped_storage().nbytes())
        count = int(t.numel())
        offset = int(t.storage_offset())
        require(pointer == base + offset * width and count > 0 and
                base <= pointer and count * width <= base + nbytes - pointer,
                "actual pointer/storage bounds")
        records.append(dict(pointer=pointer, base=base, storage_bytes=nbytes,
                            element_size=width, element_count=count, storage_offset=offset))
    return records

def disjoint_backings(records):
    for i, a in enumerate(records):
        for b in records[:i]:
            require(a["base"] + a["storage_bytes"] <= b["base"] or
                    b["base"] + b["storage_bytes"] <= a["base"], "input/output backing alias")

def same_complete(actual, expected, torch):
    return len(actual) == len(expected) and all(
        a is not None and torch.equal(a, b) for a, b in zip(actual, expected))

def safe_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")

def preserve_after(torch, path, artifact):
    try:
        torch.save(artifact, path)
    except BaseException as error:
        artifact.setdefault("artifact_save_errors", []).append(repr(error))
        return False
    return True

def execute_case(count, enabled, op, torch, torch_npu, cases, gold, old, out, report, save_report):
    name = str(count) + ("-certificate" if enabled else "-exact")
    case = dict(name=name, count=count, use_candidate=enabled, status="started",
                prepares=0, changed_turns=0, identical_repeats=REPEATS, turns=[],
                input_pointers=None, view_pointers=None)
    report["cases"].append(case)
    save_report()
    initial_rows = changing_fixture(count, TURNS - 1, cases, gold) # first actual turn0 MUST change
    safe_json(out / (name + "-prepare.rows.before.json"), initial_rows)
    initial_fingerprints = validate_rows(initial_rows, count, gold) # retain malformed fixture before rejection
    def cpu_inputs(rows):
        return [torch.tensor([cases.INPUT_GUARDS[j]] * 8 +
                [cases.signed(r[key]) for r in rows] + [cases.INPUT_GUARDS[j]] * 8,
                dtype=torch.int32) for j, key in enumerate(("x", "c", "proposal"))]
    def cpu_outputs(rows):
        values = ([cases.signed(r["bits"]) for r in rows],
                  [r["valid"] for r in rows], [r["finite"] for r in rows],
                  [r["accepted"] if enabled else 0 for r in rows])
        return [torch.tensor([cases.GUARDS[j]] * 8 + values[j] +
                             [cases.GUARDS[j]] * 8, dtype=torch.int32) for j in range(4)]
    cpu_initial = cpu_inputs(initial_rows)
    initial = dict(rows=initial_rows, before=cpu_initial, after=None, copy_errors=[],
                   dispatch_error=None, artifact_save_errors=[])
    torch.save(initial, out / (name + "-prepare.before.pt")) # BEFORE first H2D
    roots = []
    try:
        roots = [torch_npu.npu_format_cast(t.to("npu:0"), 2) for t in cpu_initial]
        views = [root[8:8+count] for root in roots]
        torch.npu.synchronize()
        baseline = pointer_records(roots)
        view_baseline = pointer_records(views)
        disjoint_backings(baseline)
        require(all(r["pointer"] % 32 == 0 for r in [*baseline, *view_baseline]) and
                all(torch_npu.get_npu_format(t) == 2 for t in [*roots, *views]),
                "three ND32B fixed guarded input buffers")
        case["input_pointers"], case["view_pointers"] = baseline, view_baseline
        op.prepare(*views, enabled)
        torch.npu.synchronize()
        case["prepares"] += 1
        initial["after"], initial["copy_errors"] = old.nullable_copy(roots)
        require(preserve_after(torch, out / (name + "-prepare.pt"), initial), "prepare artifact save")
        require(not initial["copy_errors"] and same_complete(initial["after"], cpu_initial, torch),
                "prepare raw input/guard mutation")
    except BaseException as error:
        initial["dispatch_error"] = repr(error)
        initial["after"], errors = old.nullable_copy(roots)
        initial["copy_errors"] += errors
        preserve_after(torch, out / (name + "-prepare.pt"), initial)
        case.update(status="failed", error=repr(error))
        save_report()
        raise
    previous_fingerprints = initial_fingerprints
    for turn in range(TURNS):
        rows = changing_fixture(count, turn, cases, gold)
        safe_json(out / (name + "-turn-" + str(turn) + ".rows.before.json"), rows)
        fingerprints = validate_rows(rows, count, gold)
        require(all(a != b for a, b in zip(fingerprints, previous_fingerprints)), "each fixed input must actually change")
        previous_fingerprints = fingerprints
        cpu_roots, expected = cpu_inputs(rows), cpu_outputs(rows)
        artifact = dict(name=name, turn=turn, rows=rows, before=cpu_roots, golden=expected,
                        fingerprints=fingerprints, before_pointers=baseline,
                        before_view_pointers=view_baseline, input_after_copy=None, replays=[],
                        raw_actual=None, after=None, dispatch_error=None, copy_errors=[],
                        artifact_save_errors=[], stage="before_H2D")
        path = out / (name + "-turn-" + str(turn) + ".pt")
        torch.save(artifact, out / (name + "-turn-" + str(turn) + ".before.pt"))
        outputs = []
        try:
            # prepare is deliberately NOT repeated; roots/views are never rebound.
            torch.npu.synchronize()
            artifact["stage"] = "in_place_input_update"
            for dst, src in zip(roots, cpu_roots):
                dst.copy_(src, non_blocking=False)
            torch.npu.synchronize()
            artifact["input_after_copy"], errors = old.nullable_copy(roots)
            artifact["copy_errors"] += errors
            require(preserve_after(torch, path, artifact), "updated-input artifact save")
            require(not errors and same_complete(artifact["input_after_copy"], cpu_roots, torch),
                    "actual in-place H2D payload/guard mismatch")
            require(pointer_records(roots) == baseline and pointer_records(views) == view_baseline,
                    "input/view address moved during update")
            for replay in range(REPEATS):
                artifact["stage"] = "divide_bits-" + str(replay)
                report["npu_dispatch_attempted"] = True
                outputs = list(op.divide_bits(*views, enabled))
                torch.npu.synchronize()
                report["npu_executed"] = True
                raw, copy_errors = old.nullable_copy(outputs)
                after, input_errors = old.nullable_copy(roots)
                artifact["copy_errors"] += copy_errors + input_errors
                artifact["raw_actual"], artifact["after"] = raw, after
                artifact["replays"].append(dict(replay=replay, raw=raw, inputs_after=after))
                # Persist raw bits/overflow/status/guards BEFORE every assertion.
                require(preserve_after(torch, path, artifact), "raw replay artifact save")
                require(not copy_errors and not input_errors, "nullable device-copy failure")
                require(len(outputs) == 4 and all(t.dtype == torch.int32 and
                        t.shape == (count+16,) and t.device == roots[0].device and
                        t.is_contiguous() and torch_npu.get_npu_format(t) == 2 for t in outputs),
                        "four complete physical-ND guarded output buffers")
                disjoint_backings([*baseline, *pointer_records(outputs)])
                require(pointer_records(roots) == baseline and pointer_records(views) == view_baseline,
                        "fixed input pointers drifted")
                require(same_complete(raw, expected, torch), "complete bits/flags/output guards mismatch")
                require(same_complete(after, cpu_roots, torch), "readonly raw inputs/guards changed")
        except BaseException as error:
            artifact["dispatch_error"] = repr(error) # primary attribution remains intact
            artifact["raw_actual"], errors = old.nullable_copy(outputs)
            artifact["copy_errors"] += errors
            artifact["after"], errors = old.nullable_copy(roots)
            artifact["copy_errors"] += errors
            preserve_after(torch, path, artifact)
            case.update(status="failed", error=repr(error), first_failure_artifact=str(path))
            save_report()
            raise
        case["turns"].append(dict(turn=turn, status="passed", input_fingerprints=fingerprints,
                                 identical_repeats=REPEATS, artifact=str(path), artifact_sha256=sha(path)))
        case["changed_turns"] += 1
        save_report()
    require(case["prepares"] == 1 and case["changed_turns"] == TURNS, "full fixed-buffer matrix")
    case["status"] = "passed"
    save_report()

def parse(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--execute", action="store_true")
    p.add_argument("--fixed-manifest-sha256")
    p.add_argument("--source-manifest", default=str(OLD_SOURCE))
    p.add_argument("--source-manifest-sha256", default=FROZEN[str(OLD_SOURCE.relative_to(REPO))])
    p.add_argument("--runtime-manifest", default=str(OLD_RUNTIME))
    p.add_argument("--runtime-manifest-sha256", default=FROZEN[str(OLD_RUNTIME.relative_to(REPO))])
    for name in ("library", "library-sha256", "build-receipt", "build-receipt-sha256",
                 "preflight", "preflight-sha256", "output-dir"):
        p.add_argument("--" + name)
    p.add_argument("--physical-card", type=int, choices=(4, 5, 6, 7), default=4)
    return p.parse_args(argv)

def main(argv=None):
    args = parse(argv)
    if not args.execute:
        print(json.dumps(dict(schema="damp-prefill-fixed-buffer-plan/v1", status="source_preparation_only",
             default_execute=False, launchable=False, npu_executed=False, graph_supported=False,
             counts=list(COUNTS), turns=TURNS, identical_repeats=REPEATS, prepares_per_case=1,
             missing_execution_proof=["actual build/export/load", "fresh physical canary",
                                      "MAIN admission", "explicit execute and immutable hashes"])))
        return
    required = ("fixed_manifest_sha256", "library", "library_sha256", "build_receipt",
                "build_receipt_sha256", "preflight", "preflight_sha256", "output_dir")
    require(all(getattr(args, key) for key in required), "all actual execution proofs required")
    out = Path(args.output_dir)
    require(out.is_absolute() and not out.exists(), "NEW absolute non-overwrite output required")
    out.mkdir(parents=True, exist_ok=False)
    report = dict(schema="damp-prefill-fixed-buffers-gate/v1", namespace=NAMESPACE,
                  status="started", error=None, secondary_errors=[], source_before=None, source_after=None,
                  npu_executed=False, npu_dispatch_attempted=False, graph_supported=False,
                  packing_supported=False, serving_ready=False, performance_supported=False, cases=[])
    def save_report():
        safe_json(out / "report.json", report)
    save_report()
    before = source_snapshot(args)
    safe_json(out / "SOURCE_BEFORE.json", before)
    report["source_before"] = dict(path=str(out / "SOURCE_BEFORE.json"), sha256=sha(out / "SOURCE_BEFORE.json"))
    failure = None
    try:
        report["bindings"] = bind_sources(args, before)
        proof_path = Path(args.preflight)
        require(proof_path.is_absolute() and sha(proof_path) == args.preflight_sha256, "device proof SHA")
        proof = json.loads(proof_path.read_text())
        json.dumps(proof, allow_nan=False) # reject malformed non-finite proof before report embedding
        contract = load_module("damp_fixed_device_contract", PROJECT / "tests/all_batch_gate_v1/contract.py")
        contract.validate_device(proof, args.physical_card, time.time_ns())
        cases = load_module("damp_fixed_float_cases", PROBE / "cases.py")
        gold = load_module("damp_fixed_independent_fraction", PROBE.parent / "independent_float_div.py")
        import torch
        import torch_npu
        torch.npu.set_device(0)
        require(torch.npu.get_device_name(0) == "Ascend910B4", "actual runtime SoC")
        report.update(physical_card=args.physical_card, actual_runtime_soc="Ascend910B4",
                      device_proof=dict(path=str(proof_path), sha256=args.preflight_sha256, content=proof),
                      torch_version=str(torch.__version__), device_initialized=True)
        torch.ops.load_library(args.library)
        op = getattr(torch.ops, NAMESPACE)
        report["schemas"] = check_schema(op)
        maps = Path("/proc/self/maps").read_text()
        libraries = sorted({line.split()[-1] for line in maps.splitlines() if "/" in line and
                            ("libtorch_npu.so" in line or str(Path(args.library).resolve()) in line)})
        require(str(Path(args.library).resolve()) in libraries and
                any(Path(p).name == "libtorch_npu.so" for p in libraries), "actual loaded library maps")
        report["loaded_libraries"] = [dict(path=p, sha256=sha(p)) for p in libraries]
        old = load_module("damp_fixed_copy_helpers", PROBE / "run_float_gate.py")
        for count in COUNTS:
            for enabled in (False, True):
                execute_case(count, enabled, op, torch, torch_npu, cases, gold, old, out, report, save_report)
        require(len(report["cases"]) == 4 and all(c["status"] == "passed" and
                c["prepares"] == 1 and c["changed_turns"] == TURNS for c in report["cases"]),
                "all four registered cases required")
    except BaseException as error:
        failure = repr(error)
    # Also save SOURCE_AFTER for failed admission/load/copy/dispatch/assertions.
    after = source_snapshot(args)
    safe_json(out / "SOURCE_AFTER.json", after)
    report["source_after"] = dict(path=str(out / "SOURCE_AFTER.json"), sha256=sha(out / "SOURCE_AFTER.json"))
    if not after["all_match"] or snapshot_identity(before) != snapshot_identity(after):
        drift = "immutable source closure changed or was unavailable"
        if failure is None:
            failure = drift
        else:
            report["secondary_errors"].append(drift)
    report.update(status="failed" if failure else "fixed_buffers_exact_float_pass", error=failure)
    save_report()
    if failure:
        raise RuntimeError(failure)

if __name__ == "__main__":
    main()
