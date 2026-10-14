"""Join explicit live Linux PID chains to source-bound TP worker receipts."""
import re

def audit_physical_workers(samples, worker_pids, *, owned_cid):
    if not re.fullmatch(r"[0-9a-f]{64}", owned_cid):
        raise ValueError("exact owned container ID required")
    if set(worker_pids) != set(range(4)) or len(set(worker_pids.values())) != 4:
        raise ValueError("four distinct source-bound ranks required")
    mappings = {}
    for rank, inner_pid in worker_pids.items():
        matches = set()
        for sample in samples:
            for owner in sample.get("owners", []):
                chain = owner.get("nspid")
                if not chain or len(chain) < 2 or chain[-1] != inner_pid:
                    continue
                if any(type(x) is not int or x <= 0 for x in chain):
                    raise ValueError("malformed raw PID chain")
                if chain[0] != owner.get("pid"):
                    raise ValueError("host PID differs from explicit namespace chain")
                if owner.get("owned") is not True or owned_cid not in owner.get("cgroup", ""):
                    raise ValueError("exact live cgroup ownership missing")
                if owner.get("npu") not in range(4):
                    raise ValueError("physical device outside authorized lane")
                matches.add((owner["pid"], owner["npu"]))
        if len(matches) != 1:
            raise ValueError("missing or ambiguous live rank mapping")
        host_pid, npu = matches.pop()
        mappings[rank] = {"inner_pid": inner_pid, "host_pid": host_pid, "physical_npu": npu}
    if len({x["host_pid"] for x in mappings.values()}) != 4 or {x["physical_npu"] for x in mappings.values()} != set(range(4)):
        raise ValueError("four independent physical workers required")
    return {"ranks": mappings, "scope": "explicit live PID/cgroup/physical join only; source and continuous isolation independently required"}
