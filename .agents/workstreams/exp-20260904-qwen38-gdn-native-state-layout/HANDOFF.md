# Qwen3.8 GDN fused-prefill operator optimization handoff

## 0. Status

- Workstream: `exp-20260904-qwen38-gdn-native-state-layout`.
- Branch: `work/exp-20260904-qwen38-gdn-native-state-layout`.
- Primary target: `chicaihong01`, physical NPU4-7, TP=4, endpoint `127.0.0.1:8210`.
- Git policy: `commit_implies_push`; every coherent validated checkpoint must be pushed to this workstream branch, never directly to `main`.
- Current runtime: `qwen38_gdn_fused_candidate` is the active candidate container; `qwen38_2k40_baseline` is stopped and retained for rollback.
- Current candidate is healthy on port 8210 at the latest verified checkpoint.
- Candidate performance on the final raw/natural workload has not yet been accepted or rejected; do not claim a speedup yet.

## 1. North Star

Improve Qwen3.8-27B inference with real operator/algorithm changes, not parameter-only tuning. The current hypothesis replaces the multi-kernel GDN prefill path (`chunk_scaled_dot_kkt`, `solve_tril`, `recompute_w_u`, chunk forward/state handling) with `torch_npu.npu_chunk_gated_delta_rule` while preserving correctness.

## 2. Current Focus

Run a matched A/B of the fused GDN candidate against the frozen raw business workload:

- dataset: `/home/mtuser/cch/query_rewrite.jsonl`;
- source SHA256: `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`;
- 357 raw `question` strings, no padding/truncation/2K snapshot;
- `answer` is empty for all 357 rows, so this dataset is a performance workload, not a labeled quality set;
- model output is natural generation to stop/EOS; no fixed 40-token output, no `min_tokens`, no `ignore_eos`, no artificial 8192 cap;
- concurrency/batch points: `1, 5, 8, 16`.

The final raw-natural baseline is frozen under:

`/cache/austinov/eval-runs/exp-20260904-qwen38-gdn-native-state-layout/raw-natural-baseline-v4`

All four baseline points completed 357/357 with zero errors and all `finish_reason=stop`:

| batch | wall_s | req/s | out tok/s | total tok/s | TTFT p50 ms | E2E p50 ms |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1590.26 | 0.2245 | 31.20 | 498.39 | 442.2 | 3599.7 |
| 5 | 529.65 | 0.6740 | 94.60 | 1497.31 | 575.4 | 5876.7 |
| 8 | 413.78 | 0.8628 | 123.11 | 1918.62 | 591.4 | 7030.7 |
| 16 | 326.93 | 1.0920 | 149.57 | 2422.04 | 662.3 | 10976.6 |

Baseline JSON hashes are in the experiment YAML. Average natural output is roughly 137-143 tokens/request; p50 is about 110-111 tokens.

## 3. Recent Progress

- Prefix caching was measured earlier and rejected: it caused material wall/throughput regression on the prior controlled workload. Preserve commit `615699d` and do not retry it as a claimed win without a new hypothesis/workstream.
- The user rejected parameter-only tuning and explicitly required operator/algorithm work.
- Profiling identified GDN prefill as a practical mutable hotspot. Upstream commit `77d13e2c0bfa9862b711b68811889e36b9d56aca` adds the fused CANN/torch-npu GDN prefill algorithm. Current `torch_npu 2.10.0.post4` exposes `npu_chunk_gated_delta_rule`.
- Backport patch is `patches/qwen38-gdn-state-layout/77d13e2c0-fused-gdn-prefill.patch`, SHA256 `d16712f909810c1dd1a7704d0a7d53434032f800cb2af1f9562d11475489a76e`, introduced in commit `c1ff598`.
- Candidate startup initially reapplied the patch on restart and failed with `patch does not apply`. Commit `6ca1780` made activation restart-safe by detecting the already-present fused path before applying.
- Final raw/natural benchmark protocol was reached only after superseding earlier 2K->40 and fixed-40 attempts. Commits `66d358f`, `81aa086`, and `78ff0e8` record those protocol corrections; do not mix their earlier artifacts with the final v4 baseline.
- Final raw/natural baseline was frozen and pushed in commit `b725539`.

## 4. Current Action

Verify the running fused candidate is really executing the fused GDN path (not silently falling back), then run the exact same raw/natural `1/5/8/16` workload and correctness checks. Record raw artifact hashes and compare each batch point against the frozen baseline above.

## 5. Next Actions

1. Confirm `curl http://127.0.0.1:8210/health` returns 200 and NPU4-7 workers belong only to `qwen38_gdn_fused_candidate`.
2. Prove fused-path activation with runtime evidence (operator/profiler/kernel evidence preferred; source-code presence alone is insufficient because the upstream path can fall back after probing).
3. Run deterministic correctness comparison against the saved baseline correctness artifact where applicable; retain existing general-suite regression evidence because `query_rewrite.answer` is empty.
4. Run candidate raw/natural benchmark at concurrency `1,5,8,16`, 357 requests each, with no stale client containers/processes before each measured point.
5. Summarize wall, req/s, input/output/total tok/s, TTFT p50/p95/p99, E2E p50/p95/p99, errors, finish reasons, and output-length distribution. Store raw files externally and hashes in Git.
6. Decide `accepted`, `rejected`, `inconclusive`, or `failed` using the predeclared threshold: >=5% wall or output-token-throughput improvement at one or more matched points with no material regression at the others and correctness passing.
7. If rejected/failed, stop candidate, start `qwen38_2k40_baseline`, prove health/ownership, checkpoint `recovered`, and preserve the failed candidate commits/history.
8. If accepted, checkpoint `verified`, `measured`, and `decided`; do not merge to `main` without the serialized integration gate.

## 6. Validation Commands

```text
cd /opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-gdn-native-state-layout
./scripts/validate-mst.sh
git diff --check
git status --short --branch
git log -8 --decorate --oneline
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8210/health
npu-smi info
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E '^qwen38_(gdn_fused_candidate|2k40_baseline)'
```

## 7. Do Not Do

- Do not revert to the 2K->40 snapshot or fixed-40 output protocol; those were explicitly superseded by the user.
- Do not invent output length from the empty `answer` field; use natural model termination.
- Do not compare candidate data with any invalid/overlapping-client run. Cancellation of an AgentWeb operation does not guarantee a spawned Docker client stopped.
- Do not touch external NPU0-3 workloads. The experiment owns physical NPU4-7 only.
- Do not treat source-code presence as proof the fused op ran; collect runtime evidence.
- Do not restart the candidate with a non-idempotent patch command; `6ca1780` is the restart-safe activation checkpoint.
- Do not force-push, squash away failed history, or push this workstream directly to `main`.
- Do not claim `query_rewrite` accuracy; all 357 `answer` fields are empty.

## 8. Recovery / Resume Commands

```text
cd /opt/host/vnf/austinov/worktrees/exp-20260904-qwen38-gdn-native-state-layout
git status --short --branch
sed -n '1,320p' .agents/workstreams/exp-20260904-qwen38-gdn-native-state-layout/HANDOFF.md
sed -n '1,320p' .agents/experiments/exp-20260904-qwen38-gdn-native-state-layout.yaml
docker ps -a --format '{{.Names}} {{.Status}}' | grep -E '^qwen38_(gdn_fused_candidate|2k40_baseline)'
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8210/health
npu-smi info
```

Rollback to the preserved original-GDN service if the candidate is unhealthy or rejected:

```text
docker stop -t 30 qwen38_gdn_fused_candidate
docker start qwen38_2k40_baseline
```

GitHub smart-HTTP from this host is intermittently unreliable. A localhost native tunnel to another peer has been used successfully; when needed, Git/libcurl can route only the current command through it with:

```text
git -c http.version=HTTP/1.1 -c http.curloptResolve=github.com:443:127.0.0.1 ...
```

Do not leave permanent `/etc/hosts` overrides.
