#!/usr/bin/env python3
"""Independent sweep-line replay of post-hoc CSV timeline totals."""
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path

RESULT = Path("/cache/cch/hypic-npu03-cpu-binding-fix-20261007/profile-timeline-analysis-20261013.json")
EXPECTED = "90385d77afe877b66758529d9272d0674b7d89d3798349577fd19b96b372bddd"


def main():
    data = RESULT.read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED, "result drift"
    result = json.loads(data)
    ranks_checked = 0
    for phase in result["phases"].values():
        for rank in phase["ranks"]:
            directory = Path(rank["directory"])
            for name, receipt in rank["inputs"].items():
                path = directory / name if name.startswith("profiler_info") else directory / "ASCEND_PROFILER_OUTPUT" / name
                assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"], path
            events = {}
            count = 0
            with (directory / "ASCEND_PROFILER_OUTPUT/kernel_details.csv").open(newline="") as stream:
                for row in csv.DictReader(stream):
                    start = int(Decimal(row["Start Time(us)"].strip()) * 1000)
                    duration = int(Decimal(row["Duration(us)"].strip()) * 1000)
                    assert duration >= 0
                    core = row["Accelerator Core"]
                    count += 1
                    if duration == 0:
                        continue
                    delta = [1, int(core in {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV"}),
                             int(core == "COMMUNICATION")]
                    for instant, sign in ((start, 1), (start + duration, -1)):
                        value = events.setdefault(instant, [0, 0, 0])
                        for i in range(3):
                            value[i] += sign * delta[i]
            assert count == rank["kernel_rows"]
            previous = min(events)
            state = [0, 0, 0]
            total = [0, 0, 0, 0]
            for instant, delta in sorted(events.items()):
                duration = instant - previous
                for i in range(3):
                    total[i] += duration if state[i] else 0
                total[3] += duration if state[1] and state[2] else 0
                state = [state[i] + delta[i] for i in range(3)]
                assert min(state) >= 0
                previous = instant
            assert state == [0, 0, 0]
            for key, value in zip(("all_kernel_union_ms", "compute_union_ms",
                                   "communication_union_ms", "compute_communication_overlap_ms"), total):
                assert abs(rank[key] - value / 1e6) < 1e-8, (key, rank["rank"])
            assert int(rank["first_utc_ns"]) == min(events)
            assert int(rank["last_utc_ns"]) == max(events)
            assert rank["per_step_latency_proven"] is False
            ranks_checked += 1
    assert ranks_checked == 8
    print(json.dumps({"result_sha256": EXPECTED, "phase_rank_timelines_verified": ranks_checked,
                      "independent_algorithm": "event-count sweep",
                      "per_step_latency_or_cpu_numa_cause_proven": False}))


if __name__ == "__main__":
    main()
