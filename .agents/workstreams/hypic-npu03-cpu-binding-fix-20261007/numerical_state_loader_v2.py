"""Prospective r23 import repair; frozen v1 and its experiment stay unchanged."""
import importlib.abc
import sys
import numerical_state_loader as frozen

RuntimeAdapter = frozen.RuntimeAdapter


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
