"""Prospective retained-alias-safe lifecycle; frozen r23/r24 modules unchanged."""
from __future__ import annotations
import functools
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import os
from pathlib import Path
import sys

SWITCH = "HYPIC_STATE_OBSERVER_ENABLE"
PLUGIN_SHA = "84cfc3a61ac52aec9c40f6272fbab3768d728b7e0f94225c50b40ff3857f4fd8"
TARGET = "hypic_vllm_ascend"


class Session:
    """One selected request/step per worker; sealing also executes uninstallation."""
    def __init__(self, modules, config, *, rank, device, source_hashes=None):
        from numerical_state_capture import Collector
        from numerical_state_observer_v2 import install_step_receipt
        from numerical_state_writer import RawWriter
        self.modules, self.config = modules, config
        self.step = None
        self.done = False
        self.stages = set()
        self.handles = []
        self.writer = RawWriter(config["raw_root"], metadata=dict(
            request_id=config["request_id"], rank=rank, pid=os.getpid(),
            container_visible_device=device, physical_device_proven=False,
            manifest_sha256=config["manifest_sha256"]))
        self.collector = Collector(self.writer, rank=rank,
                                   attention_module=modules["attention"])
        try:
            handle = install_step_receipt(
                modules["runner"], self.finish, request_id=config["request_id"],
                rank=rank, source_hash=(source_hashes or {}).get("runner"))
            self.handles.append(handle)
        except Exception:
            self.writer.failed = True
            raise

    def capture(self, stage, request_id, frame):
        if self.done:
            return
        step = int(frame["ctx"].batch_plan.step_id)
        if self.step is None:
            self.step = step
        if step != self.step or stage in self.stages:
            raise RuntimeError("bounded observer requires one event per stage in one step")
        self.collector(stage, request_id, frame)
        self.stages.add(stage)

    def finish(self, receipt):
        if self.done:
            return
        required = {"positions_committed", "kv_committed", "gdn_initial", "gdn_committed"}
        if receipt["step"] != self.step or self.stages != required:
            self.writer.failed = True
            raise RuntimeError("incomplete bounded integrated state capture")
        self.writer(receipt)
        for handle in reversed(self.handles):
            handle.uninstall()
        self.writer.seal()
        self.done = True

    def rollback(self):
        for handle in reversed(self.handles):
            handle.uninstall()
        self.done = True
        # Never create a success seal for an incomplete capture.


class BaseRuntimeAdapter:
    def __init__(self, plugin, config):
        self.plugin, self.config = plugin, config
        self.observer = self.session = None
        self.original = plugin.register
        if (hashlib.sha256(Path(plugin.__file__).read_bytes()).hexdigest() != PLUGIN_SHA
                or self.original.__code__.co_filename != plugin.__file__):
            raise ValueError("HYPIC registration source mismatch")

        @functools.wraps(self.original)
        def register():
            result = self.original()
            if self.observer is None:
                if os.environ.get("VLLM_ASCEND_HYPIC_ENABLE") != "1":
                    raise RuntimeError("state diagnostic requires HYPIC enabled")
                from numerical_state_observer_v2 import install
                self.modules = {name: importlib.import_module(TARGET+".patches."+name)
                                for name in ("attention", "gdn", "runner")}
                self.observer = install(self.modules, self.capture,
                    request_id=config["request_id"], layers={config["kv_layer"], config["gdn_layer"]},
                    randomized_request_id=True)
            return result
        self.replacement = register
        plugin.register = register

    def capture(self, stage, request_id, frame):
        try:
            if self.session is None:
                # Resolve actual initialized TP rank at selected hot forward.
                import torch
                from vllm.distributed.parallel_state import get_tp_group
                group = get_tp_group()
                if group.world_size != 4:
                    raise RuntimeError("diagnostic requires TP4")
                resolved_config = dict(self.config, request_id=request_id)
                self.session = Session(self.modules, resolved_config,
                    rank=int(group.rank_in_group), device=int(torch.npu.current_device()))
                self.session.handles.append(self.observer)
            self.session.capture(stage, request_id, frame)
        except Exception:
            if self.session is not None:
                self.session.writer.failed = True
                self.session.rollback()
            elif self.observer is not None:
                self.observer.uninstall()
            raise

    def uninstall(self):
        if self.session is not None:
            self.session.rollback()
        elif self.observer is not None:
            self.observer.uninstall()
        if self.plugin.register is not self.replacement:
            raise RuntimeError("registration ownership changed")
        self.plugin.register = self.original


class RuntimeAdapter(BaseRuntimeAdapter):
    def __init__(self, plugin, config):
        super().__init__(plugin, config)
        registered = self.replacement

        @functools.wraps(registered)
        def register():
            try:
                result = registered()
                print(json.dumps(dict(schema="hypic-state-observer-installed/v3",
                    pid=os.getpid(), manifest_sha256=config["manifest_sha256"],
                    plugin_sha256=PLUGIN_SHA, request_id=config["request_id"],
                    kv_layer=config["kv_layer"], gdn_layer=config["gdn_layer"])),
                    file=sys.stderr, flush=True)
                return result
            except Exception:
                # vLLM catches Exception and may silently continue serving.
                import traceback
                traceback.print_exc()
                raise SystemExit(78)
        self.replacement = register
        plugin.register = register


class RegistrationFinder(importlib.abc.MetaPathFinder):
    def __init__(self, config):
        self.config, self.adapter = config, None

    def find_spec(self, fullname, path=None, target=None):
        if fullname != TARGET:
            return None
        # Preserve PEP660 editable resolvers later in meta_path.
        spec = None
        for finder in tuple(sys.meta_path):
            if isinstance(finder, RegistrationFinder):
                continue
            method = getattr(finder, "find_spec", None)
            if method is not None:
                spec = method(fullname, path, target)
                if spec is not None:
                    break
        if spec is None or spec.loader is None:
            raise ImportError("HYPIC target not available through full meta-path")
        original_loader, owner = spec.loader, self

        class Loader(importlib.abc.Loader):
            def create_module(self, spec):
                method = getattr(original_loader, "create_module", None)
                return method(spec) if method else None

            def exec_module(self, module):
                original_loader.exec_module(module)
                owner.adapter = RuntimeAdapter(module, owner.config)

        spec.loader = Loader()
        return spec

    def uninstall(self):
        if self.adapter is not None:
            self.adapter.uninstall()
        if self in sys.meta_path:
            sys.meta_path.remove(self)


def activate(config):
    if os.environ.get(SWITCH) != "1":
        return None
    if TARGET in sys.modules:
        raise RuntimeError("install diagnostic before HYPIC import")
    if any(isinstance(item, RegistrationFinder) for item in sys.meta_path):
        raise RuntimeError("diagnostic import hook already installed")
    required = {"raw_root", "request_id", "kv_layer", "gdn_layer", "manifest_sha256"}
    if set(config) != required or not all(isinstance(v, str) and v for v in config.values()):
        raise ValueError("exact diagnostic config required")
    if config["kv_layer"] == config["gdn_layer"]:
        raise ValueError("distinct selected layers required")
    if len(config["manifest_sha256"]) != 64:
        raise ValueError("manifest identity required")
    finder = RegistrationFinder(dict(config))
    sys.meta_path.insert(0, finder)
    return finder
