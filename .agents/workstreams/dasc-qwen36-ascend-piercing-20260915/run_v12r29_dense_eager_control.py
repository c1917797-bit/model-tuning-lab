#!/usr/bin/env python3
"""Matched dense eager control for the v12r28 eager DASC failure."""
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "dasc_v12r28_trial",
    HERE / "run_v12r28_eager_resource_retry.py",
)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load DASC v12r28 eager controller")
trial = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trial)

controller = trial.controller
controller.RESULT = Path(
    "/cache/cch/dasc-qwen36-ascend-20260915/"
    "dense-eager-exact-prefix-control-v12r29"
)
controller.CONTAINER = "dasc_qwen36_dense_eager_exact_v12r29_20260918"
controller.PLUGIN_MODE = "compat-head256"
controller.PREVIOUS_CANARY = HERE / "run_dense_eager_replay_probe.py"
controller.CANARY_EXTRA_ARGS = ()
controller.ENFORCE_EAGER = True
controller.validate_allocation_evidence = lambda: None


def disable_treatment_only_verdicts(root_module) -> tuple[str, ...]:
    """Keep resource guards while removing DASC-treatment-only verdicts."""
    names = []
    seen = set()
    module = root_module
    for _ in range(32):
        if module is None or id(module) in seen:
            break
        seen.add(id(module))
        for name in (
            "validate_all_heads_evidence",
            "validate_branch_evidence",
            "validate_state_index_evidence",
        ):
            if hasattr(module, name):
                setattr(module, name, lambda: None)
                names.append(name)
        module = getattr(module, "trial", None)
    return tuple(sorted(names))


DISABLED_TREATMENT_VERDICTS = disable_treatment_only_verdicts(trial)


def main() -> int:
    return trial.main()


if __name__ == "__main__":
    raise SystemExit(main())
