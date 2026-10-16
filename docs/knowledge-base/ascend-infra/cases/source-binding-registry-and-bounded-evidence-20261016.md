# Runtime-source binding, plugin lifecycle and bounded evidence (2026-10-16)

## Scope and current acceptance

Qwen3.6-27B at /cache/efim/Qwen3.6-27B, hybrid Qwen3_5, Ascend910B4,
vLLM-Ascend0.23/CANN9.1. The old48h window ended without final acceptance.
The separately authorized24h ends2026-10-17 07:02:13UTC. No result below proves
the >=10% three-pair model throughput or final task-quality requirement.

## Actual evidence and causal attribution

- DeltaLog061 actualNPU16 completed40records and63sidecars. The owner remained
  failed: the independent domain reader rejected two runtime-to-host mappings
  missing from its source readset. Preserve that failure, not a paper no-go.
- Recovery066 consumed the same saved raw in an owned same-image Devices[]
  container. Its SOURCE_MANIFEST was4943101bytes,
  db71c3a8e456e9e7fdbf611d3b260906e90edb6f916dfe2406d791d697ca69a9.
  DOMAIN066 was329005bytes,
  c77cb818b0c62fd1650cd28f5ae5a859fc0a8c80141216d3943b1b864e0a3e52.
  All40domain rows and63sidecars passed with no failures/missing evidence.
  The original strict failure and complete_proof=False remain unchanged.
  This is a successful independent diagnostic recovery, not a new160/model
  qualification or task-accuracy result. No NPU rerun was used for recovery.
- MXR065 actually passed its13 CPU tests and four tiny device canaries, then
  failed architecture inspection before model execution: load_general_plugins
  invoked the installer in a registry subprocess before native recurrent-op
  registration. Every created container was stopped/retained and released;
  the recorded cgroup OOM count was0.
- MXR067 implements full installation deferred to a real source-checked Qwen
  first-core instance, with explicit official-op and later48-instance evidence.
  Its full long experiment was NOT started: safety review rejected an allocation
  near227.5GiB on a filesystem with about228.5GiB free. Do not bypass this
  rejection. MXR068 is a separate129-token smoke with a complete3GiB cap and
  initial32GiB-free condition, not an indirect start of the rejected long run.
- Storage capture069's first actual attempt rejected a genuine completed
  failed-operation snapshot because it incorrectly required wrapper ok=True.
  The actual09c4 response had terminal=True/status=completed, exitCode=3,
  transport peer_direct/inner ok=True, but wrapper ok=False. Preserve the
  failed capture leaf; fix the precise terminal predicate in a successor,
  without changing the observed snapshot or declaring the old command passed.

## Reusable decisions

1. Regression-test the validator using actual producer/report shapes, including
   runtime path mappings, readset membership and cross-process source identity.
   A missing evidence field does not establish a tensor or algorithm failure.
2. Plugin registration runs in API/inspection/worker contexts. Execute a genuine
   cold entrypoint check; distinguish registration from real worker installation.
   Default-OFF, real first-instance dispatch and native operator identity remain
   independently verifiable. Do not fake a worker receipt in a registry child.
3. Read the actual producer and consumer predicates. Diagnostic False fields can
   deliberately preserve scope while permitting a later diagnostic stage;
   never infer readiness or permanent failure from a field name alone.
4. Design evidence coverage and retained bytes before dispatch. Full intermediate
   dumps are an experiment choice, not a universal paper requirement. A smaller
   preregistered smoke has its own scope; it does not inherit the old full-matrix
   certificate or lower the final performance/quality acceptance.
5. Distinguish completed process from successful computation using the actual
   operation contract and source-bound exit/owner evidence. Do not suppress
   missing/running/transport/identity failures to make a seal pass.
6. For verbatim source transport, preserve final newlines. Windows Get-Content
   output added a terminal blank line to one capture tool; deployed-byte hashing
   caught it before execution. Use exact text extraction and compare full bytes,
   not merely AST or patch success.

## Workload update and next gates

The user explicitly permits2K/16K inputs. Prepare distinct2048/16384-token
profiles, fixed1024 output, same dense/candidate stack/input/concurrency/common
policy, profilingOFF and separateTTFT/TPOT. Do not require32K/40K as a predecessor.
129 tokens is a correctness smoke only. C1 screening does not proveC16 behavior.

Next: finish the source/readset and bounded storage repair, then actual
same-source CPU/Meta ->16 ->160 for DeltaLog; actual first-core/48-layer smoke
for MXR; production-relevant2K/16K correctness and matched model performance;
promising three-pair performance and GSM8K/HumanEval/MMLU smoke->full,
thinkOFF/max2048/normalEOS. HistoricalHYPIC is not a new result.

## Subsequent actual gates (same day)

- MXR068 actual operation exec-0000000000000a2d exited1 after1.71s,
  before any container was created. The retained first error was
  unowned physical compute must be idle; contemporaneous SMI showed external
  kernel-eval processes on physical5. This is admission/resource failure,
  not a model numerical result. Its output001 remains unchanged.
- Storage069-repair1 capture002 really completed (operation0a31, exit0).
  EVIDENCE069.json is6070bytes,
  eab70137ec0763daa93dbd525f28a08b6ed4ac6ae83299c095c8c8162bbc82fc.
  It wrote5436230bytes under the50MiB capture cap without changing the ledger.
- The repair1 binder0a35 completed with SOURCE_MANIFEST52969bytes,
  b9cb456d960072d8e6730bb5307dcabfc83b3ad7bffd9d3476d9b92220048f21.
  Sourceaudit0a3c verified207 source dependencies. An earlier sourceaudit CLI
  attempt0a38 rejected a CPU-list string where this CLI requires an integer;
  it never created an experiment output. Corrected arguments were derived
  from run031.py/host.py, not from a guessed affinity convention.
- Actual same-image Devices[] CPU gate0a40 completed in112.245s, exit0.
  Host owner1386bytes/54e38927342aa9c4e443cbde798768e46a421afc3fb1ba7c8e220aa3842ed3cd;
  stage5231bytes/cdc6cc7b89e5720176fc7f6274f7d411958549cb408ee565839cb8c9268d780f.
  Both actual051 production/debug libraries loaded; Meta covered13/14
  arguments and batch1/16. Primary/secondary errors are empty and the
  no-device container is stopped/retained. This does not grant NPU correctness.
- NPU16 operation0a49 has been dispatched after a fresh physical5 idle check.
  Its terminal and numerical outcome are pending at this checkpoint; do not
  infer success from dispatch or an operation being live.

External-process handling retained no-action refusals when the exact PID/start
departed or scope validation failed. No external signal or container stop has
been proved successful here. Recheck fresh ownership; never target stale PIDs.
