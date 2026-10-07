# H8 B6 retained-raw CPU reanalysis — actual partial evidence, parent failed

The CPU-only reanalysis MA0f05 exited1 after31.348s. It did not dispatch new NPU
work. The whole original terminal operation, exact prior successful source
admission, launch and actual report are preserved alongside this note. Frozen
source manifest121168e9f88cbcbc4fccc551c1c8f9a194637b427c02f6fb991fe7d13010f1c9.
RESULT SHA c5aa2fab62ab70c77c4453379d9f2f10c441d30c552e3ad5279fca951ea6d1f2.

Actual report parity subrecord says passed=true. Output error0, complete-state
L2 1.1331556615308631e-08, max per-head L2 5.7787388639726184e-08; all unchanged
numeric/log/finite/input/pointer/untouched checks and all12 state-backings x5
guard predicates are true. Both64-element redzones are intact; writable
payload is compared to its actual state view, not to the entire old backing.

This is a partial record, NOT an accepted CPU stage or full native matrix.
The process subsequently failed its explicit torch_npu not-in-sys.modules
predicate. Preserve status=failed and exit1; no original report/source/raw
rewriting, lowered gate, or unchanged rerun. A preparer reports pickle metadata
containing torch_npu Format enum as the cause; that causal artifact is pending
MAIN source review. Do not misattribute this label failure to H8 numerical
math, or claim that the no-import safety promise was fulfilled.

Independent MAIN MA0f14 exited0/800ms, consumed the immutable full original
failed operation with exact source/raw/hash/CPU process linkage, and inspected
the actual sole CPU CID d8bff358a07d22bbe4d162ddfc4ee39d39d5bb8d57eeb01ad512ef000223d062:
stopped, retained, Pid0, noExec/noOOM, noDevices/requests/rules. Its consumer
explicitly returned corrected_guard_reanalysis_verified=false, zero complete
matrix steps, model_ready=false, no pairedE2E or task evidence. Do not replace
that scope with the partial parity flag.

Memory readback in MA0f14: MemAvailable100953868KiB; NUMA0 439/439,
NUMA1 485/485, NUMA2 486/486, NUMA3 474/450 nr/free1GiB pages, all surplus0.
OVS PID27118/start11471 and actual24GiB hugepage backing remained intact.
The authorized32GiB release was already completed, not repeated by this
read-only check; no additional release is permitted.

Historical fullv2 physical6 warm-transition synchronize507035 remains
unresolved. Next relevant H8 experiment is a source-reviewed1280-step
B14/B11 eager/graph prelude followed by B6 separate native/H8 fences and raw
checkpoints, not the old fullmatrix retry. Fullmatrix/lifecycle/mixed/model,
same-stack1024 pairedE2E and final2048 tasks remain pending. SparQv4 actual ABI
failed before NPU; source-supportedv5 has69 software tests only and awaits
MAIN full review/admission. Fixed cutoffs remain Oct8 08:29:54Z (KVBuffer) and
Oct9 11:17:31Z (portfolio); no deadline reset or new accepted technique.
Git publication remains the known credential-helper blocker, not resolved.
