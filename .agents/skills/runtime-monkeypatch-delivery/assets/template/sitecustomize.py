"""Disabled-by-default loader for a copied runtime monkeypatch package."""

import importlib
import json
import os
import sys


if os.environ.get("MODEL_TUNING_RUNTIME_PATCH_ENABLE") == "1":
    module_name, callable_name = os.environ.get(
        "MODEL_TUNING_RUNTIME_PATCH_ENTRYPOINT", "patch:activate"
    ).split(":", 1)
    activate = getattr(importlib.import_module(module_name), callable_name)
    activate()
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
