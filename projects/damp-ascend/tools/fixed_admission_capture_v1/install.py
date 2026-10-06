"""Create a Git-external module-only overlay explicitly; imports never write."""
from __future__ import annotations
import argparse
import importlib.metadata
from pathlib import Path
import sys
from diag_contract import (COLLECTOR,PACKAGE_ROOT,overlay_inventory,require,source_contract,write_new)

def install(root):
    source_contract()
    root=Path(root)
    root.mkdir(parents=True,exist_ok=False)
    (root/"damp_capture").symlink_to(COLLECTOR/"damp_capture",target_is_directory=True)
    (root/"damp_admission_diagnostic").symlink_to(PACKAGE_ROOT/"damp_admission_diagnostic",target_is_directory=True)
    metadata=root/"damp_fixed_admission_diagnostic-0.1.0.dist-info"
    metadata.mkdir()
    with (metadata/"METADATA").open("x") as f:
        f.write("Metadata-Version: 2.1\nName: damp-fixed-admission-diagnostic\nVersion: 0.1.0\n")
    with (metadata/"entry_points.txt").open("x") as f:
        f.write("[vllm.general_plugins]\ndamp_capture = damp_admission_diagnostic:register\n")
    # Search only the new overlay for package metadata. The image-wide inventory
    # is independently checked in preflight inside the actual image.
    entries=[e for d in importlib.metadata.distributions(path=[str(root)]) for e in d.entry_points]
    return overlay_inventory(entries)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    print(install(a.output))
if __name__=="__main__":
    main()
