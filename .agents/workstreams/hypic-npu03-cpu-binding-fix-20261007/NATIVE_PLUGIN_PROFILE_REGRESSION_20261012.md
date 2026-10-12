# Native-plugin static delivery profile — bounded repair

2026-10-12 UTC, branch-only. HYPIC source4429e35, images, running services,
frozen packages and raw NPU roots are unchanged.

The delivery Skill already preferred supported hooks, but its validator only
accepted sitecustomize.py. exec00d7 reproduced this conflict with a native
package fixture: exit2, loader_file must be sitecustomize.py. The correction
preserves the original hook instead of adding a second activation route.

Changes:
- Optional treatment.loader_kind defaults to sitecustomize, preserving old
  packages. vllm.general_plugins checks hashed pyproject.toml entrypoint metadata,
  module or package __init__.py identity and a complete hashed source_files
  inventory below the plugin's top-level package.
- Changed/missing/duplicate/escaping/symlinked Python source is rejected.
  Launch bytes are still hash-bound. Native checks parse TOML with Python3.11;
  older Python fails explicitly for this profile, not silently skipping it.
- Existing image/source/version, controls, worker activation, quality/performance
  and executed rollback gates are not relaxed. Native metadata checks never
  import or activate the plugin.

exec00d9 passed21 CPU tests:9 legacy/startup controls and12 native-profile cases.
exec00e0 repeated both suites through the real delivery-case replay and kept
r12/r13 decisions intact. Skill Creator quick validation passed.
exec00da checked the actual clean HYPIC pyproject declaration and32 Python files
through the native-identity helper. It did NOT validate a full HYPIC manifest:
explicit version provenance and technique rollback remain missing. No fake
version strings, retrospective activation or device evidence were produced.

Native coverage: valid package without sitecustomize; omitted source; changed
helper; duplicate source; path escape; wrong group; wrong/missing declaration;
unknown profile; symlink; malformed TOML; mismatched entrypoint file.
Only declarative pyproject-based package plugins are covered, not arbitrary
setup.py execution, namespace packages or every plugin host.

Replay:
- /cache/cch/python-envs/model-tuning-lab-py311/bin/python -B -m unittest discover -s tests -p 'test_validate*package.py'
- python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_runtime_monkeypatch_delivery_case.py

Experience destination: existing Skill/reference/registry and verification case.
Trigger: an already-working native plugin is rejected by a loader-specific
template checker. Different action: preserve its supported route and validate
the matching static identity profile; never rewrite measured code merely for
a template. Regression tests and whole-tree/case checks validate this change.
This is an implementation of the earlier reuse plan, not another observer.

Actual delivery case remains partial. Counts8 bounded verified/21 partial.
Same-source descriptive performance choice and08:47:14UTC Oct13 deadline remain.
No main/remote synchronization or new device acceptance follows.
