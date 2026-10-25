"""Default-off hash-bound loader for the selective graph candidate.

The original official SourceFileLoader executes the pinned worker module first.
Only after its registration/import completes does the explicit facade install.
"""
import hashlib
import importlib.abc
import importlib.machinery
import inspect
import json
import marshal
import os
from pathlib import Path
import sys
import threading

from .source_contract import verify_raw_function

PROFILE = "selective-prefill-native-decode-v1"
WORKER = "vllm_ascend.worker.model_runner_v1"
WORKER_SHA256 = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
_NATIVE_LOADER = importlib.machinery.SourceFileLoader
_NATIVE_EXEC = _NATIVE_LOADER.exec_module
_NATIVE_CODE = _NATIVE_LOADER.get_code
_finder = None
_stop = None
_scheduler_stop = None



def _io_budget_enabled(manifest):
    value=os.environ.get("INDEPENDENT_EVIDENCE_IO_BUDGET","0")
    if value not in("0","1"):
        raise ValueError("explicit evidence IO observer environment required")
    setting=manifest.get("evidence_io_budget")
    if setting is None:
        if value!="0":raise ValueError("enabled evidence IO observer needs bound manifest")
        return False
    if(setting!={"enabled":True,"profile":"owned-evidence-io-budget-v1"}or value!="1"
       or "independent_evidence_io_budget.py"not in manifest["source_sha256"]):
        raise ValueError("evidence IO observer manifest/environment mismatch")
    return True



def _step_durability_enabled(manifest):
    value=os.environ.get("INDEPENDENT_EVIDENCE_STEP_DURABILITY","0")
    if value not in("0","1"):
        raise ValueError("explicit step durability environment required")
    setting=manifest.get("step_durability")
    if setting is None:
        if value!="0":raise ValueError("step durability needs bound manifest")
        return False
    if(setting!={"enabled":True,"profile":"selected-model-step-durability-v1"}or value!="1"
       or "independent_evidence_step_durability.py"not in manifest["source_sha256"]):
        raise ValueError("step durability manifest/environment mismatch")
    return True

def _close_durability(policy,error=None):
    if policy is None:return
    try:policy.close()
    except BaseException as cleanup:
        if error is None:raise
        if hasattr(error,"add_note"):
            error.add_note("Owned durability close failed: "+type(cleanup).__name__+": "+str(cleanup)[:512])


def _uninstall_owned():
    global _finder, _stop, _scheduler_stop
    if _stop is not None:
        _stop()
        _stop = None
    elif _finder in sys.meta_path:
        sys.meta_path.remove(_finder)
    _finder = None
    if _scheduler_stop is not None:
        _scheduler_stop()
        _scheduler_stop = None


def _verified_native_spec(spec):
    original = spec.loader
    package = sys.modules.get("vllm_ascend")
    if package is None or not getattr(package, "__file__", None):
        raise ValueError("actual official Ascend package origin required")
    path = Path(package.__file__).resolve().parent / "worker/model_runner_v1.py"
    if (spec.name != WORKER or spec.submodule_search_locations is not None
            or type(original) is not _NATIVE_LOADER
            or _NATIVE_LOADER.exec_module is not _NATIVE_EXEC
            or _NATIVE_LOADER.get_code is not _NATIVE_CODE
            or vars(original).keys() != {"name", "path"}
            or original.name != WORKER
            or Path(original.path).resolve() != path
            or Path(spec.origin).resolve() != path):
        raise ValueError("exact original native worker importer required")
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != WORKER_SHA256:
        raise ValueError("official native worker source drift")
    code = original.get_code(WORKER)
    if (Path(code.co_filename).resolve() != path
            or code != compile(source, code.co_filename, "exec",
                               dont_inherit=True, optimize=sys.flags.optimize)):
        raise ValueError("native importer executable code differs from pinned source")
    return original, path, source, code


def _manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text())
    base = path.parent
    if manifest.get("graph_profile") != PROFILE:
        raise ValueError("explicit selective graph profile required")
    sources = manifest.get("source_sha256")
    if type(sources) is not dict or not sources:
        raise ValueError("complete frozen source hash map required")
    required = {
        "graph_candidate/__init__.py", "graph_candidate/activation.py",
        "graph_candidate/source_contract.py", "graph_candidate/entry_router.py",
        "graph_candidate/prefill_bridge.py", "graph_candidate/worker_loader.py",
        "graph_candidate/native_warmup.py",
        "graph_candidate/bootstrap/sitecustomize.py",
        "independent_compact_activation.py", "independent_compact_model_hook.py",
        "independent_c2_block_table_snapshot.py", "independent_runner_context.py",
        "independent_compact_gdn_hook.py", "independent_public_gdn_hook.py",
        "experimental_c2_layer_barrier.py"}
    if not required <= sources.keys():
        raise ValueError("manifest omits graph loader or unchanged helper bindings")
    for name, digest in sources.items():
        file = (base / name).resolve()
        if (type(name) is not str or not file.is_relative_to(base)
                or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest):
            raise ValueError("graph package source drift: " + str(name))
    config_file = (base / manifest["config"]).resolve()
    if (not config_file.is_relative_to(base)
            or manifest["config"] not in sources):
        raise ValueError("graph config must be hash-bound inside package")
    # Bind the actual already imported candidate package, not an unrelated copy.
    if Path(__file__).resolve() != base / "graph_candidate/worker_loader.py":
        raise ValueError("graph manifest does not own actual loader source")
    config = json.loads(config_file.read_text())
    if "evidence_profile" in config and "independent_quality_evidence_policy.py" not in sources:
        raise ValueError("quality policy must be frozen in source map")
    if (config.get("scheduler_admission_enabled") is True
            and any(key in config for key in ("public_segments", "public_catalog_artifact"))
            and not {"independent_catalog_scheduler_loader.py",
                     "independent_catalog_scheduler_admission.py"} <= sources.keys()):
        raise ValueError("catalog scheduler must be frozen in source map")
    return path, manifest, config


def _take_quality_policy(config):
    if "evidence_profile" not in config:
        return None
    from independent_quality_evidence_policy import QualityEvidencePolicy
    return QualityEvidencePolicy(config.pop("evidence_profile"))


def _enable_bound_scheduler(manifest_path, config, raw, *, enabled, request_limit):
    if "public_segments" in config:
        from independent_catalog_scheduler_loader import enable_scheduler
        return enable_scheduler(manifest_path, config, raw, enabled=enabled,
                                request_limit=request_limit)
    from independent_pic_scheduler_loader import enable_scheduler
    return enable_scheduler(manifest_path, config, raw, enabled=enabled)


def enable():
    global _finder, _stop, _scheduler_stop
    if os.environ.get("INDEPENDENT_GRAPH_HYPIC") != "1":
        return lambda: None
    if _finder is not None or _stop is not None or WORKER in sys.modules:
        raise ValueError("graph loader must precede first official worker import")
    for name in ("independent_compact_loader", "independent_quality_compact_loader"):
        previous = sys.modules.get(name)
        if previous is not None and (getattr(previous, "_finder", None) is not None
                                    or getattr(previous, "_stop", None) is not None):
            raise ValueError("another compact worker loader is already active")
    manifest_path, manifest, config = _manifest(os.environ["INDEPENDENT_GRAPH_MANIFEST"])
    from independent_catalog_artifact import resolve_catalog_config
    from independent_evidence_limits import evidence_limits
    config = resolve_catalog_config(config)
    policy = _take_quality_policy(config)
    limits = evidence_limits(config.pop("evidence_limits", None))
    io_enabled = _io_budget_enabled(manifest)
    step_enabled = _step_durability_enabled(manifest)
    if io_enabled and step_enabled:
        raise ValueError("IO observation and durability treatment are separate")
    if (io_enabled or step_enabled) and policy is not None:
        raise ValueError("IO diagnostic/treatment requires the full original evidence profile")
    scheduler_enabled = config.pop("scheduler_admission_enabled", False)
    if type(scheduler_enabled) is not bool:
        raise ValueError("explicit scheduler admission boolean required")
    if "public_token_artifact" in config:
        if "public_tokens" in config or "public_token_recipe" in config:
            raise ValueError("ambiguous public token configuration")
        from independent_public_token_artifact import public_tokens_from_artifact
        config["public_tokens"] = public_tokens_from_artifact(config.pop("public_token_artifact"))
    if "public_token_recipe" in config:
        if "public_tokens" in config:
            raise ValueError("ambiguous public token configuration")
        from synthetic_compact_workload import public_tokens_from_recipe
        config["public_tokens"] = public_tokens_from_recipe(config.pop("public_token_recipe"))
    raw = Path(os.environ["INDEPENDENT_GRAPH_RAW"])
    if not raw.is_absolute() or not raw.is_dir():
        raise ValueError("existing absolute graph raw root required")
    _scheduler_stop = _enable_bound_scheduler(manifest_path, config, raw,
        enabled=scheduler_enabled, request_limit=limits["max_requests"])
    source_bindings = {name[:-3]: digest for name, digest in manifest["source_sha256"].items()
                       if name.endswith(".py") and "/" not in name}
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    class Loader:
        def __init__(self, original, path, source, code):
            self.original, self.path, self.source, self.code = original, path, source, code
        def create_module(self, spec):
            return self.original.create_module(spec)
        def exec_module(self, module):
            try:
                return self._exec_verified_module(module)
            except BaseException:
                # The facade unwinds its own partial hooks; remove this
                # loader's owned import/scheduler hooks as well.
                _uninstall_owned()
                raise
        def _exec_verified_module(self, module):
            global _stop, _finder
            self.original.exec_module(module)
            if (sys.modules.get(WORKER) is not module
                    or Path(module.__file__).resolve() != self.path
                    or self.path.read_bytes() != self.source
                    or self.original.get_code(WORKER) != self.code):
                raise ValueError("native worker importer/source changed during execution")
            cls = getattr(module, "NPUModelRunner", None)
            if not isinstance(cls, type) or cls.__module__ != WORKER:
                raise ValueError("actual native NPUModelRunner registration missing")
            forward_policy = inspect.getattr_static(cls, "_should_build_dummy_attn_metadata")
            verify_raw_function(module, self.source, forward_policy,
                name="_should_build_dummy_attn_metadata",
                qualname="NPUModelRunner._should_build_dummy_attn_metadata")
            path = raw / ("compact-worker-" + str(os.getpid()) + ".jsonl")
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            lock = threading.Lock()
            count = size = 0
            fsync = os.fsync
            def raw_emit(event):
                nonlocal count, size
                if policy is not None:
                    event = policy.select(event)
                    if event is None:
                        return
                event = dict(event, pid=os.getpid(), manifest_sha256=manifest_hash)
                data = (json.dumps(event, sort_keys=True) + "\n").encode()
                with lock:
                    if count >= limits["max_events"] or size + len(data) > limits["max_bytes"]:
                        raise ValueError("graph evidence bound exceeded")
                    view = memoryview(data)
                    while view:
                        written = os.write(fd, view)
                        if written <= 0:
                            raise OSError("short graph evidence write")
                        view = view[written:]
                    fsync(fd)
                    count += 1
                    size += len(data)
            durability = None
            try:
                emit = raw_emit
                if step_enabled:
                    import independent_evidence_step_durability as step_module
                    from .prefill_bridge import verify_support
                    source = verify_support(step_module, manifest["source_sha256"]["independent_evidence_step_durability.py"])
                    for name in ("selected_step", "make_durability"):
                        verify_raw_function(step_module, source, getattr(step_module, name), name=name)
                    for name, value in vars(step_module.StepDurability).items():
                        if inspect.isfunction(value):
                            verify_raw_function(step_module, source, value, name=name,
                                qualname="StepDurability." + name)
                    durability = step_module.make_durability(fd, os.fsync, lambda: (count, size))
                    fsync = durability.fsync
                    emit = durability.wrap(raw_emit)
                if io_enabled:
                    import independent_evidence_io_budget as io_module
                    from .prefill_bridge import verify_support
                    source = verify_support(io_module, manifest["source_sha256"]["independent_evidence_io_budget.py"])
                    for name in ("selected_step", "interval_union_ns", "make_budget"):
                        verify_raw_function(io_module, source, getattr(io_module, name), name=name)
                    for name, value in vars(io_module.EvidenceIOBudget).items():
                        if inspect.isfunction(value):
                            verify_raw_function(io_module, source, value, name=name,
                                qualname="EvidenceIOBudget." + name)
                    budget = io_module.make_budget(fd, os.fsync, lambda: (count, size))
                    fsync = budget.fsync
                    emit = budget.wrap(raw_emit)
                emit.source_manifest_sha256 = manifest_hash
                emit.stage_capture_root = str(raw)
                if policy is not None:
                    emit(policy.descriptor())
                emit({"event": "graph_native_worker_import_verified",
                      "graph_profile": PROFILE, "native_source_sha256": WORKER_SHA256,
                      "native_code_sha256": hashlib.sha256(marshal.dumps(self.code)).hexdigest(),
                      "native_module_origin": str(self.path),
                      "native_loader": type(self.original).__module__ + "." + type(self.original).__qualname__,
                      "original_importer_executed": True,
                      "native_dummy_metadata_policy_verified": True,
                      "scope": "source/import identity; not graph execution proof"})
                from .activation import activate_graph_candidate
                remove = activate_graph_candidate(config, enabled=True, emit=emit,
                    source_bindings=source_bindings, request_progress_limit=limits["max_requests"])
            except BaseException as error:
                try:
                    _close_durability(durability, error)
                finally:
                    os.close(fd)
                raise
            def stop():
                failure = None
                try:
                    remove()
                except BaseException as error:
                    failure = error
                    raise
                finally:
                    try:
                        _close_durability(durability, failure)
                    finally:
                        os.close(fd)
            _stop = stop
            if _finder not in sys.meta_path:
                stop()
                _stop = None
                raise ValueError("graph finder ownership changed")
            sys.meta_path.remove(_finder)

    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname != WORKER:
                return None
            spec = importlib.machinery.PathFinder.find_spec(fullname, path)
            if spec is None or spec.loader is None:
                raise ImportError(fullname)
            original, origin, source, code = _verified_native_spec(spec)
            spec.loader = Loader(original, origin, source, code)
            return spec

    _finder = Finder()
    sys.meta_path.insert(0, _finder)
    def uninstall():
        _uninstall_owned()
    return uninstall
