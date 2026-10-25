"""HOST-only warmed c16 cost profile against the unchanged independent runtime.
No algorithm, runner, scheduler or official image source is altered.
Default --check never starts a container. Profiler results are diagnostic only.
"""
import argparse
import copy
import hashlib
import json
import os
import sys
import threading
from pathlib import Path

WORKSTREAM=Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:sys.path.insert(0,str(WORKSTREAM))
import profile_tp4_warm_diagnostic as base
from independent_warm_profile_workload import validate_profile_spec,profiler_config
from host_audits import r30_graph_formal_audit as retained
ENTRY="host_audits/r31_warm_graph_profile.py"
BASE="profile_tp4_warm_diagnostic.py"
BASE_SHA="b26fa6006fd780b19aff3fd804a464e04aeb374b97152d9a24165157e1ee0100"
BOOTSTRAP="graph_candidate/bootstrap"
CAPTURE_SIZES=[1,4,8,16,24,32]
_LOCK=threading.Lock()

def profile_prerequisite(c,root):
    group=c["performance_group"]
    anchors={"G1":"93b51310cd9bf14ea89fe260d455099181fe9865743052df5a081f7f5a01a820",
             "G3":"278fc2663df36a562d2b65b3bb291d1bcfe6fab5bc2a89ff089b0b9fc84a3489"}
    path=root/("FORMAL_GRAPH_R30_"+group+"_R1_20261025_CONTRACT.json")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=anchors[group]:
        raise ValueError("original full40 source anchor drift")
    original=json.loads(path.read_bytes())
    prior=retained.prerequisite(original,root)
    for key in("image","model","model_config_sha256","formal_token_artifact","physical_npus",
               "tp","cpu_set","enforce_eager","graph_runtime","enable_prefix_caching",
               "successor_manifest"):
        if c.get(key)!=original.get(key):
            raise ValueError("actual diagnostic identity differs from full40 source anchor: "+key)
    def bindings(x):return x.get("baseline_host_source_sha256")or x["cache_diagnostic"]["source_sha256"]
    if bindings(c)!=bindings(original):
        raise ValueError("diagnostic may not alter the425runtime bindings")
    return dict(prior,original_source_contract=path.name,original_source_sha256=anchors[group],
        protocol_difference="Actual same-runtime diagnostic64 outputs; original formal1024 unchanged. No speed/quality equivalence claim.")

def check_contract(c,*,source_root=WORKSTREAM,base_module=base):
    root=Path(source_root).resolve()
    sources=c.get("host_controller_source_sha256")
    retained.native._sources(root,sources)
    own=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (set(sources)!={ENTRY,BASE,"independent_warm_profile_workload.py"}
            or sources[ENTRY]!=own or sources[BASE]!=BASE_SHA
            or c.get("host_controller_sha256")!=own
            or c.get("controller_sha256")!=BASE_SHA or c.get("base_controller_sha256")!=BASE_SHA
            or Path(base_module.__file__).resolve()!=root/BASE
            or hashlib.sha256(Path(base_module.__file__).read_bytes()).hexdigest()!=BASE_SHA):
        raise ValueError("actual profiler HOST/base/workload identity required")
    spec=validate_profile_spec(c)
    if (c.get("r31_role")!="WARMED_C16_COST_ATTRIBUTION"
            or c.get("performance_group")not in("G1","G3")
            or c.get("enforce_eager")is not False or c.get("enable_prefix_caching")is not False
            or c.get("physical_npus")!=[0,1,2,3]or c.get("tp")!=4
            or c.get("profile_byte_limit")!=2*1024**3
            or c.get("cache_free_floor")!=4*1024**3
            or c.get("max_output_tokens")!=64):
        raise ValueError("bounded actual graph/profile/physical contract required")
    cfg,manifest=retained.components._manifest(c,root)
    algorithm=c["performance_group"]=="G3"
    expected={"profile":retained.PROFILE,"candidate_enabled":algorithm,
        "compilation_mode":3,"cudagraph_mode":"FULL_DECODE_ONLY","capture_sizes":CAPTURE_SIZES,
        "official_compilation_source_sha256":retained.native.COMPILATION_SHA256,
        "official_debug_logging":False}
    if c.get("graph_runtime")!=expected:
        raise ValueError("same graph and INFO profile required")
    if algorithm:
        if not c.get("cache_diagnostic")or c["cache_diagnostic"]["compact_manifest"]!=c["successor_manifest"]:
            raise ValueError("same active independent manifest required")
    elif c.get("cache_diagnostic"):
        raise ValueError("native control cannot load algorithm")
    bindings=c.get("baseline_host_source_sha256")or c["cache_diagnostic"]["source_sha256"]
    retained.native._sources(root,bindings)
    if len(bindings)!=425:
        raise ValueError("unchanged actual R30 common runtime bindings required")
    prior=profile_prerequisite(c,root)
    raw=Path(c["raw_root"])
    if not raw.is_absolute()or raw.exists():raise ValueError("new immutable profile root required")
    from independent_execution_deadline import deadline_epoch
    deadline_epoch(c.get("absolute_stop_utc"))
    return dict(configuration_valid=True,device_run=False,device_admission_performed=False,
        controller_sha256=own,base_controller_sha256=BASE_SHA,graph_runtime=expected,
        active_manifest_sha256=manifest,source_bindings=len(bindings),profile=spec,prerequisite=prior)

def _rewrite_launch(data, contract, checked):
    """Mutate the SAME argv list consumed immediately by unchanged base.command."""
    argv = data.get("argv")
    if (not isinstance(argv, list) or data.get("controller_sha256") != BASE_SHA
            or "--enforce-eager" in argv or argv.count("--compilation-config") != 1):
        raise ValueError("unexpected real base launch profile")
    if (argv.count(contract["image"]) != 1
            or any(value == "-e" and i + 1 < len(argv)
                   and argv[i + 1].startswith("VLLM_LOGGING_LEVEL=")
                   for i, value in enumerate(argv))):
        raise ValueError("ambiguous image or pre-existing logging override")
    index = argv.index("--compilation-config") + 1
    previous = {"cudagraph_mode": "FULL_DECODE_ONLY",
                "cudagraph_capture_sizes": CAPTURE_SIZES}
    if json.loads(argv[index]) != previous:
        raise ValueError("unexpected pinned base compilation argv")
    graph = checked["graph_runtime"]
    compiled = dict(previous, mode=3)
    removed, added = [], []
    pythonpath = None
    if graph["candidate_enabled"]:
        old_manifest = "INDEPENDENT_COMPACT_MANIFEST=/probe/" + contract["cache_diagnostic"]["compact_manifest"]
        replacements = {
            "INDEPENDENT_COMPACT_HYPIC=1": "INDEPENDENT_GRAPH_HYPIC=1",
            old_manifest: "INDEPENDENT_GRAPH_MANIFEST=/probe/" + contract["cache_diagnostic"]["compact_manifest"],
            "INDEPENDENT_COMPACT_RAW=/scratch/diagnostics": "INDEPENDENT_GRAPH_RAW=/scratch/diagnostics"}
        seen = set()
        replacement_argv = []
        cursor = 0
        while cursor < len(argv):
            item = argv[cursor]
            if item == "-e":
                if cursor + 1 >= len(argv):
                    raise ValueError("incomplete environment argv")
                value = argv[cursor + 1]
                if value.startswith("INDEPENDENT_GRAPH_"):
                    raise ValueError("graph environment already installed")
                if value.startswith("INDEPENDENT_COMPACT_"):
                    if value not in replacements or value in seen:
                        raise ValueError("ambiguous old compact environment")
                    seen.add(value)
                    replacement_argv.extend(["-e", replacements[value]])
                    removed.append(value)
                    added.append(replacements[value])
                elif value.startswith("PYTHONPATH="):
                    prefix = "PYTHONPATH=/probe/compact_bootstrap:/probe:"
                    if pythonpath is not None or not value.startswith(prefix):
                        raise ValueError("exact compact bootstrap path required")
                    updated = "PYTHONPATH=/probe/" + BOOTSTRAP + ":/probe:" + value[len(prefix):]
                    pythonpath = {"from": value, "to": updated}
                    replacement_argv.extend(["-e", updated])
                else:
                    replacement_argv.extend(["-e", value])
                cursor += 2
            else:
                replacement_argv.append(item)
                cursor += 1
        if seen != set(replacements) or pythonpath is None:
            raise ValueError("complete unambiguous compact-to-graph bootstrap required")
        argv[:] = replacement_argv
    else:
        for i, value in enumerate(argv):
            if (value == "-e" and i + 1 < len(argv)
                    and (argv[i + 1].startswith("INDEPENDENT_")
                         or argv[i + 1].startswith("PYTHONPATH="))):
                raise ValueError("native G1 cannot carry probe environment")
            if ":/probe" in value:
                raise ValueError("native G1 cannot mount probe package")
    argv[argv.index("--compilation-config") + 1] = json.dumps(compiled, separators=(",", ":"))
    argv[argv.index(contract["image"]):argv.index(contract["image"])] = [
        "-e", "VLLM_LOGGING_LEVEL=INFO"]
    data["base_controller_sha256"] = BASE_SHA
    data["host_controller_sha256"] = checked["controller_sha256"]
    data["graph_runtime"] = dict(copy.deepcopy(graph), compilation_config=compiled,
        bootstrap=BOOTSTRAP if graph["candidate_enabled"] else None,
        environment_removed=removed, environment_added=added,
        common_environment_added=["VLLM_LOGGING_LEVEL=INFO"],
        pythonpath_change=pythonpath)
    return data



def run_contract(c,*,source_root=WORKSTREAM,base_module=base):
    checked=check_contract(c,source_root=source_root,base_module=base_module)
    if not _LOCK.acquire(blocking=False):raise RuntimeError("one owned profile driver")
    original_write=base_module.write;original_snapshot=base_module.snapshot;launches=0
    raw=Path(c["raw_root"])
    def write(root,name,data):
        nonlocal launches
        if name=="launch.json":
            if Path(root)!=raw or launches:raise ValueError("one exact profile launch")
            launches+=1
            _rewrite_launch(data,c,checked)
            argv=data["argv"]
            actual=json.loads(retained.native._option(argv,"--profiler-config"))
            if actual!=profiler_config(checked["profile"]):
                raise ValueError("actual official profiler argv differs")
            data["r31_profile"]={"role":c["r31_role"],"host_sources":c["host_controller_source_sha256"],
                "profile":checked["profile"],"profile_byte_limit":c["profile_byte_limit"],
                "scope":"warmed c16/32768/64 attribution; not formal speed or quality"}
        return original_write(root,name,data)
    def snapshot(cid=None):
        result=original_snapshot(cid)
        if cid:
            size=sum(p.stat().st_size for p in(raw/"profile").rglob("*")if p.is_file())
            stat=os.statvfs("/cache");free=stat.f_bavail*stat.f_frsize
            if size>c["profile_byte_limit"]or free<c["cache_free_floor"]:
                base_module.stop_owned_on_foreign(cid,image=c["image"])
                raise RuntimeError("bounded profiler storage guard stopped exact owned service")
        return result
    base_module.write=write;base_module.snapshot=snapshot
    try:
        result=base_module.run_contract(c)
        if launches!=1:raise ValueError("actual profile launch missing")
        return result
    finally:
        if base_module.write is write:base_module.write=original_write
        if base_module.snapshot is snapshot:base_module.snapshot=original_snapshot
        _LOCK.release()

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run",action="store_true")
    p.add_argument("--contract",required=True);a=p.parse_args();c=json.loads(Path(a.contract).read_bytes())
    if a.run:run_contract(c)
    else:print(json.dumps(check_contract(c)))
