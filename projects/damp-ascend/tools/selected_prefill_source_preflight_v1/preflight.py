"""Default-OFF exact-image fixture and callable preflight; no algorithm calls.

Import is stdlib-only. MAIN owns all Torch imports and target-image execution.
A callable import failure is retained and never replaced by a mock/unwrap call.
"""
import argparse
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
import types

TORCH_ROOT = "/usr/local/python3.12.13/lib/python3.12/site-packages/torch"
COMPILER = TORCH_ROOT + "/compiler/__init__.py"
DECORATORS = TORCH_ROOT + "/_dynamo/decorators.py"
EVAL_FRAME = TORCH_ROOT + "/_dynamo/eval_frame.py"
CHUNK = "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py"
GDN = "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"
PINS = {
    COMPILER: "84613b1321b2e416bd113fbe898e8d65c9fba71a05c6ace755b7812e98ed9f5d",
    DECORATORS: "9662eb8521ba76e358289eaf81aaad6e4930f1b241f17273c79e8ad5a1220cc1",
    EVAL_FRAME: "8f49ecb842a4d50281695e5b8d015fd9afd2a202b0f6c9f3f94c91415ba0d5a4",
    CHUNK: "6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5",
    GDN: "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
}
WRAPPER = "projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/op_extension/selected_prefill_torch.cpp"
WRAPPER_SHA = "dd03d2c2b56397566507952fc962b3336ac054ebd85b803eb6cd892c0b0e2236"

class Pending(RuntimeError):
    pass

def require(ok, label):
    if not ok:
        raise Pending(label)

def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def source_checks(paths, observation, reader=None):
    reader = reader or (lambda path: Path(path).read_bytes())
    raw = {}
    observation["source_sha256"] = {}
    for path, expected in paths.items():
        data = reader(path)
        observation["source_sha256"][path] = sha_bytes(data)
        require(observation["source_sha256"][path] == expected, "actual source SHA: " + path)
        raw[path] = data
    return raw

def nested_codes(code):
    yield code
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            yield from nested_codes(value)

def source_code(raw, path, qualname):
    tree = compile(raw[path], path, "exec", dont_inherit=True, optimize=sys.flags.optimize)
    # Target Python3.12 has co_qualname; the host software runner is Python3.10.
    # For it, preserve the complete lexical CodeType path, not just co_name.
    def lexical(code, prefix=""):
        name = prefix + code.co_name
        yield name, code
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                child_prefix = "" if code is tree else name + "."
                yield from lexical(value, child_prefix)
    matches = [c for name, c in lexical(tree)
               if getattr(c, "co_qualname", name) == qualname]
    require(len(matches) == 1, "unique source CodeType: " + qualname)
    return matches[0]

def prove_code(fn, raw, path, qualname, observation, label):
    record = {"function_type": type(fn).__name__, "expected_path": path,
              "expected_qualname": qualname}
    observation[label] = record
    require(type(fn) is types.FunctionType, label + ": exact FunctionType")
    record.update(filename=fn.__code__.co_filename, firstlineno=fn.__code__.co_firstlineno,
                  qualname=getattr(fn.__code__, "co_qualname", fn.__qualname__),
                  sourcefile=inspect.getsourcefile(fn))
    require(record["filename"] == path and record["sourcefile"] == path,
            label + ": loaded path, not snapshot alias")
    require(fn.__code__ == source_code(raw, path, qualname),
            label + ": loaded CodeType equals pinned source compile")

def prove_wrapper(outer, inner, eval_frame, observation):
    """Verify exactly this version's DisableContext function; do not invoke it."""
    observation["wrapper"] = {"outer_id": id(outer), "inner_id": id(inner),
                              "outer_type": type(outer).__name__, "inner_type": type(inner).__name__}
    require(type(outer) is types.FunctionType and type(inner) is types.FunctionType,
            "two exact function objects")
    context_cls = eval_frame.DisableContext
    owner = context_cls.__call__
    children = [x for x in owner.__code__.co_consts
                if isinstance(x, types.CodeType) and x.co_name == "_fn"]
    require(len(children) == 1, "unique canonical DisableContext._fn")
    record = observation["wrapper"]
    record.update(code_is_canonical=outer.__code__ is children[0],
                  globals_is_canonical=outer.__globals__ is eval_frame.__dict__,
                  wrapped_id=id(getattr(outer, "__wrapped__", None)),
                  backlink_id=id(getattr(outer, "_torchdynamo_orig_callable", None)),
                  freevars=list(outer.__code__.co_freevars))
    require(record["code_is_canonical"] and record["globals_is_canonical"],
            "actual DisableContext._fn code and globals identity")
    require(outer is not inner and getattr(outer, "__wrapped__", None) is inner and
            getattr(outer, "_torchdynamo_orig_callable", None) is inner,
            "exact two-level wrapper/backlink, no cycle")
    require(not hasattr(inner, "__wrapped__") and not hasattr(inner, "_torchdynamo_orig_callable"),
            "innermost native function, no unverified extra wrapper")
    require(getattr(outer, "_torchdynamo_disable", None) is True and
            getattr(outer, "_torchdynamo_disable_recursive", None) is True and
            getattr(outer, "_torchdynamo_disable_msg", 1) is None,
            "actual recursive disable flags")
    require(outer.__name__ == inner.__name__ and outer.__qualname__ == inner.__qualname__,
            "functools wraps name identity")
    require(outer.__closure__ is not None and len(outer.__closure__) == len(outer.__code__.co_freevars),
            "complete actual closure")
    closure = dict(zip(outer.__code__.co_freevars, (c.cell_contents for c in outer.__closure__)))
    require(set(closure) == {"fn", "self"}, "only source-defined fn/self closure")
    context = closure["self"]
    record.update(closure_fn_id=id(closure["fn"]), context_class=type(context).__qualname__,
                  context_callback_is_none=getattr(context, "callback", 1) is None,
                  context_msg_is_none=getattr(context, "msg", 1) is None,
                  context_wrapping=getattr(context, "wrapping", None))
    require(closure["fn"] is inner and type(context) is context_cls and
            context.callback is None and context.msg is None and context.wrapping is True,
            "source-bound closure fn/context options")
    return outer

def framework_proof(torch, compiler, decorators, eval_frame, raw, observation):
    require(torch.__version__ == "2.10.0+cpu", "exact immutable-image Torch version")
    require(torch.compiler is compiler and torch._dynamo.disable is decorators.disable and
            decorators.DisableContext is eval_frame.DisableContext,
            "actual compiler/dynamo/DisableContext aliases")
    prove_code(compiler.disable, raw, COMPILER, "disable", observation, "compiler_disable")
    prove_code(decorators.disable, raw, DECORATORS, "disable", observation, "dynamo_disable")
    prove_code(eval_frame.DisableContext.__call__, raw, EVAL_FRAME,
               "DisableContext.__call__", observation, "context_call")
    require(compiler.disable.__globals__ is compiler.__dict__ and
            decorators.disable.__globals__ is decorators.__dict__ and
            eval_frame.DisableContext.__call__.__globals__ is eval_frame.__dict__,
            "actual framework function global owners")

def native_proof(torch, gdn, chunk, compiler, decorators, eval_frame, observation, reader=None):
    """Reusable runtime guard. Return ORIGINAL decorated outer, never inner."""
    raw = source_checks(PINS, observation, reader)
    framework_proof(torch, compiler, decorators, eval_frame, raw, observation)
    observation["native_alias"] = {"gdn_path": getattr(gdn, "__file__", None),
                                  "chunk_path": getattr(chunk, "__file__", None)}
    require(gdn.__file__ == GDN and chunk.__file__ == CHUNK, "actual canonical module paths")
    outer = gdn.chunk_gated_delta_rule
    observation["native_alias"]["same_object"] = outer is chunk.chunk_gated_delta_rule
    require(outer is chunk.chunk_gated_delta_rule, "actual GDN canonical chunk alias")
    inner = getattr(outer, "__wrapped__", None)
    prove_code(inner, raw, CHUNK, "chunk_gated_delta_rule", observation, "inner_chunk")
    require(inner.__globals__ is chunk.__dict__ and inner.__name__ == "chunk_gated_delta_rule" and
            inner.__qualname__ == "chunk_gated_delta_rule", "actual native inner global owner/name")
    result = prove_wrapper(outer, inner, eval_frame, observation)
    after = {}
    source_checks(PINS, after, reader)
    observation["sources_after"] = after["source_sha256"]
    require(observation["sources_after"] == observation["source_sha256"], "source unchanged during proof")
    observation["verified"] = True
    observation["invocation_policy"] = "original_decorated_outer_once_per_original_algorithm_call"
    return result

def fixture_semantics(torch):
    require(torch.__version__ == "2.10.0+cpu", "exact immutable-image Torch version")
    p1 = torch.tensor([0, 0], dtype=torch.int32, device="cpu")[::2]
    p2 = torch.tensor([0, 0, 3, 0], dtype=torch.int32, device="cpu")[::2]
    require(tuple(p1.shape) == (1,) and p1.stride() == (2,) and p1.is_contiguous(),
            "legitimate singleton stride2")
    require(tuple(p2.shape) == (2,) and p2.stride() == (2,) and not p2.is_contiguous(),
            "genuine P2 noncontiguous indices")
    require(p2.dtype == torch.int32 and p2.device.type == "cpu" and
            p2.storage_offset() == 0 and p2.tolist() == [0, 3], "P2 ABI semantics")
    require(torch.empty((2, 12, 128, 128), dtype=torch.float32, device="cpu").shape[0] == p2.numel(),
            "real P2 dense, no artificial PAD")
    shapes = ((1, 12, 128, 128), (12, 128))
    for shape in shapes:
        base = torch.zeros((*shape[:-1], shape[-1] * 2), dtype=torch.float32, device="cpu")
        value = base[..., ::2]
        require(tuple(value.shape) == shape and not value.is_contiguous() and
                value.storage_offset() == 0, "genuine nonsingleton last-axis fixture")
    return {"p1": {"shape": list(p1.shape), "stride": list(p1.stride()), "contiguous": True},
            "p2": {"shape": list(p2.shape), "stride": list(p2.stride()), "contiguous": False,
                   "values": p2.tolist(), "dtype": str(p2.dtype), "device": str(p2.device)},
            "torch_version": torch.__version__, "operator_executed": False}

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--mode", choices=("fixture_cpu", "torch_wrapper", "native_callable"), default="fixture_cpu")
    parser.add_argument("--repo", type=Path, default=Path("/opt/host/vnf/austinov/model-tuning-lab"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = {"schema": "damp-selected-prefill-source-preflight/v1", "status": "disabled",
              "mode": args.mode, "default_enabled": False, "npu_executed": False,
              "algorithm_invoked": False, "operator_executed": False, "serving_ready": False,
              "performance_measurement_admitted": False, "graph_supported": False}
    if not args.execute:
        print(json.dumps(report, sort_keys=True))
        return 0
    require(args.out is not None and args.out.is_absolute() and not args.out.exists(),
            "explicit fresh absolute output JSON")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report["status"] = "running"
    exit_code = 1
    try:
        report["wrapper_sha256"] = sha_bytes((args.repo / WRAPPER).read_bytes())
        require(report["wrapper_sha256"] == WRAPPER_SHA, "unchanged compiled selected wrapper")
        observation = {}
        report["observation"] = observation
        pins = PINS if args.mode == "native_callable" else {k: PINS[k] for k in (COMPILER, DECORATORS, EVAL_FRAME)}
        raw = source_checks(pins, observation)
        os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
        torch = importlib.import_module("torch")
        if args.mode == "fixture_cpu":
            report["fixture"] = fixture_semantics(torch)
        else:
            compiler = importlib.import_module("torch.compiler")
            decorators = importlib.import_module("torch._dynamo.decorators")
            eval_frame = importlib.import_module("torch._dynamo.eval_frame")
            framework_proof(torch, compiler, decorators, eval_frame, raw, observation)
            if args.mode == "torch_wrapper":
                def explicit_framework_fixture():
                    raise AssertionError("the fixture must never be invoked")
                outer = compiler.disable(explicit_framework_fixture)
                prove_wrapper(outer, explicit_framework_fixture, eval_frame, observation)
                report["native_callable_proven"] = False
            else:
                gdn = importlib.import_module("vllm_ascend.ops.gdn")
                chunk = importlib.import_module("vllm_ascend.ops.triton.fla.chunk")
                native_proof(torch, gdn, chunk, compiler, decorators, eval_frame, observation)
                report["native_callable_proven"] = True
        after = {}
        source_checks(pins, after)
        report["source_checks_after"] = after["source_sha256"]
        require(report["source_checks_after"] == observation["source_sha256"], "source closure stable")
        report["status"] = "preflight_pass"
        exit_code = 0
    except BaseException as exc:
        report["status"] = "failed"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        report["torch_npu_imported"] = "torch_npu" in sys.modules
        with args.out.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps({"report": str(args.out), "sha256": sha_bytes(args.out.read_bytes()),
                      "status": report["status"], "npu_executed": False}, sort_keys=True))
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
