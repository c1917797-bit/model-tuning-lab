# r23 diagnostic integration failure and CPU import repair

Enabled controller exec-0000000000000cdc ended exit1 after four successful
responses, because capture seals were absent. Independent post-terminal failure
audit exec0cf1 preserves FAILED_LOADER_INTEGRATION: source/image and physical0-3
identities valid, 99 clean guard samples, exact owned container/port release.
Audit SHA256 77e039fe78bcdcbe0810b7a3ac9e9998755b4dcf7530781bfff99fb7a219054c.
Raw root and r23 frozen code/contract remain unchanged; never rerun either root.

The full enabled service log proves HYPIC entrypoint import was blocked by the
new diagnostic finder (ImportError: HYPIC target not available). vLLM catches
plugin.load() errors and continues ordinary serving. The empty HYPIC event file
and empty capture directory corroborate missing activation. This is OUR observer
integration defect, not HYPIC algorithm failure or the cause of r19 quality loss.

Root cause: PathFinder alone cannot resolve this PEP660 editable installation;
the real editable MetaPathFinder is later in sys.meta_path. New prospective
numerical_state_loader_v2.py delegates through the full remaining finder chain,
preserving order and excluding its own wrappers. Frozen v1/support package intact.
13 host tests passed exec0cef. Fixed-image CPU-only exec0cf0 (no device mapping,
no network, owned --rm container) reproduced old failure and proved the real
vllm.general_plugins entrypoint loads through v2 and cleanly uninstalls.
It did NOT call register or prove per-worker observer installation/NPU capture.

Next: version a successor package/contract, bind v2 and unchanged support hashes,
prove real register/observer installation (not merely entrypoint load), and add
startup fail-fast for swallowed plugin errors/per-worker activation before
spending time on requests. Then ONE changed-premise known-hot integrated request
after fresh direct-route physical0-3/8223 admission; no unchanged c32/full wave.
r23 disabled audit remains valid for its original bytes, not an automatic
same-package control for a successor. r19/r22 judgments unchanged. No live owned
NPU service remains from r23. No main/remote sync; 29 Skill functional acceptance
still incomplete (7 bounded verified / 22 partial).


## Immutable evidence

- Disabled: exec0ccd; independent exec0cdb; 114 clean isolation probes.
  Audit SHA256 38f25f63e7d0e114c23bc9c8229f189e047d8a440097c4292a07e04403d46bab.
- Enabled: exec0cdc; container
  179fa23dc685ed8912ece33477c8447dd1fec158f360bf07a5e73178a1dc5987.
  Released 2026-10-12T11:12:38.354990+00:00.
- Enabled log SHA256
  a3ecfa87747ecb6dfc6b39e865d1bb946aa91eab34e56696f8bbd22c457de624.
  Lines 28–45 show vLLM catching plugin.load() failure, originating at
  numerical_state_loader.py:141. API/engine/workers logged this load failure.
- Post-terminal auditor: r23_state_failure_audit.py. Its independent identity,
  response, isolation and release checks do not turn failed capture into success.
- Frozen preregistration SHA256
  b1197dfe932a656c083feea7fa15d40c7c9ce08c581c4ac84c7b30deec0320e5.

## Reusable failure lesson

Successful package installation, service health and completed responses do not
prove a requested runtime plugin was loaded. A generic plugin host may catch
import exceptions and fall back to normal inference. Test the real installed
entrypoint in the exact installation mode, not only synthetic ordinary modules
or a loader that never imports its target. Preserve every relevant meta-path
resolver when interposing on Python imports. Require positive worker activation
before accepting an enabled arm; classify absent activation as harness failure,
not negative algorithm evidence.

## Repair boundary

Post-repair full numerical-state host suite: 49 tests passed (exec0cf4).
Maintainer tree structure: 29 skills passed (exec0cf5). Task JSON and
git diff --check passed (exec0cf7/0cf6). These are not NPU activation proofs.

The v2 file is prospective and not wired into the frozen package. No original
HYPIC runtime source or official image was changed. CPU entrypoint/rollback
verification is deliberately weaker than successful register, per-worker hook
installation or numeric capture. Existing r19 quality rejection is not explained
or changed by this newly discovered r23-only bug.
