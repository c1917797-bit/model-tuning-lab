# Decode prompt-snapshot cost hypothesis — prospective2026-10-16

Current G1 exact09a6 LIVE; all141boundfiles immutable until terminal/audit/release.
G3full40 accepted09a1: weightedTPOT413.7713ms,TTFTP95518966.27ms, no freshpairyet.
G1must finish before declaring regression or changing implementation. No repeatedmatrix
expansion if first validpair misses frozenprogression. Retain completeR15outcomes.

Source: freeze_native_runner in independent_runtime_adapter.py calls freeze_prompt_tokens
at EVERY native prepare; independent_prompt_snapshot.py converts/validates allprompttokens.
activate_compact_runner already avoids compact metadata for allnative1decode, but that
branch is AFTER fullprompt copy. Thus nativeGDN directfallback alreadyexists; do NOT add
redundant GDN/operator task or assume packednative math is the puredecode bottleneck.
ExactCPU0999,12x32768=393216 tokens,50calls,median109.6787ms/snapshot on HOST Python CPU0
outside service112-191. InitialCPU8attempt0996 failedaffinity;0997 freshly provesCPU0allowed.
This is source-path/localcost evidence, NOT actual workercriticalpath, pertoken gain,
Python3.12 equivalence, or a speedresult. FourTPworkers runparallel: NEVER multiplyby4.

Cheapest falsifiable OFFLINE component: new unactivated prefill snapshot helper.
Defaultoff delegates EXACTexistingfreeze_prompt_tokens. Expliciton: only a request with
scheduled_tokens==1 AND computed_tokens>=len(prompt_token_ids) may omit immutable
prompt snapshot(returnNone); all remaining prefill/partial-prompt/publicproducer rows use
EXACToriginal snapshot implementation. No caching across requests/generations and no
mutation of tokens/state. Multimodal/embeddings remainNone. Reject bad count/type/negative
metadata and duplicateIDs; empty invalidprompts stillreject. Mixed decode rows are native;
prefill rows retain byteidentical snapshots. No C1/C2 formula/slot/finite/oracle change.

Test disabled equivalence, allnative1 noiteration, mixed exactprefills, computedboundary,
publiclastprefilltoken, >1scheduled fallback, bad metadata, negativeprefilltokens, identity
lifecycle reuse and immutable mappings. New helper/testfiles ONLY, not imported by current
package. Compare localcost only; no automatic runtime wiring or NPUstage fromthese tests.

If G1pair establishes relevant gap, first quantify actualworker/CPU/runtime opportunity,
then freeze source-bound defaultoff integration AFTER09a6terminal/release: pass computed
and scheduled counts to the helper, preserve originaldefault/unsupported behavior and all
mechanism/source/isolation guards. Newmanifest/newcontracts/newroots and bounded integrated
correctness+matchedscreen required. Do notpool R15/R16 timings or call CPU pass fullHYPIC.
Quality catalog remains exact127x3 eacharm/nonthinking1024/default or thinking2048sameboth;
Paper-to-Ascend/29functional/lifecycle remainfullscope. StopOct17T06:48:09Z unchanged.
