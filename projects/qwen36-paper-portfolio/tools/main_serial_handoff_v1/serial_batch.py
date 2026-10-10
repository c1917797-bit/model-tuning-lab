"""DEFAULT OFF, finite MAIN-reviewed stage handoff; not an experiment controller.

Each subprocess retains its own frozen admission/monitor/cleanup implementation.
This file never stops a container, retries a stage, or manufactures AW terminals.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

MAX_STAGES = 8
MAX_JSON = 2 ** 20
SELF_RSS = 64 * 2 ** 20


def need(value, message):
    if not value:
        raise ValueError(message)


def reference(path):
    p = Path(path)
    need(p.is_absolute() and ".." not in p.parts, "absolute component-safe path")
    for q in (p,) + tuple(p.parents):
        need(not q.is_symlink(), "no symlink in evidence/source path")
    before = p.stat()
    need(stat.S_ISREG(before.st_mode) and before.st_size > 0, "nonempty regular artifact")
    digest = hashlib.sha256()
    with p.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        need((opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino), "artifact replaced before open")
        for part in iter(lambda: handle.read(2 ** 20), b""):
            digest.update(part)
    after = p.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "artifact changed while hashing")
    return {"path": str(p), "bytes": before.st_size, "sha256": digest.hexdigest()}


def checked(value):
    need(type(value) is dict and set(value) == {"path", "bytes", "sha256"} and
         type(value["bytes"]) is int and value["bytes"] > 0 and
         type(value["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", value["sha256"]), "strict three-field Ref")
    need(reference(value["path"]) == value, "entire artifact size/SHA binding")
    return value


def obj(value):
    checked(value)
    need(value["bytes"] <= MAX_JSON, "bounded JSON receipt")
    return json.loads(Path(value["path"]).read_bytes())


def publish(path, value):
    p = Path(path)
    need(not p.exists() and not p.is_symlink(), "never overwrite evidence")
    data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    need(len(data) <= MAX_JSON, "bounded batch receipt")
    temporary = p.with_name(p.name + ".pending-" + str(os.getpid()))
    with temporary.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(str(temporary), str(p))
    if os.name != "nt":
        fd = os.open(str(p.parent), os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    temporary.unlink()  # Only this successful publication's temporary alias.
    return reference(p)


def source_gate(path, expected):
    source_ref = reference(path)
    need(source_ref["sha256"] == expected, "exact reviewed batch source")
    lock = obj(source_ref)
    need(lock["schema"] == "main.finite-serial-handoff-source/v1" and lock["default_enabled"] is False, "source packet not experiment authority")
    names = set()
    for row in lock["files"]:
        need(Path(row["name"]).name == row["name"] and row["name"] not in names, "unique relative own filename")
        names.add(row["name"])
        checked({"path": str(Path(path).parent / row["name"]), "bytes": row["bytes"], "sha256": row["sha256"]})
    need({"serial_batch.py", "skvq010_adapter.py", "test_serial_batch.py"} == names, "complete three-file reviewed packet")
    return source_ref


def validate_ticket(ticket):
    need(type(ticket) is dict and set(ticket) == {
        "id", "source_ref", "entry_ref", "argv", "output_root", "result_name", "owner",
        "image", "physical", "protected", "wall_seconds", "cutoff_epoch", "review_ref", "adapter_ref"
    }, "complete reviewed stage ticket; no implicit defaults")
    need(type(ticket["id"]) is str and re.fullmatch("[A-Za-z0-9_-]{1,64}", ticket["id"]), "bounded stage identifier")
    for key in ("source_ref", "entry_ref", "adapter_ref"):
        checked(ticket[key])
    review = obj(ticket["review_ref"])
    need(review["schema"] == "main.reviewed-stage-admission/v1" and review["reviewed_by"] == "MAIN" and
         review["ready_for_gate"] is True and review["state"] == "ACTUAL_PREREQUISITES_CONSUMED" and
         review["gate"] in ("image-preflight", "npu-numerical", "model-screen", "formal-pair", "final-tasks") and
         review["ticket_id"] == ticket["id"] and review["source_ref"] == ticket["source_ref"] and
         review["entry_ref"] == ticket["entry_ref"] and review["adapter_ref"] == ticket["adapter_ref"] and
         review["argv"] == ticket["argv"] and review["output_root"] == ticket["output_root"] and
         review["owner"] == ticket["owner"] and review["missing"] == [],
         "MAIN review for this exact gate, not a software-prepared boolean")
    need(review["stage_policy"] == {key: ticket[key] for key in
         ("image", "physical", "protected", "wall_seconds", "cutoff_epoch", "result_name")},
         "review binds unchanged stage budget/clock/isolation/result path")
    need(type(review["actual_prerequisites"]) is list and 0 < len(review["actual_prerequisites"]) <= 64,
         "actual independently consumed gate predecessors")
    for row in review["actual_prerequisites"]:
        need(type(row) is dict and set(row) == {"artifact_ref", "consumer_ref", "acceptance_ref"}, "original and actual consumer predecessor")
        for ref in row.values():
            checked(ref)
    argv = ticket["argv"]
    need(type(argv) is list and argv and all(type(v) is str and v and "\x00" not in v for v in argv), "exact non-shell argv")
    need(Path(argv[0]).is_absolute() and ticket["entry_ref"]["path"] in argv and
         ticket["source_ref"]["sha256"] in argv, "explicit actual source-bound executable entry")
    need(ticket["physical"] == [4, 5, 6, 7] and ticket["protected"] == [0, 1, 2, 3], "unchanged serial/protected device scope")
    need(type(ticket["wall_seconds"]) is int and 0 < ticket["wall_seconds"] <= 14400 and
         type(ticket["cutoff_epoch"]) is int and ticket["cutoff_epoch"] > 0, "unchanged finite stage including cleanup")
    need(type(ticket["owner"]) is str and ticket["owner"] and re.fullmatch("sha256:[0-9a-f]{64}", ticket["image"]), "exact owner/image")
    output = Path(ticket["output_root"])
    need(output.is_absolute() and ".." not in output.parts and Path(ticket["result_name"]).name == ticket["result_name"], "exact prospective output root/result")
    for q in (output,) + tuple(output.parents):
        need(not q.is_symlink(), "output ancestors not symlinks")
    need(not output.exists(), "fresh stage output; no retry or resume of a failed run")
    return ticket


def validate_plan(plan):
    need(type(plan) is dict and set(plan) == {"schema", "reviewed_by", "stages", "empty_reason", "batch_resources"} and
         plan["schema"] == "main.finite-serial-stage-plan/v1" and plan["reviewed_by"] == "MAIN", "MAIN frozen finite plan")
    stages = plan["stages"]
    need(type(stages) is list and len(stages) <= MAX_STAGES, "finite batch at most eight, never a daemon")
    need(len({s["id"] for s in stages}) == len(stages) and
         len({s["output_root"] for s in stages}) == len(stages), "no duplicate ticket/output or automatic retry")
    need(len({(s["source_ref"]["sha256"], s["entry_ref"]["sha256"], s["owner"]) for s in stages}) == len(stages),
         "no second unchanged owner/entry/source attempt inside a batch")
    resources = plan["batch_resources"]
    need(resources == {"host_cpu_shared": 1, "max_rss_bytes": SELF_RSS,
                       "additional_ordinary_ram_bytes": SELF_RSS,
                       "fresh_ancestor_admission_required": True}, "small batch overhead explicitly jointly admitted")
    need(stages or (type(plan["empty_reason"]) is str and plan["empty_reason"]), "concrete no-ready-stage idle cause")
    return plan


class LocalBackend:
    """Real synchronous process terminals; never an AW operation emulation."""
    def __init__(self, source_ref=None):
        self.source_ref = source_ref

    def now(self):
        return time.time()

    def self_guard(self):
        need(os.name == "posix" and Path("/proc/self/status").is_file(), "actual Linux MAIN host required")
        rows = [line for line in Path("/proc/self/status").read_text().splitlines() if line.startswith("VmRSS:")]
        need(len(rows) == 1 and int(rows[0].split()[1]) * 1024 <= SELF_RSS, "batch actual RSS64MiB")

    def run_adapter(self, ticket, action, ticket_ref, terminal_ref, output):
        need(self.source_ref is not None, "reviewed batch source required by actual adapter")
        source_gate(self.source_ref["path"], self.source_ref["sha256"])
        checked(ticket["adapter_ref"])
        argv = [sys.executable, "-I", "-B", ticket["adapter_ref"]["path"], "--execute",
                "--action", action, "--ticket", ticket_ref["path"], "--ticket-sha256", ticket_ref["sha256"],
                "--output", str(output), "--batch-source-manifest-sha256", self.source_ref["sha256"]]
        if terminal_ref:
            argv += ["--terminal", terminal_ref["path"], "--terminal-sha256", terminal_ref["sha256"]]
        started = time.time_ns()
        # Adapter is a separately reviewed bounded read-only observer, not stop/create.
        p = subprocess.run(argv, capture_output=True, timeout=120)
        raw = publish(output.with_name(output.name + ".CLI.json"), {
            "schema": "main.batch-adapter-child-terminal/v1", "argv": argv, "exit_code": p.returncode,
            "started_ns": started, "finished_ns": time.time_ns(),
            "stdout": p.stdout.decode(errors="replace"), "stderr": p.stderr.decode(errors="replace")})
        need(p.returncode == 0, "read-only adapter failure retained: " + str(raw))
        return obj(reference(output))

    def launch(self, ticket, directory):
        so = directory / "stdout.raw"
        se = directory / "stderr.raw"
        started = time.time_ns()
        with so.open("xb") as stdout, se.open("xb") as stderr:
            child = subprocess.Popen(ticket["argv"], stdout=stdout, stderr=stderr, shell=False)
            proc = Path("/proc") / str(child.pid)
            text = (proc / "stat").read_text()
            start_ticks = int(text[text.rfind(")") + 2:].split()[19])
            launch_ref = publish(directory / "LAUNCH.json", {
                "schema": "main.serial-owned-child-launch/v1", "pid": child.pid, "start_ticks": start_ticks,
                "argv": ticket["argv"], "source_ref": ticket["source_ref"], "started_ns": started})
            try:
                code = child.wait(timeout=ticket["wall_seconds"])
            except subprocess.TimeoutExpired:
                return {"schema": "main.serial-child-unknown/v1", "launch_ref": launch_ref,
                        "pid": child.pid, "start_ticks": start_ticks, "reason": "child not reaped within original stage budget",
                        "stdout_pending_path": str(so), "stderr_pending_path": str(se),
                        "AW_terminal_claimed": False}
        need(not proc.exists(), "PID still present/reused after actual wait; independent recovery required")
        return {"schema": "main.serial-child-terminal/v1", "launch_ref": launch_ref,
                "pid": child.pid, "start_ticks": start_ticks, "argv": ticket["argv"],
                "source_ref": ticket["source_ref"], "exit_code": code, "reaped": True,
                "started_ns": started, "finished_ns": time.time_ns(),
                "stdout_ref": reference(so) if so.stat().st_size else None,
                "stderr_ref": reference(se) if se.stat().st_size else None,
                "empty_stdout": so.stat().st_size == 0, "empty_stderr": se.stat().st_size == 0,
                "AW_terminal_claimed": False}


def execute(plan, root, backend=None):
    validate_plan(plan)
    root = Path(root)
    need(root.is_absolute() and ".." not in root.parts and not root.exists() and not root.is_symlink() and root.parent.is_dir(), "new batch output only")
    for ancestor in root.parents:
        need(not ancestor.is_symlink(), "batch output ancestors not symlinks")
    root.mkdir()
    backend = backend or LocalBackend()
    rows = []
    stop = "NO_READY_TICKET"
    reason = plan["empty_reason"] or "finite frozen queue exhausted"
    for index, ticket in enumerate(plan["stages"]):
        directory = root / ("stage-%02d" % index)
        directory.mkdir()
        row = {"id": ticket["id"], "source_ref": ticket["source_ref"], "state": "PENDING"}
        rows.append(row)
        # Ticket-local preparation failure owns no lease. It cannot starve an independent ready successor.
        try:
            validate_ticket(ticket)
            need(backend.now() + ticket["wall_seconds"] <= ticket["cutoff_epoch"], "complete original stage no longer fits fixed cutoff")
        except Exception as err:
            row.update(state="PREPARATION_MISSING", first_fault=repr(err), stage_launched=False)
            publish(directory / "SKIPPED_REPAIR.json", row)
            continue
        try:
            backend.self_guard()
            ticket_ref = publish(directory / "TICKET.json", ticket)
            prepared = backend.run_adapter(ticket, "prepare", ticket_ref, None, directory / "FRESH.json")
            need(prepared["schema"] == "main.serial-fresh-readonly/v1" and prepared["source_ref"] == ticket["source_ref"] and
                 prepared["owner"] == ticket["owner"] and prepared["physical_idle"] == [4, 5, 6, 7] and
                 prepared["ordinary_batch_overhead_bytes"] == SELF_RSS and prepared["original_host_admission_unchanged"] is True,
                 "fresh source-qualified aggregate admission; no borrowed idle proof")
            row["fresh_ref"] = reference(directory / "FRESH.json")
            # Original stage still performs its own fresh admission, not this adapter alone.
            try:
                validate_ticket(ticket)
                need(backend.now() + ticket["wall_seconds"] <= ticket["cutoff_epoch"], "fresh check spent time: full original stage must still fit")
            except Exception as err:
                row.update(state="PREPARATION_MISSING", first_fault=repr(err), stage_launched=False)
                publish(directory / "SKIPPED_REPAIR.json", row)
                continue
            backend.self_guard()
            row["launch_attempted"] = True
            terminal = backend.launch(ticket, directory)
            row["stage_launched"] = True
            terminal_ref = publish(directory / "CHILD_TERMINAL.json", terminal)
            row["child_terminal_ref"] = terminal_ref
            need(terminal["schema"] == "main.serial-child-terminal/v1" and terminal["reaped"] is True and
                 terminal["AW_terminal_claimed"] is False and terminal["source_ref"] == ticket["source_ref"] and
                 terminal["argv"] == ticket["argv"] and type(terminal["exit_code"]) is int,
                 "actual reaped exact child required; lost AW handle/files are not a terminal")
            original_ref = reference(Path(ticket["output_root"]) / ticket["result_name"])
            row["original_result_ref"] = original_ref  # Before independent post-stage observation.
            released = backend.run_adapter(ticket, "release", ticket_ref, terminal_ref, directory / "RELEASE.json")
            need(released["schema"] == "main.serial-exact-owned-release/v1" and released["source_ref"] == ticket["source_ref"] and
                 released["owner"] == ticket["owner"] and released["child_terminal_ref"] == terminal_ref and
                 released["original_result_ref"] == original_ref and released["exact_owned_release"] is True and
                 released["physical_idle"] == [4, 5, 6, 7] and released["external_stopped"] is False and
                 released["AW_terminal_claimed"] is False, "fresh independent exact-own release before successor")
            row["release_ref"] = reference(directory / "RELEASE.json")
            row["state"] = "REPAIR" if terminal["exit_code"] != 0 or released["original_failed"] else "STAGE_TERMINAL_RELEASED"
            row["numeric_or_performance_pass_claimed"] = False
            publish(directory / "HANDOFF.json", row)
        except Exception as err:
            row.update(state="UNKNOWN_OR_BLOCKED", first_fault=repr(err))
            publish(directory / "FIRST_FAULT.json", row)
            stop, reason = "UNKNOWN_OR_BLOCKED", repr(err)
            break
    else:
        if any(row.get("launch_attempted") for row in rows):
            stop = "FINITE_QUEUE_EXHAUSTED"
        elif rows:
            reason = "all frozen tickets require preparation; exact causes in SKIPPED_REPAIR.json"
    result = {"schema": "main.finite-serial-handoff-result/v1", "state": stop, "idle_reason": reason,
              "stages": rows, "stage_count": len(rows), "automatic_retry": False, "daemon": False,
              "launch_attempt_count": sum(bool(row.get("launch_attempted")) for row in rows),
              "AW_terminal_claimed": False, "numerical_pass_claimed": False,
              "actual_cross_paper_zero_idle_claimed": False}
    publish(root / "RESULT.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--reviewed-plan")
    parser.add_argument("--reviewed-plan-sha256")
    parser.add_argument("--source-manifest")
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--output")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"default_enabled": False, "stage_dispatched": False}))
        return
    need(os.environ.get("MAIN_FINITE_SERIAL_HANDOFF_ENABLE") == "1", "explicit MAIN opt-in")
    source_ref = source_gate(args.source_manifest, args.source_manifest_sha256)
    need(Path(source_ref["path"]).parent == Path(__file__).resolve().parent, "actual running batch entry source root")
    plan_ref = reference(args.reviewed_plan)
    need(plan_ref["sha256"] == args.reviewed_plan_sha256, "exact MAIN-reviewed plan SHA")
    result = execute(obj(plan_ref), args.output, LocalBackend(source_ref))
    print(json.dumps(result, sort_keys=True))
    if result["state"] == "UNKNOWN_OR_BLOCKED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
