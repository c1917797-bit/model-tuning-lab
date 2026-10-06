# T1..16 source-capacity proof — not an execution receipt

Original header SHA15142a83..., complete source was read. Actual lines:
metaIn160B L85; Process tasks L122; LoadValidateMetadata L144–180;
fixed B1/B16 rejection L162; LoadToken L296; StoreHead L512; ProcessTask L532.
The exact line mapping is recorded from readback, not a guessed newer source.

For T in1..16:
- indices INT32[T] occupy ceil8(T) elements after DataCopyPad, at most16,
  starting local[0]. right-padding=(8−T%8)%8 is0..7.
- lengths INT32[T+1] occupy ceil8(T+1), at most24, starting local[16].
  Last padded element is local[39], within160B/40INT32 queue.
- local work meta has64INT32. DataCopy of40 elements and matching V_S wait
  already cover all initialized active indices[0..T−1], initiallength[16],
  and active lengths[17..16+T]. Other uninitialized queue gaps are never read
  by the validation or ProcessTask; no computation depends on them.
- Range validation checks all active slots before writer dispatch, accepts only
  lengths[0]=0/allremaining1, and rejects duplicates. Invalid metadata still
  takes the original no-state-write/NaN-output branch.
- tasks=12T is12..192. blockNum=min(vectorCoreNum,12T). The strided task loop
  visits each task exactly once, mapping token=floor(task/12), head=task%12.
  Unique slots make all (slot,head) owners distinct. Four fixed group32 writers
  retain original full-head readout and output ownership.

Per-token q/k and v vectors have256B per head; offsets include token using
uint64_t. g has48B per token and beta24B; DataCopyPad performs exact logical-byte
reads plus UB padding, not over-reading the GM tensor's padded-length bytes.
Their row starts may not be32B aligned, even in the already-run B16 path.
The actual base pointer still needs32B alignment. This extension adds no new
row-alignment class beyond that existing B16 path, but all new shapes still
need device checks, not an inferred public API pass.

Per-head output is256B, total3072T, always32B aligned. Group stores are unchanged
hi1024/lo3584/scales448 bytes. Neither slot bytes nor UB depends on T.
Explicit UB remains141312B and the existing8192B Broadcast workspace is reused.
The static tiling sizeof1056, ABI2, core-count query, Q scale, dtype/layout and
one-token semantics are unchanged.

Thus the source geometry has no found T2–15 capacity/ownership obstacle once
the device's deliberately narrow token predicate is separately adapted.
This is not an ISA/compiler/DMA proof or NPU pass. Out-of-range T0/>16 remains
rejected by host before dispatch; malformed dynamic lengths/slot values remain
rejected by the kernel before any state writer.

The copied header is exactly old text after include-guard/include-path and one
predicate substitution, ignoring only redundant EOF newlines. This establishes
the mathematical bodies have not been edited. It does not establish those
bodies execute correctly for newly admitted T or make a C16 model service ready.
