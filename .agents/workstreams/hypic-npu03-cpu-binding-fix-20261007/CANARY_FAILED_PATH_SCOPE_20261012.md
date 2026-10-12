# Canary acceptance scope correction — 2026-10-12

## Finding

The current case next_gate required isolating quality/activation failure and
justifying a changed candidate before further Skill acceptance. That is the
admission path for another optimization attempt, not the only way to validate
the Canary Skill. It risked sending the agent into indefinite algorithm/root-cause
work after a complete negative experiment.

Exact main ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2, Skill blob
07dceac8c65c9d1696d8e2fa5543d9b8784a7628, explicitly has a failed-outcome
branch: workflow8 requires failed classification and active-code recovery.
Workflow9 and11 are conditional on correctness/surviving the canary. None of
its11 workflow steps requires implementing paper C3 or proving a quality
root cause before recognizing a correctly handled failure.

## What is corrected, and what is not

- Case next_gate now distinguishes failed-path Skill validation from admission
  of another changed candidate. It preserves the original historical replay task.
- C3 remains a paper-completeness limitation, not an added Canary Skill gate.
- Correctness remains mandatory before scale. A failed canary cannot pass
  performance/adoption gates by relabeling it.
- Original3ad0967 both-wrong canary and c12060c r13 negative quality stay frozen.
  Prospective4429e35 lifecycle evidence cannot fill historical provenance gaps.
- No acceptance promotion: historical preimplementation evidence and complete
  claimed workflow coverage still need proof. Current recovery has no terminal
  result yet. Do not infer disabled/uninstalled success from a running controller.

## Current evidence and next bounded action

Original historical replay stays verify_ascend_canary_implementation_case.py.
Native enabled failure is independently replayable with
native_lifecycle_failure_audit.py: correct source, four-worker hot path, wrong
A versus D answer with2048-token cutoff and exact release. It proves a failed
canary, not an implementation root cause.

Recovery-only disabled controller exec-0000000000000165 is the sole live
device action. Await terminal, audit unchanged request/control gates, and
only then admit uninstall if disabled audit and fresh lane availability pass.
No enabled repeat, full quality rerun, standalone GDN or observer expansion.

## Audit boundary

Source read0169 directly matched exact-main wording to the current Skill.
This case-only correction does not change Skill bytes, native runtime bytes,
frozen raw evidence, scoring or heat gates, source/quality/performance claims.
Counts remain8 bounded verified/21 partial. Main/remote integration remains
incomplete and unchanged authentication must not be retried.
