"""Thin callbacks for an existing owner/atomic journal, no controller or device calls."""
import hashlib, inspect, os
from pathlib import Path

ASSIGN_SHA = "c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"
NPU_SHA = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"

def source_guard(function, digest):
    p = Path(inspect.getsourcefile(function))
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
        raise ValueError("actual loaded source drift or wrong installation order")
    return p

def process_identity():
    p = os.getpid()
    raw = Path("/proc/%d/stat" % p).read_text()
    rest = raw[raw.rfind(")") + 2:].split()
    return {"pid": p, "start_ticks": int(rest[19]),
            "cgroup": Path("/proc/%d/cgroup" % p).read_text()}

def install_assignment(input_processor_cls, emit):
    # Install after normal source verification, before first HTTP request.
    original = input_processor_cls.assign_request_id
    source_guard(original, ASSIGN_SHA)
    if getattr(original, "_actual_identity_capture", False):
        raise ValueError("duplicate identity capture")
    def assign(request):
        event = {"schema": "vllm023.actual-assignment/v1",
                 "source_sha256": ASSIGN_SHA, "identity": process_identity(),
                 "before_request_id": request.request_id,
                 "before_external_req_id": request.external_req_id,
                 "disable_request_id_randomization":
                     bool(original.__globals__["envs"].VLLM_DISABLE_REQUEST_ID_RANDOMIZATION)}
        result = original(request)
        event.update(after_request_id=request.request_id,
                     after_external_req_id=request.external_req_id)
        emit("assignment", event)  # caller's actual atomic owner journal; must fail closed
        return result
    assign._actual_identity_capture = True
    input_processor_cls.assign_request_id = staticmethod(assign)
    return original

def install_worker(npu_runner_cls, rank, emit):
    # Before algorithm/HYPIC wrappers; every real worker installs independently.
    # Existing caller binds rank to its real WorkerWrapper + exact controller proof.
    if type(rank) is not int or rank not in range(4):
        raise ValueError("actual TP rank required")
    original = npu_runner_cls._update_states
    source_guard(original, NPU_SHA)
    if getattr(original, "_actual_identity_capture", False):
        raise ValueError("duplicate worker identity capture")
    seq = 0
    def update(self, output):
        nonlocal seq
        seq += 1
        event = {"schema": "vllm023.actual-worker-update/v1", "seq": seq,
                 "rank": rank, "identity": process_identity(),
                 "source_sha256": NPU_SHA,
                 "new_req_ids": [r.req_id for r in output.scheduled_new_reqs],
                 "cached_req_ids": list(output.scheduled_cached_reqs.req_ids),
                 "num_scheduled_tokens": dict(output.num_scheduled_tokens),
                 "total_num_scheduled_tokens": output.total_num_scheduled_tokens,
                 "finished_req_ids": sorted(output.finished_req_ids),
                 "requests_before": sorted(self.requests)}
        # Never skip zero-token/finished-only calls; native removes finished states.
        result = original(self, output)
        event.update(requests_after=sorted(self.requests),
                     batch_after=list(self.input_batch.req_ids))
        emit("worker_update", event)
        return result  # preserve original deferred-corrections callable
    update._actual_identity_capture = True
    npu_runner_cls._update_states = update
    return original
