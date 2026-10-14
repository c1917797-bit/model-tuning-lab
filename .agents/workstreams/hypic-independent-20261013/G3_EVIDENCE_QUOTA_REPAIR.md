# G3r1 evidence quota repair

G3r1/03bc failed at exactly10000 events/worker, about3.62MiB, not at the
32MiB byte limit. Independent terminal audit03da binds the original failure.
The successor config changes ONLY evidence_limits; all algorithm, model,
public artifact, pool and mixed/chunk settings remain the R3 values.

Prospective cap:100000 events,128MiB,128 distinct requests per worker.
Four workers bound total raw ledger storage at512MiB. This is within the
existing validated evidence_limits ceilings, not unlimited logging or silent
truncation. Same-size algorithm logs remain available for independent audit.
The client has40 measured plus4 warmup requests;128 identity slots leave
headroom but do not authorize new workload requests or retries.

One hot-containing step may emit64 receipts for each mixed native/hot request.
For40 measured requests and at most16 client in-flight requests,40*16*64=40960
layer receipts before replay/metadata overhead;10000 was plainly too small.
This calculation assumes one hot step/request and is NOT a bound on native
preemption/recompute repetitions. Unexpected repetitions still fail closed at
new finite caps and need their own diagnosis. Do not promise this alone makes
the complete run succeed. Concurrent partial-PIC admission remains unfixed.

No new device execution by this config change. New source manifest/contract/root
and fresh physical admission are required before any successor NPU stage.
