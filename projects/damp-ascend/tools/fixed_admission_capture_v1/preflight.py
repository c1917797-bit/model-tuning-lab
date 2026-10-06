"""MAIN-only target-image no-device import/entrypoint preflight; does not load a model."""
from __future__ import annotations
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading
import unittest
from diag_contract import (COLLECTOR,PACKAGE_ROOT,RUNTIME,canonical,file_sha,overlay_inventory,require,
                           source_contract,write_new,runtime_environment)

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    packet=source_contract()
    environment=runtime_environment(Path(a.report).parent)
    require(sys.version_info[:2]==(3,12) and callable(getattr(threading,"getprofile",None)),
            "actual target public threading.getprofile unavailable")
    require(sys.getprofile() is None and threading.getprofile() is None,
            "target preflight must start with no foreign profile hooks")
    suite=unittest.defaultTestLoader.discover(str(PACKAGE_ROOT/"tests"),pattern="test_contract.py")
    software=unittest.TextTestRunner(verbosity=2).run(suite)
    require(software.wasSuccessful(),"target Python3.12 stdlib behavior regression failed")
    require("torch" not in sys.modules,"no-device stdlib unexpectedly loaded Torch")
    require(str(COLLECTOR) not in sys.path and
            os.environ.get("DAMP_ADMISSION_TRACE_ENABLE")!="1",
            "preflight must be no-device/defaultOFF; old collector metadata path prohibited")
    require(not Path("/dev/davinci0").exists() and not Path("/dev/davinci4").exists(),
            "no-device preflight unexpectedly exposes NPU")
    inventory=overlay_inventory(importlib.metadata.entry_points())
    module=importlib.import_module("damp_capture")
    diagnostic=importlib.import_module("damp_admission_diagnostic")
    require(Path(module.__file__).resolve()==COLLECTOR/"damp_capture/__init__.py" and
            Path(diagnostic.__file__).resolve()==PACKAGE_ROOT/"damp_admission_diagnostic/__init__.py",
            "module-only overlay resolves to wrong source")
    before=set(sys.modules)
    require(diagnostic.register() is None, "defaultOFF register changed state")
    require(not any(name=="torch" or name.startswith("torch.") for name in set(sys.modules)-before),
            "defaultOFF diagnostic imported Torch")
    for path,digest in RUNTIME.items():
        require(file_sha(path)==digest,"actual immutable image source differs: "+path)
    # Frozen runner module is importable through module-only overlay; importing it
    # is stdlib-only and must not run main/create outputs/start model.
    runner=importlib.import_module("damp_capture.run")
    require(Path(runner.__file__).resolve()==COLLECTOR/"damp_capture/run.py","runner source mismatch")
    write_new(a.report,{"schema":"damp-fixed-admission-preflight/v1","status":"source_import_pass",
        "packet":packet,"entrypoint":inventory,"actual_environment":environment,
        "software":{"tests":software.testsRun,"failures":len(software.failures),"errors":len(software.errors),
                    "target_public_profile_api_verified":True},"runtime_sources":RUNTIME,"npu_executed":False,
        "actual_worker_hook_registered":False,"source_lock_issued":False})
    print(json.dumps({"status":"source_import_pass","npu_executed":False}))
if __name__=="__main__":
    main()
