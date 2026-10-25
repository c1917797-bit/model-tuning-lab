"""HOST-only INFO formatter correction for the immutable R30 full40 audit.

Original contracts, raw files, controller and frozen auditor are not changed.
The original parser consumed DEBUG-layout INFO records in its tests. Official
NewLineFormatter uses record.filename in INFO mode. Only that observer schema
is corrected here; transport, source, hot, numeric and release rules are retained.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

WORKSTREAM=Path(__file__).resolve().parent.parent
if str(WORKSTREAM)not in sys.path:sys.path.insert(0,str(WORKSTREAM))
from host_audits import r30_graph_formal_audit as predecessor

native=predecessor.native
components=predecessor.components
audit_r18_base=predecessor.audit_r18_base
audit_physical_workers=predecessor.audit_physical_workers
validate_policy=predecessor.validate_policy
prerequisite=predecessor.prerequisite
BASE_SHA=predecessor.BASE_SHA
PROFILE=predecessor.PROFILE
ENTRY="host_audits/r30b_graph_formal_audit.py"
ORIGINAL="host_audits/r30_graph_formal_audit.py"
FORMATTER_SHA="d8caa69bf25884f6d4f59ca1b3c27e1162f7ab775874b236afc32e0696d5fe7c"


def definition_binding(contract_path,definition):
    cp=Path(contract_path).resolve();root=cp.parent;dp=Path(definition).resolve()
    if dp.parent!=root:raise ValueError("source-bound observer definition must be in owning workstream")
    c=native._read(cp);d=native._read(dp);sources=d.get("source_sha256")
    native._sources(root,sources)
    required={ENTRY,ORIGINAL,"host_audits/r26_group_performance.py",
              "host_audits/r27_graph_canary_audit.py"}
    if (set(sources)!=required
            or sources.get(ENTRY)!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            or sources.get(ORIGINAL)!="b60c8c8138a4ad39528e0a9a5a5a492fe5a1fee80b57fb9d5178d74515b53398"
            or d.get("official_image")!=predecessor.IMAGE
            or d.get("producer_formatter_sha256")!=FORMATTER_SHA
            or d.get("rule")!="INFO_RECORD_FILENAME_NOT_DEBUG_RELPATH"):
        raise ValueError("exact actual observer/source/producer identity required")
    frozen=d.get("original_contracts",{}).get(c.get("performance_group"),{})
    if (frozen.get("path")!=cp.name or frozen.get("raw_root")!=c.get("raw_root")
            or frozen.get("sha256")!=hashlib.sha256(native._read(cp,json_value=False)).hexdigest()):
        raise ValueError("observer cannot change original contract/raw identity")
    return {"definition":dp.name,"definition_sha256":hashlib.sha256(native._read(dp,json_value=False)).hexdigest(),
            "source_sha256":sources,"change":"Only official INFO record.filename vs DEBUG relpath; original numerical/transport/hot/source/release criteria retained",
            "old_frozen_auditor_preserved":True}


def parse_info_graph(log_bytes):
    if type(log_bytes) is not bytes:
        raise ValueError("original service log bytes required")
    workers={};replays=[];finishes=[]
    load = re.compile(native._PREFIX+r"INFO "+native._TIME+
        r" \[model_runner_v1\.py:3718\] Starting to load model /model\.\.\.")
    finish = re.compile(native._PREFIX+r"INFO "+native._TIME+
        r" \[monitor\.py:53\] torch\.compile took [0-9]+\.[0-9]+ s in total")
    for number,raw in enumerate(log_bytes.decode("utf-8").splitlines(),1):
        line=native._ANSI.sub("",raw)
        m=load.fullmatch(line)
        if m:
            rank,pid=int(m[1]),int(m[2])
            if rank in workers and workers[rank]!=pid:raise ValueError("native worker PID changed")
            workers[rank]=pid
        for pattern,rows in ((finish,finishes),(native._REPLAY,replays)):
            m=pattern.fullmatch(line)
            if m:
                rank,pid=int(m[1]),int(m[2])
                if rank!=0:raise ValueError("pinned info_once local-first source scope differs")
                rows.append((number,pid))
    if set(workers)!=set(range(4)) or not finishes or not replays:
        raise ValueError("actual four-worker INFO startup and local-first compile/replay required")
    if (any(pid!=workers[0]for _,pid in finishes+replays)
            or min(x[0]for x in finishes)>=min(x[0]for x in replays)):
        raise ValueError("native source-owned successful compile/replay identity/order differs")
    return {"workers":workers,"compile_complete_lines":[x[0]for x in finishes],
        "replay_directly_observed_rank":0,"replay_lines":[x[0]for x in replays],
        "service_log_sha256":hashlib.sha256(log_bytes).hexdigest(),
        "scope":"actual native INFO replay; capture compatibility proved by same-source R29 canary, not per-token/all-rank completed replay counts"}



def audit(path, *, definition, live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if Path.cwd().resolve()!=root:raise ValueError("owning workstream cwd required")
    c=native._read(cp);binding=definition_binding(cp,definition)
    predecessor.host_binding(c,root)
    cfg,manifest=components._manifest(c,root)
    policy=validate_policy(c,cfg);prior=prerequisite(c,root)
    native._sources(root,c.get("host_controller_source_sha256"))
    report=audit_r18_base(cp,live_release=live_release)
    raw=Path(c["raw_root"]);launch=native._read(raw/"launch.json")
    if (launch.get("controller_sha256")!=BASE_SHA
            or launch.get("base_controller_sha256")!=BASE_SHA
            or launch.get("host_controller_sha256")!=c.get("host_controller_sha256")
            or c["host_controller_source_sha256"].get("host_audits/r30_graph_formal_controller.py")!=c["host_controller_sha256"]):
        raise ValueError("real base/HOST/launch identity split mismatch")
    argv=launch["argv"];env=native._environment(argv);actual=launch.get("graph_runtime",{})
    if (any(actual.get(k)!=v for k,v in c["graph_runtime"].items())
            or json.loads(native._option(argv,"--compilation-config"))!=native.COMPILATION
            or native._option(argv,"--tensor-parallel-size")!="4"
            or native._option(argv,"--data-parallel-size")!="1"
            or native._option(argv,"--max-model-len")!="40960"
            or native._option(argv,"--max-num-batched-tokens")!="40960"
            or native._option(argv,"--max-num-seqs")!="32"
            or "--enforce-eager"in argv or "--no-enable-prefix-caching"not in argv
            or "--enable-prefix-caching"in argv
            or env.get("VLLM_LOGGING_LEVEL")!="INFO"):
        raise ValueError("actual formal graph/common INFO/noPDC launch mismatch")
    events=components._events(raw,"compact-worker-")
    if policy["algorithm_on"]:
        if (native.OLD_COMPACT & env.keys()
                or env.get("INDEPENDENT_GRAPH_HYPIC")!="1"
                or env.get("INDEPENDENT_GRAPH_MANIFEST")!="/probe/"+c["successor_manifest"]
                or env.get("INDEPENDENT_GRAPH_RAW")!="/scratch/diagnostics"
                or not env.get("PYTHONPATH","").startswith("/probe/graph_candidate/bootstrap:/probe:")):
            raise ValueError("actual graph treatment environment mismatch")
        workers=report["hot"]["worker_pids"]
        for event in ("graph_native_worker_import_verified","graph_candidate_hooks_installed"):
            rows=[e for e in events if e.get("event")==event]
            if len(rows)!=4 or {e.get("pid")for e in rows}!=set(workers.values()) or any(
                e.get("manifest_sha256")!=manifest or e.get("profile",e.get("graph_profile"))!=PROFILE for e in rows):
                raise ValueError("four actual graph source activations required")
        if any(e.get("source_owned_native_compile_warmup")is not True for e in events if e.get("event")=="graph_candidate_hooks_installed"):
            raise ValueError("actual warmup repair activation missing")
    elif (any(k.startswith("INDEPENDENT_")for k in env)
            or any(":/probe" in x for x in argv)
            or (raw/"diagnostics").exists()):
        raise ValueError("native group cannot import or mount an algorithm")
    report.update(components._algorithm_evidence(c,cfg,report,events,manifest,policy["algorithm_on"]))
    info=parse_info_graph(native._read(raw/"service.log",json_value=False))
    if policy["algorithm_on"] and info["workers"]!=report["hot"]["worker_pids"]:
        raise ValueError("actual native log worker mapping differs from mechanism")
    journal=[json.loads(x)for x in native._read(raw/"events.jsonl",json_value=False).decode().splitlines()]
    samples=[e["snapshot"]for e in journal if e.get("event")=="isolation"]
    start=native._read(raw/"service-start.json")
    physical=audit_physical_workers(samples,info["workers"],owned_cid=start["container_id"])
    report.update(graph=info,physical=physical,numerical_prerequisite=prior,
        formal_graph_profile_verified=True,r30_host_audit=c["r30_host_audit"]["source_sha256"],
        r30_info_format_audit=binding,policy=policy,
        scope="one actual full40 same-source graph G1/G3 phase; necessary mechanism/safety evidence overhead counted. Matched/repeated speed,paired quality,lifecycle andwholepaper remain separate")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--contract",required=True)
    parser.add_argument("--definition",required=True)
    parser.add_argument("--live-release",action="store_true");args=parser.parse_args()
    print(json.dumps(audit(args.contract,definition=args.definition,live_release=args.live_release)))
