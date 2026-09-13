# Model-switch validation contract

Latest user choice (2026-09-13): Qwen3-32B BF16 -> Qwen3.8-27B BF16.
Not NVFP4 or Qwen3.5. This supersedes historical QUALITY_PROTOCOL.md for this task.

## Comparable conditions

- Control /cache/austinov/Qwen3-32B; candidate /cache/austinov/Qwen3.8-27B.
  Pin source revisions, weight/index hashes, each model's native tokenizer and
  template, actual launch argv, image digest and device/software fingerprints.
  A model card or served alias alone does not prove official provenance.
- Official unmodified vLLM-Ascend 0.23.0, BF16, MTP/speculation/quantization off.
  Owned disposable containers; read-only source/model mounts. Never overwrite
  host/framework/image site-packages or stop other owners' containers.
- Primary comparison TP8/DP1 on the same eight 910B4 cards. TP4/DP2 is a separate
  deployment comparison, not a relabelled TP8 result. TP8 is not claimed optimal.
- Identical semantic messages, native templates, enable_thinking=false,
  temperature=0, seed=1024, output cap4096, common context limit40960 for this
  short-workload test, max_num_seqs16, max_num_batched_tokens32768. Record
  architecture-required config differences, token counts, cache policy, graph
  mode, CPU binding and warmup. Never force shared tokenizer bytes across models.

## Execution

1. Recheck live NPU0-7 processes/device holders, all containers' state and device
   declarations, port10010, MemAvailable>=48GiB and resource lease. If another
   owner uses any card, stop our launch/testing, not theirs. Old snapshots cannot
   grant a lease. No unconditional old-controller cleanup/restart commands.
2. Run paired32 chat diagnostics with v4 and separate warmup. Save raw responses
   and SSE outside Git. Check /tokenize vs usage counts and eight-rank execution.
   For empty output, compare streaming vs non-streaming before blaming weights.
3. Resolve empty/whitespace outputs, unexpected reasoning, truncation, request
   or parser failures before full-matrix expansion. Preserve failures.
4. Full357 query_rewrite, c1/c5/c8/c16, three measured repetitions per arm,
   balanced order AB/BA/AB, fresh lifecycles and identical warmup. Resume exact
   valid cells only; changed protocols/bytes use new artifact identities.
5. MMLU57 subjects/14042 test, 5-shot log-likelihood accuracy; GSM8K1319 test,
   pinned harness5-shot strict-match primary/flexible-extract secondary;
   HumanEval164 tasks, one deterministic completion, pass@1. Freeze task YAML,
   token limits, template application and evaluator revisions before generation.
   Resume by item identity. Generated Python executes only in the restricted
   network-disabled CPU sandbox, never host or NPU serving container.
6. Save per-item paired scores. Report paired-bootstrap95% intervals with fixed
   seed (MMLU subject-stratified), MMLU micro and macro averages. HumanEval's164
   tasks give coarse resolution; wide intervals are inconclusive, not parity.

## Metrics and acceptance

TTFT is request start to first content/reasoning-bearing event, never role,
usage or finish-only events. Reasoning fails this no-thinking protocol.
TPOT is client-observed (stream_end-first_token)/(usage_output_tokens-1),
undefined for <=1 token; disclose excluded counts. It is not kernel timing.
Report per-cell P50/P95/P99, repetition spread, E2E, output lengths, request/token
throughput and peak memory. Do not interpret shorter/empty outputs as faster
computation. Fixed-length diagnostics, if used, are a separate secondary test.

The business dataset has no usable reference answers. Save paired outputs for
blinded owner review of intent preservation, correctness and formatting.
Automated string equality or benchmark totals cannot establish business parity.
Until the owner specifies acceptable quality loss and required performance,
report conditional recommendations and uncertainty, not an invented threshold
or automatic production migration.

## Existing results

Raw /v1/completions historical cells remain original-protocol references only;
server chat-template defaults do not render raw prompts. Historical paired chat
sentinel used Qwen3.8, but92 empty candidate outputs and v3 finish-event timing
make it diagnostic/failure evidence, not a passed switch gate. Keep it unchanged.
Offline dataset checks and58 executable text tasks passed; these are not model
quality scores or v4 NPU performance results.
