# Native HYPIC disabled recovery terminal — 2026-10-12

## Decision

FAILED_SEMANTIC_GUARD. Original enabled failure and r19 negative quality stay.
This is a completed recovery control, not missing test rows, not algorithm
adoption and not a quality-cause diagnosis. Do not retry the same control.

| Evidence | Enabled | Disabled recovery |
|---|---|---|
| Controller | exec-0000000000000141 | exec-0000000000000165 |
| Execution | exit0,563.354s | exit0,541.448s |
| Requests completed | 3/3 | 3/3 |
| Target prediction/reference | A/D | A/D |
| Target output/end |2048/length |2048/length |
| HYPIC evidence events |101; four-worker target hot proof |0 |
| Clean isolation samples |104 |100 |
| Exact owned release UTC |23:03:44 |23:29:26 |

The disabled control therefore proves switch-off without treatment events and
real request completion, but fails the frozen correct-natural-stop gate.
Removing the plugin is not proven to restore correct semantics. No uninstall
device stage was started; its root remains absent under the recovery plan.

## Independent evidence

Raw disabled root:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-lifecycle-20261012-disabled

Container:
724a542622bf36e764da14f179f6d965f7be368f2ca52527ff843757d757324f

Recovery plan checkpoint c5df4863; contract SHA256
10e9be3d1ed36b4c235788d2453d570b13e01ff653a6b6e583ab8d0193ffe877.
Frozen audit0171 independently passed the source/spec/request/rank/physical/
isolation/release/disabled-marker checks before failing its semantic gate.
New failure recorder0173 replays that exact failure without modifying/mocking
the frozen auditor. It independently rescored both controls and checked:
- identical normalized command, mounts and frozen fingerprint;
- only the enable switch differs after normalizing distinct evidence paths;
- matching recorded OS/architecture, driver digest and tokenizer/config digests.
Unrecorded firmware/clock/topology fields are not established by these matches.

Failure audit:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-recovery-20261012-disabled-failure-audit.json
SHA256 b528aef3639ab8d3229e8f9f34fa890fcf8a73010db7a24a4fea0b9155045c7f.
Disabled target SHA256
e78a900346d0c87b5f52a206ea4f637d806040c00b671393939be3219aaa4eef.
Disabled service log SHA256
bc78daaf414877ae461843561b4c583a3a46c60a25d10c700082f1780c143cfe.
All raw artifact hashes are bound in the failure audit.

Replay: python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/native_recovery_failure_audit.py

## Interpretation and remaining obligations

Enabling HYPIC is not necessary for this observed wrong/truncated response:
the off control also exhibits it. This is not proof that both implementations
are numerically equivalent, that HYPIC never affects quality, or that r19's
population loss is explained. The texts differ and this is one target response
per control, without repeated statistical power. No cap change, easier sample,
observer or independent GDN experiment is introduced.

Canary Skill failure classification and exact resource recovery have new real
evidence; package switch-off is exercised. Full delivery and all29 Skill
acceptance remain incomplete. Counts remain8 bounded verified/21 partial.
The original canary, original lifecycle and recovery protocols are immutable.
Uninstall/post-uninstall semantic verification remains unexecuted, not passed.
Any proposal to change recovery progression needs an explicit prospective
rationale separate from the unchanged failed decision; do not silently bypass it.

Current-source4429e35 performance still awaits the pending descriptive-only
choice after quality failure; no performance launch follows from this result.
Fixed deadline2026-10-13T08:47:14Z. Working-branch evidence only, not main/remote
integration. Unchanged Git authentication is not retried.
