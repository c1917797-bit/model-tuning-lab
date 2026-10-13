# Selective runtime template repair — 2026-10-13

## Decision and scope
Offline candidate integration PASS for the existing main sitecustomize template.
The full runtime-monkeypatch-delivery Skill remains partial-evidence.
No HYPIC source, NPU execution, quality rerun, main ref, or remote was changed.

Exact target: ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Candidate tree: 401e86402860220029d268fc748c8e5af24b6442.
Retained fixture: /cache/cch/mst-runtime-selective-kk_oc_zi.
Five files are selected from existing validated commits. The validator comes
from72bd32946345054f8251c856fb8c896443640443; the tests and three template assets
come from10a99926aaa05eca4ddb72cad514e2d58b60b473. The frozen plan records each
path/source. This deliberately does not import the later native-plugin profile,
observer, HYPIC package, modified Skill prose, or historical workstream records.
It repairs only the main route already documented, not every branch capability.

## Execution and separate review
mc operation exec-000000000000008c completed exit0. In an isolated checkout of
the exact target plus ONLY those five files:
- Nine CPU functional tests passed: customized identity, placeholder rejection,
  patch/launcher drift, path escape, missing disabled control, same-wrapper
  unset/0/1 behavior, enabled worker failure exit78 and disabled broken hook.
- The target's own validate-mst.sh passed29 Skill structure checks.
- Candidate staged diff whitespace validation passed.
- Source checkout HEAD and status were unchanged throughout the fixture run.

A separate read-only Git-object review exec-000000000000008e completed exit0:
all175 other target paths/modes were unchanged, exactly five selected blobs
matched their source commits, no unrelated workstream path entered the patch,
and retained patch/result hashes matched. It did not call the maker's auditor.
This is separate implementation evidence, not an independent human/agent review.

Original result SHA256:
60e0c8d7da86f7516f08ed9e20d47baa45283b489192502b9da30b0cd8cc341a.
Decoded diff SHA256:
1abaae8168bc3bdda702592df7894a614917345410ebbd42ca81d149702b948a.
The lossless diff is in integration/runtime-template/repair.diff.json.
The raw fixture retains command/stdout/stderr checksums and source states.

## Reuse and integration gate
Use the existing fixture for audit, not another --run:
```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_runtime_selective_integration.py --audit /cache/cch/mst-runtime-selective-kk_oc_zi
```
This clone uses the source repository's object store; retain both until archived.
Temporary package directories created by unittest were automatically cleaned;
the original fixture and its receipts remain.

Before actual integration: authenticate/refresh the target, resolve any target
drift, publish the source workstream checkpoint, reconstruct this exact minimal
change in a named integration workstream, validate the final target-owned tree,
and follow serialized no-ff integration with independent remote verification.
Do not merge the entire HYPIC branch, bypass the remote-start policy, or infer
full device delivery acceptance from these CPU tests.

Latest remote probe007f timed out after20 seconds: current remote state UNKNOWN,
not a new authentication-failure diagnosis. The connected MCPGit Guest repo list
does not contain this repository. No push was attempted or service provisioned.
No further unchanged remote retry is warranted.

## Reusable lesson
Trigger: a repair passes in a large experiment branch but has not reached main.
Action: validate the exact target plus the smallest complete repair, including
runtime startup failures; distinguish static identity and CPU controls from
device activation and deployment acceptance.
Destination: this executable integration eval, frozen plan and delivery case.
Verification: exact Git tree/source-byte review, target-local functional tests,
and the final-tree integration gate above. Counts remain12 bounded/17 partial.
