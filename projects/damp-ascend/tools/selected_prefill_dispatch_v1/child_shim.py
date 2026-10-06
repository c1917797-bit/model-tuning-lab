"""Same-process frozen gate shim; no substitute math, snapshots or PASS receipts."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback

sys.dont_write_bytecode = True
os.environ["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
import controller as c

def image_admission(argv, packet_sha):
    c.packet(packet_sha)
    runtime, contract, _, _, _, _, _ = c.closure()
    c.require(argv and argv[0] == str(c.GATE/"run.py"), "exact frozen entrypoint")
    sys.path.insert(0,str(c.GATE))
    # Canonical 'run' is required by the unchanged native_feedback imports.
    runner=c.load("run",c.GATE/"run.py")
    args=runner.parser().parse_args(argv[1:])
    c.require(args.execute and args.batches == [1,16] and
      args.stage in ("isolated","native_feedback") and args.physical_card in (4,5,6,7),
      "actual full B1/B16 frozen CLI")
    c.require(str(args.runtime_manifest) == str(c.GATE/"RUNTIME_MANIFEST.json") and
      args.runtime_manifest_sha256 == c.RUNTIME_SHA and str(args.library)==str(c.SO) and
      str(args.build_receipt)==str(c.BUILD/"build-receipt.json"), "explicit pinned selected authorities")
    if args.stage=="native_feedback":
        c.require(str(args.decode_library)==str(c.DECODE) and args.decode_library_sha256==c.DECODE_SHA and
          str(args.decode_build_receipt)==str(c.DECODE_BUILD/"build-receipt.json") and
          str(args.reference_library)==str(c.REFERENCE) and args.reference_library_sha256==c.REFERENCE_SHA and
          str(args.native_anchor_report)==str(c.ANCHOR), "actual pinned decode/reference/native authorities")
    runner.admission(args) # actual image OPP/source23/binary before Torch/device
    c.require("torch" not in sys.modules and "torch_npu" not in sys.modules, "no backend auto-acquisition in source preflight")
    return runner,args,runtime

def observation(stage,runtime):
    """Read actual mapped addresses, runtime modules and file bytes in gate PID."""
    row={"schema":"damp-selected-prefill-same-process/v1","stage":stage,"pid":os.getpid(),
      "observed_ns":time.time_ns(),"runtime":None,"loaded_libraries":{},
      "runtime_image_sources":{},"maps_lines":[],"secondary_errors":[]}
    def attempt(label,fn):
        try:return fn()
        except BaseException as error:
            row["secondary_errors"].append({"stage":label,"error":repr(error)});return None
    maps=attempt("actual_proc_self_maps",lambda:Path("/proc/self/maps").read_text().splitlines())
    if maps is not None:
        paths={}
        for line in maps:
            words=line.split(None,5)
            if len(words)==6 and words[-1].startswith("/"):
                p=Path(words[-1])
                # A deleted mapping is NOT proof of the current file's bytes.
                if p.is_file() and not words[-1].endswith(" (deleted)"):
                    paths.setdefault(str(p.resolve()),[]).append(line)
        for p,pin in c.expected_libraries(stage).items():
            actual=attempt("mapped:"+p,lambda p=p: str(Path(p).resolve()))
            if actual in paths:
                digest=attempt("mapped_bytes:"+p,lambda p=p:c.sha(p))
                if digest is not None: row["loaded_libraries"][p]=digest
                row["maps_lines"].extend(paths[actual])
    torch,npu=sys.modules.get("torch"),sys.modules.get("torch_npu")
    if torch is not None and npu is not None:
        row["runtime"]=attempt("actual_runtime_modules",lambda:{"soc":torch.npu.get_device_name(0),
          "torch":torch.__version__,"torch_npu":npu.__version__,"opp_version_info_sha256":c.sha(c.OPP)})
    if stage=="native_feedback":
        for p,pin in runtime["actual_image_sources"].items():
            digest=attempt("actual_image_source:"+p,lambda p=p:c.sha(p))
            if digest is not None: row["runtime_image_sources"][p]=digest
    return row

def run(argv, packet_sha, out, preflight_only=False):
    runner,args,runtime=image_admission(argv,packet_sha)
    output=Path(args.out)
    c.require(output.parent.name=="stage-output" and output.name==args.stage and
      output.parent.parent.parent==c.ROOT and
      output.parent.parent.name.startswith("selected-prefill-dispatch-") and
      out.parent==output.parent and out.name=="same-process-observation.json" and
      output.parent.is_dir() and not out.exists() and not out.is_symlink(),
      "only this fresh stage-output is writable; MAIN audit is not")
    if preflight_only:
        print(json.dumps({"schema":"damp-selected-prefill-image-source/v1","status":"actual_source_admission_pass",
          "stage":args.stage,"source_runtime_sha256":c.RUNTIME_SHA,"torch_imported":False,"npu_executed":False}))
        return 0
    # The original gate owns its output directory creation and all numerical checks.
    code,primary=None,None
    try:
        code=runner.main(argv[1:])
        c.require(type(code) is int,"frozen runner integer exit")
    except BaseException as error:
        primary={"error":repr(error),"traceback":traceback.format_exc()}
        print(primary["traceback"],file=sys.stderr,flush=True)
    row=observation(args.stage,runtime)
    row.update(gate_returncode=code,primary_error=primary,gate_entry=str(c.GATE/"run.py"),
               gate_args=argv[1:],gate_output=str(output))
    # Source/CLI end identity is checked without calling closure's no-Torch guard.
    try:
        c.packet(packet_sha)
        for table in (runtime["sources"],runtime["dependencies"]):
            for p,pin in table.items():c.checked(c.REPO/p,pin)
    except BaseException as error:row["secondary_errors"].append({"stage":"end_source_identity","error":repr(error)})
    try:c.write(out,row)
    except BaseException as error:
        print("SECONDARY observation-save "+repr(error),file=sys.stderr,flush=True)
        return 1 # original trace above retained; cannot manufacture a complete child receipt
    if primary is not None or row["secondary_errors"]:return 1
    return code

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    c.require("--" in argv,"explicit frozen gate argv separator")
    pos=argv.index("--")
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--packet-sha256",required=True)
    p.add_argument("--observation",type=Path,required=True)
    p.add_argument("--preflight-only",action="store_true")
    args=p.parse_args(argv[:pos])
    return run(argv[pos+1:],args.packet_sha256,args.observation,args.preflight_only)

if __name__=="__main__":raise SystemExit(main())
