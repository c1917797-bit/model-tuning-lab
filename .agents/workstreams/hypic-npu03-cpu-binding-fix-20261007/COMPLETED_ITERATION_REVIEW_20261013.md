# Completed iteration checkpoint review — 2026-10-13

## Scope and outcome

Real task: exact-main repository onboarding after the user stopped further
HYPIC quality work. This review exercises the repaired planning Skill's
in-progress → executed evidence → done/publication lifecycle without any NPU
task or repetition of the completed HYPIC experiment.

- Initial plan: d7b1738495f53ebac59bad3f2e0969eebf036284.
- Executed evidence: f98bcc675882091138491eb557b14976642437e0.
- Later case publication: c142c93f3849d9de4a4620ebdacfae572259193e.
- Original execution receipt: mc exec-000000000000003e, exit 0.
- New lifecycle audit: mc exec-0000000000000051, exit 0.

## Defect and correction

The newly completed onboarding plan pointed to the correct evidence commit,
but its declared changed file was the case JSON updated in the later publication
commit. Merely resolving validated_commit would miss this mismatch.

The corrected plan declares the four evidence files present at the validated
checkpoint and records the later case publication separately. Original commits
remain intact. The new read-only auditor rejects the old published plan, checks
the corrected four files byte-for-byte against that checkpoint, and binds the
executed helper/test hashes to the retained successful receipt. It does not run
commands taken from the YAML or claim that existence of a commit proves execution.

Seven focused tests pass: valid scope, unrun/unknown checkpoint, stale file bytes,
missing commands, non-completed status, missing lesson destination, duplicate scope.
The 29-Skill structure validator and git diff --check also pass.

## Reproduction

From the task repository:

```bash
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_completed_iteration.py
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_completed_iteration.py
```

## Lesson and acceptance boundary

Classification 5 (verification case): when completing an iteration, distinguish
the tested artifact checkpoint from later bookkeeping/publication. Check declared
file bytes and retained execution evidence, not just whether Git resolves a name.
The source/test hashes are checked by the auditor; sampling an execution receipt
is bounded provenance evidence, not a trusted attestation of arbitrary commands.

Main's original planning example still has its previously demonstrated schema
defect. Branch planning behavior now has both real in-progress and completed
examples with negative controls. Main acceptance stays partial until the repair
is integrated and tested from main. No quality conclusion, main/remote sync,
or full29-Skill success is claimed. Live count remains10 bounded verified/19 partial.
