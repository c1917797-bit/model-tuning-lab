# Dense090 opportunity diagnostic — source only, not candidate qualification

Repair1 preserves old090. Root cause was str(Path('/opt/...')) on Windows,
which serializes backslashes. The serializer now emits OUTPUT_POSIX and asserts
Path.as_posix consistency; the actual host consumes the original string through
the same output_argument before converting to Path. Cold real-I CLI positives
and Windows/relative/wrong-root negatives exercise that exact helper. New root,
owner label and absent output are repair1 identities; measurement is unchanged.

No remote/container/NPU execution. Existing075 CLI cannot directly do this:
host_pair.py requires candidate qualification and loops dense/candidate; its
protocol and readers fix2K/C1 only. This successor reuses its genuine052→025
Joint/Controller/create/observe/stop-retain implementation, not a new controller.
Only workflow is native-only, one model service and two independent profiles.

Frozen native common mode:Qwen3.6-27B/660,TP4,HF32OFF,sync/eager,PDCoff,mamba-none,
lazy safetensors, maxmodel17408/maxbatched16384/maxseq1, profilingOFF. Every profile
submits real tokenizer-built exact integer token IDs:input2048 then16384;
prefix1024 is merely submitted content, prefix cache remainsOFF. Each has one
untimed warmup1024 output, then one measured request1024 output, C1/ignoreEOS.
Total4requests/4096generatedtokens, not40/C16/formal performance qualification.
Same model remains loaded across profiles; second-profile order/warm-cache bias
is explicit. All raw warmup/request TTFT/duration/output/error fields are kept.

Original canonical benchmark49810/cba2... is reused. Its warmup helper alone
changes max_tokens1→args.output_tokens with an AST inverse. Measured function
and timer unchanged. Real token-ID INPUTS and source identity are saved; host
ownership/native-source BEFORE/AFTER barriers lie outside measured duration.
No kernel profiling, tensor capture, candidate math, or task scoring is enabled.

Native worker signal receipt verifies actual copied Qwen target equals original
Ascend native core and original solve callable/source, all4 actual SMI/PID/NSpid/
start/cgroup mappings, plus HF32 effective readback. It neither mutates the math
nor wraps per-token core. Only explicit owned signal computes these receipts.

Original075 resources retained:48GiB model/no-swap +.5GiB host +8GiB reserve =
56.5GiB initial ordinaryRAM. CPU8GiB/16.5initial. No32GiB trial inheritance.
Whole3600s including shared180cleanup; CPU120,canary180,startup900,each profile900
are maxima additionally clipped by original whole remaining budget. Sum of
these maxima is not a promise all fit; runtime fails closed rather than extends.
Output32GiB cap +8.5GiB opt initial reserve, independent Docker8.5GiB, read-only
rootfs/log16m×2/owned cache paths/sole output leaf are unchanged. Exact newopt
run root registered in external025; no output deletion or reuse. Deadline fixed
2026-10-17T07:02:13Z. MAIN must actually admit resources; source prep is not READY.

CPU preflight uses actual mountedsource/driver AST, command builder and sixcold
controls without Torch/native platform imports. Native parser is not faked or
claimed Devices[]-verified; real server parser executes after all4tiny and before
weight loading. Unknown CLI/import/device/source failure remains actual failure.

Consumer reports request-level TTFT/TPOT/wholewall/throughput/outputcounts and
failure rows. With complete fixed output, it reports only conditional loose
opportunity bounds: f=ΣTTFT/wholewall, max possible prefill-only throughput gain
f/(1-f) IF allTTFT can vanish with other costs unchanged; postfirst analogous.
TTFT includes more than solve, postfirst includes more than recurrent. These are
not exposed kernel fractions, measured candidate gain, or10% evidence. C1 cannot
be extrapolated to C16/16K candidate/task/graph. Failures never produce the bound.

COMMANDS090 sourceaudit precedes execution. MAIN exclusively schedules after
current owned loads release. SOURCE_MANIFEST and delivery provide full exact
closure; no candidate numeric certificate is required for this native-only
diagnostic. Model/algorithm/task qualification remains false even if it succeeds.
