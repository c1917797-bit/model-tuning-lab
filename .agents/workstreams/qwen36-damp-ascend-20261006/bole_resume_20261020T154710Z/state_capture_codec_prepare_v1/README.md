# Bounded two-base state-capture codec (prepared only)

This is a source-only representation fix, not an algorithm, numerical or performance PASS. No authority, frozen source, container or NPU was created. Exactly five new files live here; frozen parents/results are untouched.

## Actual source path and changes

`render_state_codec.adapt(files)` takes the actual qualification-tapped string source map, returns `(files,inverse)`; `undo` restores every original file and removes the sole added helper. It changes only observer, sink and service_runner. Tested on both the actual131 TAP and the current numeric2k rendered source. Mathematical reference, FIA five-operand proof, all128 transaction writes, TP phases/rollback, candidate computation and numerical thresholds are unchanged.

The actual FAST route is `service_runner.install.sample -> transaction.publish(...collect_diagnostic=False)`, not a fictitious `FAST.publish`. The tap runs synchronously after actual proposal creation/decision and **before that actual transaction call**. A test executes the actual rendered sample publication AST suffix: pre-witness -> transaction -> live publication -> original observer publication. No installed qualifier means no codec hook.

The codec is default OFF: source manifest must explicitly declare `state_capture_codec.CONTRACT` and environment `BOLE_STATE_CAPTURE_CODEC_ENABLE=1`. Installation calls `require_runtime_admission`, which still **unconditionally rejects unbound actual joint budgets**. Existing numeric2k runtime rejection is also retained. This package cannot currently run on NPU.

## Evidence-equivalent encoding

Only 48 GDN layers and four state roles per layer are encoded. Complete actual native before and after tensors remain stored: two bases, shape12x128x128 FP32, 786432 bytes each.

| Role | Stored base/view | Actual witness time |
|---|---|---|
| canonical GDN input | actual before transposed and unsqueezed | actual GDN input |
| staged state.before | actual before | before transaction.publish |
| staged state.after | actual after | hash of actual staged.after **before** transaction.publish, compared to actual after |
| observed applied state | actual after | actual published arena read |

192 strict typedRefs contain complete source/rank/request/generation/slot/length/version/layer/role/view/phase and full finite NPU digest. There are no arbitrary paths, external references, cyclic references, cross-layer/owner refs, or missing role fallback. CPU restore recomputes complete base/view digest from reopened saved raw, then passes the restored frame into the **unchanged original independent consumer**. Restoration makes tensor views, not cloned substitute values. Original selected-state oracle, 128 actual writes, conv and FA checks remain in force.

The actual proposal is never modified; only shallow evidence containers replace redundant captured state tensors. The model-owned proposal/rollback state allocations still exist and are not counted as memory savings.

## First failure, no substitution or ACK

A mismatch raises `CaptureMismatch` containing the actual bad tensor, actual relevant base, complete source/owner/rank/layer/role/timing. It immediately attempts bounded full-payload export to a fresh host receipt `G*-O*-STATE-ALIAS-FAIL.pt`, with O_EXCL/NOFOLLOW, file and directory fsync, exact reopened bytes/SHA Ref. Nonfinite actual bad state is allowed in this failure-only payload. It never replaces bad data with a good base, never ACKs, never passes this filename through successful raw RELEASE, and never broad-cleans old files. If preservation itself fails, the original mismatch is re-raised with preservation error attached, not converted to success.

Normal clone/snapshot pre-allocation checks reserve two complete states inside the original384MiB cap. Failure serialization reserves actual raw CPU pair, BytesIO/wire and digest temporary space conservatively (8 state payloads), plus unchanged checkpoint/metadata reservations; measured wire is checked **before** exclusive write. Actual Torch serialization and real tensor failure preservation remain pending same-image tests.

## Budget scope and corrected arithmetic

`EVIDENCE.json` retains actual0aca shape-ledger command/result and actual historical131 cache metadata Ref used to establish FP32 state and 11-wide conv ABI. These are not new2k observations. Original FA estimate was wrong by factor2: native24 complete K/V before+after over16FA is96MiB, not192MiB. Six GDN state evidence copies are216MiB. The actual source shape-object lower bound (including required conv/normalized inputs and FIA scratch) is385.3240356MiB, not408MiB, conditional on native24/conv11. Other fields are excluded, so it is a lower bound.

The codec removes144MiB of redundant capture/export state storage, reducing that **same lower-bound subset** to241.3240356MiB. It is not225.324MiB and is not a fit proof. CPU decoded refs are views of retained bases; exporter/reopened raw are still distinct allocations. Original fixed128MiB checkpoint and64MiB metadata, first G1-O0 raw, current export/reopened copies, failed payload/wire, original CPU oracle workspace and model-owned tensors must all be measured together. The existing1GiB sink precheck and384MiB export cap are retained; neither is raised. Actual wire/storage overhead, current+checkpoint overlap, GPU/CPU high-water, release timing and failure case remain unbound, hence admission stays hard closed.

Concrete remaining long-stream blocker (actual0b06): the existing long helper charges retained_first_wire + 2*current_logical + current_wire + checkpoint + metadata. In a conservative same-worst-subset estimate, if first/current wire each equals241.324MiB, it needs1213512960B=1157.2961426MiB with the original192MiB fixed reservations, exceeding1GiB by139771136B. This is not an actual first-frame measurement: L2048 uses17 private pages, not25, so its corresponding subset can be16MiB smaller (225.324MiB); using that first subset and the worst current subset gives1141.2961426MiB. These are conditional estimates, not exact Torch wire or an inevitable frame2 failure: frame2 need not have worst25 private pages. The codec resolves the known384MiB same-frame clone defect but **does not establish retained-first joint fit**. Real first/current wire storage sharing, actual/reserved checkpoint/metadata and temporary overlap remain unbound. Do not use the shorter original sink precheck to bypass the long helper.

A possible next bounded design, not implemented here, is immediate validated previous-after checkpoint to current-before dedup for exactly128 actual before tensors (48 state,48 full conv,16 FA K/V pairs). For this conditional geometry that removes90783744B=86.578125MiB per nonfirst frame, leaving a154.7459106MiB current subset; with the conservative241.324MiB first subset the analogous ledger is about897.5617676MiB before omitted overhead. Every current-before NPU full hash, previous original ACK/report and source/request/rank/next-length/version, exact physical slot/pages and checkpoint full bytes must be joined before restoring views. First frame remains complete, different request/generation/new page cannot borrow a previous checkpoint, failures retain the actual unequal payload. Current codec deliberately supports **only same-frame refs** and rejects this future cross-frame representation. This is a design lead, not an admission or measured fit.

## Software evidence and next actual step

Actual0aff:9 software controls passed in2.363s, no skips, no Torch/NPU. Tests cover192 refs, strict corruption negatives, no proposal mutation, actual transaction seam ordering, whole inverse, current numeric2k/FIA composition, default OFF/unbound rejection, and real exclusive temporary-file Ref/fsync ABI. The file writer test serializes explicit software fixture bytes, **not real tensor evidence**.

Run source software tests with isolated Python and this directory in sys.path, loading `test_state_codec.py` via importlib/unittest. Default renderer CLI performs no work; arguments are rejected. This is a library source delta, not another controller. MAIN must review composition/readset/commands and bind a new source in a lawful window. Then same-image real Torch restoration/serialization and real NPU witness/joint-budget validation are required before removing any unbound guard; no inherited numerical qualification or formal1024 performance gate is satisfied here.
