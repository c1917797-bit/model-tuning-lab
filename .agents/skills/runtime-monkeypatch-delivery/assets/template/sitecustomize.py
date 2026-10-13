"""Disabled-by-default loader for a copied runtime monkeypatch package."""

import importlib
import json
import os
import sys


if os.environ.get("MODEL_TUNING_RUNTIME_PATCH_ENABLE") == "1":
    try:
        module_name, callable_name = os.environ.get(
            "MODEL_TUNING_RUNTIME_PATCH_ENTRYPOINT", "patch:activate"
        ).split(":", 1)
        activate = getattr(importlib.import_module(module_name), callable_name)
        activate()
    except Exception as exc:
        # CPython can swallow sitecustomize exceptions and run the service
        # unpatched. A launcher probe cannot prove worker-local activation.
        try:
            print(
                json.dumps(
                    {"event": "MODEL_TUNING_PATCH_FAILED", "pid": os.getpid(),
                     "error_type": type(exc).__name__},
                    sort_keys=True,
                ),
                file=sys.stderr,
                flush=True,
            )
        finally:
            os._exit(78)
    print(
        json.dumps(
            {
                "event": "MODEL_TUNING_PATCH_ACTIVE",
                "pid": os.getpid(),
                "module": module_name,
                "entrypoint": callable_name,
            },
            sort_keys=True,
        ),
        file=sys.stderr,
        flush=True,
    )
