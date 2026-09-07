# Maintainer Takeover Runbook

Use this runbook with `AGENTS.md`, `.agents/HANDOFF.md`, the relevant
branch-local workstream handoff, and the narrow maintainer skills.

## 1. Start-of-turn sequence

1. Read `AGENTS.md`.
2. Read `.agents/HANDOFF.md`.
3. Run `git worktree list --porcelain`.
4. For every active `work/*` tree, read its `task.json` and `HANDOFF.md` before
   touching claimed files or resources.
5. Run `git status --short --branch` and `git log -8 --decorate --oneline`.
6. Select only the narrow skills needed for the task.

For performance work, always include:

- `ascend-npu-environment-orientation`
- `ascend-inference-tuning-loop`
- `ascend-benchmark-evidence`

## 2. Current resource warning at this handoff

At the 2026-09-07 live check, the unrelated
`vllm-ep-310p-research-910b-monitor` container was not an idle monitor. It
ran a TP2/EP W8A8 Qwen3-30B-A3B vLLM service on physical NPU0/1 while mapping
device nodes NPU0-7. It is not part of either Qwen3.5 workstream and blocks a
safe NPU0-3 TP4 launch. Do not stop it without explicit owner/user
authorization; re-check its exact container ID, command, process tree, and NPU
workers because this snapshot can expire.

The Qwen3.5 performance workstream may use physical NPU0-3 only after an
exclusive live lease is proven. The Qwen3.5 Paper-to-Ascend workstream
currently owns no NPU or port lease. NPU4-7 remain excluded from both tasks
unless a future explicit lease changes that boundary.

Historical resource snapshot follows.

At the 2026-09-04 live check:

- `qwen38_eval_baseline` was serving on `127.0.0.1:8200`.
- physical NPU4-7 were occupied by its four TP workers at about 29 GiB process
  memory each and roughly 31.8 GiB HBM usage/device;
- `qwen38_eval_client_run1` was running;
- NPU0-3 had no NPU processes;
- port 8100 was not listening;
- ordinary `MemAvailable` was about 64 GiB;
- `Hugetlb` remained about 1.9 TiB.

This is **snapshot evidence, not a permanent reservation**. Re-check live state
before every action. Do not interfere with NPU4-7 while the prefix-cache
workstream owns that resource.

## 3. Live environment orientation

Capture at minimum:

```sh
hostname
uname -a
docker ps
npu-smi info
ss -lntp
grep -E '^(MemTotal|MemAvailable|Hugetlb):' /proc/meminfo
```

For the historical 1 GiB HugeTLB pool, inspect the 1 GiB sysfs entries rather
than relying only on the default 2 MiB `HugePages_Total` fields in
`/proc/meminfo`.

Also record:

- model/tokenizer revision or content hashes;
- dtype/quantization;
- vLLM and vllm-ascend;
- PyTorch and torch-npu;
- CANN, driver, firmware;
- container image digest;
- NPU model/count/topology;
- CPU/NUMA affinity;
- full launch command;
- exact target NPU process proof.

Substantive environment drift requires a new baseline.

## 4. Git/workstream routing

Repository policy is `commit_implies_push` with non-trivial branch-first
routing.

Use direct `main` only if every direct-primary exception in
`.agents/git-policy.yaml` holds. Performance evidence, shared handoff truth,
multi-file changes, long-running work, and protected paths require a named
`work/*` branch and independent worktree.

Before implementation:

1. fetch origin;
2. prove primary divergence `0 0`;
3. create one stable task id/work branch/worktree;
4. declare claims and freeze constraining hashes;
5. create the branch-local start state;
6. validate;
7. commit and push the remote start checkpoint;
8. verify local HEAD equals its workstream upstream.

Do not begin protected-path/product edits before step 8 succeeds.

## 5. Experiment contract

Use IDs such as:

```text
exp-YYYYMMDD-name
```

Each experiment record must predeclare:

- bottleneck hypothesis;
- objective;
- one primary variable;
- correctness guardrails;
- acceptance threshold;
- regression threshold;
- abort conditions;
- benchmark command and fixed workload;
- warmup;
- repetitions;
- rollback.

Expected lifecycle:

```text
planned -> baselined -> attempted -> verified -> measured -> decided
                                                        -> recovered (if needed)
```

Commit and push each coherent tuning stage. Preserve failed/rejected evidence;
recover failed active code in a later checkpoint rather than rewriting history.

## 6. Benchmark evidence gate

Do not claim an improvement until baseline and candidate are apples-to-apples.

Cover as applicable:

- cold: load, compile, first request, first token;
- steady: throughput, TTFT, TPOT, latency distributions;
- boundary: batch, context, concurrency, memory/OOM;
- lifecycle: restart, cache, long run, recovery;
- resources: HBM, NPU utilization, CPU, RAM, I/O, power, process count.

Use repeated runs and report dispersion/tails (for example p50/p95/p99) rather
than a single lucky measurement.

## 7. Profiling workflow

For the current vLLM-Ascend stack, first use its integrated
`torch_npu.profiler` path. The source baseline uses Level1 + PipeUtilization.

Rules:

1. warm first compilation/JIT outside the measured window;
2. profile Prefill and Decode separately unless comparison is the purpose;
3. keep the capture bounded;
4. immediately validate output completeness;
5. keep large raw traces under `/cache`, not Git.

Inspect in this order:

1. timeline gaps and serialization;
2. per-step latency;
3. top operator total time;
4. top kernel total time/call count/shapes;
5. AIC MAC / MTE / AIV pipeline ratios;
6. HCCL communication and compute overlap;
7. CPU/NUMA/scheduler correlation;
8. map the hot path to `vllm-ascend`, `ops-transformer`, or a system setting;
9. compare with `cann-recipes-infer` when useful.

## 8. Artifact policy

Put large raw artifacts in persistent `/cache` storage:

- profiler raw trees;
- trace JSON/DB bundles;
- CANN dumps;
- large benchmark logs;
- model/data payloads.

Commit only maintainable evidence:

- environment snapshot;
- commands/config;
- aggregate tables;
- hashes;
- artifact paths;
- compact analysis;
- experiment decisions.

Never commit credentials, `.ssh`, shell history, private certificates, model
weights, datasets, or generated multi-GB outputs.

## 9. Hugepage safety gate

Do not reduce the 1 GiB HugeTLB pool until all of the following are proven:

- current hugepage consumers are identified;
- OVS/DPDK/VNF dependency is understood;
- only genuinely free pages are targeted;
- network/workload health checks are prepared;
- per-NUMA before/after state is captured;
- rollback is defined.

The fact that hugepages are free inside the pool is not approval to release
them.

## 10. End-of-turn handoff gate

Before leaving non-trivial work:

1. update branch-local HANDOFF with exact state and resume point;
2. update durable lesson/runbook only when future behavior actually changed;
3. run required validation;
4. commit and push according to policy;
5. leave a clean worktree or an explicit recovery command;
6. if integrating, reconcile global `.agents/HANDOFF.md` on the final target
   tree and bind validation to the exact source/target commits.

A new maintainer should be able to answer from Git alone:

```text
What is integrated truth?
What workstream is active?
What resources does it own?
What succeeded?
What failed and why?
What is only a known risk?
What validation actually ran?
What is the next safe high-value action?
```

## 11. Paper-to-Ascend applicability gate

Before opening a paper implementation workstream, answer these in Git:

1. **Architecture fit:** does the installed checkpoint actually contain the
   mechanism the paper needs (for example MTP head, MoE experts, quantization
   metadata, sparse structure, or compatible attention form)?
2. **Inference-time fit:** can the method be tested without retraining under the
   user's current scope? If retraining is required, stop unless explicitly
   authorized.
3. **Bottleneck fit:** what measured Decode/Prefill/kernel/system bottleneck is
   the paper expected to improve?
4. **Production path:** does the installed vLLM/vLLM-Ascend/CANN stack already
   expose a usable implementation seam? Prefer built-in exact paths before
   authoring new kernels.
5. **Decision scope:** predeclare whether the first result is router/operator,
   block, or full-model evidence; never overstate a narrower result.
6. **Resource isolation:** reserve a concrete NPU/port/CPU set and prove it live
   before baseline and candidate runs.

For the current dense target, the active Paper-to-Ascend candidate is exact
speculative decoding using the checkpoint's built-in Qwen3.5 MTP head. Dynamic
MoE remains a superseded audit exemplar, not an active optimization path.
