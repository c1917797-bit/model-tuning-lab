# V6 bounded service static review

Result: no additional confirmed blocking defect was found in the reviewed
first-request131/four-output-token path after the late target-head hook and
hybrid12x FA ownership fixes. This is a source review, not an executed lifecycle
or numerical pass. I did not change service_work, frozen files, Git, the host,
containers or devices.

Reviewed local candidate identities (all five files parse as Python):

| File under `/workspace/scratch/6d9e7cc63b51/service_work/` | SHA256 |
|---|---|
| service_runner.py | 08ef1c89a54f2870dec26263f97a3521d535cac98b5ff93df413ae3042f1e966 |
| live_owner.py | f87789c5cdccafc8d2bd4ddab1170ce21ff3764377e80d0693d1f526f32a0073 |
| consume_service.py | e193efc32a72b442e578cf3a6a568d553a4eedbf738c869098eddd5bc80fd27d |
| service_bridge.py | eca1b010b67a2604bcc01bc0f2c13f286f8381edd8c6b9d45eb853f98feb40e8 |
| transaction.py | fdc008e7e2912da9efb7860cc19c781386340e1123fcca9dfb3c528eb6945a6a |

## Prefill source guards: the late head fix addresses the concrete conflict

Exact frozen input_identity.py is available at
`/workspace/scratch/6d9e7cc63b51/bole_service_reference/input_identity.py`.
Its capture function checks native runner `_preprocess`, base `_preprocess`
and `_prepare_mm_inputs`; it does not source-check the runner's already wrapped
`_prepare_inputs`, `_sample`, `sample_tokens` or proposer methods. Therefore
those wrappers do not produce an additional prefill source-identity failure.

The embedding route does call `actual_logits_head` before native prefill,
which requires the original source-bound compute_logits method. Current
service_runner.py installs the head observer only at the end of after_prefill
(line326), after input_identity.capture and cache registration have completed.
Native runner.py then calls the target compute_logits after its model forward
returns (post-process section around2350), so the observer is installed in time
to capture the initial real head operand. No other early head patch remains in
the final hook-installation list. The callback's use of `guard(target_head)` is
valid: callback execution starts after install has defined guard and completed
the outer hook installation.

The exact native input capture also checks original text token IDs and their
embedding lookup; the service bridge uses the actual inner embed_input_ids
method for padded-tree embedding construction and checks admitted embeddings.
For this text-only fixed profile, no new source-guard conflict was found there.

## FA owner expansion now matches the native mapping

live_owner.py check_fa freezes actual block geometry and expands raw request
physical blocks by `physical_id*ratio+j` only for native hybrid blocks.
This matches qualified/fa_prefill131r10.py mapping, including ratio12,
physical1536/kernel128 and CP1. It compares the expanded row against both the
registered and current CPU allocated kernel-page row and checks actual layer,
backend and cache aliases. The earlier raw physical-ID versus expanded-row
equality failure is removed from FA ownership validation.

The `_snap` ownership proof is produced from that same live check, and the
consumer reconstructs the expansion independently. Actual FA page snapshots
contain only the first two selected pages while ownership covers the full
allocated row; this is consistent with the131..135 prefix restriction.

The GDN slot check remains the separately qualified GDN group/slot path. I found
no evidence in the inspected native source that FA's12x expansion should be
applied to GDN state-slot IDs; doing so merely by analogy would be incorrect.

## Real positions and hidden buffers support the child2 compaction order

Native base_runner.py `_get_positions` (around979) returns views of the same
native position buffers used by `_preprocess` (around3500). The service bridge
changes that real GPU position view to tree depths. Native
propose_draft_token_ids later reads those positions through `_get_positions`.
Thus the proposer does not silently re-read an untouched linear-position
buffer in this path.

Native runner.py `_bookkeeping_sync` (2646+) updates CPU output history before
proposal. The candidate leaves that CPU history unchanged. Its
propose_drafts hook (428+) compacts actual GPU input IDs and the actual returned
native-hidden view before original propose_draft_token_ids constructs its
advanced-index copies (native runner1878..1897). For selected child2 the order
is `(0,2,1)`; all admitted rows remain present. This is the required native
ordering rather than an accepted-only truncation.

Native Ascend proposer.prepare_inputs_padded (1893+) retains all admitted rows
and chooses query_end-1-rejected as its sampled row. Native
set_inputs_first_pass (1337+) shifts target IDs and writes the emitted bonus at
that sampled row. The selected live first-pass prefix is therefore child2 then
bonus for a two-token child2 result, or bonus alone for root-only. Rejected
tail contents are not assumed to be known. The reader now checks actual target
int64 versus native drafter int32 positions through an exact round trip, so
that previously identified ABI difference is not a false bitwise failure.

## MTP capture uses the genuine original first pass

The hook saves the original bound `_propose` before installing its wrapper and
captures the original function signature. It temporarily sets the actual
drafter field to1, calls that original function, and restores8 in finally.
Native proposer._run_merged_draft exits after the first pass when the field is1
(around1183); it reaches model.compute_logits for methodmtp through its actual
source path. This agrees with the single-call capture requirement.

The metadata fields copied by `_metadata` are Tensor/None in the inspected
native path: native runner3155..3172 supplies seq_lens_cpu and _seq_lens_cpu
from Torch optimistic-sequence-length tensors, not NumPy arrays. I found no
detachment failure from those fields.

Returning a two-wide CPU list avoids the native fixed-width Tensor D2H copy:
native runner._copy_draft_token_ids_to_cpu returns when the draft result is not
a Tensor, and base_runner._get_draft_token_ids_cpu (4731+) directly returns a
stored list. Native scheduler.update_draft_token_ids accepts the actual list
and schedule uses its real length. The global configured8 is not used as an
assertion that this returned list has length8 in the inspected path.

## TP ordering, output budget and retirement

The initial canonical-logit join, first-MTP join and later target/MTP joins are
entered in the same source order by each TP rank. The native scheduler supplies
the same C1 admitted row count; transaction additionally all-gathers the full
admitted count, target-next IDs, terminal, emitted tuple and remaining budget
before persistent writes. I found no collective that only the owning rank or
only the child2 rank is instructed to execute in the normal path.

Remaining output is read before native bookkeeping. At remaining1, eligibility
forces root-only and transaction rejects a longer publication. This prevents
the native scheduler's later output trimming from disagreeing with the manual
cache advance for the fixed ignore-EOS four-token profile.

After original sample_tokens returns, the candidate checks actual target cache
postimages, snapshots real arenas/pages and closes the frame only against the
actual ModelRunnerOutput IDs. The next actual `_prepare_inputs` acknowledges
the previous publication's computed length and unprocessed bonus. The final
publication deliberately has no fabricated next-counter observation; the
independent reader joins HTTP and native retirement.

Late head-hook installation adds its restorer after the other hooks. Reverse
restoration on retirement therefore restores the head first, then restores
outer service hooks, leaving the original W prefill wrapper in place before
`restore_native_prefill` checks its identity. The64-layer bridge is restored
while BUS is clear. This ordering is internally consistent for the explicit
native-only retirement-barrier request.

## Scope of this result

No additional static change is justified by this review alone. The actual
running V6 result still determines whether new prefixes pass the unchanged
numeric bounds, all real buffers satisfy the asserted runtime ABI, the full
payload fits the original cap, and the native engine/HTTP/retirement join
completes. This review does not turn those unexecuted checks into a pass and
does not qualify repeated requests,1024 outputs, tasks or performance.
