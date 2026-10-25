"""Offline R34 producer/parser integration using immutable R33 archive bytes.
The inspect/command adapter is an archived fixture, never a current Docker probe.
"""
import argparse,hashlib,json,sys,tempfile,re
from pathlib import Path
from types import SimpleNamespace
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r34_prefix_terminal_trial as owner
from host_audits.r34_live_native_log import take_owned_log
from host_audits.r30b_graph_formal_audit import parse_info_graph
from host_audits.r33_prefix_terminal_evidence import pre_timing_proof,first_shape_rows
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def replay():
    case=json.loads((W/"R33_A1_CONTROL_TOOLING_FAILURE_20261025.json").read_bytes())
    c=json.loads((W/case["contract"]).read_bytes());raw=Path(c["raw_root"])
    if sha(W/case["contract"])!=case["contract_sha256"]:raise ValueError("original contract changed")
    before={n:sha(raw/n)for n in case["review"]["raw_sha256"]}
    if before!=case["review"]["raw_sha256"]:raise ValueError("immutable original raw changed")
    ready=json.loads((W/"R34_HOST_AUTHORITY_LIFECYCLE_VALIDATION_20261025.json").read_bytes())
    if sha(owner.__file__)!=ready["controller_sha256"]:raise ValueError("R34 tested source changed")
    final=(raw/"service.log").read_bytes();info=parse_info_graph(final)
    # Actual ordered startup prefix through the first native replay; this is not
    # presented as a captured live snapshot or proof of wall-clock availability.
    lines=final.splitlines(keepends=True);cut=info["replay_lines"][0]
    startup=b"".join(lines[:cut]);early=parse_info_graph(startup)
    if early["workers"]!=info["workers"]:raise ValueError("actual startup/final workers differ")
    cfg,manifest=owner.retained.components._manifest(c,W)
    proof=pre_timing_proof(raw,early["workers"],manifest)
    events=owner.retained.components._events(raw,"compact-worker-")
    state=first_shape_rows(events,early["workers"],manifest)
    if len(state)!=8 or any(e["terminal_only"]is not False for e in state):
        raise ValueError("control archive incorrectly relabeled enabled")
    start=json.loads((raw/"service-start.json").read_bytes());cid=start["container_id"]
    meta={"Id":cid,"Image":start["image"],"Config":{"Labels":{"model-tuning-lab.task":owner.base.TASK}},
        "State":{"Running":True},"HostConfig":{"Devices":[{"PathOnHost":d}for d in start["devices"]]}}
    calls=[]
    def inspect_fixture(value):
        if value!=cid:raise ValueError("wrong archive CID")
        return meta
    def command_fixture(argv,timeout):
        if argv!=["docker","logs",cid]or timeout!=30:raise ValueError("wrong producer call")
        calls.append(argv);return startup.decode()
    fixture=SimpleNamespace(TASK=owner.base.TASK,inspect=inspect_fixture,command=command_fixture)
    with tempfile.TemporaryDirectory(prefix="r34-archive-producer-",dir="/cache/cch")as tmp:
        temp=Path(tmp);(temp/"service-start.json").write_bytes((raw/"service-start.json").read_bytes())
        if(temp/"service.log").exists():raise ValueError("terminal fixture must be absent")
        captured,receipt=take_owned_log(temp,c,backend=fixture)
        if captured!=startup or len(calls)!=1 or parse_info_graph(captured)["workers"]!=early["workers"]:
            raise ValueError("actual archive bytes failed production helper/parser")
        if receipt["sha256"]!=hashlib.sha256(startup).hexdigest()or(temp/"service.log").exists():
            raise ValueError("receipt or producer phase wrong")
    rejected=0
    for corrupt in (b"".join(lines[:cut-1]),
                    b"\n".join(x for x in startup.splitlines()if b"Starting to load model /model..."not in x)):
        try:parse_info_graph(corrupt)
        except ValueError:rejected+=1
        else:raise ValueError("incomplete native startup was accepted")
    if {n:sha(raw/n)for n in before}!=before:raise ValueError("original archive mutated")
    return {"schema":"hypic-r34-archived-producer-replay/v1","production_live_log_helper_and_parser":"PASS",
        "actual_startup_final_worker_parity":True,"actual_control_private_states":len(state),
        "actual_warm_shape_lengths":[8,39],"actual_worker_streams":len(proof["worker_prefixes"]),
        "incomplete_startup_negative_controls":rejected,"archived_startup_bytes":len(startup),
        "archived_startup_sha256":hashlib.sha256(startup).hexdigest(),"original_raw_unchanged":True,
        "fixture_scope":"Identity adapter constructed from historical service-start receipt; log bytes and worker evidence are actual archive. No live Docker or device query.",
        "live_container_producer_verified":False,"enabled_candidate_proven":False,
        "timed_experiment_valid":False,"new_device_work":False,"full_goal_complete":False,
        "source_sha256":{str(Path(__file__).relative_to(W)):sha(__file__),
            "host_audits/r34_prefix_terminal_trial.py":sha(owner.__file__),
            "host_audits/r34_live_native_log.py":sha(W/"host_audits/r34_live_native_log.py")},
        "raw_root":str(raw),"original_raw_sha256":before}
if __name__=="__main__":print(json.dumps(replay(),sort_keys=True))
