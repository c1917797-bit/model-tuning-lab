"""Build standard lm-eval configs with local datasets; no serving or scoring.

Inspection only: returned configs contain unresolved function references and
must NOT be passed to an evaluator. Runtime/scoring readiness is a separate gate.
Only custom_dataset changes. HumanEval utilities are deliberately not imported:
the pinned upstream utils module loads code_eval and executes a sample on import.
"""
import argparse
from functools import partial
from pathlib import Path
import sys

import offline_standard_data as local


def inspect_configs(harness, data_root):
    from lm_eval.tasks._yaml_loader import load_yaml
    task_root = Path(harness) / "lm_eval/tasks"
    specs = [(p, local.mmlu, p.stem.removeprefix("mmlu_"))
             for p in sorted((task_root / "mmlu/default").glob("mmlu_*.yaml"))]
    specs += [(task_root / "gsm8k/gsm8k.yaml", local.gsm8k, None),
              (task_root / "humaneval/humaneval_instruct.yaml", local.humaneval, None)]
    if len(specs) != 59:
        raise ValueError("Expected 57 MMLU subjects and two other tasks")
    configs = []
    for path, provider, subject in specs:
        original = load_yaml(path, resolve_func=False)
        config = dict(original)
        kwargs = {"data_root": str(data_root)}
        if subject is not None:
            kwargs["subject"] = subject
        config["custom_dataset"] = partial(provider, **kwargs)
        assert all(config[k] == v for k, v in original.items())
        configs.append(config)
    return configs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--data-root", required=True)
    args = parser.parse_args()
    sys.path.insert(0, args.harness)
    import datasets

    def no_hub(*args, **kwargs):
        raise AssertionError("Unexpected datasets.load_dataset/Hub call")
    datasets.load_dataset = no_hub
    configs = inspect_configs(args.harness, args.data_root)
    total = 0
    for config in configs:
        data = config["custom_dataset"]()
        count = len(data[config["test_split"]])
        total += count
        if config["task"].startswith("mmlu_"):
            assert config["output_type"] == "multiple_choice"
            assert len(data["dev"]) == 5
            assert config["doc_to_choice"] == ["A", "B", "C", "D"]
            assert all(0 <= x < 4 for x in data["test"]["answer"])
        elif config["task"] == "gsm8k":
            assert len(data["train"]) == 7473 and count == 1319
            assert config["num_fewshot"] == 5
        else:
            assert config["task"] == "humaneval_instruct" and count == 164
        print(config["task"], count)
    assert total == 15525
    assert not any("/humaneval/utils.py" in str(getattr(m, "__file__", ""))
                   for m in tuple(sys.modules.values()))
    print("PASS: 59 standard config inspections; 15525 test rows; no Hub loader calls")
    print("Scope: unresolved configs and datasets only; no model requests or scoring")


if __name__ == "__main__":
    main()
