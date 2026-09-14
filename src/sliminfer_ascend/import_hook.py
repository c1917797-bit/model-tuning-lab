"""One-shot post-import callback used to patch vLLM lazily.

Adapted from the Apache-2.0 HYPIC plugin already validated in this lab.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import sys
from typing import Callable


class PostImportLoader(importlib.abc.Loader):
    def __init__(
        self,
        loader: importlib.abc.Loader,
        callback: Callable,
        finder: "PostImportFinder",
    ) -> None:
        self._loader = loader
        self._callback = callback
        self._finder = finder

    def create_module(self, spec):  # pragma: no cover - import machinery
        create_module = getattr(self._loader, "create_module", None)
        if create_module is None:
            return None
        return create_module(spec)

    def exec_module(self, module):  # pragma: no cover - import machinery
        self._loader.exec_module(module)
        self._finder.uninstall()
        self._callback(module)


class PostImportFinder(importlib.abc.MetaPathFinder):
    def __init__(self, module_name: str, callback: Callable) -> None:
        self._module_name = module_name
        self._callbacks = [callback]
        self._installed = False

    def add_callback(self, callback: Callable) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _run_callbacks(self, module) -> None:
        for callback in tuple(self._callbacks):
            callback(module)

    def install(self) -> None:
        if self._installed:
            return
        for finder in sys.meta_path:
            if (
                isinstance(finder, PostImportFinder)
                and finder._module_name == self._module_name
            ):
                for callback in self._callbacks:
                    finder.add_callback(callback)
                return
        sys.meta_path.insert(0, self)
        self._installed = True

    def uninstall(self) -> None:
        if not self._installed:
            return
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass
        self._installed = False

    def find_spec(self, fullname, path, target=None):  # pragma: no cover
        if fullname != self._module_name:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None:
            return spec
        spec.loader = PostImportLoader(spec.loader, self._run_callbacks, self)
        return spec
