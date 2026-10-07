# Native C1 failure and KVBuffer successor — 2026-10-07 07:45Z

## Goal check and decision

Long-term deliverable remains a training-free non-HYPIC Ascend plugin/
monkeypatch, >=10% same-stack/common-optimized dense E2E output throughput
at fixed1024 outputs, separate TTFT/TPOT, final thinkingOFF/max2048/normalEOS
LongBench-v2/GSM8K. Audit original no-loss and later <=1% task allowance
separately; do not relax numerical implementation gates. Medium goal is
actual mechanism/source/NPU/lifecycle/E2E/task evidence. Short goal is the
proved C1 observation gap and the actual runnable KVBuffer successor.

No accepted new throughput or quality result exists. HYPIC is historical
success, not this checkpoint's claimed result. DAMP deadline remains
2026-10-07T08:48:03Z; portfolio2026-10-09T11:17:31Z. KVBuffer preparation
does not start its formal24h timer. At DAMP cutoff preserve scoped failed/
inconclusive acceptance, never infer paper-wide impossibility from this guard.

## Actual native OFF-A result; no compressed failure attribution

The committed v2 code5083c8d23eb9ececcd7e739d86c83a5aaac9603e passed actual
no-device preflight, then MAIN ran one new physical4–7 TP4 C1/1024/33
eager/no-prefix/no-chunk common-observer diagnostic. Four workers reached
real NPUModelRunner.execute_model->_model_forward. OFF-A child exit1,
elapsed257.39457379002124s, first model exception:

`v2_observer.py:169 ValueError: native admission shape/time differs from fixed protocol`.

This predicate precedes off_native_bindings/turn_begin/recurrent raw capture.
OFF-B and ON did not run. MB0498/0499 full run-root rglob found precisely
four off-a/trace-rank-{0,1,2,3}/events.jsonl, all0B. The actual arm sets
DAMP_CAPTURE_OUTPUT=root/off-a. Source writes/flushes a started event before
the predicate, so this missing evidence must be retained as a separate
observation gap, not used to guess which predicate conjunct failed.

The frozen actual image model_runner_v1 SHA
94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968
and gdn_attn_builder SHA
42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16
were read from the stopped owned container MA0875. Source initializes GDN
CPU/np starts from real scheduled tokens; source alone does not supply the
failed run's actual values. No guard change is justified.

Next NEW opt-in v3 may retain independent exclusive/fsync pre-guard metadata
and preserve the exact old call/exception. MAIN must fully review, exercise
the actual software/entrypoint/source closure and freshly admit one bounded
run before the unchanged deadline. No unchanged deterministic v2 retry.

## Actual artifacts, ownership and RPC boundary

Artifacts remain outside Git under
/cache/cch/qwen36-damp-20261006/fixed-admission-c1-v2/:

- 06-off-a.log SHA0d372a17ff50ffb29f18eacd8840066d7b78f7a236955fdc5f6da8d420db67c1.
- 06-off-a.receipt.json SHAa64fffddfb87cd1aaf33bad8b8b2ed06c216593b4c5a09d4a5931fece4f75b92.
- FAILURE.json SHAf29b410ad0fe5bdaf5fa2dbba93b059ec6855a7f85dc599ca2a3bc10087bc79c.
- owned stop JSON SHA2eddb8cadf88e3159f2a14f9afeb61993aa21f74272bdd484cabe3fc83b0ded6.

MAIN MA0874 original readback saved at
/cache/cch/qwen36-damp-20261006/fixed-admission-MA0874-failure-readback-original.json
SHA1611bcdc5c4f13cb174b4eed91a130b38f1d1e93442b6be5499815aa651866f1.
It proves actual owned container
2e3f31a6b470aa747504746f6a4c55706be391136d8e021ed0ea32dcf8a33f0c
is stopped/Pid0/noOOM/ExecIDsnull with only physical4–7 mappings. Fresh
07:34:20.831977Z no compute PIDs/AICore0 and HBM4–7 idle2864/2861/2861/2861MiB.
No external/protected workload was signalled. Recheck before any new load.

Owned last cgroup peak19963609088B, failcnt0, through_observation and
model_process_completed=false is partial failed-diagnostic evidence, NOT
full-model budget proof or permission to reduce72GiB admission.

MA0862 later operation_get is aged/not_found. Saved literal response:
 /cache/cch/qwen36-damp-20261006/fixed-admission-MA0862-native-failure-original.json
 SHA19e945de997aa1b89bace8d5fa794308e245b9036e6612579e2fc439c4059d50.
Despite its misleading filename this contains ONLY the later NOT_FOUND query,
not original RPC execution/terminal/exit. Do not cite it as a terminal receipt.
The actual native failure is evidenced by child/log/readback above. Future
terminal persistence requires found+record+state+exit+route/target, not
terminal=true alone. Preserve this mistake rather than silently rewrite it.

## KVBuffer thin adapter: actual preparation, not NPU acceptance

MAIN applied exactly2 files under
projects/kvbuffer-parallel-ascend/tools/middle_batch_launch_v1:

- main_program.py SHA9c2ea05ff8e7910d84fc0ebb7e3d409118c30bf45d1971b00f11acb7ad641923.
- READY.md SHA6b0921f1cb1ca9a3db4f4cb192a6c5b497e8bb12b384391293695253b2fbba4a.

The NEW consumer uses the published source-bound v2 release helper to inspect
actual host-job cleanup, not fabricated original MA070e RPC. It pins helper
v2_release e60e399cc2710796d8e9c2b6c418bbf2063ba05f9a93e1b87d4a47e55844fb0b,
v2_contract666b0e8956cb371b8c03bcba8fa51dd4d4eec207108366e06590fe7a763e3815,
and original diagb1d6096bb5852a8de3c500e0519c1f95e78e6ea078e279c3f1c5a49929860c11.
Original49 sources plus those3, launcher and READY make actual54 closure.

MAIN MA0876 actually compiled exact landed source, invoked real --source-audit
(source54 and all trueT2–15 groups) and real defaultCLI (OFF/npu_executed=false).
Original saved:
 /cache/cch/qwen36-damp-20261006/kvbuffer-MA0876-landed-source-tests-original.json
 SHA fedc40cc4c0569b07f7f35978f1d497c2f26d43d4698de2e2cdf33f299d6be3f.
Agent MA0847 original57 software consumer checks and MA0872 actual readonly
Ref/import/Meta14/source audits are distinct scopes; no device proof.

Meta14 report
/cache/cch/qwen36-kvbuffer-parallel-20261006/preflight-middle-meta14-v1/results/report.json
SHA1c417ac0cae44e11842bd2a9434acd1cf537568f2bf19878ebb19dca64c65e75
remains no-device positive schema/Meta prerequisite, NOT device correctness.

Prepared disjoint physical groups:
4=[2,14,15],5=[7,11,13],6=[3,4,9,12],7=[5,6,8,10].
Protocol56 cases/8960feedback steps plus8 repeated reads, eager/NPUGraph,
wholestate/untouched/guard/alias and unchanged2e-6/.00303 gates.
Four nonprivileged1CPU/8GiB jobs+8GiBreserve require one summed40GiB/
CPU/disk fresh admission. MAIN actual identity/start/launch/ref inputs remain
pending; source-only/defaultOFF do not authorize Docker or timer start.
All TP4 model/formal performance phases are exclusive. Service integration,
same-dense E2E and task acceptance are distinct unfinished gates.

## Ready queue and lessons

Parallel agents prepare three useful scopes: NEW DAMP failure observation,
KVBuffer real producer/consumer/launch packet, and fullmatrix cost/E2E seam.
MAIN alone applies/shared Git/admission/Docker/NPU/normalpush. Protect0–3.
Preparation must test actual CLI/constructor/report/mount/source interfaces
before acquiring scarce cards, not only synthetic helper assertions.

The prior37/64 count is machine-verified9+9+10+9; partial step rows are not
complete. Do not revive39/64 or full64 PASS. Preserve valid source-bound cases
and first failures; no padded batch, dummy load, lowered gate or automatic
timeout extension. Idle cards need a concrete missing prerequisite and
runnable successor, not a claim of24/7 occupation.
