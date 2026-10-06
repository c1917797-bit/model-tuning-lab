"""Parent-owned one-shot step45 trace; physical NPU4 only, no old result edits."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from run_collector_smoke import IMAGE, PYTHON, REPO, RESULT, idle_snapshot, output, require, write_new

SCRIPT = REPO/"projects/damp-ascend/operator/diagnostic/run_saved_step45_trace.py"
SCRIPT_SHA = "64cc9ee98a6354d16a49fa90f9c16170d9852c080cf576fad03e3183b4eb0b9a"
FROZEN = [
    ("fixture", RESULT/"restricted-native-golden-v2/first_failure.pt", "59795deab9d00328df79dfeeefa08ff6d917f455bfe9d7565d0fd9c3cbf70598"),
    ("source-report", RESULT/"restricted-native-golden-v2/report.json", "b9cc99b0d655ad054fe4575b18ef78215a974f8e62abf5c6ed1308c3e3cbc68f"),
    ("oracle", REPO/"projects/damp-ascend/tests/independent_oracle.py", "fc92395d65db63810ff70341dca255f7f4455d80f0fccbe80f48ff3bb679625a"),
    ("production-library", RESULT/"operator-build-v4/libqwen36_gdn_damp_decode_ops.so", "22f522cf5befcf6afa12560dd2624fd6ddb1c99cc8d9bf04a4b08502363b3937"),
]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", required=True)
    p.add_argument("--trace-library", type=Path, required=True)
    p.add_argument("--trace-sha256", required=True)
    args = p.parse_args()
    require(re.fullmatch(r"v[1-9][0-9]*", args.run_id), "NEW version required")
    require(Path.cwd().resolve() == REPO, "canonical cwd required")
    trace = args.trace_library.resolve(strict=True)
    require(trace.is_relative_to(RESULT) and sha(trace) == args.trace_sha256, "trace library identity/root changed")
    require(sha(SCRIPT) == SCRIPT_SHA, "reviewed diagnostic script changed")
    for _, path, expected in FROZEN:
        require(sha(path) == expected, "frozen input drift: "+str(path))
    name = "qwen36_damp_saved_trace_npu4_20261006_"+args.run_id
    audit = RESULT/("saved-step45-trace-"+args.run_id+"-launch")
    result = RESULT/("saved-step45-trace-"+args.run_id)
    cpu = RESULT/("saved-step45-trace-"+args.run_id+"-cpu-audit")
    require(not any(x.exists() for x in (audit,result,cpu)), "output exists; no overwrite")
    require(subprocess.run(["docker","inspect",name],capture_output=True).returncode != 0, "container exists")
    require(json.loads(output(["docker","image","inspect",IMAGE]))[0]["Id"] == IMAGE, "image drift")
    snapshot = idle_snapshot()
    require(next(int(x.split()[1]) for x in snapshot["meminfo"].splitlines() if x.startswith("MemAvailable:")) >= 4*1024*1024, "ordinary RAM low")
    audit.mkdir()
    write_new(audit/"prelaunch.json",snapshot)
    create = ["docker","create","--name",name,"--network","none","--shm-size","1g",
        "--memory","4g","--memory-swap","4g","--cpus","2","--pids-limit","256",
        "-e","ASCEND_RT_VISIBLE_DEVICES=0","-e","PYTHONDONTWRITEBYTECODE=1","-e","OMP_NUM_THREADS=1",
        "-v","/usr/local/Ascend/driver:/usr/local/Ascend/driver:ro",
        "-v",str(REPO)+":"+str(REPO)+":ro","-v",str(RESULT)+":"+str(RESULT)+":rw",
        "--device","/dev/davinci4:/dev/davinci0","--device","/dev/davinci_manager",
        "--device","/dev/devmm_svm","--device","/dev/hisi_hdc","-w",str(REPO),IMAGE,"sleep","infinity"]
    created = False
    try:
        cid = output(create).strip(); created = True
        ins = json.loads(output(["docker","inspect",name]))[0]
        expected = {"/dev/davinci4":"/dev/davinci0", **{s:s for s in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")}}
        require(ins["Id"] == cid and ins["Image"] == IMAGE and not ins["HostConfig"]["Privileged"]
            and ins["HostConfig"]["NetworkMode"] == "none"
            and {d["PathOnHost"]:d["PathInContainer"] for d in ins["HostConfig"]["Devices"]} == expected
            and not ins["HostConfig"]["DeviceRequests"], "mapping/isolation mismatch")
        mounts = {m["Destination"]:m for m in ins["Mounts"]}
        require(set(mounts) == {str(REPO),str(RESULT),"/usr/local/Ascend/driver"}
            and not mounts[str(REPO)]["RW"] and mounts[str(RESULT)]["RW"]
            and not mounts["/usr/local/Ascend/driver"]["RW"], "mount boundary changed")
        proof = audit/"device-proof.json"
        write_new(proof,dict(physical_npu_ids=[4],logical_to_physical={"0":4},privileged=False,
            exclusive_resource_check_passed=True,observed_at_unix_ns=time.time_ns(),container_id=cid,
            image_id=IMAGE,devices=ins["HostConfig"]["Devices"],mounts=ins["Mounts"],
            prelaunch_evidence=str(audit/"prelaunch.json"),prelaunch_sha256=sha(audit/"prelaunch.json")))
        output(["docker","start",name])
        base = ["docker","exec",name,PYTHON,"-B",str(SCRIPT)]
        for field,path,expected_sha in FROZEN:
            base += ["--"+field,str(path),"--"+field+"-sha256",expected_sha]
        base += ["--trace-library",str(trace),"--trace-library-sha256",args.trace_sha256,
            "--preflight-receipt",str(proof),"--preflight-receipt-sha256",sha(proof),
            "--physical-device","4","--logical-device","0"]
        for phase, destination, tail in (("cpu-audit",cpu,["--audit-only"]),("npu-trace",result,[])):
            argv = base+["--output-dir",str(destination)]+tail
            started = time.monotonic()
            with (audit/(phase+".log")).open("x") as f:
                run = subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
            write_new(audit/(phase+".receipt.json"),dict(argv=argv,returncode=run.returncode,
                seconds=time.monotonic()-started,log_sha256=sha(audit/(phase+".log"))))
            print(phase+" rc="+str(run.returncode),flush=True)
            require(run.returncode == 0, phase+" failed; preserve and do not retry unchanged")
        report = json.loads((result/"report.json").read_text())
        require(report["status"] == "PASS" and report["attribution_ready"], "trace identity/guards failed")
        write_new(audit/"RESULT.json",dict(status="diagnostic-pass",report=str(result/"report.json"),
            report_sha256=sha(result/"report.json"),
            scope="actual saved-step45 arithmetic attribution; original correctness failure remains"))
        print(json.dumps(dict(report=str(result/"report.json"),boundaries=report["boundaries"],
            updated_vs_native=report["updated_vs_native"])),flush=True)
    except BaseException as exc:
        write_new(audit/"FAILURE.json",dict(error_type=type(exc).__name__,error=str(exc)))
        raise
    finally:
        if created:
            stop = subprocess.run(["docker","stop","--time","30",name],capture_output=True,text=True,timeout=45)
            write_new(audit/"stop.json",dict(returncode=stop.returncode,stdout=stop.stdout,stderr=stop.stderr))
            require(stop.returncode == 0, "stop failed; attention required")
            print("STOPPED AND RETAINED "+name,flush=True)

if __name__ == "__main__": main()

