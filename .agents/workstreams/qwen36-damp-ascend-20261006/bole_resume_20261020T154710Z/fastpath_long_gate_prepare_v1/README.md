# Long qualification: software-only downstream preparation

Status: PREPARED160 COMPONENT RENDERER, NOT A BOUND SOURCE OR EXECUTABLE NPU PACKET.
No authority, container, NPU execution, mathematical PASS, or performance claim
was created. Current short8 source and the formal1024 gate were not edited.

## Concrete failures found before using cards

The real `consume_frame` final return AST is evaluated with explicitly synthetic
schema operands by `check_long_gate.py`; no synthetic report is saved as a run.
It includes64 metrics,128 write rows and224 full-tensor digests. The minimum-value
fixture serializes to67,882 bytes; original STATE STEP duplicates43,044 bytes.
Its lossless compressed representation is11,665 bytes, but that compression
ratio is only a software observation, not a bound on actual NPU reports.

Actual BOLE emits one or two tokens per tree frame, after the initial root.
Each request therefore has80..159 frames for160 outputs,512..1023 for1024.
Two generations have at most318/2046 frames; reserve one further failure event.
The unchanged full-report representation already exceeds64MiB at1024 frames.
The unchanged STATE representation exceeds its10MiB cap at318 frames.
Thus simply enabling longer profiles cannot cover the registered domain.

The current cross-frame consumer compares entire FA snapshot tensors. A newly
owned physical page changes their shape despite preserving all prior pages.
The new exact renderer changes only that continuity block, retaining the GDN
comparisons and every mathematical reference, bound, and per-frame128-write
check. The physical-page helper rejects corruption, aliasing, reordering,
storage-identity changes and cross-generation reuse. New page initialization
and outside-table arena coverage are explicitly NOT proven by this helper.
Per-frame original `fa_owner`/attention/full-page before-after checks remain.

The original capacity gate deliberately reserves length+3 physical rows, while
tree depth addresses length/length+1 and accepted paths contain at most2 tokens.
Their different page formulas alone are NOT evidence of an algorithmic bug.
Maximum reserved pages are3 and10 for the two proposed domains.

## Implemented minimal reusable code

- `long_gate_primitives.py`: lossless canonical full-report compression; strict
  wire Ref/decoded hash checks; bounded single-stream decode rejecting bombs,
  extra streams and mixed field types; complete128-row recovery with all
  original metrics/flags retained; shared fixed metadata/raw reservations;
  request-owned physical-page continuity. It does not emit an ACK or PASS.
- `render_page_delta.py`: exact/invertible replacement of the existing FA
  continuity block only. It returns source text, does not materialize or bind it.
- `check_long_gate.py`:20 pure-software positive/negative controls, including
  real return-AST shape, old budget rejection, exact roundtrip, bool layer,
  wrong frame/wire hash, scope promotion, corrupted old page, duplicate page,
  reordering, new page, generation and arena changes.
- `render160.py`: actual minimal sink/observer/STATE/reader/HTTP domain adaptation
  plus physical-page continuity, with a complete reversible14-file delta.
  It returns420 source bytes in memory and keeps the original runtime validator
  closed. It creates no source/output directories or authority.
- `check160.py`: actual generated160 select/emit/reader-obj/store functions,
  unchanged mathematical/transaction sources, wrong-profile refusal, lossless
  roundtrip and rejection before file creation when the budget is exhausted.

The decoder returns the COMPLETE original report and rows. Integration must
still pass them to the unchanged numeric/STATE validators. Lossless transport
and a row count do not establish independent numerical or lifecycle success.

## Fixed budget and concrete remaining integration edges

Current target is160, not1024 execution. Per event:20KiB complete compressed
report,1536-byte lossless envelope,1536-byte release and2048-byte compact STATE.
Reserve319 numeric events including failure; conservatively also charge325 old
FRAME/ACK/REPORT/RELEASE events (318 steps plus2x open/retire/close plus failure).
Keep ALL original51MiB fixed buckets, including8MiB projection, and reserve
4x256KiB BEGIN/RETIRE files per rank. The combined per-rank metadata bound is
66,155,552 bytes, below the original67,108,864-byte cap. No old bucket is removed.
The original STATE reader's10MiB is ALL4 ranks together:4x319x2048 plus
16x256KiB non-step receipts is6,807,552 bytes. It is NOT a per-rank10MiB cap.

1024 remains pending. Its2047x4 compact STATE representation already exceeds
that all-rank cap; prior illustrative10MiB fixed evidence is not an admission
proof. Actual whole-leaf measurements and any later lossless representation
need independent review. No existing budget was raised.

Each actual full report must satisfy the20KiB compressed subcap BEFORE durable
publication. It is retained losslessly. A failing report or failed frame cannot
be deleted to make that cap pass. The original complete first G1-O0 raw and any
unacknowledged/failed raw remain retained. Actual short8 first-frame logical,
wire, checkpoint and fixed JSON sizes are still PENDING. The384MiB frame cap
does not prove retained-first+current/failed+copies+checkpoint+JSON fit1GiB.
`raw_reservation` supplies a conservative combined check and a legal-individual-
subcaps-but-unsafe-combination negative control, not a claim the real model fits.

Implemented160 edges and precise remaining gaps:

1. Generated sink stores the COMPLETE compressed report and envelope durably,
   reopens and exactly compares it before original raw release. All bytes are
   reserved before the exclusive create. Original failure/first-raw rules stay.
2. Generated STATE emits a lossless report Ref and a source-bound full-profile
   digest, instead of repeatedly writing159 ordinals and224 tensor hashes.
   Generated reader restores the exact full profile/rows before ALL original
   row/state/lifecycle assertions. HTTP uses160/160/1 and steps80..159. Original
   native speculative-token count8 is NOT changed; it is not an output limit.
3. Terminal160 consumer keeps original metric/HTTP/state assertions and unions
   actual original budget Refs with ALL new report/envelope/STATE files, avoiding
   both omission and double counting. Per-rank64MiB and all-rankSTATE10MiB remain
   separate. Complete metric arrays/flags are not replaced by a transport ACK.
4. New helper and renderer must enter a separately reviewed whole-source closure;
   actual worker entry, profile/domain, source/commands and budgets need binding
   under a fresh legitimate window. Formal1024 performance gate is untouched.
5. Original stream ownership/TP4 ACK semantics are not replaced with invented
   successful fields. This new numeric observer does not prove native MTP/head
   vocabulary, whole-model equivalence, final task quality, or timed speedup.

## Evidence

Host-Python software `09ba` was the20-control earlier helper iteration;
`09d5` completed exit0 for4 generated160-entry controls. Final current-source
checks and Refs are delivered separately to MAIN. Earlier `09b1`/`09b7` retain
13/17-control iterations. This is not same-image evidence. MAIN owns later same-image
test, binding, source audit and NPU admission. Default CLI is OFF:

```text
python3 -I -B check_long_gate.py --check
python3 -I -B render_page_delta.py --check
python3 -I -B check160.py --check
python3 -I -B render160.py --check
```
