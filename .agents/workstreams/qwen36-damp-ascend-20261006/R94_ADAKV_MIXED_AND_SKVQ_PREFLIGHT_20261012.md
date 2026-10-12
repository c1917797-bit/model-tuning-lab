# R94 actual failures and repair dispatch

Active authority remains R87, ending 2026-10-13T08:06:34Z. No clock reset, gate relaxation, accepted performance or final task result.

## AdaKV current dense007: model warmup failed, not a performance measurement

Actual Ma exec-0000000000000053 completed exit1 in 464.077 seconds. TP4 weights loaded and the server reached health200; the warmup requests then triggered an EngineCore failure. The measured fixed1024 requests never started. Do not derive throughput, TTFT or TPOT from this run.

The first exception is adakv_grouped_service/evidence.py attention_forward line131: unsupported graph/attention state. The later computed timeline rewind occurred after that incomplete forward and is not established as an independent primary fault. Original observer accepts PrefillNoCache, DecodeOnly and ChunkedPrefill, but not PrefillCacheHit. The preparer's retained scheduler-dump/native-source analysis identifies a legitimate mixed new-prefill and existing-decode path using that enum even with prefix caching OFF; a new narrowly admitted mixed adapter and independent NPU test are required. Merely adding an enum to the allowlist is insufficient because candidate prefill dispatch must also initialize the correct causal output.

Exact original directory: /cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_adakv_current_prepare/R87/run-adakv-current-dense-main-20261012-007.
HOST_RESULT.json15398/fe8f7bca4d8cb218d9cfde8948a89ae765bc5ec466cf9ef71b206130afbf05aa.
server.stdout124917/fb648efe2f45507c97e6da0300f59d6cf2a7d76ade2e4ba111f758ac077786b8.
server.stderr5872/4eff15bd69e7aa64571978f2811d74267880e470ef8ec136be0de5e68bc86775.
Terminal and independent-release envelopes are saved under MAIN-adakv007-currentboot-canary-001 as DENSE007_TERMINAL_ORIGINAL_MA0053.json and DENSE007_RELEASE_ORIGINAL_MA0071.json. The latter proves owned CID1e5ee660... stopped-retained/Pid0/noExec/noOOM, and physical4-7 without processes/HBM2861,2860,2859,2860MiB at that observation. It does not establish continuous30-minute utilization. No protected0-3 mutation.

## SKVQ012: actual no-device regression failure

MAIN deployed the source-reviewed012 snapshot without changing011. Ma007c completed0 with literal175320-byte manifest14c0a06e448aea963480b1be780af6a14cee193903f56e664c5a77bfd0319cdd and complete602-source readback. Actual same660-image Devices[] CPU104 Ma007e completed1 in25.983 seconds. The first failing test is test_replay_adapter.Tests.test_private_clock: its old R67 authority fixture is rejected by the actual R87 clock contract. This is a test/admission-contract defect, not a measured SKVQ numerical or performance failure.

Original RESULT is /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-skvq-r87-cpu104-main-001/RESULT.json,141688/2c4353bd481b047576bc26705fdd5275393e9213288847ea25b1c619a0700156. The full failed child is cpu-preflight/source104-1791839857479101500.json,19099 bytes. No complete104 PASS or NPU qualification is claimed. Owner prepares a new source-bound fixture repair; old012 and its failed output remain immutable.

## Successors and scheduling

AdaKV owner prioritizes a forced production-relevant mixed-prefill/decode NPU smoke with independent references before another measured model run. SKVQ owner repairs the exact stale test contract, then resumes its current production smoke. KIVI owner continues the actual006-source-derived R87 eager640 successor while graph-specific missing seams remain separate. Three parallel preparers are active; MAIN alone admits physical4-7. Four-card paired timing remains exclusive.

Single positive candidates below10% may be retained for complementary combination under R87_COMBINATION_AUTHORITY_20261012_2111.md. This is not a combined success claim. Current idle gap is preparation/adaptation readiness, not proved external occupation; no dummy utilization.
