#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Print read-only source hashes to stdout before MAIN-controlled fresh build."""
import json
from pathlib import Path
from run_compaction_gate import COMPILED,RUNTIME,sha
root=Path(__file__).resolve().parent
print(json.dumps({"compiled_files":list(COMPILED),
    "files":{p:sha(root/p) for p in RUNTIME}},sort_keys=True,indent=2))
