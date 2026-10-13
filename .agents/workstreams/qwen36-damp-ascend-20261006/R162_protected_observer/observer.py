"""Bounded protected-card process observation. No resource or numerical grant.
For a PID listed by npu-smi that has exited before /proc inspection, retain
raw evidence and confirm absence in two proc frames plus a fresh SMI sample.
Never retire a live/unreadable/reused PID or our known PID. No signaling.
"""
import hashlib, os, time
from pathlib import Path

class ObservationError(RuntimeError):
    pass

def need(value, message):
    if not value:
        raise ObservationError(message)

def stat_fields(text, pid):
    end = text.rfind(")")
    fields = text[end + 2:].split()
    need(end > text.find("(") >= 1 and int(text[:text.find("(")].strip()) == pid
         and len(fields) >= 20 and fields[19].isdigit(), "malformed actual proc stat")
    return dict(start_ticks=int(fields[19]), state=fields[0])

def snapshot(pid, root=Path("/proc")):
    reads = {}
    for key, filename in (("stat_before", "stat"), ("cgroup", "cgroup"),
                          ("cmdline", "cmdline"), ("stat_after", "stat")):
        try:
            raw = (root / str(pid) / filename).read_bytes()
            reads[key] = dict(status="ok", hex=raw.hex()) if key == "cmdline" else dict(status="ok", text=raw.decode())
        except (FileNotFoundError, ProcessLookupError) as e:
            reads[key] = dict(status="missing", errno=e.errno, operation="read", path=str(root / str(pid) / filename))
        except OSError as e:
            reads[key] = dict(status="error", errno=e.errno, operation="read", path=str(root / str(pid) / filename), error=repr(e))
    return dict(pid=pid, observed_ns=time.time_ns(), reads=reads)

def frames(s):
    need(set(s["reads"]) == {"stat_before", "stat_after", "cgroup", "cmdline"}, "complete proc snapshot")
    need(all(r["status"] in ("ok", "missing") for r in s["reads"].values()), "live unreadable/permission failure")
    return [stat_fields(s["reads"][k]["text"], s["pid"]) for k in ("stat_before", "stat_after")
            if s["reads"][k]["status"] == "ok"]

def observe(rows, read_snapshot, fresh_smi, parse_rows, publish, *, owned_pids=(), owned_cids=()):
    """Return only proven live identities; separately publish expired SMI rows."""
    need(len(rows) <= 4096 and len(set(rows)) == len(rows), "bounded unique protected rows")
    need(all(n in (0, 1, 2, 3) and chip == 0 and type(pid) is int and pid > 1 for n, chip, pid in rows),
         "protected scope only")
    proof, events = [], []
    try:
        for physical, chip, pid in rows:
            need(pid not in owned_pids, "owned PID on protected card")
            a = read_snapshot(pid)
            fa = frames(a)
            for r in a["reads"].values():
                if r["status"] == "ok" and "text" in r:
                    need(not any(cid in r["text"] for cid in owned_cids), "owned CID on protected card")
            if all(r["status"] == "ok" for r in a["reads"].values()):
                need(len(fa) == 2 and fa[0]["start_ticks"] == fa[1]["start_ticks"]
                     and all(f["state"] != "Z" for f in fa), "live identity changed or zombie")
                cg = a["reads"]["cgroup"]["text"]
                need(cg, "live empty cgroup")
                proof.append(dict(physical=physical, chip=chip, pid=pid,
                    start_ticks=fa[0]["start_ticks"], cgroup=cg,
                    cmdline_sha256=hashlib.sha256(bytes.fromhex(a["reads"]["cmdline"]["hex"])).hexdigest()))
                continue
            b = read_snapshot(pid)
            fb = frames(b)
            need(not fb and all(r["status"] == "missing" for r in b["reads"].values()),
                 "partial read is not proven departure")
            raw = fresh_smi()
            need(raw["exit_code"] == 0, "fresh SMI failed")
            current = parse_rows(raw["stdout"])
            need(not any(p == pid for _, _, p in current), "expired PID still listed by fresh SMI")
            c = read_snapshot(pid)
            fc = frames(c)
            need(not fc and all(r["status"] == "missing" for r in c["reads"].values()), "PID reused or alive after SMI")
            need(len({f["start_ticks"] for f in fa}) <= 1, "PID reuse during first snapshot")
            events.append(dict(physical=physical, chip=chip, pid=pid,
                classification="expired_smi_row_confirmed_absent_not_zero_rss",
                initial_identity_known=bool(fa), before=a, absent_before=b, fresh_smi=raw, absent_after=c,
                numerical_authority=False, resource_authority=False))
    except BaseException as e:
        publish(dict(schema="ascend.protected-process-observation/v1", events=events,
                     live=proof, primary=repr(e), current_pid=locals().get("pid"),
                     current_snapshot=locals().get("a"), failed=True))
        raise
    if events:
        publish(dict(schema="ascend.protected-process-observation/v1", events=events,
                     live=proof, primary=None, failed=False))
    return sorted(proof, key=lambda x: (x["physical"], x["chip"], x["pid"]))

def install(H, helper_ref, output, write, owned):
    """Modify one private loaded helper only, never shared source/runtime."""
    F = H.frozen()
    p = Path(F.__file__)
    raw = p.read_bytes()
    need(str(p) == helper_ref["path"] and len(raw) == helper_ref["bytes"] and
         hashlib.sha256(raw).hexdigest() == helper_ref["sha256"], "exact helper source")
    old = F.protected
    need(old.__globals__ is F.__dict__ and old.__code__.co_filename == str(p), "actual original protected function")
    def protected(text):
        pids, cids = owned()
        return observe([r for r in F.legacy().process_rows(text) if r[0] in (0, 1, 2, 3)],
                       snapshot, lambda: F.run([F.SMI, "info"], timeout=3),
                       F.legacy().process_rows,
                       lambda value: write(Path(output) / ("protected-lifetime-" + str(time.time_ns()) + ".json"), value),
                       owned_pids=tuple(set(pids) | {os.getpid()}), owned_cids=cids)
    F.protected = protected
    need(H.frozen() is F, "actual reused private helper")
    return dict(original=helper_ref, adapter_path=__file__, changes=["private protected observer only"],
                resources_unchanged=True, model_ready=False, performance_ready=False)

