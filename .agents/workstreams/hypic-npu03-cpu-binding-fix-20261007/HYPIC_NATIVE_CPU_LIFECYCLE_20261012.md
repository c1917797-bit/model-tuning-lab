# HYPIC native image identity and CPU lifecycle — 2026-10-12

## Result and boundaries

The real unchanged HYPIC 4429e35177979c874bf053ab29789e4773f39b22 package
was installed through its existing vllm.general_plugins entrypoint in the
pinned image. Actual metadata discovery and register() calls passed with the
switch unset and with 0; bootstrap, vLLM and torch_npu were not imported.
Uninstall followed by a new interpreter proved distribution, entrypoint and
module discovery absent. This is a CPU-only installation/disabled/uninstall
result, NOT enabled hook activation, real-request control, NPU rollback,
quality acceptance or a historical service restoration.

No mock bootstrap was used in this probe. No image/framework/plugin source was
changed. The earlier host-only mocked register test remains narrower evidence.

## Immutable image contents, not a guessed tag

exec-00000000000000f2 inspected installed distribution metadata and the CANN
installation information inside image
sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.

| Component | Installed metadata |
| --- | --- |
| Python | 3.12.13 |
| vLLM | 0.23.0+empty |
| vLLM-Ascend | 0.23.0 |
| torch | 2.10.0+cpu |
| torch-npu | 2.10.0.post4 |
| transformers | 5.5.4 |
| triton-ascend | 3.2.2 |
| CANN toolkit | 9.1.0; inner V100R001C11SPC001B243 |

CANN info resolves to
/usr/local/Ascend/cann-9.1.0/aarch64-linux/ascend_toolkit_install.info,
SHA256 a9b17ef608ebeb70ade09cde1c12a545eb5e8f3e5312f6806ca0d368b0464848.

These are the immutable image's package/version files, observed now. The
torch +cpu suffix is retained verbatim, not interpreted as a failed Ascend
stack. No enabled framework import was attempted. Historical r19 attests this
same image ID but mounted host driver files; this probe does not establish the
old driver bytes, tokenizer state, mutable container layer or runtime API/ABI.

## Actual package lifecycle probe

exec-00000000000000f7 completed exit0 in15.097s. The probe uses:
- exact image above, read-only root, no network, no mapped devices;
- capability drop ALL, no-new-privileges,1 CPU/1GiB,128 PID limit;
- read-only source/probe mounts and disposable512MiB /tmp;
- a system-site-packages temporary virtual environment;
- offline --no-deps --no-build-isolation editable install into that environment;
- separate fresh interpreters for unset/0 controls and post-uninstall checks.

The source's32 Python files matched both before and after copying/testing:
a5ebed77cc4ae0035e2634b81dc0606d8e37cc9d32f8894b984325bec1056692.
The hash uses sorted paths relative to hypic_vllm_ascend/, NUL, file bytes, NUL.
The tested register function came from /tmp/hypic/hypic_vllm_ascend/__init__.py.
No numbered NPU or manager device node was present. Both controls returned
without a plugin_build_active marker or bootstrap/framework import.

exec00f9 independently observed both named inspection containers absent and
the original HYPIC checkout clean. Their tmpfs/virtual environment disappeared
with --rm; no foreign container or persistent source was removed.
Root/ remains full; /cache had136GiB free at00f1. No disk cleanup occurred.

## Receipts and replay

Raw records are outside Git under:
/cache/cch/hypic-npu03-cpu-binding-fix-20261007/native-delivery-cpu-20261012

- image-probe-record.json:
  af1632019b98eba1fcb3d975ed894b0da60883b660d20762e047ee377c453c54
- cpu-lifecycle-record.json:
  40010d430a660de87c76d74b025cb1e0a1e03ff63c1a0ebc1746821a6d076189

Tracked probe: probe_native_hypic_cpu_lifecycle.py,
SHA25616fd5ba69df7b4d002b5c2f163d81a07ddb187fa7d5d25e2a88812d42f28e8b1.
The saved raw record includes the exact isolated Docker invocation. Do not
rerun it merely to increase validation counts. The existing runtime-delivery
case verifier now checks hashes, identities, isolation arguments and the
explicit negative claim boundaries without launching any container.

## Remaining obligations

Image version metadata is now available for a prospective native manifest.
A full hash-bound HYPIC MANIFEST, live target-object identity, complete
per-process enabled/disabled request controls, and device disable/uninstall/
restart rollback remain incomplete. No retrospective MANIFEST can create
missing historical proof. Static package success does not imply adoption.

r19 quality verdict, missing4429e35 performance, all old raw roots and the
pending prospective descriptive-performance choice remain unchanged.
Exact-main29 counts remain8 bounded verified/21 partial. This adds real package
evidence to the original runtime-delivery case; it does not replace that case
with a smaller goal or promote it to verified. Main/remote are not synchronized.
The fixed deadline2026-10-13T08:47:14Z is unchanged.
