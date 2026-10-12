"""Prospective r23 import repair; frozen v1 and its experiment stay unchanged."""
import importlib.abc
import functools
import json
import os
import sys
import numerical_state_loader as frozen


class RuntimeAdapter(frozen.RuntimeAdapter):
    def __init__(self, plugin, config):
        super().__init__(plugin, config)
        registered = self.replacement

        @functools.wraps(registered)
        def register():
            try:
                result = registered()
                print(json.dumps(dict(schema="hypic-state-observer-installed/v2",
                    pid=os.getpid(), manifest_sha256=config["manifest_sha256"],
                    plugin_sha256=frozen.PLUGIN_SHA, request_id=config["request_id"],
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


class RegistrationFinder(frozen.RegistrationFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != frozen.TARGET:
            return None
        # PEP660 editable installs can live in a later MetaPathFinder.
        spec = None
        for finder in tuple(sys.meta_path):
            if isinstance(finder, frozen.RegistrationFinder):
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


def activate(config):
    # Reuse frozen validation, replacing only its not-yet-used finder.
    handle = frozen.activate(config)
    if handle is None:
        return None
    position = sys.meta_path.index(handle)
    replacement = RegistrationFinder(handle.config)
    sys.meta_path[position] = replacement
    return replacement
