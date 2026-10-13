#!/usr/bin/env python3
"""Replay retained transformation history through the delivered validator."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FIXTURE = HERE / "skill-fixtures" / "repository-transformation" / "target"
spec = importlib.util.spec_from_file_location(
    "delivered_mst_validator", DEFAULT_FIXTURE / "scripts/verify_maintainer_tree.py")
delivered = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivered)
verify_registry_contract = delivered.verify_registry_contract

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    snapshot = json.loads((args.fixture.resolve().parent / "input-snapshot.json").read_text())
    delivered.require(snapshot["misplaced_runtime_skill"].startswith(".agents/skills/"),
                      "input does not exercise runtime separation")
    return delivered.main()

if __name__ == "__main__":
    raise SystemExit(main())
