# Selective graph compatibility component — offline only

This new directory has a new explicit bootstrap/worker loader. It is disabled
by default and does not change the 413 frozen runtime files, any existing
service, or R25 evidence. Native G1 remains the ordinary official runtime.

Pinned qwen3_5.py208 decorates Qwen3_5Model itself. The ordinary causal-LM
wrapper forward (501-513) calls that model at509; Qwen3NextModel.forward is
the inherited native body. The new entry validates the actual generated
compiler decorator rather than unwrapping arbitrary callables.

Pinned official source distinguishes compiler mode from graph capture:
the Ascend runner enables ACL graphs only with VLLM_COMPILE, a non-NONE graph
profile and enforce_eager false. FULL_DECODE_ONLY uses runtime FULL only for
uniform decode; prefill/mixed runtime NONE may still enter the Torch compiler.
The official decorator supports skip_compiled per forward. ACL graph replay
does not call the Python runnable.

entry_router.py is a small falsifiable component for that distinction. A
source-owned outer entry permits native decode tracing only after verifying the
actual native config and FULL uniform one-token descriptor. Model and layer
adapters route to source-verified preactivation native functions before any
HYPIC ContextVar access. NONE forwards temporarily use the official
skip_compiled field, restored on exceptions; no do_not_compile/config flags are
forged. Unknown compiler entry, mixed FULL, wrong wrappers and changed owners
fail closed.

prefill_bridge.py now establishes the real selected-prefill NONE/no-ubatch
snapshot scope using the unchanged validator and scope, then calls the
unchanged row-pruning helper with its actual outer scope explicitly attributed
in receipts. It never pretends the old helper's global NONE guard passed.
The unchanged C1/C2 layer checks, lease/slot/finite/completion checks and public
producer path remain in place. Selection is computed once per prefill.

activation.py is an explicit startup-only facade: capture exact native targets
before our hooks, temporarily intercept one known installer export, restore it,
then install owned outer entry/model/layer adapters. It verifies only the known
GDN -> public producer -> native and C2 -> native chains. Unknown wrappers fail.
The official chunk producer remains installed for NONE prefill. It is unreachable
on the pinned native GDN decode branch (ops/gdn.py384-402) because FULL admission
also requires actual zero-prefill metadata; no all-globals-unpatched gate is used.

This is not yet an accepted graph-compatible HYPIC package. Before service use:

1. The new bootstrap checks INDEPENDENT_GRAPH_HYPIC=1, reads
   INDEPENDENT_GRAPH_MANIFEST and INDEPENDENT_GRAPH_RAW, and installs a finder
   before the first official worker import. The loader delegates to the exact
   native SourceFileLoader only after verifying its get_code matches a fresh
   compile of the pinned worker source; after exec_module completes, it verifies
   the native NPUModelRunner dummy metadata policy and calls the real facade.
   Exact source-map values must come from the frozen unchanged package, plus
   all new graph runtime files. No new manifest or service run is accepted here.
2. Test actual pinned-image constructor/owner checks and atomic assembly.
   CPU tests use real unchanged helper/snapshot logic with a fake native runtime;
   they do not execute the actual official model or prove all startup paths.
3. The proposed Python authorization branch must pass the pinned image's actual
   compiler, not merely a CPU toy. Public producer and mixed prefill must
   demonstrate normal C1/C2 behavior with pure decode remaining native.
4. A new immutable bounded integration contract must record actual argv,
   VLLM_COMPILE/FULL_DECODE_ONLY/no-enforce-eager, native G1, four-worker
   mechanism proof, source, continuous isolation and exact release. Official
   graph logs or CANN must prove capture/replay; no counter here proves replay.
5. Only then compare matched performance. Graph compatibility is a hypothesis,
   not a demonstrated cause of the earlier regression.

No all-call bypass baseline is included. No guard is silently removed. This
component and its CPU tests do not certify NPU correctness, performance,
numerical equivalence, a completed paper reproduction or deployment readiness.
