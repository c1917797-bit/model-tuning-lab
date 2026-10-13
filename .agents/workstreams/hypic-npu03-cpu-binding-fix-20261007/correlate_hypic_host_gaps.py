#!/usr/bin/env python3
"""Read-only temporal association of retained HYPIC gaps and host trace events."""
import collections
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from analyze_hypic_profile_timeline import ROOTS, BASE, merge, ns

def correlate(gap, events):
    start, end = gap
    if end <= start:
        raise ValueError("gap must be positive")
    labels = {}
    for event in events:
        if event.get("ph") == "M" and event.get("name") == "process_name":
            pid, label = event["pid"], event.get("args", {}).get("name")
            if pid in labels and labels[pid] != label:
                raise ValueError("ambiguous trace process label")
            labels[pid] = label
    if not {"Python", "CANN"}.issubset(set(labels.values())):
        raise ValueError("required host lanes absent")
    clips, top, counts = [], [], collections.Counter()
    for index, event in enumerate(events):
        label = labels.get(event.get("pid"))
        if label not in {"Python", "CANN"} or event.get("ph") != "X":
            continue
        a = ns(event["ts"])
        b = a + ns(event["dur"])
        left, right = max(start, a), min(end, b)
        if right <= left:
            continue
        clips.append((left, right))
        counts[label] += 1
        top.append({"index": index, "name": event.get("name"), "lane": label,
                    "pid": event.get("pid"), "tid": event.get("tid"),
                    "start_ns": str(a), "end_ns": str(b),
                    "overlap_ns": right-left})
    union = sum(b-a for a,b in merge(clips))
    return {"gap_start_ns": str(start), "gap_end_ns": str(end),
            "gap_ms": (end-start)/1e6, "host_union_ms": union/1e6,
            "no_exported_host_event_ms": (end-start-union)/1e6,
            "host_event_counts": dict(counts),
            "top_host_events": sorted(top, key=lambda x:x["overlap_ns"], reverse=True)[:5],
            "causality_proven": False, "cpu_numa_attribution_proven": False}

def main():
    reference_path = BASE / "profile-timeline-analysis-20261013.json"
    reference_bytes = reference_path.read_bytes()
    assert hashlib.sha256(reference_bytes).hexdigest() == "90385d77afe877b66758529d9272d0674b7d89d3798349577fd19b96b372bddd"
    reference = json.loads(reference_bytes)
    results = []
    for phase, root in ROOTS.items():
        directories = sorted(root.glob("rank*_ascend_pt"))
        assert len(directories) == 4
        for rank, directory in enumerate(directories):
            out = directory / "ASCEND_PROFILER_OUTPUT"
            kernel_path, trace_path = out / "kernel_details.csv", out / "trace_view.json"
            kernel_hash = hashlib.sha256(kernel_path.read_bytes()).hexdigest()
            prior = reference["phases"][phase]["ranks"][rank]
            assert str(directory) == prior["directory"]
            assert kernel_hash == prior["inputs"]["kernel_details.csv"]["sha256"]
            with kernel_path.open(newline="") as stream:
                intervals = merge([(ns(r["Start Time(us)"]),
                    ns(r["Start Time(us)"])+ns(r["Duration(us)"]))
                    for r in csv.DictReader(stream)])
            gap = max(((a[1],b[0]) for a,b in zip(intervals,intervals[1:])),
                      key=lambda pair: pair[1]-pair[0])
            assert abs((gap[1]-gap[0])/1e6-prior["largest_no_exported_kernel_gap_ms"]) < 1e-9
            raw = trace_path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            obj = json.loads(raw, parse_float=Decimal)
            del raw
            events = obj if isinstance(obj,list) else obj["traceEvents"]
            result = correlate(gap, events)
            result.update(phase=phase, rank=rank, trace_path=str(trace_path),
                          trace_sha256=digest, kernel_sha256=kernel_hash)
            results.append(result)
            del obj, events
    print(json.dumps({"schema":"hypic-host-gap-association/v1",
        "source_commit":"c12060cd47e7575ead059983d7a8bb4704165c98",
        "scope":"largest exported-kernel gap per rank; temporal association only",
        "new_device_work":False, "rows":results}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
