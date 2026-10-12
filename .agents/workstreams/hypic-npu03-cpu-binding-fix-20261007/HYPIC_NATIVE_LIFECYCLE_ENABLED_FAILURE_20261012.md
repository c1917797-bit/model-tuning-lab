# Actual native HYPIC enabled lifecycle — terminal semantic failure

Source4429e35177979c874bf053ab29789e4773f39b22, native package manifest
dbac56e41b40214eff24ed305af77e18b50799a36b20e023f381a8dd3af05691.
No HYPIC implementation change or observer was used.

## Measured result
Controller exec-0000000000000141 terminated exit0 in563.354 seconds.
Service ready23:00:49 UTC, target returned23:03:37, exact owned release23:03:44
on2026-10-12. Three responses: two1-token warmups and one max2048 target.
The target had20414 input tokens,2048 completion tokens, finish_reason=length.
Frozen LongBench scorer extracted A; reference D. Semantic correctness failed
independently of the additional natural-stop requirement: removing that latter
condition would not make this response correct.

All four physical0-3 workers executed the target hot path and reported16376
skipped tokens each. Host PIDs2855581/2855582/2855583/2855584 map to container
PIDs270/271/272/273, engine244. These are historical identities, not current
occupancy claims.104 guard samples found no foreign process or probe error.
Source, pinned command/environment/binds, request IDs/payloads, worker identity,
engine activation and exact owned container/NPU/8223 release passed independent
checks. No NPU4-7 action or foreign-workload modification.

## Decisions and evidence
Frozen auditor exec0154 exited1 at the final semantic/natural-stop gate.
It is retained unchanged; no hot request is relabelled cold, no response omitted,
no higher output cap and no unchanged retry. Supplemental failure recorder0157
re-executes the frozen audit expecting this exact failure, separately recomputes
the score, and seals all original artifact hashes without rewriting originals.

External root:
 /cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-lifecycle-20261012-enabled
Failure audit:
 /cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-lifecycle-20261012-enabled-failure-audit.json
SHA256:94dd02e81529acedf25ace6979cc6b72a1e265505adf1ea2cf36afd29e7bf82a.

Read-only replay: python3 -B native_lifecycle_failure_audit.py
Decision FAILED_SEMANTIC_GUARD, NOT a canary pass or adoption success.
Disabled and uninstalled phases were not started under the frozen stop-on-failure
progression. Full delivery/rollback acceptance therefore remains incomplete.
A future recovery-only protocol must be explicitly distinguished from proceeding
as if this stage passed; do not change the failed contract or reuse its root.

## What this changes
Historical serial sample59 success did not guarantee this fresh output.
The response demonstrably traversed HYPIC on every worker; lack of activation
cannot explain this particular failure. This one sample is not a paired quality
comparison and does not isolate HYPIC, driver, sampler, truncation or context
semantics as a cause. Preserve r19 full LongBench REJECT_OR_QUALIFY and GSM8K PASS,
and do not rerun those suites.

Current environment/tokenizer/driver facts are recorded prospectively in
exp-20261012-hypic-native-lifecycle.yaml and original environment.json. They do
not repair missing historical r19 fields. Unknown firmware/topology/compiler
details remain explicit. Reuse the lifecycle source/activation/isolation evidence
as a supplement to relevant Skill cases, without automatic promotion.
Counts8 bounded verified/21 partial, main/remote not integrated; authentication
unchanged. Same-source descriptive performance still awaits its pending choice.
Fixed deadline08:47:14UTC Oct13 is unchanged.

## Next action
Complete the Skill failure/recovery evidence mapping. Review whether separate
bounded disabled/uninstalled recovery controls are warranted after a failed
canary; recovery is not adoption or performance escalation. Do not add another
numerical observer, repeat enabled sample59 unchanged, restart terminal roots,
or substitute an independent GDN test.
