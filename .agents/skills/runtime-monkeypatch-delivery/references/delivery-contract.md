# Runtime monkeypatch delivery contract

Use this contract when a canary becomes a packaged service candidate.

## Package shape

```text
runtime-monkeypatch/
├── MANIFEST.json
├── patch.py
├── sitecustomize.py
├── run_with_patch.sh
└── tests/
```

Additional native libraries are allowed, but record each path, ABI identity,
build source, and SHA256. Never overwrite files in the official image.

## Manifest identity

### Existing native vLLM plugin profile

Keep a working `vllm.general_plugins` registration instead of adding a second
`sitecustomize` activation route. The static validator accepts optional
`treatment.loader_kind` values `sitecustomize` (default, backward compatible)
or `vllm.general_plugins`.

For the native profile, bind `loader_file: pyproject.toml` and its SHA256,
`entry_point_group: vllm.general_plugins`, `entry_point_name`, and the exact
`module:callable` entrypoint. `patch_file` identifies that module's `.py` or
package `__init__.py`; it does not substitute for whole-package identity.
Include top-level `source_files`, a complete list of `{path, sha256}` for all
Python files below the plugin's top-level package. Duplicate, missing, changed,
escaping or symlinked source files fail validation. Bind the actual launch
wrapper by path/SHA256 without requiring a new activation wrapper.

Native TOML validation uses Python3.11's standard `tomllib`; on chicaihong01 use
the existing host-test Python environment described by host-maintenance.
Older Python can still validate the legacy profile; the native profile fails
with a clear version requirement rather than silently skipping TOML checks.

All source/image/framework/CANN identity and live control/rollback obligations
remain. Static declaration/source-file matching is not installed-entrypoint
discovery, process activation or delivery acceptance. Missing historical version
evidence remains missing; a retrospective manifest cannot create runtime proof.
No native profile requires an algorithm rewrite or a new observer.

`MANIFEST.json` records:

- schema, candidate name, and terminal state;
- official image digest, framework/CANN versions, live module/object, and live
  source SHA256;
- one environment switch, enabled value, patch file, entrypoint, patch SHA256,
  loader file/SHA256, launch wrapper file/SHA256, and the one primary variable;
- required worker/rank/engine roles, marker prefix, and disabled-control rule;
- disable and uninstall commands;
- experiment ID, work branch, and exact Git commit.

Run the validator after any patch-byte or manifest change. A stale hash makes
the package invalid, not approximately equivalent.
The validator checks static package identity only; it cannot prove the live
module, per-worker activation, output quality, or rollback execution.

## Activation ledger

For enabled and disabled arms record:

- service instance and configuration hash;
- PID, rank, worker/engine role, physical and container-visible NPU;
- switch value, manifest hash, patch hash, and imported live-source hash;
- planner/scheduler selection, ready state, worker/device hot-path event, and
  missing/failure event lists;
- request ID and raw activation-log SHA256.

Launcher-only output is insufficient. Every process that can execute the
treatment must prove activation. Disabled control must complete a real request
without treatment markers. Use the same wrapper and command for both arms;
unset or `0` is disabled and `1` is enabled in the provided template.

## Attribution

Use three arms when upstream capability is involved:

- A: unchanged official image;
- B: exact upstream vLLM-Ascend/CANN capability;
- C: B plus the smallest local original increment.

Only C-minus-B is local contribution. Packaging repair, harness improvement,
upstream reuse, and local performance improvement remain separate evidence
categories.

## Required gate order

1. source and ABI/loadability;
2. exact layer/state/shape oracle;
3. repeated stress and per-process activation;
4. sensitive semantic set;
5. c1 fail-fast;
6. full repeated performance matrix;
7. paired reference-backed quality repetitions;
8. disable, uninstall, restart, and resource-release rollback.

Do not spend the full matrix after a preregistered gate fails. Do not use a
microbenchmark, profile, or compile-cache hit as a service-level win.

## Hot-unloadable instrumentation: retained references

Only for packages supporting in-process hot uninstall: restoring a module
attribute does not invalidate function aliases retained by callers or compiled
graphs. Test a saved callable after uninstall and a real post-uninstall request
before claiming serving rollback. This is not a new gate for every paper.

Do not delete callback globals still needed by retained aliases. Use an explicit
safe rollback, such as restarting the owned service or generation-specific inert
dispatchers that release session references and cannot reactivate old aliases on
reinstall. Disclose inert names remaining until restart; active-hook removal is
not zero namespace residue.

Example: HYPIC diagnostic r24 completed its target and four-worker capture, then
failed its post-uninstall request with a missing callback global. See workstream
`.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/`:
`HYPIC_R24_PARTIAL_CAPTURE_AND_UNINSTALL_FAILURE_20261012.md` and CPU regression
`test_numerical_state_observer_v2.py`. Valid partial captures do not upgrade a
failed lifecycle gate. Observer failure is not automatically HYPIC quality loss.
CPU/import tests are not device rollback; r25/r25retry1 pre-health isolation
failures provide no device result for this fix.

## Terminal decision

Record `accepted`, `partial-component`, `rejected`, `failed`, or
`inconclusive`, including:

- exact failed or passed gates;
- allowed and forbidden claims;
- raw artifact locations and hashes;
- safe-tree state after the decision;
- concrete changed premise required to reopen a closed route.

Only `accepted` may become the removable delivery PR. Rejected active hooks
must be removed or disabled while their Git history and evidence remain
reachable.
