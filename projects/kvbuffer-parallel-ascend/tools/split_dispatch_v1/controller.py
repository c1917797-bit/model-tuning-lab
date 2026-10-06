#!/usr/bin/env python3
"""MAIN-only prepare-joint + two real run-arm operations. Default OFF; never serving/performance."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kvbp_new_dispatch_contracts", BASE/"contracts.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

def secondary(label, function, errors):
    try:
        return function()
    except BaseException as e:
        row = dict(stage=label,error=repr(e),traceback=traceback.format_exc())
        errors.append(row)
        print("KVBUFFER_SECONDARY_EVIDENCE_ERROR "+json.dumps(row),file=sys.stderr)
        return None

class Commands:
    """Original subprocess streams first; evidence errors never replace original execution failure."""
    def __init__(self, audit):
        self.audit, self.index, self.secondary_errors = Path(audit), 0, []
    def run(self, label, argv, timeout=90, allowed=(0,)):
        self.index += 1
        stem = "%04d-%s" % (self.index,label)
        out, err = self.audit/(stem+".stdout"), self.audit/(stem+".stderr")
        started = time.monotonic()
        process = None
        primary = None
        try:
            with out.open("xb") as stdout, err.open("xb") as stderr:
                process = subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=timeout,check=False,
                                         cwd=str(c.ROOT))
            if process.returncode not in allowed:
                raise RuntimeError("original command nonzero: %s exit%d" % (stem,process.returncode))
        except BaseException as e:
            primary = e
        row = dict(argv=argv,command=argv[0],cwd=str(c.ROOT),
                   exit_code=None if process is None else process.returncode,
                   error=None if primary is None else repr(primary),
                   elapsed_seconds=time.monotonic()-started,automatic_retry=False,
                   stdout=str(out),stderr=str(err))
        try:
            row.update(stdout_sha256=c.sha(out),stderr_sha256=c.sha(err))
            c.write_new(self.audit/(stem+".receipt.json"),row)
        except BaseException as evidence_error:
            if primary is None:
                raise
            secondary("command-receipt",lambda: (_ for _ in ()).throw(evidence_error),
                      self.secondary_errors)
        if primary is not None:
            raise primary
        return out.read_text(),process.returncode
    def json(self,label,argv):
        raw,_ = self.run(label,argv)
        return c.clean(raw)

def source_audit(packet_sha):
    packet,pins,bridge,split,host,float_helper = c.sources(packet_sha)
    producer = {str(BASE/n):h for n,h in packet["sources"].items()}
    producer[str(BASE/"PACKET.json")] = packet_sha
    return packet,pins,producer,bridge,split,host,float_helper

def parent_stopped(cmd, inputs):
    original = c.clean(c.read_ref(inputs["parent_operation"]))
    desc = c.parent_terminal(original,inputs["parent_expected"])
    rows = []
    for cid in c.PARENT_IDS:
        entry = cmd.json("parent-inspect",["/usr/bin/docker","inspect",cid])
        c.require(type(entry) is list and len(entry) == 1 and entry[0]["Id"] == cid,
                  "exact allT owned ID; never infer absence/stopped")
        e = entry[0]
        c.require(e["Image"] == c.IMAGE and
                  e["Config"].get("Labels",{}).get("model-tuning-lab.owner") == "damp-allT-dispatch-v1" and
                  e["State"].get("Running") is False and e["State"].get("Pid") == 0,
                  "all four original allT containers must actually be stopped")
        rows.append(dict(id=cid,name=e["Name"],state=e["State"]))
    return dict(original_operation=inputs["parent_operation"],terminal=desc,stopped=rows)

def admitted_peer_pid(pid, batch, cid, host, fh):
    """Only a claimed same-joint arm's genuine gate or exact separate canary may own peer NPU."""
    j = own_jobs[batch]
    claim = c.clean((Path(j["job_root"])/"ARM_CLAIM.json").read_bytes())
    wanted_joint = c.ref(Path(j["job_root"]).parent/"JOINT.json")
    c.require(claim.get("batch") == batch and claim.get("joint") == wanted_joint,
              "peer NPU PID requires exclusive same-joint actual arm claim")
    row = host.owner_pid(pid,cid)
    argv = [x.decode() for x in Path("/proc",str(pid),"cmdline").read_bytes().split(b"\0") if x]
    gate = c.gate_argv(j,cid)
    expected_gate = gate[gate.index(c.PYTHON):]
    canary = [c.PYTHON,"-B","-c",fh.CANARY_CODE,str(j["physical_card"]),
              c.digest(c.canonical(j["create_argv"])),fh.CANARY_SHA]
    c.require(argv == expected_gate or argv == canary,
              "unknown own-peer process is not an admitted gate/canary")
    return row

def resources(cmd, host, fh, own=None, active_batch=None, protected=None, phase_seconds=10800):
    own = own or {}
    raw,_ = cmd.run("npu-smi",[c.NPU_SMI,"info"])
    rows,telemetry = host.parse_processes(raw),fh.telemetry(raw)
    c.require(set(telemetry) == set(range(8)), "fresh complete actual card telemetry")
    protect = host.protected_fingerprint(rows)
    c.require(protected is None or protected == protect, "protected0-3 PID/cgroup/start unchanged")
    for card in (5,6):
        peer = next((cid for b,cid in own.items() if c.CARDS[b] == card),None)
        for row in rows[card]:
            c.require(peer is not None and (active_batch is None or c.CARDS[active_batch] != card),
                      "target card not idle or external real process")
            admitted_peer_pid(row["pid"],{5:1,6:16}[card],peer,host,fh)
        if not rows[card]:
            c.idle_card(telemetry[card])  # actual frozen3165 envelope, never no-PID alone
    engine = cmd.json("docker-info",["/usr/bin/docker","info","--format","{{json .}}"])
    c.require(type(engine.get("NCPU")) is int and engine["NCPU"] >= c.JOINT_CPU, "fresh Docker joint3 CPUs")
    memory = Path("/proc/meminfo").read_text()
    m = re.search(r"^MemAvailable:\s*(\d+)\s+kB",memory,re.M)
    c.require(m and int(m[1])*1024 >= c.JOINT_RAM, "ordinaryRAM24GiB; no HugeTLB/reclaim policy change")
    disk = shutil.disk_usage(c.RESULT_ROOT).free
    c.require(disk >= c.phase_disk_need(phase_seconds),"fresh two-arm remaining-phase disk headroom")
    running,_ = cmd.run("running-IDs",["/usr/bin/docker","ps","--quiet","--no-trunc"])
    owners = []
    for cid in running.splitlines():
        c.require(re.fullmatch("[0-9a-f]{64}",cid),"actual full running container ID")
        e = cmd.json("live-inspect",["/usr/bin/docker","inspect",cid])[0]
        labels = e["Config"].get("Labels") or {}
        if any(k.startswith("model-tuning-lab.") for k in labels):
            c.require(cid in own.values(),"unknown live MAIN owner: no joint resource proof/no stop")
            owners.append(dict(id=cid,labels=labels,cgroup=host.cgroup_record(e,cid,c.MEMORY,1)))
    for b,cid in own.items():
        e = cmd.json("owned-resource-inspect",["/usr/bin/docker","inspect",cid])[0]
        c.inspect_proof(e,own_jobs[b],cid)
    mount = host.mount_budget(cmd)
    return dict(observed_ns=time.time_ns(),npu_smi=raw,meminfo=memory,processes=rows,
                telemetry=telemetry,protected=protect,docker_info=engine,
                ordinary_available_bytes=int(m[1])*1024,joint_minimum_bytes=c.JOINT_RAM,
                joint_cpu_with_reserve=c.JOINT_CPU,free_disk_bytes=disk,mount_headroom=mount,
                live_owners=owners,source_of_proof="actual host reads, not prepared admission",
                idle_envelope_source=dict(path=str(c.IDLE_SOURCE),sha256=c.IDLE_SOURCE_SHA,
                                          function="idle_snapshot",hbm_max_mib=c.idle_hbm_ceiling()))

def stop_owned(cmd,job,cid):
    entry = cmd.json("cleanup-owned-inspect",["/usr/bin/docker","inspect",cid])[0]
    c.inspect_proof(entry,job,cid)
    if entry["State"]["Running"]:
        cmd.run("stop-retain",["/usr/bin/docker","stop","--time","20",cid])
    entry = cmd.json("stopped-inspect",["/usr/bin/docker","inspect",cid])[0]
    c.require(entry["State"]["Running"] is False and entry["State"]["Pid"] == 0,
              "own exact container not actually stopped")
    return dict(container_id=cid,stopped=True,retained=True,deleted=False)

def no_overlap_created_name(cmd, name):
    _,code = cmd.run("name-absence",["/usr/bin/docker","container","inspect",name],allowed=(0,1))
    receipt = c.clean((cmd.audit/("%04d-name-absence.receipt.json"%cmd.index)).read_bytes())
    stderr = Path(receipt["stderr"]).read_text()
    c.require(code == 1 and ("No such object: "+name in stderr or "No such container: "+name in stderr),
              "name not proven absent; never overwrite/restart/retry")

def prepare(inputs, packet_sha):
    packet,pins,producer,bridge,split,host,fh = source_audit(packet_sha)
    plan = c.plan(inputs)
    root = Path(plan["root"])
    c.require(not root.exists(),"new joint root required; no retry/overwrite")
    root.mkdir()
    audit = root/"prepare";audit.mkdir()
    cmd = Commands(audit)
    known = {}
    primary = None
    try:
        released_parent = parent_stopped(cmd,inputs)
        first = resources(cmd,host,fh,phase_seconds=max(plan["phase_seconds"].values()))
        c.write_new(audit/"fresh-before-create.json",first)
        for job in plan["jobs"]:
            no_overlap_created_name(cmd,job["container_name"])
            Path(job["job_root"]).mkdir()
            Path(job["launch_root"]).mkdir()
            Path(job["output_root"]).mkdir()
            c.write_new(audit/("create-b%d.json"%job["batch"]),dict(argv=job["create_argv"]))
            raw,_ = cmd.run("create-b"+str(job["batch"]),job["create_argv"])
            cid = raw.strip()
            c.require(re.fullmatch("[0-9a-f]{64}",cid),"create outcome uncertain: never infer owned ID")
            known[job["batch"]] = cid
            e = cmd.json("created-inspect",["/usr/bin/docker","inspect",cid])[0]
            c.inspect_proof(e,job,cid)
            cmd.run("start-sleep",["/usr/bin/docker","start",cid])
            e = cmd.json("started-inspect",["/usr/bin/docker","inspect",cid])[0]
            c.inspect_proof(e,job,cid)
            host.cgroup_record(e,cid,c.MEMORY,1)
            job["container_id"] = cid
        for path,h in pins.items():
            c.require(c.sha(path) == h,"source changed before prepared receipt")
        joint = dict(schema="kvbp.split-joint-prepared/v1",plan=plan,inputs=inputs,
                     packet_sha256=packet_sha,producer_sources=producer,source_pins=pins,
                     parent=released_parent,protected=first["protected"],prepared_ns=time.time_ns(),
                     actual_device_proof_pending=True,resource_readiness_is_not_live=True,
                     npu_executed=False,service_ready=False,performance=False)
        value = c.write_new(root/"JOINT.json",joint)
        print("MAIN_KVBUFFER_SPLIT_JOINT "+json.dumps(value))
        return joint
    except BaseException as e:
        primary = e
        secondary("prepare-failure",lambda:c.write_new(audit/"FAILURE.json",
                  dict(error=repr(e),traceback=traceback.format_exc(),known_ids=known)),cmd.secondary_errors)
        for job in plan["jobs"]:
            if job["batch"] in known:
                secondary("prepare-stop-own",lambda j=job:stop_owned(cmd,j,known[j["batch"]]),
                          cmd.secondary_errors)
        raise primary

def image_sources(cmd, cid, packet):
    expected = dict(packet["native_image_sources"])
    code = "import hashlib,json,pathlib; expected="+repr(expected)+"; actual={p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in expected}; assert actual==expected; print(json.dumps(actual,sort_keys=True))"
    raw,_ = cmd.run("image-source-audit",["/usr/bin/docker","exec",cid,c.PYTHON,"-B","-c",code])
    c.require(c.clean(raw) == expected,"actual image source mismatch before Torch/canary")
    return c.ref(cmd.audit/("%04d-image-source-audit.stdout"%cmd.index))

def wait_pid(cmd, cid, batch, host):
    until = time.monotonic()+30
    while time.monotonic() < until:
        raw,_ = cmd.run("top-wait",["/usr/bin/docker","top",cid,"-eo","pid,args"])
        matches = []
        for line in raw.splitlines()[1:]:
            pid,_,text = line.strip().partition(" ")
            if pid.isdigit() and "kvbuffer-await-b"+str(batch) in text:
                matches.append(int(pid))
        c.require(len(matches) <= 1,"ambiguous wait PID")
        if matches:
            return c.gate_process(matches[0],cid,batch,host,require_python=False)
        time.sleep(.1)
    raise TimeoutError("real waiting bash PID not observed; no release")

def run_arm(joint_ref, batch, packet_sha):
    packet,pins,producer,bridge,split,host,fh = source_audit(packet_sha)
    joint = c.clean(c.read_ref(joint_ref))
    c.require(joint.get("schema") == "kvbp.split-joint-prepared/v1" and
              joint["packet_sha256"] == packet_sha and joint["producer_sources"] == producer and
              joint["source_pins"] == pins,"exact actual prepared joint/source receipt")
    inputs = joint["inputs"];c.bounds(inputs)
    jobs = {j["batch"]:j for j in joint["plan"]["jobs"]}
    c.require(set(jobs) == {1,16},"two actual prepared jobs")
    global own_jobs
    own_jobs = jobs
    job = jobs[batch];cid = job["container_id"]
    audit = Path(job["job_root"])/"run-arm";audit.mkdir()
    c.write_new(Path(job["job_root"])/"ARM_CLAIM.json",dict(batch=batch,claimed_ns=time.time_ns(),
                joint=joint_ref,automatic_retry=False))
    cmd = Commands(audit);process=None;primary=None;cleanup=None;child=None;observed=[]
    own = {b:j["container_id"] for b,j in jobs.items()}
    try:
        parent_stopped(cmd,inputs)
        for b,j in jobs.items():
            entry = cmd.json("arm-inspect",["/usr/bin/docker","inspect",j["container_id"]])[0]
            c.inspect_proof(entry,j,j["container_id"])
            if b == batch:
                c.require(entry["State"]["Running"],"arm must be live original prepared sleep; no restart")
                top,_ = cmd.run("target-top",["/usr/bin/docker","top",cid,"-eo","pid,args"])
                c.require(len(top.splitlines()) == 2 and "sleep infinity" in top,
                          "target already used/contains another process")
        first = resources(cmd,host,fh,own,batch,joint["protected"],max(joint["plan"]["phase_seconds"].values()))
        c.write_new(audit/"fresh-before-canary.json",first)
        image_source = image_sources(cmd,cid,packet)
        create_sha = c.digest(c.canonical(job["create_argv"]))
        canary,_ = cmd.run("canary",["/usr/bin/docker","exec",cid,"/bin/bash","-c",fh.BOOTSTRAP,
              "kvbuffer-separate-canary",c.PYTHON,"-B","-c",fh.CANARY_CODE,
              str(job["physical_card"]),create_sha,fh.CANARY_SHA],timeout=90)
        cv = c.clean(canary)
        c.require(cv["status"] == "actual_canary_pass" and cv["expected_physical_card"] == job["physical_card"]
                  and cv["create_argv_sha256"] == create_sha and cv["canary_program_sha256"] == fh.CANARY_SHA,
                  "independent tiny canary: not same process as numerical gate")
        canary_ref = c.ref(cmd.audit/("%04d-canary.stdout"%cmd.index))
        mapping = cmd.json("mapping-inspect",["/usr/bin/docker","inspect",cid])
        c.inspect_proof(mapping[0],job,cid)
        mapping_ref = c.ref(cmd.audit/("%04d-mapping-inspect.stdout"%cmd.index))
        second = resources(cmd,host,fh,own,batch,joint["protected"])
        raw_ref = c.write_new(audit/"fresh-prelaunch.json",second)
        argv = c.gate_argv(job,cid)
        out,err = audit/"gate.stdout",audit/"gate.stderr"
        started = time.monotonic()
        with out.open("xb") as stdout,err.open("xb") as stderr:
            process = subprocess.Popen(argv,stdout=stdout,stderr=stderr,cwd=str(c.ROOT))
            waiting = wait_pid(cmd,cid,batch,host)
            waiting_ref = c.write_new(audit/"WAIT_PID.json",waiting)
            utc = datetime.now(timezone.utc).isoformat()
            e = cmd.json("cgroup-inspect",["/usr/bin/docker","inspect",cid])[0]
            cg = host.cgroup_record(e,cid,c.MEMORY,1)
            cg_ref = c.write_new(audit/"cgroup.json",cg)
            proof = dict(schema="kvbp.split-main-device-binding/v1",container_id=cid,image_id=c.IMAGE,
                 physical_devices=[job["physical_card"]],logical_to_physical={"0":job["physical_card"]},
                 same_process_pid=waiting["pid"],preflight_utc=utc,evidence_kind="actual-main-execution",
                 observed_role="prelaunch_wait_bash_not_native",gate_process_confirmation_required=True,
                 raw_refs=dict(canary=canary_ref,mapping=mapping_ref,host_processes=raw_ref,cgroup=cg_ref))
            proof_ref = c.write_new(audit/"device-proof.json",proof)
            manifest,meta = bridge.frozen(packet["bridge_manifest"],lambda p:Path(p).read_bytes())
            drivers = {p.rsplit("/",1)[1]:h for p,h in manifest["frozen_dependencies"].items()
                       if "/tools/split_gate_v1/" in p}
            identity = dict(schema="kvbp.split-launch-identity/v1",image_id=c.IMAGE,
                 physical_devices=[job["physical_card"]],logical_to_physical={"0":job["physical_card"]},
                 fresh_idle_verified=True,nonprivileged=True,source_canary_passed=True,
                 memory_cgroup_bytes=c.MEMORY,protocol=split.protocol(batch,job["physical_card"]),
                 library_sha256=bridge.LIBRARY,build_receipt_sha256=bridge.BUILD,
                 meta_receipt_sha256=bridge.META,repo_sources=manifest["repo_pins"],
                 native_sources=manifest["native_pins"],driver_sources=drivers,preflight_utc=utc,
                 evidence=dict(device_proof=proof_ref,container_inspect=mapping_ref,
                               separate_canary=canary_ref,waiting_bash=waiting_ref,image_source=image_source))
            identity_ref = c.write_new(Path(job["launch_root"])/"identity.json",identity)
            for path,h in pins.items():
                c.require(c.sha(path) == h,"source changed before exclusive release")
            c.write_new(Path(job["launch_root"])/"RELEASE",dict(identity=identity_ref,joint=joint_ref,
                        approved_release_ns=time.time_ns(),not_a_pass=True))
            last_check=0
            last_budget=0
            budget_index=0
            resource_refs=[]
            last_live_peaks={}
            while process.poll() is None:
                c.require(time.monotonic()-started <= job["phase_timeout_seconds"],"original arm phase timeout; no retry")
                c.require(datetime.now(timezone.utc).timestamp()+180 <
                   datetime.fromisoformat(inputs["deadline_utc"].replace("Z","+00:00")).timestamp(),
                   "fixed MAIN deadline cleanup reserve; never extend")
                if time.monotonic()-last_check >= 1:
                    raw,_ = cmd.run("gate-npu-processes",[c.NPU_SMI,"info"])
                    rows = host.parse_processes(raw)
                    c.require(host.protected_fingerprint(rows) == joint["protected"],"0-3 changed")
                    for card in (5,6):
                        for row in rows[card]:
                            admitted_peer_pid(row["pid"],{5:1,6:16}[card],own[{5:1,6:16}[card]],host,fh)
                    for row in rows[job["physical_card"]]:
                        c.require(row["pid"] == waiting["pid"],"unexpected own NPU PID")
                        actual = c.gate_process(row["pid"],cid,batch,host,require_python=True)
                        c.require(actual["start_ticks"] == waiting["start_ticks"],"PID reused instead of exec")
                        if not observed:
                            observed.append(c.write_new(audit/"ACTUAL_GATE_NPU_PID.json",
                                dict(process=actual,physical_card=job["physical_card"],npu_smi=raw,
                                     waiting=waiting_ref,canary_same_process=False)))
                    last_check=time.monotonic()
                if time.monotonic()-last_budget >= 30:
                    budget_index += 1
                    groups={}
                    for b,j in jobs.items():
                        entry = cmd.json("live-cgroup-inspect",["/usr/bin/docker","inspect",j["container_id"]])[0]
                        c.inspect_proof(entry,j,j["container_id"])
                        if entry["State"]["Running"]:
                            record=host.cgroup_record(entry,j["container_id"],c.MEMORY,1)
                            record["running"]=True
                            groups[b]=record
                            last_live_peaks[b]=record["memory_peak_bytes"]
                        else:
                            groups[b]=dict(container_id=j["container_id"],running=False,
                                stopped_verified=True,pid=entry["State"]["Pid"],
                                memory_limit_bytes=entry["HostConfig"]["Memory"],
                                cpu_quota=entry["HostConfig"]["NanoCpus"]//10**9,
                                last_observed_live_peak=last_live_peaks.get(b),
                                peak_unavailable_after_stop=b not in last_live_peaks)
                    meminfo=Path("/proc/meminfo").read_text()
                    match=re.search(r"^MemAvailable:\s*(\d+)\s+kB",meminfo,re.M)
                    c.require(match is not None,"actual runtime ordinaryRAM parse")
                    elapsed=time.monotonic()-started
                    own_remaining=max(0,job["phase_timeout_seconds"]-elapsed)
                    peer_remaining=jobs[{1:16,16:1}[batch]]["phase_timeout_seconds"]
                    remaining=max(own_remaining,peer_remaining) # full peer budget if exact elapsed unknown
                    engine=cmd.json("live-docker-capability",["/usr/bin/docker","info","--format","{{json .}}"])
                    c.require(type(engine.get("NCPU")) is int and engine["NCPU"]>=c.JOINT_CPU,
                              "live Docker joint3 CPU capability")
                    # Save original budget inputs before interpreting them.
                    inputs_ref=c.write_new(audit/("RUNTIME_BUDGET_INPUTS-%04d.json"%budget_index),
                        dict(observed_ns=time.time_ns(),meminfo=meminfo,free_disk_bytes=shutil.disk_usage(c.RESULT_ROOT).free,
                             remaining_seconds=remaining,own_elapsed_seconds=elapsed,
                             own_remaining_seconds=own_remaining,
                             peer_remaining_upper_bound_seconds=peer_remaining,cgroups=groups,docker_info=engine))
                    inputs_value=c.clean(c.read_ref(inputs_ref))
                    budget=c.runtime_budget(int(match[1])*1024,inputs_value["free_disk_bytes"],remaining,groups)
                    raw_observations=[]
                    for b,j in jobs.items():
                        raw_files=list((Path(j["output_root"])/"gate").glob("raw-step-*.pt"))
                        c.require(len(raw_files)<=1,"unexpected simultaneous raw checkpoints; retain all")
                        for raw_file in raw_files:
                            try:
                                st=raw_file.lstat()
                            except FileNotFoundError:
                                # Frozen passed cleanup may remove it between enumeration/stat.
                                # No passed/numerical inference; unchanged worst-case ceiling remains.
                                raw_observations.append(dict(path=str(raw_file),batch=b,
                                    observation="concurrently_disappeared",passed_inferred=False))
                                continue
                            c.require(st.st_mode & 0o170000 == 0o100000 and
                                      st.st_size<=c.raw_step_ceiling(b),
                                      "actual raw checkpoint exceeds source-shaped policy; do not delete/clip")
                            raw_observations.append(dict(path=str(raw_file),batch=b,
                                observed_bytes=st.st_size,ceiling_bytes=c.raw_step_ceiling(b),
                                observation="actual_lstat",passed_inferred=False))
                    budget["raw_checkpoint_observations"]=raw_observations
                    budget["inputs"]=inputs_ref
                    resource_refs.append(c.write_new(audit/("RUNTIME_BUDGET-%04d.json"%budget_index),budget))
                    last_budget=time.monotonic()
                time.sleep(.1)
        execution = dict(command=argv[0],args=argv[1:],cwd=str(c.ROOT),exit_code=process.returncode,
                         error=None,cancelled=False,timed_out=False,stdout=c.ref(out),stderr=c.ref(err),
                         elapsed_seconds=time.monotonic()-started)
        c.write_new(audit/"EXECUTION.json",execution)
        c.require(process.returncode == 0 and observed,"actual original gate zero + NPU/PID observation required")
        report_path = Path(job["output_root"])/"gate/report.json"
        report_ref = c.ref(report_path)
        report = c.clean(c.read_ref(report_ref,limit=64*1024*1024))
        c.stage_report(report,identity,batch,bridge,split,manifest,meta)
        for path,h in pins.items():
            c.require(c.sha(path) == h,"source drift after gate")
        cleanup = stop_owned(cmd,job,cid)
        raw,_ = cmd.run("release-npu-processes",[c.NPU_SMI,"info"])
        rows = host.parse_processes(raw)
        c.require(not rows[job["physical_card"]] and host.protected_fingerprint(rows) == joint["protected"],
                  "exact own card not released/protected0-3 changed")
        child = dict(schema="kvbp.split-child-execution/v1",report=report_ref,identity=identity_ref,
             evidence_kind="actual-main-execution",execution=execution,producer_sources=producer,
             image_identity_path=job["image_identity"],image_output_dir=job["image_output"],
             container_inspect=mapping_ref,device_proof=proof_ref,
             native_library=packet["artifacts"]["native_library"],
             actual_gate_process=observed,joint=joint_ref,cleanup=cleanup,runtime_resource_budgets=resource_refs,
             source_before=pins,source_after=pins,separate_canary_not_gate=True,
             parent_operation_authority_pending=True,service_ready=False,performance=False)
        c.write_new(audit/"SOURCE_AFTER.json",{p:c.sha(p) for p in pins})
        child_ref = c.write_new(audit/"CHILD.json",child)
        print(c.PREFIX+json.dumps(dict(report=report_ref,identity=identity_ref,child=child_ref)))
        return child
    except BaseException as e:
        primary=e
        if process is not None and process.poll() is None:
            secondary("terminate-local-docker-client",lambda:process.terminate(),cmd.secondary_errors)
        if process is not None:
            secondary("collect-original-client-outcome",lambda:process.wait(timeout=15),cmd.secondary_errors)
            secondary("failed-original-execution",lambda:c.write_new(audit/"FAILED_EXECUTION.json",
                dict(command=argv[0],args=argv[1:],cwd=str(c.ROOT),exit_code=process.returncode,
                     error=repr(e),cancelled=False,timed_out="phase timeout" in str(e),
                     stdout=c.ref(out),stderr=c.ref(err),elapsed_seconds=time.monotonic()-started,
                     outcome_may_be_incomplete=process.poll() is None)),cmd.secondary_errors)
        secondary("raw-primary-failure",lambda:c.write_new(audit/"PRIMARY_FAILURE.json",
                  dict(error=repr(e),traceback=traceback.format_exc(),actual_gate_observations=observed,
                       no_retry=True,child_success_marker=False)),cmd.secondary_errors)
        raise primary
    finally:
        if cleanup is None:
            secondary("stop-retain-own-only",lambda:stop_owned(cmd,job,cid),cmd.secondary_errors)
        if primary is not None:
            secondary("source-after",lambda:c.write_new(audit/"SOURCE_AFTER.json",
                      {p:c.sha(p) for p in pins}),cmd.secondary_errors)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",nargs="?",choices=("plan","source-audit","prepare-joint","run-arm"),default="plan")
    parser.add_argument("--packet-sha256")
    parser.add_argument("--inputs",type=Path)
    parser.add_argument("--inputs-sha256")
    parser.add_argument("--joint",type=Path)
    parser.add_argument("--joint-sha256")
    parser.add_argument("--batch",type=int,choices=(1,16))
    parser.add_argument("--execute",action="store_true")
    a=parser.parse_args()
    if a.mode == "plan" and a.inputs is None:
        print(json.dumps(dict(enabled=False,source_only=True,npu_executed=False,service_ready=False,
             required_main_refs=["actual allT MA06a0 terminal + exact argv","four exact owned stopped",
                                 "joint source freeze","phase budgets + real formal clock","fresh resources"],
             split_operations_required=True,ordinary_ram_bytes=c.JOINT_RAM,joint_cpu=c.JOINT_CPU)))
        return
    c.require(a.packet_sha256 is not None,"explicit fixed source packet SHA")
    if a.mode == "source-audit":
        packet,pins,*_ = source_audit(a.packet_sha256)
        print(json.dumps(dict(status="source_and_actual_artifact_audit_only",sources=len(pins),
                              npu_executed=False,execute_authorized=False)))
        return
    if a.mode in ("plan","prepare-joint"):
        c.require(a.inputs is not None and a.inputs_sha256 is not None,"actual MAIN inputs Ref")
        inputs = c.clean(c.read_ref(dict(path=str(a.inputs),sha256=a.inputs_sha256)))
        if a.mode == "plan":
            print(json.dumps(c.plan(inputs)));return
        c.require(a.execute and os.environ.get("KVBUFFER_SPLIT_DISPATCH_EXECUTE") == "1",
                  "MAIN opt-in execution only; default OFF")
        prepare(inputs,a.packet_sha256)
    else:
        c.require(a.execute and os.environ.get("KVBUFFER_SPLIT_DISPATCH_EXECUTE") == "1" and
                  a.joint is not None and a.joint_sha256 is not None and a.batch in c.CARDS,
                  "MAIN actual joint + explicit single arm opt-in")
        run_arm(dict(path=str(a.joint),sha256=a.joint_sha256),a.batch,a.packet_sha256)
if __name__ == "__main__":
    main()
