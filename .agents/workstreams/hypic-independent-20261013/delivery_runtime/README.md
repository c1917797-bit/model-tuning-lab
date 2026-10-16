# Independent HYPIC delivery adapter — draft, not service-wired

Reuses the reviewed runtime-monkeypatch template workflow, not old HYPIC code.
The adapter only validates this package and the already independent parent
compact runtime, then calls its import-hook installer. No algorithm/operator/
runner/scheduler code is copied into this adapter.

Single switch: INDEPENDENT_COMPACT_HYPIC. Unset or0 remains disabled.
Enabled startup errors terminate78 even when CPython would swallow sitecustomize
exceptions. HYPIC_DELIVERY_IMPORT_HOOK_READY means only import-hook installation;
actual engine/TPworker roles,48C1/16C2 and per-request mechanism are separate.

Host controls:8subprocess tests0b3f pass. Enabled success uses an explicitly fake
loader with generated fixture manifests; no framework or NPU activation is
claimed. Source/manifest/support-file drift fail before service execution.
Generic skill validator0b40 passes package structure/patch hash. This does not
by itself prove full source closure, CANN compatibility, real worker behavior,
lifecycle rollback, performance, quality or production acceptance.

Current LIFECYCLE_R16_*_R1_CONTRACTs still use compact_bootstrap, NOT this adapter.
Do not claim it has been connected to those frozen contracts. Next wiring must
use a separately reviewed successor controller/manifest/contracts, preserve
ownership/guard/cleanup AST invariants, and prove exact worker startup path.
Do not silently alter old156/159/147source bindings or reuse existing raw roots.

MANIFEST.evidence.commit names the tested adapter source checkpoint112c3e5961a03ea18295636d8497d53324e991f8;
wrapper code digests must match that exact checkpoint and the validator rerun.
Read-only pinned image probe0b4b identifies CANN Toolkit9.1.0 from hashed install
metadata and confirms the runner source digest. Active device ABI/numerics remain
separate; this was no-device/no-network/no-model inspection. No devRPC/admin surface added.
