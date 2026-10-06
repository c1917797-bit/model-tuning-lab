#!/usr/bin/env python3
"""Actual explicit library load/schema/Meta only; no NPU dispatch."""
import argparse
import ctypes
import json
import traceback
from gate_contract import (add_identity_arguments, source_bindings, cann_environment_checks,
                           new_output, require, NAMESPACE)
from candidate_adapter import Candidate, loaded_libraries, safe_json

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_identity_arguments(parser)
    args = parser.parse_args()
    out = new_output(args.output_dir)
    report = {"schema":"damp_integer_compaction_meta_v1","status":"running",
              "npu_executed":False,"graph_supported":False,"namespace":NAMESPACE,
              "scope":"actual dlopen/registration/schema/Meta; not NPU arithmetic or serving"}
    try:
        report["bindings"] = source_bindings(args)
        report["cann_environment"] = cann_environment_checks(report["bindings"])
        import torch
        import torch_npu
        report["versions"] = {"torch":torch.__version__,"torch_npu":torch_npu.__version__}
        # RTLD_NOW catches unresolved host symbols before a false Meta receipt.
        handle = ctypes.CDLL(report["bindings"]["library"],mode=ctypes.RTLD_GLOBAL)
        require(getattr(handle,"qwen36_gdn_damp_integer_compaction_v1_decode_kernel",None) is not None,
                "actual exported host launcher absent")
        torch.ops.load_library(report["bindings"]["library"])
        candidate = Candidate()
        report["schemas"] = candidate.schemas()
        report["meta"] = candidate.meta_gate()
        report["loaded_libraries"] = loaded_libraries()
        require(report["loaded_libraries"].get(report["bindings"]["library"]) ==
                args.library_sha256, "actual loaded library path/hash absent")
        report["status"] = "actual_no_device_load_schema_meta_pass"
        return 0
    except BaseException as error:
        report.update(status="failed",error=repr(error),traceback=traceback.format_exc())
        return 1
    finally:
        (out/"report.json").write_text(json.dumps(safe_json(report),indent=2,allow_nan=False)+"\n")
        print(json.dumps({"status":report["status"],"npu_executed":False,"report":str(out/"report.json")}))
if __name__=="__main__":
    raise SystemExit(main())
