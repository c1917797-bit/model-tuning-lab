"""Parent-owned one-shot packed DAMP gate on physical NPU4 only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from run_collector_smoke import IMAGE, MODEL, PYTHON, REPO, RESULT, idle_snapshot, output, require, write_new

REFERENCE = Path("/cache/austinov/src/vllm-ascend")
REF_COMMIT = "5cb98caaadeff42b5b62b996e34bb2aaa29d20fd"
NATIVE_HEADER = "csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h"
HEADER_SHA = "96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b"
RUNNER = REPO / "projects/damp-ascend/tests/restricted_native_golden_gate.py"
RUNNER_SHA = "f8b04cc7650cf2cc330a526cb261ffd85062454e56e1a9692b5913c18445a6b4"
HELPER = RUNNER.parent / "native_compressed_golden.py"
HELPER_SHA = "95d11c42bea88daa14dbb2ce462e16a7d1864b3f2169faf360942fb0c16bea19"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--sha256", required=True)
    args = p.parse_args()
    require(re.fullmatch(r"v[1-9][0-9]*", args.run_id), "new version identity required")
    require(Path.cwd().resolve() == REPO, "canonical cwd required")
    library = args.library.resolve(strict=True)
    require(library.is_relative_to(RESULT) and sha(library) == args.sha256, "library identity/root mismatch")
    require(sha(RUNNER) == RUNNER_SHA, "reviewed gate runner changed")
    require(sha(HELPER) == HELPER_SHA, "reviewed native golden helper changed")
    name = "qwen36_damp_packed_npu4_20261006_" + args.run_id
    audit = RESULT / ("restricted-native-" + args.run_id + "-launch")
    report = RESULT / ("restricted-native-golden-" + args.run_id)
    require(not audit.exists() and not report.exists(), "output already exists; no overwrite")
    require(subprocess.run(["docker", "inspect", name], capture_output=True).returncode != 0,
            "owned container name already exists")
    require(json.loads(output(["docker", "image", "inspect", IMAGE]))[0]["Id"] == IMAGE,
            "immutable image mismatch")
    require(output(["git", "-C", str(REFERENCE), "rev-parse", "v0.23.0^{commit}"]).strip() == REF_COMMIT,
            "native reference tag changed")
    require(sha(REFERENCE/NATIVE_HEADER) == HEADER_SHA, "native reference header drift")
    snapshot = idle_snapshot()
    available_kib = next(int(line.split()[1]) for line in snapshot["meminfo"].splitlines()
                         if line.startswith("MemAvailable:"))
    require(available_kib >= 2 * 1024 * 1024,
            "operator gate requires 2GiB ordinary available RAM; never release HugeTLB")
    audit.mkdir(parents=True, exist_ok=False)
    write_new(audit/"prelaunch.json", snapshot)
    files = {}
    for scope in ("operator", "tests", "tools"):
        for path in sorted((REPO/"projects/damp-ascend"/scope).rglob("*")):
            if path.is_file():
                require("__pycache__" not in path.parts, "generated code unexpectedly in source")
                files[str(path.relative_to(REPO))] = sha(path)
    write_new(audit/"source.json", dict(files=files, commit=output(["git","rev-parse","HEAD"]).strip(),
                                       operator_library=str(library), operator_sha256=args.sha256))
    provenance = dict(reference_root=str(REFERENCE), reference_commit=REF_COMMIT,
                      recurrent_header_path=NATIVE_HEADER, recurrent_header_sha256=HEADER_SHA,
                      image_id=IMAGE, operator_library=str(library), operator_sha256=args.sha256,
                      note="reference source identity is not a loaded-binary proof; runner records actual maps/library hashes")
    write_new(audit/"native-source.json", provenance)
    create = ["docker","create","--name",name,"--network","none","--shm-size","1g",
              "--memory","4g","--memory-swap","4g",
              "-e","ASCEND_RT_VISIBLE_DEVICES=0","-e","PYTHONDONTWRITEBYTECODE=1",
              "-e","OMP_NUM_THREADS=1",
              "-v","/usr/local/Ascend/driver:/usr/local/Ascend/driver:ro",
              "-v",str(REPO)+":"+str(REPO)+":ro",
              "-v",str(RESULT)+":"+str(RESULT)+":rw",
              "--device","/dev/davinci4:/dev/davinci0",
              "--device","/dev/davinci_manager","--device","/dev/devmm_svm","--device","/dev/hisi_hdc",
              "-w",str(REPO),IMAGE,"sleep","infinity"]
    created = False
    try:
        cid = output(create).strip()
        created = True
        inspect = json.loads(output(["docker","inspect",name]))[0]
        devices = {d["PathOnHost"]:d["PathInContainer"] for d in inspect["HostConfig"]["Devices"]}
        require(devices == {"/dev/davinci4":"/dev/davinci0",
                **{s:s for s in ("/dev/davinci_manager","/dev/devmm_svm","/dev/hisi_hdc")}},
                "unexpected physical device mapping")
        require(inspect["Id"] == cid and inspect["Image"] == IMAGE and
                inspect["HostConfig"]["Privileged"] is False and inspect["HostConfig"]["NetworkMode"] == "none",
                "container identity/isolation mismatch")
        mounts = {m["Destination"]:m for m in inspect["Mounts"]}
        require(mounts[str(REPO)]["RW"] is False and mounts[str(RESULT)]["RW"] is True,
                "source/result mutability mismatch")
        require(str(MODEL) not in mounts, "model weights not needed for operator gate")
        write_new(audit/"device-proof.json", dict(physical_npu_ids=[4], logical_to_physical={"0":4},
                  privileged=False, exclusive_resource_check_passed=True,
                  observed_at_unix_ns=time.time_ns(), container_id=cid, image_id=IMAGE,
                  devices=inspect["HostConfig"]["Devices"], mounts=inspect["Mounts"],
                  prelaunch_evidence=str(audit/"prelaunch.json"), prelaunch_sha256=sha(audit/"prelaunch.json")))
        output(["docker","start",name])
        require("python" not in output(["docker","top",name,"-eo","pid,args"]), "unexpected owned workload")
        argv = ["docker","exec",name,PYTHON,"-B",str(RUNNER),
                "--operator-library",str(library),"--operator-sha256",args.sha256,
                "--device-proof",str(audit/"device-proof.json"),
                "--native-source-manifest",str(audit/"native-source.json"),
                "--output-dir",str(report)]
        started = time.monotonic()
        with (audit/"gate.log").open("x") as log:
            result = subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=900)
        write_new(audit/"gate.receipt.json",dict(argv=argv,exit_code=result.returncode,
                  seconds=time.monotonic()-started,scope="restricted numerical gate, not performance"))
        require(result.returncode == 0, "restricted NPU gate failed; retain failure, no unchanged retry")
        receipt = json.loads((report/"report.json").read_text())
        require(receipt["status"] == "restricted_native_numerical_pass" and receipt["steps"] == 160 and
                len(receipt["cases"]) == 4 and all(c["status"] == "passed" for c in receipt["cases"]),
                "complete restricted native matrix did not pass")
        write_new(audit/"RESULT.json",dict(status="restricted_native_numerical_pass",
                  report_sha256=sha(report/"report.json"),
                  not_proven=["general SR","graph","TP4 full-model serving","performance","task accuracy"]))
        print("RESTRICTED NPU MATRIX PASSED", flush=True)
    except BaseException as error:
        write_new(audit/"FAILURE.json",dict(error_type=type(error).__name__,error=str(error)))
        raise
    finally:
        if created:
            stopped = subprocess.run(["docker","stop","--time","30",name],capture_output=True,text=True,timeout=45)
            write_new(audit/"stop.json",dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr))
            require(stopped.returncode == 0, "owned container stop failed; attention required")
            print("STOPPED AND RETAINED " + name, flush=True)

if __name__ == "__main__":
    main()
