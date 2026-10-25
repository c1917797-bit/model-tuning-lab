"""Rehearse the actual retained launch constructor; intercept before allocation."""
import contextlib,copy,io,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r36_step_durability_controller as owner

class CaptureOnly(RuntimeError):pass

def capture_contract(contract):
    checked=owner.check_contract(contract,source_root=W,require_new_root=True)
    live=copy.deepcopy(contract);original_command=owner.base.command;captured=[]
    empty={"utc":"rehearsal-not-telemetry","raw":"","processes":[],"owners":[],"foreign":[]}
    def command(argv,**kwargs):
        if argv==["docker","image","inspect",contract["image"]]:
            return original_command(argv,**kwargs)
        if argv==["git","rev-parse","HEAD"]:return original_command(argv,**kwargs)
        if argv[:3]==["ss","-H","-ltn"]:return ""
        if argv[:2]==["docker","run"]:
            captured.append(list(argv))
            raise CaptureOnly("actual base argv captured before Docker allocation")
        raise AssertionError("external action forbidden in launch rehearsal: "+str(argv))
    with tempfile.TemporaryDirectory(prefix="hypic-r36-launch-rehearsal-",dir="/cache/cch")as tmp:
        live["raw_root"]=str(Path(tmp)/"raw")
        with patch.object(owner.base,"snapshot",lambda cid=None:copy.deepcopy(empty)),\
             patch.object(owner.base,"port_free",lambda port:None),\
             patch.object(owner.base,"command",command),contextlib.redirect_stdout(io.StringIO()):
            try:owner.run_contract(live,source_root=W)
            except SystemExit as stopped:
                if stopped.code!=1:raise
            else:raise AssertionError("rehearsal must never complete a device unit")
        terminal=json.loads((Path(live["raw_root"])/"result.json").read_bytes())
        if(len(captured)!=1 or terminal["error"]["type"]!="CaptureOnly"
           or terminal["release"]["owned_container"]is not None):
            raise AssertionError("did not intercept exact actual base allocation boundary")
    argv=captured[0]
    return {"schema":"hypic-r36-actual-launch-capsule/v1","arm":contract["r33_arm"],
        "checked_manifest":contract["successor_manifest"],"source_bindings":checked["source_bindings"],
        "image":contract["image"],"argv":argv,
        "automatic_python_environment":[x for x in argv if x.startswith(("PYTHONPATH=","INDEPENDENT_"))],
        "new_device_allocation":False,"physical_admission_proven":False,
        "scope":"Actual retained base builder and R36 wrapper consumed these arguments, intercepted before Docker run. Only rehearsal scratch path changes; physical/port checks are mocked here and require separate fresh real admission."}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--contract",required=True)
    a=p.parse_args();print(json.dumps(capture_contract(json.loads(Path(a.contract).read_bytes())),sort_keys=True))
