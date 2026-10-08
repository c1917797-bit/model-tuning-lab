# Runtime monkeypatch delivery: real HYPIC task, partial case

Tested against locally tracked main
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`:
`runtime-monkeypatch-delivery/SKILL.md` blob
`5ac9f8b07d8e092dcba7e1b0cfd5423469534666`,
delivery reference blob `302cf8cde20e7fda93b2972bbf1e5bab9fd81dde`,
registry blob `2611864bbcf719d57920aae03ff9eb85521526b4`.
The main Skill instructs
`scripts/validate_monkeypatch_package.py <package-dir>`, but
`git cat-file -e origin/main:scripts/validate_monkeypatch_package.py`
returned exit 128: no such path in that main tree. This is a reproducible
workflow defect, not a failed HYPIC runtime result.

The real task was the r12 HYPIC Qwen3.6-27B BF16 TP4 plugin source
`c12060cd47e7575ead059983d7a8bb4704165c98` mounted read-only into
official image
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
on physical NPU0–3. The independent raw audit verified 19/19 samples,
57/57 scored responses, 52/57 four-worker hot proofs, 279 clean guard
probes, and exact owned container/port release. Five scored requests had
no four-worker hot proof. The source's directory-rebuild regression had
passed focused CPU tests, but r12 does not isolate that branch's NPU
causal effect. See HOTPATH_CACHE10R12_TERMINAL_AUDIT.md.

| Main delivery gate | Observation and boundary |
| --- | --- |
| Static package identity | Main lacks the named validator. This branch adds a standard-library static validator, binds patch/loader/launcher SHA256 in the template and passes six positive/negative tests. The r12 plugin was not packaged in that manifest shape; this repair is not retroactive package acceptance. |
| Official image and live source | Image digest, read-only source commit, worker PID map and physical cards were captured. No completed manifest binds the imported live object/source SHA and package bytes. |
| Enabled and disabled control | Enabled r12 emitted request-local four-worker proof on 52/57 scored requests. No same-identity disabled control proves marker absence while requests succeed. |
| Exact-shape, stress and semantic gates | One 19-sample c8 stress finished, but the strict activation gate failed. A one-token canary matched; full semantic/quality gates remain absent. |
| Performance and paired quality | No same-identity 0.85 no-cache control, complete repeated TTFT/TPOT/throughput matrix or paired 2048-token LongBench-v2/GSM8K quality for this plugin source. |
| Rollback and attribution | Exact owned service/container/port release passed. Disable, uninstall, restart and A/B/C local-increment attribution were not exercised. |

Decision: `partial-evidence` for this Skill's real-task case, **not**
`accepted` runtime delivery or HYPIC paper success. The branch-local
validator only checks static identity; its success cannot prove live import,
per-worker activation, output quality or rollback. The new validator and
template are not integrated in main/remote.

Replay on the target host with
`python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_runtime_monkeypatch_delivery_case.py`;
it rechecks main/branch/plugin source identities, the main missing-path
counterexample, focused validator tests and r12's immutable raw audit.
After the prospective full-pair decision rule is fixed, package the actual
candidate, validate its manifest, run a disabled control, repair or account
for cold fallbacks, then complete the gate order from the delivery
contract. Use only actually idle physical NPU0–3; do not rerun r12 unchanged
or claim a release from the static repair.
