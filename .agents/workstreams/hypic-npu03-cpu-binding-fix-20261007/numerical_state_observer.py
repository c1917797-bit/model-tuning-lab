"""Opt-in source-bound observation seams; no device launcher or acceptance claim."""
from __future__ import annotations

import ast
import hashlib
import os
import re
import types
from dataclasses import dataclass
from pathlib import Path

SWITCH = "HYPIC_STATE_OBSERVER_ENABLE"
HOOK = "_hypic_diagnostic_state_observer"
SPECS = {
    "attention": ("0e13fbf953f40d3e6103fc7e4b1858755d8992d108d8b1763659aa29fb502876",
                  "_repair_position_independent_kv"),
    "gdn": ("72d58fdf03a4317ee4493ac475cd4b059ae3ed7f9138243446737a860537623d",
            "_position_independent_gdn_core"),
    "runner": ("5d3078267d55e6ca41000ba195c387e2f3fc6fec6bbe89cf73b8a67fbfb8f8e0", "_rewrite_position_independent_inputs"),
}


def hook(stage):
    return ast.Expr(ast.Call(ast.Name(HOOK, ast.Load()),
                             [ast.Constant(stage), ast.Call(
                                 ast.Name("locals", ast.Load()), [], [])], []))


class GDNHooks(ast.NodeTransformer):
    def __init__(self):
        self.initial = self.committed = 0

    def visit_Assign(self, node):
        if any(isinstance(t, ast.Name) and t.id == "cache_composes"
               for t in node.targets):
            self.initial += 1
            return [hook("gdn_initial"), node]
        return node

    def visit_Expr(self, node):
        value = node.value
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "index_copy_"
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "ssm_cache"):
            self.committed += 1
            return [node, hook("gdn_committed")]
        return node


def instrument(source, filename, function_name, namespace, component):
    tree = ast.parse(source, filename)
    definitions = [node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == function_name]
    if len(definitions) != 1:
        raise ValueError("expected one exact function")
    function = definitions[0]
    if function.decorator_list:
        raise ValueError("unexpected decorator; review source boundary")
    if component == "gdn":
        injector = GDNHooks()
        function = injector.visit(function)
        if (injector.initial, injector.committed) != (1, 1):
            raise ValueError("GDN observation seam drift")
    elif component in {"attention", "runner"}:
        function.body.append(hook("kv_committed" if component == "attention"
                                  else "positions_committed"))
    else:
        raise ValueError("unknown observation component")
    unit = ast.fix_missing_locations(ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[
            ast.alias(name="annotations")], level=0), function], type_ignores=[]))
    local = {}
    exec(compile(unit, filename, "exec", dont_inherit=True), namespace, local)
    return local[function_name]


@dataclass
class Handle:
    changes: list
    globals_added: list

    def uninstall(self):
        # Refuse to overwrite another actor's later patch.
        for module, name, original, replacement in self.changes:
            if getattr(module, name) is not replacement:
                raise RuntimeError("observer function ownership changed")
        for module, callback in self.globals_added:
            if getattr(module, HOOK) is not callback:
                raise RuntimeError("observer global ownership changed")
        for module, name, original, _replacement in reversed(self.changes):
            setattr(module, name, original)
        for module, _callback in self.globals_added:
            delattr(module, HOOK)
        self.changes.clear()
        self.globals_added.clear()


class RequestIdentity:
    """Bind once to one observed ID; never use an unconstrained prefix match."""
    def __init__(self, request_id, randomized=False):
        self.request_id = request_id
        self.randomized = randomized
        self.bound = None

    def resolve(self, request_ids):
        pattern = re.escape(self.request_id) + r"-[0-9a-f]{8}"
        matches = [value for value in request_ids
                   if (re.fullmatch(pattern, value) if self.randomized
                       else value == self.request_id)]
        if len(matches) > 1:
            raise RuntimeError("ambiguous diagnostic request identity")
        if not matches:
            return None
        actual = matches[0]
        if self.bound is not None and actual != self.bound:
            raise RuntimeError("diagnostic request identity rebound")
        self.bound = actual
        return actual


def install(modules, callback, *, request_id, layers, source_hashes=None,
            randomized_request_id=False):
    """Bind to explicit modules. Callback must synchronously copy owned snapshots.

    Disabled mode returns before source reads, imports, or mutations. No log
    or snapshot alone is a substitute for independently joined hot receipts.
    """
    if os.environ.get(SWITCH) != "1":
        return Handle([], [])
    if not request_id or not layers or not callable(callback):
        raise ValueError("explicit request, layer allowlist and callback required")
    if set(modules) != set(SPECS):
        raise ValueError("all three exact runtime modules required")
    hashes = source_hashes or {k: v[0] for k, v in SPECS.items()}
    prepared = []
    for component, (_expected, name) in SPECS.items():
        module = modules[component]
        path = Path(module.__file__)
        raw = path.read_bytes()
        if not hashes.get(component) or hashlib.sha256(raw).hexdigest() != hashes[component]:
            raise ValueError("runtime source hash mismatch: " + component)
        if hasattr(module, HOOK):
            raise RuntimeError("observer global already exists")
        original = getattr(module, name)
        # Refuse to replace unrelated wrappers, even if the file matches.
        if (not isinstance(original, types.FunctionType)
                or original.__code__.co_filename != str(path)
                or original.__name__ != name):
            raise ValueError("runtime callable identity mismatch: " + component)
        replacement = instrument(raw.decode(), str(path), name, module.__dict__, component)
        prepared.append((module, name, original, replacement))

    allowed_layers = frozenset(layers)
    identity = RequestIdentity(request_id, randomized_request_id)

    def observe(stage, frame):
        ctx = frame.get("ctx")
        if ctx is None:
            return
        actual_id = identity.resolve(ctx.req_ids)
        if actual_id is None:
            return
        if stage != "positions_committed" and frame.get("layer_name") not in allowed_layers:
            return
        plan = ctx.plans.get(actual_id)
        if plan is None or not any(entry is not None for entry in plan.entries):
            return
        callback(stage, actual_id, frame)

    handle = Handle([], [])
    try:
        for module, name, original, replacement in prepared:
            setattr(module, HOOK, observe)
            handle.globals_added.append((module, observe))
            setattr(module, name, replacement)
            handle.changes.append((module, name, original, replacement))
    except Exception:
        handle.uninstall()
        raise
    return handle


def install_step_receipt(runner, emit, *, request_id, rank, source_hash=None):
    """Observe successful existing hybrid validation, without weakening it."""
    if os.environ.get(SWITCH) != "1":
        return Handle([], [])
    import functools
    import inspect
    if not request_id or type(rank) is not int or rank not in range(4) or not callable(emit):
        raise ValueError("explicit request/rank/emitter required")
    path = Path(runner.__file__)
    expected = source_hash or SPECS["runner"][0]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("receipt runner source hash mismatch")
    name = "_validate_and_emit_hot_request_evidence"
    original = getattr(runner, name)
    if (not isinstance(original, types.FunctionType)
            or original.__code__.co_filename != str(path)
            or original.__name__ != name):
        raise ValueError("receipt callable identity mismatch")
    signature = inspect.signature(original)

    @functools.wraps(original)
    def observed(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        result = original(*args, **kwargs)
        ctx = bound.arguments["ctx"]
        skipped = ctx.verified_hot_request_tokens.get(request_id, 0)
        if skipped > 0:
            emit({
                "schema": "hypic-state-step-receipt/v1",
                "event": "observer_validated_hot_step",
                "request_id": request_id, "rank": rank, "pid": os.getpid(),
                "step": int(ctx.batch_plan.step_id),
                "skipped_prefix_tokens": int(skipped),
                "expected_full_layers": sorted(bound.arguments["expected_full_layers"]),
                "expected_gdn_layers": sorted(bound.arguments["expected_gdn_layers"]),
                "validation_completed": True,
                "runtime_source_sha256": expected,
            })
        return result

    setattr(runner, name, observed)
    return Handle([(runner, name, original, observed)], [])
