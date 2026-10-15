# Prospective R6 C2 completion barrier gate — 2026-10-15

This is a new candidate, not a correction to old measured outcomes.
The R5 first-pair regression remains TPOT +59.919% and TTFT P95 +76.720%.
The original R5 algorithm files are recoverable at ecaf4c02 parent history;
old raw roots must never be reused. Source-bound retrospective replay must
use the recorded checkpoint, not assume current activation bytes are unchanged.

## Single runtime change

The c2_layer_completion_barrier boolean defaults false. True selects the
independently authored experimental_c2_layer_barrier wrapper. It preserves
query-window ordering, KV slot ownership, relocation math and backend calls,
but waits once after all C2 plans in a layer before issuing any receipts.
Material leases cover execution, barrier and receipt publication.
There is no claimed native batch-kernel optimization or removed evidence fsync.
GDN, scheduler, shape, c16/full40 client and output ruler are unchanged.

## Gates and falsification

Host controls0461 cover explicit boolean routing, default-off behavior, hot
KV seam/suffix, nonfinite rejection, missing leases, completion failure and
reverse uninstall. CPU doubles are not NPU or cross-stream equivalence proof.
New R6 manifest includes all changed support bytes. Old R5 manifests correctly
reject current activation drift; they remain historical immutable contracts.

Run only the new full40 c16 integrated root in its contract after fresh direct
route, physical0-3/8233/HCCL idle checks. Absolute stop19:04:09UTC today.
Require full40 transport, each request fourrank48/16 body-skip proof, source,
physical namespace joins, continuous clean isolation and exact owned release.
Compare timing to retained R5 and nativeG1 only after scope/identity review.
Any invalid mechanism, device error or performance regression is preserved
and not retried unchanged. Quality and full matrix acceptance remain separate.
