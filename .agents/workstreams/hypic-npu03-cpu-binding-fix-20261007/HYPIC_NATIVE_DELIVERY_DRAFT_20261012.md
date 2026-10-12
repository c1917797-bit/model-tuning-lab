# HYPIC native delivery draft — 2026-10-12

## What is now complete

A prospective native delivery bundle exists at:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-delivery-package-20261012

It exports all71 tracked files of HYPIC commit
4429e35177979c874bf053ab29789e4773f39b22 unchanged, plus a draft MANIFEST
and a small identity-check/pass-through launcher. Native plugin registration
remains hypic_vllm_ascend:register via vllm.general_plugins. There is no new
sitecustomize hook, observer, algorithm edit, framework edit or image rebuild.

exec010b passed the complete static package validator, not merely its helper.
Manifest SHA256:
dbac56e41b40214eff24ed305af77e18b50799a36b20e023f381a8dd3af05691.
exec0112 independently verified all71 archive blobs against Git, both tracked
delivery assets,32 Python files, raw receipts and explicit non-acceptance flags.

This is NOT the historical r19 launch wrapper and does not retroactively
convert r19 into a MANIFEST-package run. The new launcher only verifies the
installed entrypoint/import location/version and all declared Python files,
defaults the existing enable switch to0, then execs the supplied command.
Both future arms must use this same launcher and unchanged service arguments.
Creating the bundle does not authorize or start a service.

## Source-location correction

exec0104 failed because distribution metadata did not locate runtime code
under site-packages. exec0105 used the actual top-level import spec without
importing vLLM-Ascend and located:
/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py

AST confirmed NPUModelRunner; file SHA256:
94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968.

The manifest's live_module/live_object fields identify intended targets.
live_import_proven=false is deliberate: image-file/AST evidence is not a live
worker import or host-driver ABI check. Image package/CANN metadata comes from
HYPIC_NATIVE_CPU_LIFECYCLE_20261012.md, not a guessed tag. The source commit in
evidence identifies the HYPIC implementation only; new delivery assets are
bound by file hashes and the later maintainer checkpoint, not falsely claimed
to exist in the older source commit.

## Launcher CPU test

exec010c completed exit0 in9.599s inside the pinned image, no network/devices,
read-only mounts/image,1CPU/1GiB and disposable512MiB /tmp.

An actual offline editable install was used, not mocked package metadata:
- unset enable switch forwards0; explicit0 forwards0; explicit1 forwards1;
-1 was forwarded only to a harmless environment-report command, NOT register;
- invalid switch exits78 before downstream dispatch;
- absent command exits64;
- source-hash drift and uninstalled plugin prevent downstream dispatch.

The probe never tests enabled hooks, real inference, NPU rollback or quality.
exec010e found the owned inspection containers absent and original HYPIC source
clean. Foreign containers, physical NPU0-7 and old immutable experiment roots
were untouched. The draft is disabled by default and not promotion-ready.

## Reuse / rebuild

Tracked assets are in hypic-native-delivery/ within this workstream.
Use an explicitly new output directory; never overwrite the existing bundle.
Export source with git archive of4429e35177979c874bf053ab29789e4773f39b22,
then copy only MANIFEST.json and run_with_native_plugin.sh into the archive.
Install the native package only inside the exact owned serving environment,
then invoke bash run_with_native_plugin.sh with the existing service command.
Do not execute device controls from this document without fresh admission,
a frozen control/rollback plan, and physical0-3/8223 isolation.

Read-only replay (Python3.11, no Docker launch):
/cache/cch/python-envs/model-tuning-lab-py311/bin/python -B \
.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_native_hypic_package.py

## Raw receipts

Root:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-delivery-package-evidence-20261012

| File | SHA256 |
| --- | --- |
| image-source-assumption-failed.json | 1c48ebd7570684e67c64687e3feae38f29f345df91a5931285b66122277c8b0a |
| image-source-spec.json | 00f43ef5e41d84c847b16ce7407b661c2f329a2732ea218b62ee2041189704cc |
| assembly-static-check.json | ae86147c4373d2ca0422a68b766e619c0065fe569fe1bbff5dff9378c9dc7646 |
| launcher-cpu.json | ab57995e346d00d507479374d95d7d12f77cd94479425d872f7ca683d43e684f |
| owned-release-check.json | f7282ba492324174fa71ee4e1649b798a2eea36972738f933d03238808e6e2cb |

## Remaining gates / next action

The full static identity gap is closed for this prospective draft only.
Current-source performance, live per-process enabled/disabled real-request
controls and executed technique-level disable/uninstall/restart/resource
rollback remain missing. r19 LongBench REJECT_OR_QUALIFY is unchanged.
A fast or statically valid package cannot overwrite the quality verdict.

Do not expand the package/observer again just to gain test counts. Next map
the draft's remaining live obligations onto the existing source-matched
control/rollback protocol; decide admission explicitly, without treating the
unanswered descriptive-performance question as permission. Do not rerun
terminal full quality. Exact-main Skill counts remain8 bounded verified and21
partial; no main/remote synchronization. Deadline08:47:14UTC Oct13 unchanged.
