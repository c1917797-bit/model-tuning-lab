"""Independent HOST full40 graph audit composed from real terminal/hot helpers.

Formal INFO logs intentionally omit per-worker DEBUG capture. The same Python
runtime has accepted R29 capture/ordering evidence; this phase adds actual
INFO replay plus exact physical ownership and all40 transport/mechanism proof.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))
from host_audits import r26_group_performance as components
from host_audits import r27_graph_canary_audit as native
from audit_r18_terminal_base import audit_r18_base
from audit_physical_worker_namespaces import audit_physical_workers

ENTRY = "host_audits/r30_graph_formal_audit.py"
HOST_HELPERS = {ENTRY, "host_audits/r26_group_performance.py",
                "host_audits/r27_graph_canary_audit.py"}
BASE_SHA = "bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
PROFILE = "selective-prefill-native-decode-v1"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
GRAPH = {"profile": PROFILE, "compilation_mode": 3,
    "cudagraph_mode": "FULL_DECODE_ONLY", "capture_sizes": [1,4,8,16,24,32],
    "official_compilation_source_sha256": native.COMPILATION_SHA256,
    "official_debug_logging": False}


def host_binding(c, root):
    mapping = c.get("r30_host_audit", {}).get("source_sha256")
    native._sources(root, mapping)
    if (set(mapping) != HOST_HELPERS
            or mapping.get(ENTRY) != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError("exact actual formal graph HOST audit closure required")
    return mapping


def validate_policy(c, cfg):
    group = c.get("performance_group")
    if group not in ("G1", "G3"):
        raise ValueError("this first-screen successor supports actual G1/G3 only; PDC needs its own observer")
    on = group == "G3"
    if (c.get("image") != IMAGE or c.get("controller_sha256") != BASE_SHA
            or c.get("base_controller_sha256") != BASE_SHA
            or c.get("formal_performance") is not True
            or c.get("formal_quality") is not False
            or c.get("enable_thinking") is not False
            or c.get("max_output_tokens") != 1024
            or c.get("enable_prefix_caching") is not False
            or c.get("physical_npus") != [0,1,2,3] or c.get("tp") != 4
            or c.get("enforce_eager") is not False
            or c.get("performance_round") not in (1,2,3)
            or type(c.get("performance_round")) is not int):
        raise ValueError("full40 graph source/profile/physical/ruler mismatch")
    if c.get("graph_runtime") != dict(GRAPH, candidate_enabled=on):
        raise ValueError("exact native graph profile with common INFO required")
    if (cfg.get("prefill_prompt_snapshot") is not True
            or cfg.get("prompt_snapshot_probe_batches") != 0
            or type(cfg.get("prompt_snapshot_probe_batches")) is not int
            or cfg.get("c1_performance_mode") is not True
            or cfg.get("c1_layer_shadow_validation") is not False
            or cfg.get("c1_first_divergence") is not False
            or cfg.get("c1_first_divergence_head_policy") != "head0"
            or cfg.get("c1_async_material_verify") is not False
            or c.get("protocol_notes", {}).get("timed_diagnostics") is not False):
        raise ValueError("explicit timed mode, no numerical/probe workload required")
    if (c.get("transfer_treatment") != ("async" if on else "native")
            or cfg.get("c1_async_material_transfer") is not on
            or c.get("lazy_snapshot_treatment") != ("on" if on else "native")
            or cfg.get("c1_lazy_initial_snapshot") is not on
            or cfg.get("c1_partitioned_render") is not on
            or c.get("r18_partitioned_acceptance", {}).get("enabled") is not on):
        raise ValueError("actual algorithm axes differ")
    if on:
        diag = c.get("cache_diagnostic")
        if not isinstance(diag,dict) or diag.get("compact_manifest") != c.get("successor_manifest"):
            raise ValueError("actual active graph manifest required")
        required = ("c1_packed_wave","native_decode_batch","c1_layer_completion_barrier",
            "c2_layer_completion_barrier","forward_metadata_snapshot","c2_layer_finite_gate",
            "c1_short_suffix_recurrent","c2_block_table_snapshot","c2_block_table_diagnostic")
        if any(cfg.get(k) is not True for k in required):
            raise ValueError("retained numerical safety/ownership/mechanism profile absent")
    elif (c.get("cache_diagnostic")
            or c.get("independent_acceptance",{}).get("require_hypic_markers_absent") is not True):
        raise ValueError("native control must be actually algorithm-free")
    return {"group":group,"algorithm_on":on,"pdc_on":False}


def prerequisite(c, root):
    cp = native._inside(root,c.get("required_canary_contract"))
    if hashlib.sha256(native._read(cp,json_value=False)).hexdigest() != c.get("required_canary_sha256"):
        raise ValueError("R29 canary contract binding drift")
    prior = native._read(cp)
    context_keys = ("image", "model", "model_config_sha256", "physical_npus", "tp",
        "cpu_set", "port", "hccl_ports", "enable_thinking", "max_output_tokens",
        "formal_token_artifact", "enable_prefix_caching", "enforce_eager",
        "absolute_stop_utc")
    if any(c.get(k) != prior.get(k) for k in context_keys):
        raise ValueError("current model/image/input/CPU/profile differs from accepted graph canary")
    ev = c.get("numerical_prerequisite_evidence",{})
    ep = native._inside(root,ev.get("path"))
    if hashlib.sha256(native._read(ep,json_value=False)).hexdigest() != ev.get("sha256"):
        raise ValueError("R29 accepted report binding drift")
    proof = native._read(ep);audit = proof.get("audit",{})
    if (proof.get("contract") != cp.name or proof.get("contract_sha256") != c["required_canary_sha256"]
            or proof.get("raw_root") != prior.get("raw_root")
            or audit.get("warmup_repair_bounded_valid") is not True
            or audit.get("live_release_verified") is not True
            or audit.get("hot",{}).get("denominator") != 2
            or prior.get("base_controller_sha256") != BASE_SHA):
        raise ValueError("accepted bounded graph/numerical prerequisite identity absent")
    raw = Path(proof["raw_root"])
    for name,digest in dict(proof["raw_sha256"],**proof["worker_evidence_sha256"]).items():
        if hashlib.sha256(native._read(native._inside(raw,name),json_value=False)).hexdigest()!=digest:
            raise ValueError("R29 immutable raw drift")
    old_mf = native._read(native._inside(root,prior["cache_diagnostic"]["compact_manifest"]))
    mf = native._read(native._inside(root,c["successor_manifest"]))
    old_py={n:h for n,h in old_mf["source_sha256"].items() if n.endswith(".py")}
    new_py={n:h for n,h in mf["source_sha256"].items() if n.endswith(".py")}
    if old_py != new_py:
        raise ValueError("timed runtime Python differs from accepted R29")
    if c["performance_group"]=="G3":
        old_cfg=native._read(native._inside(root,old_mf["config"]))
        want=dict(old_cfg,c1_performance_mode=True,c1_layer_shadow_validation=False,
                  c1_first_divergence=False,prompt_snapshot_probe_batches=0,
                  c1_first_divergence_head_policy="head0",c1_async_material_verify=False)
        cfg=native._read(native._inside(root,mf["config"]))
        if cfg!=want:
            raise ValueError("timed candidate changed more than declared diagnostic workload")
    return {"report":ep.name,"sha256":ev["sha256"],"python_sources":len(new_py),
            "scope":"same runtime Python and bounded graph/numerical prerequisites; not formal quality"}


def parse_info_graph(log_bytes):
    if type(log_bytes) is not bytes:
        raise ValueError("original service log bytes required")
    workers={};replays=[];finishes=[]
    load = re.compile(native._PREFIX+r"INFO "+native._TIME+
        r" \[model_runner_v1\.py:3718\] Starting to load model /model\.\.\.")
    finish = re.compile(native._PREFIX+r"INFO "+native._TIME+
        r" \[compilation/monitor\.py:53\] torch\.compile took [0-9]+\.[0-9]+ s in total")
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


def audit(path, *, live_release=False):
    cp=Path(path).resolve();root=cp.parent
    if Path.cwd().resolve()!=root:raise ValueError("owning workstream cwd required")
    c=native._read(cp);binding=host_binding(c,root)
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
        formal_graph_profile_verified=True,r30_host_audit=binding,policy=policy,
        scope="one actual full40 same-source graph G1/G3 phase; necessary mechanism/safety evidence overhead counted. Matched/repeated speed,paired quality,lifecycle andwholepaper remain separate")
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--contract",required=True)
    parser.add_argument("--live-release",action="store_true");args=parser.parse_args()
    print(json.dumps(audit(args.contract,live_release=args.live_release)))
