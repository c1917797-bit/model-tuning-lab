"""Hash-pinned AST adaptation of real GDN consumer; stdlib/source-only."""
import ast
import copy
import textwrap

def specialize_core(source):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "AscendGatedDeltaNetAttention")
    core = copy.deepcopy(next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                              and n.name == "_forward_core"))
    calls = [n for n in ast.walk(core) if isinstance(n, ast.Call)
             and ast.unparse(n.func) == "torch.ops._C_ascend.npu_recurrent_gated_delta_rule"]
    if len(calls) != 3:
        raise RuntimeError("native GDN consumer count drift")
    # The spec route is unreachable by admission and remains native in source.
    # Match the exact state-indices keyword rather than relying on AST order.
    count = 0
    for call in calls:
        indices = next(k.value for k in call.keywords if k.arg == "ssm_state_indices")
        if ast.unparse(indices) == "spec_state_indices_tensor.flatten()":
            continue
        call.func = ast.Name("_deltalog_route", ast.Load())
        call.args.insert(0, ast.Name("self", ast.Load()))
        count += 1
    if count != 2:
        raise RuntimeError("mixed/pure non-spec routes drift")
    ast.fix_missing_locations(core)
    result = ast.unparse(core) + "\n"
    compile(result, "<DeltaLog pinned GDN core>", "exec")
    return result

def clone_core(source, globals_dict, route):
    ns = dict(globals_dict)
    ns["_deltalog_route"] = route
    exec(compile(specialize_core(source), "<DeltaLog pinned GDN core>", "exec"), ns)
    return ns["_forward_core"]

def copy_edge(state_pointer, stride_bytes, inner_bytes, source_pointer,
              destination_pointer, copy_bytes, slots):
    if stride_bytes < inner_bytes or copy_bytes != inner_bytes:
        raise ValueError("temporal partial/padded copy unsupported")
    ids = []
    for ptr in (source_pointer, destination_pointer):
        offset = ptr - state_pointer
        if offset < 0 or offset % stride_bytes:
            raise ValueError("copy pointer is not a real temporal slot")
        slot = offset // stride_bytes
        if slot >= slots:
            raise ValueError("copy outside temporal arena")
        ids.append(slot)
    return tuple(ids)

def validate_edges(edges):
    dests = [d for s, d in edges if s != d]
    if len(dests) != len(set(dests)):
        raise ValueError("concurrent writes to one temporal destination")
    for source, dest in edges:
        if source != dest and source in dests:
            raise ValueError("copy dependency cycle/chain requires staged snapshots")
    return True
