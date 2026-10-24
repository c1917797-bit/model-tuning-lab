"""Read-only CPU bridge over already retained MXR tensors. No native/NPU execution."""
import argparse, ast, hashlib, importlib.util, json, math, os, signal, sys, time, traceback
from pathlib import Path
HERE = Path(__file__).resolve().parent

def need(value, message):
    if not value:
        raise ValueError(message)

def checked(r):
    need(type(r) is dict and set(r) == {"path", "bytes", "sha256"}, "exact input Ref3")
    p = Path(r["path"])
    need(p.is_absolute() and p.is_file() and not any(q.is_symlink() for q in (p, *p.parents)), "ordinary input")
    before = p.stat()
    h = hashlib.sha256()
    size = 0
    with p.open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block); size += len(block)
    after = p.stat()
    need(size == r["bytes"] and h.hexdigest() == r["sha256"] and
         (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "complete stable input")
    return p

def no_device():
    need(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0" and
         os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "", "explicit Devices[] environment")
    need("torch_npu" not in sys.modules and not any(Path("/dev/davinci" + str(i)).exists() for i in range(8)), "CPU only")
    fdroot = Path("/proc/self/fd")
    for p in fdroot.iterdir():
        try:
            target = os.readlink(p)
        except FileNotFoundError:
            continue
        need(not any(x in target for x in ("/dev/davinci", "/dev/devmm_svm", "/dev/hisi_hdc")), "no NPU file descriptor")

def load(r, name):
    p = checked(r)
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def syntax_facts(r, names):
    text = checked(r).read_text()
    tree = ast.parse(text)
    parts = [ast.get_source_segment(text, n) for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    return dict(source=r, functions=parts, exp_calls=sorted(set(
        ast.unparse(n.func) for n in ast.walk(tree)
        if isinstance(n, ast.Call) and ast.unparse(n.func).split(".")[-1] in ("exp", "exp2", "cumsum"))))

def source_contract(plan):
    """Inspect pinned source only: never import Triton/native modules."""
    need(len(plan["g_producer_sources"]) == 2, "actual chunk/cumsum Ref3 pair")
    trees = [ast.parse(checked(r).read_bytes()) for r in plan["g_producer_sources"]]
    functions = {n.name: n for tree in trees for n in tree.body if isinstance(n, ast.FunctionDef)}
    forward = functions["chunk_gated_delta_rule_fwd"]
    calls = [n for n in ast.walk(forward) if isinstance(n, ast.Call)]
    cumulative = [n for n in calls if ast.unparse(n.func) == "chunk_local_cumsum"]
    need(len(cumulative) == 1 and [ast.unparse(a) for a in cumulative[0].args] == ["g"] and
         {k.arg: ast.unparse(k.value) for k in cumulative[0].keywords} ==
         {"chunk_size": "chunk_size", "cu_seqlens": "cu_seqlens", "block_indices": "block_indices_cumsum"},
         "actual G caller leaves scale/reverse/head_first/output_dtype defaults unchanged")
    need(any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "chunk_size" for t in n.targets)
             and isinstance(n.value, ast.Constant) and n.value.value == 64 for n in forward.body), "actual BT64")
    for name in ("chunk_local_cumsum", "chunk_local_cumsum_scalar"):
        f = functions[name]
        args = f.args.posonlyargs + f.args.args
        defaults = {a.arg: ast.unparse(d) for a, d in zip(args[-len(f.args.defaults):], f.args.defaults)}
        need(all(defaults[k] == v for k, v in {"reverse": "False", "scale": "None", "head_first": "False", "output_dtype": "torch.float"}.items()),
             "actual cumsum defaults")
    scalar = functions["chunk_local_cumsum_scalar_kernel"]
    scans = [n for n in ast.walk(scalar) if isinstance(n, ast.Call) and ast.unparse(n.func) == "tl.cumsum"]
    need(len(scans) == 2 and all({k.arg: ast.unparse(k.value) for k in n.keywords} ==
         {"axis": "0", "reverse": "REVERSE"} for n in scans), "actual F32 chunk-local forward scan")
    loads = [n for n in ast.walk(scalar) if isinstance(n, ast.Call) and ast.unparse(n.func) == "tl.load(ptr_s, boundary_check=(0,)).to"]
    need(len(loads) == 2 and all([ast.unparse(a) for a in n.args] == ["tl.float32"] for n in loads), "actual F32 scan inputs")
    stores = [n for n in ast.walk(scalar) if isinstance(n, ast.Call) and ast.unparse(n.func) == "tl.store"]
    need(len(stores) == 1 and ast.unparse(stores[0].args[1]) == "b_o.to(s.dtype.element_ty)", "actual store casts to input dtype")
    native_h = [n for n in calls if ast.unparse(n.func) == "torch.ops._C_ascend.chunk_gated_delta_rule_fwd_h"]
    need(len(native_h) == 1 and {k.arg: ast.unparse(k.value) for k in native_h[0].keywords}.get("use_exp2") == "False", "actual H natural exp domain")
    continuous = ast.parse(checked(plan["continuous_source"]).read_bytes())
    expressions = {ast.unparse(n) for n in ast.walk(continuous) if isinstance(n, ast.Subscript)}
    layout = {"Hentry": "y['Hentry'].reshape(1, 12, 32, 128, 128)[0]",
              "Vnew": "y['Vnew'].reshape(1, 12, 2048, 128)[0]"}
    need(all(v in expressions for v in layout.values()), "reuse exact already-verified continuous-H extraction, not inferred reshape")
    return dict(producer=plan["g_precision_facts"], Hentry_Vnew_layout_source=plan["continuous_source"],
                Hentry_Vnew_expressions=layout, source_contract_checked=True,
                instruction_exact_scan_order_or_exp_claimed=False)

def observed_layout(y):
    # Same extraction as pinned continuous_h.consume, whose 32-chunk parity is retained.
    return (y["Hentry"].reshape(1, 12, 32, 128, 128)[0],
            y["Vnew"].reshape(1, 12, 2048, 128)[0])

def analyze(torch, plan):
    producer_contract = source_contract(plan)
    C = load(plan["continuous_source"], "_exact_existing_continuous_h")
    need(C.FIXED == plan["fixed_inputs"], "same retained real case and three arms")
    old = json.loads(checked(plan["existing_attribution"]).read_bytes())
    need(old["fixed_inputs"] == C.FIXED and old["canonical_reconstruction_bitwise"] is True and
         old["diagnostic_complete"] is True and old["qualification"] is False, "reuse existing completed attribution")
    fp_module = C.load(C.FIXED["donor"], "_bridge_real_frame", {"need", "fp", "equal", "validate_frame"})
    metrics = C.load(C.FIXED["metrics"], "_bridge_original_metrics", {"metrics"})
    oracle = C.load(C.FIXED["canonical"], "_bridge_original_canonical")
    codec = C.load(C.FIXED["codec"], "_bridge_original_codec")
    checked(C.FIXED["case"]["raw_sidecar"])
    saved = codec.read(torch, checked(C.FIXED["case"]["raw"]))
    x = fp_module.validate_frame(torch, saved)
    need(x["cu_seqlens"].tolist() == [0, 2048] and x["already_normalized"] is True, "same complete normalized 2K frame")
    probe = json.loads(checked(plan["actual_probe"]).read_bytes())
    sr = probe["source"]; manifest = json.loads(checked(sr).read_bytes())
    need(sr == plan["actual_source"] and manifest["files"]["wu_boundary.py"] == plan["actual_reference_source"], "exact actual source and WU reference bindings")
    W = C.load(manifest["files"]["wu_boundary.py"], "_bridge_actual_WU_reference", {"need", "reference"})
    wy_facts = syntax_facts(plan["wy_source"], {"recompute_w_u_fwd", "recompute_w_u_fwd_kernel"})
    need("tl.exp" in wy_facts["exp_calls"] and "tl.exp2" not in wy_facts["exp_calls"], "actual WY uses natural exp")
    g_facts = [syntax_facts(r, set(plan["g_producer_function_names"])) for r in plan["g_producer_sources"]]
    ref = oracle.evaluate(torch, x)
    trace = ref["trace"]; need(len(trace) == 32, "reuse original 32 canonical chunks once")
    wanted = {k: fp_module.fp(torch, x[k]) for k in ("q", "k", "v", "g", "beta", "initial_state", "cu_seqlens")}
    arms = {}
    arm_refs = {}
    for name, r in zip(("saved_candidate", "native", "cpu64_cast"), C.FIXED["arms"]):
        y = torch.load(checked(r), map_location="cpu", weights_only=True)
        need(y["arm"] == name and y["inputs_after"] == wanted and torch.equal(y["A"], saved["solve"]["A"]), "same actual A/input arm")
        need(tuple(y["A"].shape) == tuple(y["B"].shape) == (1, 2048, 12, 64), "actual source-bound A/B ABI")
        need(y["A"].dtype == torch.float32 and y["B"].dtype == torch.bfloat16, "actual A32/BF16 boundaries")
        need(y["G"].dtype == torch.float32 and tuple(y["G"].shape) == (1, 2048, 12), "actual G32 ABI")
        need(all(y[k].dtype == torch.bfloat16 and tuple(y[k].shape) == (1, 2048, 12, 128)
                 for k in ("W", "U", "output")), "actual W/U/O BF16 ABI")
        need(y["Hentry"].dtype == torch.bfloat16 and y["Hentry"].numel() == 12 * 32 * 128 * 128 and
             y["Vnew"].dtype == torch.bfloat16 and y["Vnew"].numel() == 12 * 2048 * 128 and
             y["state"].dtype == torch.float32 and tuple(y["state"].shape) == (1, 12, 128, 128), "actual H/Vnew/state ABI")
        for k in ("A", "B", "G", "W", "U", "Hentry", "Vnew", "state", "output"):
            need(y[k].device.type == "cpu" and bool(torch.isfinite(y[k]).all()), "complete CPU evidence " + k)
        arms[name] = y; arm_refs[name] = r
    candidate, native, cast = (arms[k] for k in ("saved_candidate", "native", "cpu64_cast"))
    need(torch.equal(candidate["B"], saved["solve"]["output"]) and
         torch.equal(candidate["state"], saved["final_state"]) and
         torch.equal(candidate["output"], saved["output"]), "original complete saved candidate anchor")
    need(all(torch.equal(y["A"], native["A"]) and torch.equal(y["G"], native["G"]) for y in arms.values()), "actual three-arm A/G unchanged")
    first = {}; rows = []
    def score(a, b, key, chunk=None, head=None):
        got = metrics.metrics(torch, a, b)
        result = {k: got[k] for k in ("finite", "frob_relative", "r2", "rmse_over_mean_ref_abs", "pass")}
        result["changed_values"] = int(torch.count_nonzero(a.double() != b.double()))
        tag = dict(chunk=chunk, head=head)
        if chunk is not None and result["changed_values"] and key + ".first_nonzero" not in first:
            first[key + ".first_nonzero"] = tag
        if chunk is not None and not result["pass"] and key + ".first_threshold_failure" not in first:
            first[key + ".first_threshold_failure"] = tag
        return result
    layouts = {name: observed_layout(y) for name, y in arms.items()}
    aggregate = dict(
        candidate_vs_native={k: score(candidate[k], native[k], "candidate_native." + k)
                             for k in ("W", "U", "Hentry", "Vnew", "output", "state")},
        native_vs_independent_canonical={k: score(native[k], ref[k], "native_canonical." + k)
                                        for k in ("output", "state")},
        candidate_vs_independent_canonical={k: score(candidate[k], ref[k], "candidate_canonical." + k)
                                           for k in ("output", "state")})
    for c, tr in enumerate(trace):
        z = slice(c * 64, (c + 1) * 64)
        per_arm = {}
        for name, y in arms.items():
            operands = {k: x[k][:, z].contiguous() for k in ("k", "v", "beta")}
            operands.update(B=y["B"][:, z].contiguous(), G=y["G"][:, z].contiguous())
            conditional = W.reference(torch, **operands)
            per_arm[name] = dict(
                A=y["A"][0, z].permute(1, 0, 2).double(),
                B=y["B"][0, z].permute(1, 0, 2).double(),
                G=y["G"][0, z].transpose(0, 1).double(),
                W=y["W"][0, z].transpose(0, 1).double(),
                U=y["U"][0, z].transpose(0, 1).double(),
                conditional_W=conditional["W"][0].transpose(0, 1).double(),
                conditional_U=conditional["U"][0].transpose(0, 1).double(),
                Hentry=layouts[name][0][:, c].double(),
                Vnew=layouts[name][1][:, z].double(),
                output=y["output"][0, z].transpose(0, 1).double())
        for h in range(12):
            row = dict(chunk=c, head=h, upstream={}, candidate_vs_native={}, native_vs_canonical={})
            for name, values in per_arm.items():
                comparisons = {
                    "G_actual_vs_natural_canonical_C": (values["G"][h], tr["g_cumsum"][h]),
                    "A_operand_direct_vs_canonical_A32": (values["A"][h], tr["A32"][h]),
                    "B_vs_canonical_B": (values["B"][h], tr["B"][h]),
                    "B_vs_existing_cpu64_cast_same_A": (values["B"][h], per_arm["cpu64_cast"]["B"][h]),
                    "W_vs_held_BG_FP32": (values["W"][h], values["conditional_W"][h]),
                    "U_vs_held_BG_FP32": (values["U"][h], values["conditional_U"][h])}
                row["upstream"][name] = {k: score(a, b, name + "." + k, c, h) for k, (a, b) in comparisons.items()}
            for k in ("W", "U", "Hentry", "Vnew", "output"):
                row["candidate_vs_native"][k] = score(per_arm["saved_candidate"][k][h], per_arm["native"][k][h], "candidate_native." + k, c, h)
            for k, target in (("W", tr["W"]), ("U", tr["U"]), ("Hentry", tr["Hstart"]), ("output", tr["output"])):
                row["native_vs_canonical"][k] = score(per_arm["native"][k][h], target[h], "native_canonical." + k, c, h)
            rows.append(row)
    for r in (plan["continuous_source"], plan["existing_attribution"], plan["actual_probe"], plan["wy_source"],
              sr, manifest["files"]["wu_boundary.py"], *plan["g_producer_sources"],
              *C.FIXED["arms"], C.FIXED["case"]["raw"]):
        checked(r)
    no_device()
    return dict(schema="mxr.existing-raw-upstream-baseline-bridge/v1", source_refs=plan,
                actual_source=sr, actual_reference_source=manifest["files"]["wu_boundary.py"],
                case=C.FIXED["case"], reused_arms=arm_refs,
                existing_results_reused=dict(original_registered_pair_and_canonical=old["original_registered_pair_and_canonical"],
                    observed_first_bad_chunk={c["arm"]: next((r["chunk"] for r in c["variants"]["observed"]["chunks"] if not r["next_vs_canonical"]["pass"]), None) for c in old["cases"]}),
                precision_contract=dict(WY_consumer="tl.exp natural-domain; wrapper transpose/contiguous only",
                    G_producer_source_status="pinned caller/kernel source contract checked; natural-domain FP32 scan, not instruction-exact canonical equivalence",
                    G_producer_sources=g_facts, WY_source=wy_facts,
                    G_producer_contract=producer_contract, raw_G_dtype=str(x["g"].dtype),
                    canonical="original evaluate: FP64 cumsum then F32 boundary; exp natural; FP64 inverse then BF16 B",
                    A_comparison="direct same-ABI operands; original source conventions retained, no alternate sign or solve introduced",
                    same_A_inverse="reuse actual source-produced cpu64_cast arm; no new inverse implementation",
                    oracle_and_thresholds_changed=False, instruction_exact=False),
                aggregate=aggregate, first_differences=first, chunk_head_rows=rows,
                diagnostic_complete=True, qualification=False, performance=False, task_accuracy=False,
                new_NPU_execution=False, candidate_patch=False, native_floor_grants_relaxation=False)

def main():
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--inputs", type=Path, default=HERE / "INPUTS.json")
    p.add_argument("--output", type=Path)
    p.add_argument("--deadline-epoch", type=float)
    a = p.parse_args()
    plan = json.loads(a.inputs.read_bytes())
    if not a.execute:
        need(a.output is None and a.deadline_epoch is None, "no ignored execution inputs")
        print('{"enabled":false,"NPU":false,"qualification":false}')
        return 0
    no_device()
    now = time.time()
    need(a.deadline_epoch is not None and math.isfinite(a.deadline_epoch) and
         now < a.deadline_epoch <= min(now + 300, plan["cutoff_epoch"] - 90), "unchanged bounded CPU deadline")
    need(a.output == Path(plan["output"]) and a.output.is_absolute() and a.output.parent.is_dir() and
         not a.output.exists() and not any(q.is_symlink() for q in (a.output, *a.output.parents)), "new exact CPU evidence path")
    need(hasattr(signal, "SIGALRM"), "Linux CPU owner only")
    def expired(*_):
        raise TimeoutError("bounded CPU bridge deadline")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, a.deadline_epoch - time.time())
    try:
        import torch
        torch.set_num_threads(1)
        value = analyze(torch, plan)
        raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
        need(len(raw) <= 8 * 2**20, "complete bounded 8MiB bridge report")
        with a.output.open("xb") as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        print(json.dumps(dict(path=str(a.output), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                              new_NPU_execution=False, qualification=False)))
        return 0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

if __name__ == "__main__":
    raise SystemExit(main())
