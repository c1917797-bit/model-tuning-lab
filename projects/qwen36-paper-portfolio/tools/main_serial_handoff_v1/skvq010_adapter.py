"""Read-only serial handoff adapter for the frozen SKVQ010 controller.

Reuses its exact Control.validate, protected boundary, H8 idle and RAM/CPU
admission functions. No stop/create/exec command, numerical reader or retry.
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from serial_batch import checked, obj, reference, need, publish, SELF_RSS, source_gate

PROFILE_ROOT = Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-010")
OWNER = "skvq-current72h-preprojection-v1-010"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"


def load_host(ticket):
    need(ticket["owner"] == OWNER and ticket["image"] == IMAGE and
         Path(ticket["source_ref"]["path"]) == PROFILE_ROOT / "SOURCE_MANIFEST.json" and
         Path(ticket["entry_ref"]["path"]) == PROFILE_ROOT / "MAIN_HOST.py", "only reviewed SKVQ010 profile, never guessed other owner")
    checked(ticket["source_ref"])
    checked(ticket["entry_ref"])
    # Fresh adapter interpreter: no shared controller globals or configure reset.
    sys.path.insert(0, str(PROFILE_ROOT))
    spec = importlib.util.spec_from_file_location("_main_serial_skvq010_host", ticket["entry_ref"]["path"])
    need(spec is not None and spec.loader is not None, "source-qualified original host module")
    host = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = host
    spec.loader.exec_module(host)
    source = host.C.configure(ticket["source_ref"]["sha256"])
    need(source == ticket["source_ref"] and host.OWNER == OWNER and host.IMAGE == IMAGE and
         host.HERE == PROFILE_ROOT and host.TOTAL == 7200 and host.CLEANUP == 180 and
         host.DEADLINE == ticket["cutoff_epoch"], "exact original source/clock/budget")
    own = {row["path"]: row for row in obj(source)["files"]}
    for module, name in ((host.C, "current_contract.py"), (host.R, "resources.py"),
                         (host.M, "mount_preflight.py"), (host.D, "input_dependency.py")):
        need(Path(module.__file__) == PROFILE_ROOT / name and reference(module.__file__) == own[str(PROFILE_ROOT / name)],
             "actual loaded module closure, no ambient substitutions")
    expected = ["/usr/bin/env", "MAIN_SKVQ_HOST_ENABLE=1", "/usr/bin/prlimit", "--cpu=7200:7200", "--",
                "/usr/bin/python3", "-B", str(PROFILE_ROOT / "MAIN_HOST.py"), "--execute",
                "--source-manifest-sha256", source["sha256"], "--output", ticket["output_root"]]
    need(ticket["argv"] == expected and ticket["wall_seconds"] == 7200 and ticket["result_name"] == "HOST_RESULT.json",
         "unmodified original full capture host argv, no CPU-only ticket promotion")
    return host


def command(argv, output, label):
    need(argv[:2] == ["/usr/bin/docker", "inspect"] or argv == ["/usr/local/sbin/npu-smi", "info"], "only readonly inspect/SMI")
    if argv[0] == "/usr/bin/docker":
        need(len(argv) == 3 and len(argv[2]) == 64 and all(c in "0123456789abcdef" for c in argv[2]), "exact full owned CID only")
        wrapped = ["/usr/bin/prlimit", "--as=unlimited", "--"] + argv
    else:
        wrapped = argv
    result = subprocess.run(wrapped, capture_output=True, text=True, timeout=30)
    value = {"argv": argv, "actual_wrapped_argv": wrapped, "exit_code": result.returncode,
             "stdout": result.stdout, "stderr": result.stderr, "observed_epoch": time.time()}
    raw = publish(output.parent / (output.name + "." + label + ".json"), value)
    need(result.returncode == 0, "read-only original command failed, preserved " + str(raw))
    return value, raw


def idle(host, output, baseline=None, owned=None, original_host_pid=None):
    raw, ref = command(["/usr/local/sbin/npu-smi", "info"], output, "SMI")
    helper = host.R.helper().frozen()
    for card in (4, 5, 6, 7):
        helper.idle_one(raw["stdout"], card)  # Original process + physical3GiB reserve gate.
    current = helper.protected(raw["stdout"])
    boundary = None
    if baseline is not None:
        boundary = host.C.protected_module().protected_boundary(
            baseline, current, [row["cid"] for row in owned], [original_host_pid])
    return ref, current, boundary


def check_owned(host, original, output):
    owned = original["owned"]
    need(type(owned) is list and len(owned) <= 3 and len({row["cid"] for row in owned}) == len(owned), "complete unique original owned cohort")
    need([row["phase"] for row in owned] in ([], ["preflight"], ["preflight", "tp4-capture"],
         ["preflight", "tp4-capture", "independent-consumer"]), "original phase prefix, no omitted/interleaved owner")
    records = []
    control = object.__new__(host.Control)  # Call its pure validator; never constructor/cleanup.
    for index, row in enumerate(owned):
        need(row["source"] == original["source_lock"]["sha256"] and row.get("released") is True, "original owner source + release latch")
        phase_memory = {"preflight": 8 * 2 ** 30, "tp4-capture": 64 * 2 ** 30, "independent-consumer": 2 * 2 ** 30}
        need(row["mem"] == phase_memory[row["phase"]] and row["npu"] is (row["phase"] == "tp4-capture") and
             row["devices"] == host.Control.devices(None, row["npu"]), "original fixed phase memory and Devices[]/all4 scope")
        saved = obj(row["release_ref"])
        need(saved["cid"] == row["cid"] and saved["released"] is True and saved["retained"] is True and
             saved["deleted"] is False and not saved.get("secondary"), "actual own-only original release receipt")
        stop = obj(saved["stop"])
        need(stop["argv"] == ["/usr/bin/docker", "stop", "--time", "15", row["cid"]] and stop["exit_code"] == 0,
             "original exact own stop, no new stop authorization")
        need(stop["actual_wrapped_argv"] == ["/usr/bin/prlimit", "--as=unlimited", "--"] + stop["argv"], "original Docker-only AS wrapper")
        inspect_original = obj(saved["inspect"])
        need(inspect_original["argv"] == ["/usr/bin/docker", "inspect", row["cid"]] and inspect_original["exit_code"] == 0,
             "original inspect provenance")
        need(inspect_original["actual_wrapped_argv"] == ["/usr/bin/prlimit", "--as=unlimited", "--"] + inspect_original["argv"], "original inspect wrapper")
        # JSON converts original tuples to lists; project only this documented wire field.
        need(type(row["mounts"]) is dict and all(type(k) is str and type(v) is list and len(v) == 2 and
             type(v[0]) is str and type(v[1]) is bool for k, v in row["mounts"].items()), "exact serialized mount pairs")
        expected = dict(row, mounts={k: (v[0], v[1]) for k, v in row["mounts"].items()})
        for value in (inspect_original,):
            xs = json.loads(value["stdout"])
            need(len(xs) == 1, "single original owned inspect")
            host.Control.validate(control, xs[0], expected)
            state = xs[0]["State"]
            need(state["Running"] is False and state["Pid"] == 0 and not xs[0].get("ExecIDs"), "original stopped/Pid0/noExec")
        fresh, fresh_ref = command(["/usr/bin/docker", "inspect", row["cid"]], output, "INSPECT-%d" % index)
        xs = json.loads(fresh["stdout"])
        need(len(xs) == 1, "one fresh exact owned inspect")
        host.Control.validate(control, xs[0], expected)
        state = xs[0]["State"]
        need(state["Running"] is False and state["Pid"] == 0 and not xs[0].get("ExecIDs"), "fresh stopped/Pid0/noExec; no live owner handoff")
        records.append({"cid": row["cid"], "original_release_ref": row["release_ref"], "fresh_inspect_ref": fresh_ref,
                        "OOMKilled": state["OOMKilled"]})
    return records


def actual_aw_terminal(value, argv):
    """Original registry envelope only; no disk-result reconstruction or retry."""
    need(value["schema"] == "agentweb.operation/v1" and value["terminal"] is True and value["status"] == "completed",
         "real completed AW original, not lost handle/running")
    operation = value["operation"]
    need(operation["ok"] is True and operation["result"]["state"] == "completed" and
         operation["routeDecision"] == "peer_direct" and operation["targetPeerId"] == "lgw_a6109c51076a4a2c9d2674ca5a8704a0",
         "actual ma direct execution transport original")
    record = operation["result"]["record"]
    need(record["state"] == "completed" and [record["command"]] + record["args"] == argv and type(record["exitCode"]) is int and
         record["exitCode"] in (0, 1) and record.get("timedOut") is False and record.get("cancelled") is False,
         "exact completed original argv/exit; no timeout/cancel/unknown")
    if record["exitCode"] == 0:
        need(value["succeeded"] is True and value["error"] is None and record.get("error") is None, "actual successful original")
    else:
        need(value["succeeded"] is False and value["error"] == "exit code" and record.get("error") in (None, "exit code"),
             "actual exit1 failure terminal retained, not transport failure")
    return record


def released_original(host, ticket, original, result_ref, output):
    need(original["schema"] == "SKVQ_HOST_CAPTURE_RESULT_V1" and original["source_lock"] == ticket["source_ref"] and
         original["max_total_seconds"] == 7200 and original["cleanup_included_seconds"] == 180 and
         original["cpu_input_only"] is False and type(original["host_pid"]) is int and original["host_pid"] > 1,
         "entire original exact host source/PID/stage budget")
    need(original["status"] in ("FAILED", "FULL_NATIVE_BASELINE_CAPTURE_CONSUMED_NOT_CALIBRATED"), "known actual terminal status")
    need(not Path("/proc/%d" % original["host_pid"]).exists(), "original host absent; PID reuse requires recovery")
    records = check_owned(host, original, output)
    smi, protected, boundary = idle(host, output, original["protected0_3"], original["owned"], original["host_pid"])
    need(reference(result_ref["path"]) == result_ref, "original terminal unchanged after fresh independent observations")
    return {"schema": "main.serial-exact-owned-release/v1", "source_ref": ticket["source_ref"], "owner": OWNER,
            "original_result_ref": result_ref, "owned": records, "exact_owned_release": True,
            "physical_idle": [4, 5, 6, 7], "smi_ref": smi, "protected_boundary": boundary,
            "external_stopped": False, "original_failed": original["status"] == "FAILED" or
            original["primary"] is not None or bool(original["secondary"]),
            "first_fault": original["primary"], "secondary": original["secondary"],
            "AW_terminal_claimed": False, "numeric_or_performance_pass_claimed": False}


def run(ticket, action, ticket_ref, terminal_ref, output):
    host = load_host(ticket)
    need(os.name == "posix", "actual Linux host, not a local fixture")
    if action == "prepare":
        need(not Path(ticket["output_root"]).exists(), "new stage cannot retry existing output")
        # Extra wrapper RAM is admitted in addition to unchanged original host512MiB/reserve8GiB.
        resource = host.R.fresh(64 * 2 ** 30 + SELF_RSS, Path(ticket["output_root"]).parent)
        need(resource["disk_available_bytes"] >= 320 * 2 ** 30, "unchanged full capture disk320GiB")
        os.sched_setaffinity(0, {resource["allocation"]["host_cpu"]})
        # The batch and stage share this single host slot; the batch waits, never reserves an eighth CPU.
        need(os.getppid() > 1, "actual batch parent")
        os.sched_setaffinity(os.getppid(), {resource["allocation"]["host_cpu"]})
        smi, protected, boundary = idle(host, output)
        rr = publish(output.with_name(output.name + ".RESOURCES.json"), resource)
        value = {"schema": "main.serial-fresh-readonly/v1", "source_ref": ticket["source_ref"], "owner": OWNER,
                 "ticket_ref": ticket_ref, "physical_idle": [4, 5, 6, 7], "smi_ref": smi,
                 "protected_snapshot": protected, "resource_ref": rr, "ordinary_batch_overhead_bytes": SELF_RSS,
                 "original_host_admission_unchanged": True, "device_created": False}
    else:
        need(action == "release" and terminal_ref is not None, "exact release action")
        terminal = obj(terminal_ref)
        need(terminal["schema"] == "main.serial-child-terminal/v1" and terminal["reaped"] is True and
             terminal["source_ref"] == ticket["source_ref"] and terminal["argv"] == ticket["argv"] and
             terminal["AW_terminal_claimed"] is False, "real exact waited child, not AW-registry inference")
        need(type(terminal["pid"]) is int and terminal["pid"] > 1 and not Path("/proc/%d" % terminal["pid"]).exists(),
             "original host absent; a reused PID requires independent recovery, not ignored")
        result_ref = reference(Path(ticket["output_root"]) / ticket["result_name"])
        original = obj(result_ref)
        need(original["host_pid"] == terminal["pid"], "source-bound waited host PID")
        value = released_original(host, ticket, original, result_ref, output)
        value["child_terminal_ref"] = terminal_ref
    publish(output, value)
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--action", choices=("prepare", "release"))
    p.add_argument("--ticket")
    p.add_argument("--ticket-sha256")
    p.add_argument("--terminal")
    p.add_argument("--terminal-sha256")
    p.add_argument("--output")
    p.add_argument("--original-aw")
    p.add_argument("--original-aw-sha256")
    p.add_argument("--existing-root")
    p.add_argument("--source-manifest-sha256")
    p.add_argument("--batch-source-manifest-sha256")
    a = p.parse_args()
    if not a.execute:
        print(json.dumps({"default_enabled": False, "readonly": True}))
        return
    source_gate(Path(__file__).resolve().parent / "SOURCE_MANIFEST.json", a.batch_source_manifest_sha256)
    if a.original_aw:
        # Standalone read-only audit of an already terminal stage, never adopt/relaunch it.
        source_ref = reference(PROFILE_ROOT / "SOURCE_MANIFEST.json")
        need(source_ref["sha256"] == a.source_manifest_sha256, "exact original producer source")
        ticket = {"owner": OWNER, "image": IMAGE, "source_ref": source_ref,
                  "entry_ref": reference(PROFILE_ROOT / "MAIN_HOST.py"), "output_root": a.existing_root,
                  "wall_seconds": 7200, "cutoff_epoch": 1791788425, "result_name": "HOST_RESULT.json"}
        ticket["argv"] = ["/usr/bin/env", "MAIN_SKVQ_HOST_ENABLE=1", "/usr/bin/prlimit", "--cpu=7200:7200", "--",
                          "/usr/bin/python3", "-B", str(PROFILE_ROOT / "MAIN_HOST.py"), "--execute",
                          "--source-manifest-sha256", source_ref["sha256"], "--output", a.existing_root]
        original_ref = reference(a.original_aw)
        need(original_ref["sha256"] == a.original_aw_sha256, "actual original AW Ref")
        record = actual_aw_terminal(obj(original_ref), ticket["argv"])
        host = load_host(ticket)
        result_ref = reference(Path(a.existing_root) / "HOST_RESULT.json")
        original = obj(result_ref)
        need((record["exitCode"] == 1) == (original["status"] == "FAILED"), "actual AW exit bound to original host outcome")
        marker = json.loads(record["stdout"].strip())
        need(type(marker) is dict and set(marker) == {"host_result", "status"} and
             marker["host_result"] == result_ref and marker["status"] == original["status"], "original AW stdout actual immutable HOST_RESULT binding")
        value = released_original(host, ticket, original, result_ref, Path(a.output))
        value.update(original_aw_ref=original_ref, original_operation_verified=True, new_stage_admitted=False,
                     numeric_or_performance_pass_claimed=False)
        publish(a.output, value)
        print(json.dumps(value, sort_keys=True))
        return
    tr = reference(a.ticket)
    need(tr["sha256"] == a.ticket_sha256, "exact batch ticket")
    rr = reference(a.terminal) if a.terminal else None
    need(rr is None or rr["sha256"] == a.terminal_sha256, "exact actual child terminal")
    print(json.dumps(run(obj(tr), a.action, tr, rr, Path(a.output)), sort_keys=True))


if __name__ == "__main__":
    main()
