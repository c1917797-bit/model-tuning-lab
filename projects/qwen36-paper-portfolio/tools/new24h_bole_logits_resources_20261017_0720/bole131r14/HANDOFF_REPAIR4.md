# R4: post-native cache metadata observability only

R3 did not persist the full pooled cache/group/CPU allocation metadata before
cache_registry.register. This successor adds one exclusive, flushed/fsynced JSON
per actual rank before that unchanged function. Existing same-slot, alias,
source, static-object, selected-region and numerical guards remain byte-identical.

BOLE-PREFILL-CACHE-RANK-{rank}.json records all48 actual conv/state tensor geometry,
GPU prefill-index geometry (not contents), actual pooled tensor shared_by/size,
group/spec shapes/dtypes, allocated CPU block-table row, strong request.block_ids,
static/dispatcher object binding, actual context identity and source Ref3s.
No tensor values, device-to-host transfer or inferred slot/epoch proof is added.
Only the actual first post-native-prefill callback ordinal is claimed; no
scheduler epoch is manufactured. Same-slot/region failure still fails the run.

Metadata is capped at2MiB/rank, within the unchanged1GiB/rank whole diagnostic cap.
Three focused controls PASS0.007s: heterogeneous rows observed without admission,
wrong request/context rejected, no device-copy calls and exact unchanged register
source. The old48 controls are NOT rerun locally. Actual same-image entry now
includes all51 and remains required. No NPU or model qualification is claimed.

All other runtime/source identities derive from R3, with unique R4 root/output.
Deployment uses actual fully copied R3 as donor. COMMANDS retains explicit default
OFF/cold/bind/sourceaudit/CPU/model sequence and all actual component requirements.
