# Oct15 real NPU lifecycle repair and remaining acceptance edges

Fixed cutoff 2026-10-16T07:18:17Z remains unchanged. No new accepted whole-model performance/task result.

## Actual DeltaLog experiments
003 MA045b ended exit3 after88.491s. Correcting the flush counter from7->1 to7->0 allowed both baseline/KDMA B1 trajectories to finish160ticks. B16step0 then failed candidate/native output0.71497, although candidateCPU64state3.55e-8; saved nativeCPU64state1.7596 contradicted a valid control.

The deployed native source26497B/96e6d966... reads actual_seq_lengths[batch+1] as a LENGTH and accumulates seq1. It is not the cumulative cu_seqlens ABI used by chunk/prefill.004 changes only the native control to[0,1,1,...], retains candidate inputs/math/libs and both old failures, captures both metadata tensors and adds original7.92e-7 native-state checkpoint checking.

004 sameimage CPU MA0469 exit0 passed actual FP64, flush and B1/8/16 sequence checks; exact owned Devices[] release independently checked MA046b. Numerical MA046c ended exit3/97.789s: B1both160PASS; B16bothfirstfailure step3. Native ABI repair removed the huge first-step error; the residual0.003105590062111801 exceeds unchanged0.00303. Candidate/native state errors3.864e-8/7.268e-8 and all storage/lifecycle invariants pass, but do not erase the failed output gate. Saved-frame readout/reassociation diagnosis remains UNKNOWN, not a new tolerance or paper no-go. Exact both owned CIDs stopped/retained/Pid0/noExec/noOOM were checked MA0471.

## Prepared successors and real resource boundary
MAIN deployed004 observerless MXR and007 once-candidate correctness packet byte-exact. MA047d actual60file,6cold,5CLI and692Ref source audit passed. These are not sameimage/NPU/model results. Long32768/40960, full state/metadata lifecycle, three matched1024 pairs and final tasks remain required. No old short shadow or helper PASS grants these.

MA0473 observed external HYPIC on protected0-3 and physical4-7 idle, but ordinary available RAM62605592KiB below model73GiB initial floor. Do not infer card occupation or change model budget from aggregate host/CLI RSS; it does not measure full container/worker peak. No additional HugeTLB release or foreign workload stop is authorized here. Cache free106754043904B cannot admit a guessed160/256GiB raw ticket.

At07:30Z GE060 MAIN0482 source/sameimage CPU preflight is confirmed RUNNING, not an NPU lease. Pending next: actual same-source CPU success/release then fresh physical6 short full-GDN matrix. MXR007 remains resource/sameimage pending. Parallel owners prepare MXR long closure, DeltaLog savedraw diagnosis and final task runner/input closure. No artificial card load or continuous-utilization claim.

## Recovery
See adjacent JSON for exact source/results/Releases. The tracked deltalog_lifecycle_v004 directory preserves reviewed source bytes; manifest paths intentionally retain original cache locations. To re-execute, materialize exact files to the recorded root through scoped patching and recheck all immutable dependencies; don't rewrite identities to run from the archive. DefaultOFF is safe; --execute requires real inputs/authority/owned resource admission. It is not a final production plugin.

Knowledge commit d11b12cd is local; normal push remains unconfirmed. Worktree has unrelated old modified/untracked files; stage only explicitly reviewed paths. Do not claim remote success from a missing operation registry entry.
