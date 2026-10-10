# R19 LongBench response-prefix variability (post-hoc, read-only)

This diagnostic reads the already audited, immutable repaired-source r19
LongBench-v2 max-2048/c32 control and HYPIC-only roots. It does not rerun a
request, modify either root, or change the frozen `REJECT_OR_QUALIFY` quality
decision. The paired audit SHA256 is
`40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`.

For each of the 127 matched samples, compare the `response_text` strings of
repetitions (1,2), (1,3), and (2,3) within each arm. Measure the number of
identical leading Unicode characters before the first difference, yielding
381 within-arm comparisons per arm. Read every `samples/000.json` through
`samples/126.json` from these roots:

- Control: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-baseline`.
- HYPIC: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-hypic`.

| Pair | Control median prefix (characters) | HYPIC median prefix (characters) |
| --- | ---: | ---: |
| Repetition 1 vs 2 | 653 | 185 |
| Repetition 1 vs 3 | 636 | 219 |
| Repetition 2 vs 3 | 871 | 171 |
| All three pair types (381/arm) | 678 | 186 |

Median response length was 3815 characters / 936 completion tokens for
control and 3875 characters / 985 completion tokens for HYPIC, so the shorter
HYPIC shared prefix is not an artifact of shorter median outputs. Among the
23 control-correct/HYPIC-wrong matched responses, the median *cross-arm*
shared prefix was 253 characters. For sample 059, whose three control runs
all stopped naturally with the correct answer D and whose three HYPIC runs
all hit the 2048-token cap and were scored A, the matched cross-arm prefixes
were 339, 3, and 401 characters, respectively.

An additional read-only cross-tab joins all 381 matched scored rows to
`worker_hot_request_verified` by the scored API request ID plus the exact
eight-hex internal suffix, requiring four distinct worker PIDs for the
`proved-hot` label. It then intersects paired correctness with the
candidate's recorded finish reason:

| Paired outcome | Proved-hot: candidate length / stop | Unproved: candidate length / stop |
| --- | ---: | ---: |
| Both correct | 2 / 73 | 2 / 127 |
| Control wrong, HYPIC correct | 0 / 4 | 3 / 8 |
| Control correct, HYPIC wrong | 7 / 1 | 9 / 6 |
| Both wrong | 13 / 34 | 31 / 61 |

The rows sum to 134 proved-hot and 247 unproved requests, matching the frozen
audit; 16/23 paired losses hit the candidate length cap, including 7/8
proved-hot losses. Sample 059's first scored request had four-worker hot proof,
while its other two scored requests were unproved; all three were wrong and
length-limited. Thus the observed wrong-and-length-limited pattern is not
confined to the unproved stratum. These post-hoc, outcome-selected groups
cannot establish whether truncation caused the wrong answer, whether hot
execution caused early response divergence, or whether unproved requests were
actually cold.

For a separate post-hoc stratum check, join each candidate scored API request
ID to `worker_hot_request_verified` internal IDs by removing their eight-hex
suffix and require four distinct worker PIDs. This reproduces 134/381
proved-hot scored requests. Across each within-sample repetition pair, the
control/HYPIC median shared prefixes were 697/203 characters when both
candidate requests were proved hot (89 pairs), 679/205 when neither had a
four-worker event (202 pairs), and 678/168 for mixed pairs (90). The
"unproved" stratum is **not** a proven cold path. Earlier divergence is
visible in all three observed strata; this is not a causal activation test.

Interpretation is limited: under this workload, HYPIC repetitions diverged
earlier in text than control repetitions, consistent with the separately
observed answer variability and increased length-cap rate. A character
prefix is not a token-level numerical-difference trace. These descriptive,
post-hoc comparisons do not identify the first differing token's kernel,
establish HYPIC materialization as the cause, prove a truncation mechanism, or
license a quality/adoption reclassification. Any repair must be prospective,
source-matched, and independently tested; do not change the old roots or
transfer older-source performance gains to repaired-source r19.
