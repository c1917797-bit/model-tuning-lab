"""HOST-only R27 audit; candidate receipts never prove native ACL execution.

No controller, device runner, graph candidate or old HTTP evaluator is executed.
The mechanism report is explicitly partial until an independently verified
official capture/replay evidence adapter is available.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

WORKSTREAM = Path(__file__).resolve().parent.parent
if str(WORKSTREAM) not in sys.path:
    sys.path.insert(0, str(WORKSTREAM))

from audit_full40_hot_coverage import _audit_hot
from audit_prompt_snapshot_canary import audit_probe_rows
from audit_physical_worker_namespaces import audit_physical_workers
from audit_c1_partitioned_canary import audit_partition_rows
from audit_r19_lazy_snapshot_canary import audit_snapshot_receipts as audit_lazy
from audit_r20_metadata_canary_v2 import audit_metadata_receipts
from audit_r21_c2_finite_canary import audit_finite_receipts
from audit_r24_c2_snapshot_canary import audit_snapshot_receipts as audit_c2_snapshot

HOST_CONTROLLER = "host_audits/r27_graph_controller.py"
HOST_AUDITOR = "host_audits/r27_graph_canary_audit.py"
BASE_CONTROLLER = "formal_r15_tp4.py"
BASE_SHA256 = "bf55661d61618a7f83537ce6bf477b66e80ccaf097ac714938ceee9bdf199d33"
PROFILE = "selective-prefill-native-decode-v1"
COMPILATION_SHA256 = "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913"
NATIVE_RUNNER_SHA256 = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
CAPTURE_SIZES = [1, 4, 8, 16, 24, 32]
COMPILATION = {"mode": 3, "cudagraph_mode": "FULL_DECODE_ONLY",
               "cudagraph_capture_sizes": CAPTURE_SIZES}
OLD_COMPACT = {"INDEPENDENT_COMPACT_HYPIC", "INDEPENDENT_COMPACT_MANIFEST",
               "INDEPENDENT_COMPACT_RAW"}
GRAPH_ENV = {"INDEPENDENT_GRAPH_HYPIC", "INDEPENDENT_GRAPH_MANIFEST",
             "INDEPENDENT_GRAPH_RAW"}
GRAPH_FILES = {"graph_candidate/__init__.py", "graph_candidate/activation.py",
               "graph_candidate/source_contract.py", "graph_candidate/entry_router.py",
               "graph_candidate/prefill_bridge.py", "graph_candidate/worker_loader.py",
               "graph_candidate/bootstrap/sitecustomize.py"}
_HASH = re.compile(r"[0-9a-f]{64}")


class GraphEvidencePending(ValueError):
    def __init__(self, report):
        super().__init__("official per-worker ACL capture/replay evidence not independently verified")
        self.partial_report = report


def _read(path, *, json_value=True):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular evidence/source file required")
    raw = path.read_bytes()
    return json.loads(raw) if json_value else raw


def _inside(base, name):
    if type(name) is not str or not name or Path(name).is_absolute():
        raise ValueError("relative source identity required")
    original = base / name
    path = original.resolve()
    if original.is_symlink() or not path.is_relative_to(base):
        raise ValueError("source escapes frozen workstream")
    return path


def _sources(base, mapping):
    if type(mapping) is not dict or not mapping:
        raise ValueError("nonempty frozen source map required")
    for name, digest in mapping.items():
        if (type(digest) is not str or not _HASH.fullmatch(digest)
                or hashlib.sha256(_read(_inside(base, name), json_value=False)).hexdigest() != digest):
            raise ValueError("source binding drift: " + str(name))


def _option(argv, name):
    if argv.count(name) != 1:
        raise ValueError("one actual argv option required: " + name)
    index = argv.index(name)
    if index + 1 >= len(argv):
        raise ValueError("missing argv value")
    return argv[index + 1]


def _environment(argv):
    env = {}
    for index, item in enumerate(argv):
        if item not in ("-e", "--env"):
            continue
        if index + 1 >= len(argv) or "=" not in argv[index + 1]:
            raise ValueError("explicit actual environment value required")
        name, value = argv[index + 1].split("=", 1)
        if name in env:
            raise ValueError("duplicate launch environment")
        env[name] = value
    return env


def _controller_and_launch(base, contract, launch):
    sources = contract.get("host_controller_source_sha256")
    _sources(base, sources)
    own = contract.get("controller_sha256")
    if (not {HOST_CONTROLLER, BASE_CONTROLLER} <= sources.keys()
            or sources[HOST_CONTROLLER] != own
            or sources[BASE_CONTROLLER] != BASE_SHA256
            or contract.get("base_controller_sha256") != BASE_SHA256
            or launch.get("controller_sha256") != BASE_SHA256
            or launch.get("host_controller_sha256") != own
            or launch.get("base_controller_sha256") != BASE_SHA256):
        raise ValueError("actual HOST/base/launch controller identities differ")
    arm = contract.get("graph_canary_group")
    if arm not in ("G1", "G3") or (
            "performance_group" in contract and contract["performance_group"] != arm):
        raise ValueError("unambiguous bounded G1/G3 group required")
    expected = {"profile": PROFILE, "candidate_enabled": arm == "G3",
                "compilation_mode": 3, "cudagraph_mode": "FULL_DECODE_ONLY",
                "capture_sizes": CAPTURE_SIZES,
                "official_compilation_source_sha256": COMPILATION_SHA256, "official_debug_logging": True}
    if contract.get("graph_runtime") != expected or contract.get("enforce_eager") is not False:
        raise ValueError("frozen actual native graph profile required")
    actual = launch.get("graph_runtime", {})
    if any(actual.get(k) != v for k, v in expected.items()) or actual.get("compilation_config") != COMPILATION:
        raise ValueError("actual launch graph profile differs")
    argv = launch.get("argv")
    if type(argv) is not list or any(type(x) is not str for x in argv):
        raise ValueError("actual launch argv required")
    if ("--enforce-eager" in argv or json.loads(_option(argv, "--compilation-config")) != COMPILATION
            or _option(argv, "--tensor-parallel-size") != "4"
            or _option(argv, "--data-parallel-size") != "1"
            or "--no-enable-prefix-caching" not in argv
            or "--enable-prefix-caching" in argv):
        raise ValueError("actual graph/TP4/noPDC argv differs")
    env = _environment(argv)
    if env.get("VLLM_LOGGING_LEVEL") != "DEBUG":
        raise ValueError("common source-owned official graph DEBUG logging required")
    return arm, env, argv


def _requests(contract, records, journal):
    if (len(records) != 3 or {r.get("index") for r in records} != {0, 1, 2}
            or [{k: v for k, v in e.items() if k != "event"}
                for e in journal if e.get("event") == "response"] != records):
        raise ValueError("complete three-response raw journal required")
    spec = contract["formal_token_artifact"]
    path = Path(spec["path"])
    if not path.is_absolute():
        raise ValueError("absolute frozen token artifact required")
    raw = _read(path, json_value=False)
    if hashlib.sha256(raw).hexdigest() != spec["sha256"]:
        raise ValueError("frozen token artifact drift")
    artifact = json.loads(raw)
    first = artifact["requests"][0]
    end = first["segment_end"]
    expected = [artifact["public_segment"] + first["token_ids"][end:end+256],
                first["token_ids"], artifact["requests"][1]["token_ids"]]
    ids = []
    for item in records:
        index = item["index"]
        payload, response = item["payload"], item["response"]
        usage = response["usage"]
        length, output = (16640, 1) if index == 0 else (32768, 1024)
        if (payload.get("prompt") != expected[index] or len(expected[index]) != length
                or payload.get("max_tokens") != output or payload.get("ignore_eos") is not True
                or payload.get("temperature") != 0 or payload.get("seed") != 0
                or usage.get("prompt_tokens") != length or usage.get("completion_tokens") != output):
            raise ValueError("actual bounded payload/usage differs from frozen protocol")
        rid = response.get("id")
        if not isinstance(rid, str) or not rid or rid in ids:
            raise ValueError("three unique actual HTTP response ids required")
        ids.append(rid)
    return [r["response"]["id"] for r in records if r["index"] in (1, 2)]


def _terminal(contract, raw):
    result = _read(raw / "result.json")
    records = _read(raw / "responses.json")
    journal = [json.loads(x) for x in _read(raw / "events.jsonl", json_value=False).decode().splitlines()]
    if (result.get("valid") is not True or result.get("error") is not None
            or result.get("guard_errors") or result.get("responses") != 3
            or [e for e in journal if e.get("event") == "terminal"] != [{"event": "terminal", "result": result}]):
        raise ValueError("complete successful terminal required")
    private_ids = _requests(contract, records, journal)
    samples = _read(raw / "isolation.json")
    if (not samples or samples != [e["snapshot"] for e in journal if e.get("event") == "isolation"]
            or len(samples) != result.get("isolation_samples") or any(s["foreign"] for s in samples)):
        raise ValueError("continuous clean isolation inventory required")
    start, release = _read(raw / "service-start.json"), _read(raw / "release.json")
    if (not isinstance(start.get("container_id"), str) or not _HASH.fullmatch(start["container_id"])
            or start.get("image") != contract["image"]
            or set(start.get("devices", [])) != {"/dev/davinci"+str(i) for i in range(4)}
            or release != result.get("release") or release.get("owned_container") != start["container_id"]
            or release.get("removed") is not True or release.get("port_free") is not True
            or release.get("final_physical_processes")):
        raise ValueError("exact source image/physical0-3/owned release required")
    return private_ids, samples, start


def _verify_live_release(contract, start):
    # These base functions are source-bound above; import defines helpers only.
    from formal_r15_tp4 import snapshot, port_free
    cid = start["container_id"]
    probe = subprocess.run(["docker", "inspect", cid], capture_output=True, text=True)
    if (probe.returncode == 0 or probe.stdout.strip() != "[]"
            or not ("No such object" in probe.stderr or "No such container" in probe.stderr)):
        raise ValueError("independent exact owned container absence not proved")
    if snapshot()["processes"]:
        raise ValueError("independent live physical0-3 release not empty")
    port_free(contract["port"])


def audit_mechanism(contract_path, *, live_release=False):
    """Return an explicitly partial raw/source/mechanism audit, never graph valid."""
    cp = Path(contract_path).resolve()
    base, contract = cp.parent, _read(cp)
    auditor_sources = contract.get("r27_host_audit", {}).get("source_sha256")
    _sources(base, auditor_sources)
    if (HOST_AUDITOR not in auditor_sources
            or hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != auditor_sources[HOST_AUDITOR]):
        raise ValueError("actual independent HOST auditor source identity differs")
    if (contract.get("physical_npus") != [0, 1, 2, 3] or contract.get("tp") != 4
            or contract.get("formal_performance", False) is not False
            or contract.get("formal_quality", False) is not False
            or contract.get("enable_prefix_caching") is not False):
        raise ValueError("bounded physical0-3 TP4 noPDC canary only")
    raw = Path(contract["raw_root"])
    if not raw.is_absolute() or raw.is_symlink():
        raise ValueError("absolute immutable raw root required")
    launch = _read(raw / "launch.json")
    arm, env, argv = _controller_and_launch(base, contract, launch)
    private_ids, samples, start = _terminal(contract, raw)
    if live_release:
        _verify_live_release(contract, start)
    paths = sorted((raw / "diagnostics").glob("compact-worker-*.jsonl"))
    diagnostic = contract.get("cache_diagnostic")
    report = {"valid": False, "bounded_mechanism_audited": True, "arm": arm,
              "controller_sha256": contract["controller_sha256"], "base_controller_sha256": BASE_SHA256,
              "graph_execution_verified": False, "graph_evidence_status": "OFFICIAL_CAPTURE_REPLAY_PENDING",
              "live_release_verified": live_release,
              "isolation_samples": len(samples), "quality_acceptance": "NOT_DECIDED",
              "scope": "bounded3 responses/two private requests; graph proof pending; not performance/fullquality"}
    if arm == "G1":
        _sources(base, contract.get("baseline_host_source_sha256"))
        if (diagnostic or paths or any(k.startswith("INDEPENDENT_") for k in env)
                or "/probe:" in env.get("PYTHONPATH", "")
                or any(x.split(":")[1:2] == ["/probe"] for x in argv if ":" in x)
                or launch["graph_runtime"].get("bootstrap") is not None):
            raise ValueError("G1 must be native without old/new algorithm package")
        observed = {o["npu"] for s in samples for o in s.get("owners", [])
                    if o.get("owned") is True and start["container_id"] in o.get("cgroup", "")}
        if observed != set(range(4)):
            raise ValueError("native physical0-3 ownership missing")
        report["physical"] = {"native_owned_physical_cards": sorted(observed), "rank_assignment_claimed": False}
        report["hot"] = None
        return report
    if not isinstance(diagnostic, dict):
        raise ValueError("G3 graph package binding required")
    sources = diagnostic["source_sha256"]
    _sources(base, sources)
    manifest_path = _inside(base, diagnostic["compact_manifest"])
    manifest_raw = _read(manifest_path, json_value=False)
    manifest = json.loads(manifest_raw)
    mh = hashlib.sha256(manifest_raw).hexdigest()
    if (manifest.get("graph_profile") != PROFILE or not GRAPH_FILES <= manifest["source_sha256"].keys()
            or any(sources.get(n) != h for n, h in manifest["source_sha256"].items())
            or manifest["config"] not in manifest["source_sha256"]):
        raise ValueError("complete source-bound graph manifest required")
    config = _read(_inside(base, manifest["config"]))
    required = ("prefill_prompt_snapshot", "c1_layer_shadow_validation", "c1_first_divergence",
                "c1_partitioned_render", "c1_lazy_initial_snapshot", "forward_metadata_snapshot",
                "c2_layer_completion_barrier", "c2_layer_finite_gate", "c2_block_table_snapshot",
                "c2_block_table_diagnostic")
    if (any(config.get(k) is not True for k in required) or config.get("prompt_snapshot_probe_batches") != 2
            or config.get("c1_performance_mode", False) is not False):
        raise ValueError("unchanged bounded numeric/snapshot diagnostics required")
    if (OLD_COMPACT & env.keys() or env.get("INDEPENDENT_GRAPH_HYPIC") != "1"
            or env.get("INDEPENDENT_GRAPH_MANIFEST") != "/probe/" + diagnostic["compact_manifest"]
            or env.get("INDEPENDENT_GRAPH_RAW") != "/scratch/diagnostics"
            or not env.get("PYTHONPATH", "").startswith("/probe/graph_candidate/bootstrap:/probe:")
            or launch["graph_runtime"].get("bootstrap") != "graph_candidate/bootstrap"):
        raise ValueError("G3 must use exact new graph namespace without double activation")
    if len(paths) != 4:
        raise ValueError("four actual worker evidence files required")
    events = [json.loads(x) for p in paths for x in _read(p, json_value=False).decode().splitlines()]
    hot = _audit_hot(events, private_ids, manifest_sha256=mh, expected_count=2)
    if not hot["accepted_hot_coverage"]:
        raise ValueError("two-request same-step fourrank48/16 hot proof required")
    workers = hot["worker_pids"]
    installs = [e for e in events if e.get("event") == "compact_hypic_hooks_installed"]
    if (len(installs) != 4 or {e["pid"] for e in installs} != set(workers.values())
            or any(e.get("manifest_sha256") != mh or any(e.get(k) is not True for k in required)
                   or e.get("prompt_snapshot_probe_batches") != 2 for e in installs)):
        raise ValueError("four-worker actual diagnostic activation required")
    graph_installs = [e for e in events if e.get("event") == "graph_candidate_hooks_installed"]
    if (len(graph_installs) != 4 or {e["pid"] for e in graph_installs} != set(workers.values())
            or any(e.get("manifest_sha256") != mh or e.get("profile") != PROFILE for e in graph_installs)):
        raise ValueError("four-worker graph adapter source activation required")
    imported = [e for e in events if e.get("event") == "graph_native_worker_import_verified"]
    if (len(imported) != 4 or {e["pid"] for e in imported} != set(workers.values())
            or any(e.get("manifest_sha256") != mh or e.get("graph_profile") != PROFILE
                   or e.get("native_source_sha256") != NATIVE_RUNNER_SHA256
                   or e.get("original_importer_executed") is not True
                   or e.get("native_dummy_metadata_policy_verified") is not True for e in imported)):
        raise ValueError("four-worker real official importer/source identity required")
    models = [e for e in events if e.get("event") == "compact_model_rows_completed"]
    if any(e.get("c2_snapshot_scope_owner") != "graph_candidate.prefill_bridge"
           or e.get("inner_helper_c2_snapshot") is not False for e in models):
        raise ValueError("real outer snapshot scope provenance required")
    acceptance = contract.get("c2_snapshot_acceptance", {})
    if acceptance.get("enabled") is not True or acceptance.get("group_source") != "verified-native-full-attention-spec":
        raise ValueError("frozen real C2 snapshot inventory required")
    runtime_ids = {e["request_id"] for e in events if e.get("event") == "compact_gdn_body_composed"
                   and any(e.get("request_id", "").startswith(api+"-") for api in private_ids)}
    report.update(hot=hot, probe=audit_probe_rows(events, workers, mh, runtime_ids),
        partition=audit_partition_rows(events, workers, mh),
        lazy_snapshot=audit_lazy(events, workers, mh),
        metadata_snapshot=audit_metadata_receipts(events, workers, mh),
        c2_finite=audit_finite_receipts(events, workers, mh),
        c2_snapshot=audit_c2_snapshot(events, workers, mh, enabled=True,
            expected_group=None, expected_layers=acceptance.get("layers", ())),
        physical=audit_physical_workers(samples, workers, owned_cid=start["container_id"]),
        source_bindings=len(sources))
    return report


# Source-owned default format: logger.py22-26 + formatter.py; executor derives
# TP rank before system_utils.decorate_logs prefixes this namespace PID.
OFFICIAL_LOG_SOURCES = {
    "vllm/distributed/parallel_state.py": "df02e5386bc83e6ac644ff46f0297fdd19003bd55584c629840348a5fda8473f",
    "vllm_ascend/compilation/acl_graph.py": "27f3b838f223dec86113649625f65b158969a30ce0265271d6a3ce1403db2491",
    "vllm/v1/executor/multiproc_executor.py": "a2837f18010a1f3539ea062b0824ae6dacaced0ec5813910a4b6edef7875af18",
    "vllm/utils/system_utils.py": "26127b114d896f776da2d5ba90eac5a023704150f07b1703eb66252bedf7eaa6",
    "vllm/logger.py": "233720900b1207434e4824bbddcf86dba0dc8557a0bfe78a639545462a9e85b5",
    "vllm/logging_utils/formatter.py": "d8caa69bf25884f6d4f59ca1b3c27e1162f7ab775874b236afc32e0696d5fe7c",
    "vllm/forward_context.py": "1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5",
}
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PREFIX = r"\(Worker_TP([0-3]) pid=([1-9][0-9]*)\) "
_TIME = r"[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}"
_CAPTURE = re.compile(_PREFIX + r"DEBUG " + _TIME +
    r" \[acl_graph\.py:164\] Capturing a aclgraph on \(FULL,BatchDescriptor\("
    r"num_tokens=([1-9][0-9]*), num_reqs=([1-9][0-9]*), uniform=True, "
    r"has_lora=False, num_active_loras=0\)\)")
_REPLAY = re.compile(_PREFIX + r"INFO " + _TIME +
                     r" \[acl_graph\.py:243\] Replaying aclgraph")
_WORKER = re.compile(_PREFIX)


def audit_official_graph_log(log_bytes, *, samples, owned_cid, expected_workers=None):
    """Exact pinned official messages + successful terminal (checked by caller).

    Both messages precede their operation. Capture DEBUG is per worker, but
    info_once defaults to scope="local": logger.py96-105/127-134 calls
    parallel_state.is_local_first_rank(), whose initialized world condition is
    _WORLD.local_rank == 0 (parallel_state.py2224-2232). In this single-node
    TP4/PP1/DP1 canary only TP0 replay is directly observed. No per-token or
    four-rank completed replay-call count is inferred.
    Candidate self-report events are deliberately not consumed.
    """
    if type(log_bytes) is not bytes:
        raise ValueError("original official service.log bytes required")
    captures, replays, pids, diagnostic_lines = {}, {}, {}, []
    for number, raw_line in enumerate(log_bytes.decode("utf-8").splitlines(), 1):
        line = _ANSI.sub("", raw_line)
        owner = _WORKER.match(line)
        if owner and ("Traceback (most recent call last):" in line
                      or re.search(r" (ERROR|CRITICAL) " + _TIME + r" \[", line)):
            # Ordinary worker diagnostics do not override the independently
            # checked terminal/request result or become a generic new gate.
            diagnostic_lines.append(number)
        capture, replay = _CAPTURE.fullmatch(line), _REPLAY.fullmatch(line)
        matched = capture or replay
        if matched is None:
            continue
        rank, pid = int(matched[1]), int(matched[2])
        if rank in pids and pids[rank] != pid:
            raise ValueError("official graph worker PID changed")
        pids[rank] = pid
        if capture:
            size, reqs = int(capture[3]), int(capture[4])
            if size not in CAPTURE_SIZES or size != reqs:
                raise ValueError("official capture descriptor outside frozen pure-decode profile")
            captures.setdefault(rank, []).append((number, size))
        else:
            replays.setdefault(rank, []).append(number)
    if (set(pids) != set(range(4)) or set(captures) != set(range(4))
            or 0 not in replays
            or min(replays[0]) <= min(x[0] for x in captures[0])):
        raise ValueError("four-rank capture and local-first official replay evidence missing")
    if expected_workers is not None and pids != expected_workers:
        raise ValueError("official log PID/rank differs from actual HYPIC worker receipts")
    physical = audit_physical_workers(samples, pids, owned_cid=owned_cid)
    return {"official_native_graph_path_reached": True,
            "official_format_source_sha256": OFFICIAL_LOG_SOURCES,
            "log_sha256": hashlib.sha256(log_bytes).hexdigest(),
            "worker_pids": pids, "physical": physical,
            "capture_ranks": sorted(captures),
            "replay_directly_observed_ranks": sorted(replays),
            "source_default_local_first_replay_rank": 0,
            "ordinary_worker_diagnostic_lines": diagnostic_lines,
            "per_rank": {r: {"capture_lines": [n for n, size in captures[r]],
                             "capture_sizes_observed": sorted({size for n, size in captures[r]}),
                             "replay_lines": replays.get(r, [])} for r in pids},
            "scope": "four owned ranks reached native FULL capture; local-first TP0 replay directly logged plus successful TP4 requests/terminal; pre-operation logs do not prove four-rank completed replay calls or per-request/token coverage"}


def audit(contract_path, *, graph_evidence=None, live_release=False):
    report = audit_mechanism(contract_path, live_release=live_release)
    contract = _read(Path(contract_path).resolve())
    raw = Path(contract["raw_root"])
    official = raw / "service.log"
    if graph_evidence is not None and (
            not isinstance(graph_evidence, (str, Path))
            or Path(graph_evidence).resolve() != official.resolve()):
        report["graph_evidence_status"] = "UNVERIFIED_NON_SERVICE_LOG_INPUT"
        raise GraphEvidencePending(report)
    if not official.is_file():
        raise GraphEvidencePending(report)
    samples, start = _read(raw / "isolation.json"), _read(raw / "service-start.json")
    graph = audit_official_graph_log(_read(official, json_value=False),
        samples=samples, owned_cid=start["container_id"],
        expected_workers=report["hot"]["worker_pids"] if report["hot"] else None)
    report.update(valid=True, bounded_graph_canary_valid=True,
                  graph_execution_verified=True,
                  graph_evidence_status="OFFICIAL_NATIVE_PATH_REACHED_SUCCESSFUL_TERMINAL",
                  graph=graph, physical=graph["physical"],
                  scope="bounded3 responses/two private requests with source/mechanism/physical/isolation/release and official native graph path evidence; not formal speed/fullquality/per-token graph coverage")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--graph-evidence")
    parser.add_argument("--live-release", action="store_true")
    args = parser.parse_args()
    try:
        output = audit(args.contract, graph_evidence=args.graph_evidence, live_release=args.live_release)
    except GraphEvidencePending as error:
        print(json.dumps(error.partial_report))
        raise SystemExit(2)
    print(json.dumps(output))
