"""One complete matched workload unit; service lifecycle owned by caller."""
import hashlib,json
from pathlib import Path
from independent_formal_warmups import build_warmups,execute_warmups
from independent_formal_client import run_full40
from independent_performance_summary import summarize_phase

def run_formal_workload(spec,*,send_warmup,send_measured,guard,record,
                       require_material_ready):
    p=Path(spec["path"])
    if not p.is_absolute() or p.is_symlink() or p.stat().st_size>33554432:
        raise ValueError("bounded absolute artifact required")
    data=p.read_bytes()
    if hashlib.sha256(data).hexdigest()!=spec["sha256"]:
        raise ValueError("formal workload input drift")
    artifact=json.loads(data)
    # Warmups and measurements use the SAME immutable token snapshot.
    execute_warmups(build_warmups(artifact),send=send_warmup,guard=guard,
        record=record,require_material_ready=require_material_ready)
    def scored(item):record(dict(item,event="measured-response",scored=True))
    result=run_full40(artifact["requests"],send=send_measured,guard=guard,record=scored)
    if not result["valid"]:
        return dict(result,summary=None,input_sha256=spec["sha256"])
    return dict(result,summary=summarize_phase(result["results"]),
                input_sha256=spec["sha256"])
