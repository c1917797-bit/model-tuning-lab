# Active local launcher draft: v4

Review `main_admission_v4.py`, `historical_owner_context_v1.py`, `complete_inspect_receipt_v1.py` and the unchanged `restore_snapshot_mounts_v1.py`. Earlier unfrozen launcher versions and their controls remain preserved. V4 addresses only the independent review's B1/I1/I2 findings. It remains default OFF, with `REVIEWED_FROZEN=False` and all three helper runtime pins unset.

## B1: exact independent historical context

The original active `external025.OUT` is the new output root after `owned_substrate.load`. Reusing that active validator for an old OWNED leaf deterministically fails its original directory predicate. V4 creates a separate pure validator for each historical owner using that owner's exact source manifest and output root. It never switches, patches or restores the active new global OUT.

The historical and current original external, adapter, cap32, observer and output-scanner files are fully reopened through their source-owned exact Refs and matched to the independently reviewed full-file hashes. The two owned_substrate versions are pinned independently, and their complete nested base-environment function ASTs must agree. Both bind the same original model_contract, safety_host and host_once Refs.

Private namespaces compile the original model_contract constants/require and original safety function ASTs. The genuine cap32 provider operates on that private S, preserving its original before-cap checks and resulting MEM32/reserve8/host0.5 values. This construction is not a physical 73-GiB host admission. The current actual source's final 40.5-GiB initial threshold remains authoritative.

The original complete g2 derive functions perform their exact forward/inverse checks on the original whole safety source. The resulting create/inspect functions are compiled unchanged into private globals. The entire original g2 environment function is retained, with its original nonconsumer first branch explicitly verified. Only the six registered old cpu-preflight/dense owners can use these contexts. Original create argv, before/after historical inspect and current full inspect all use their own per-CID context. Whole labels, environments, resource/isolation/device predicates and mount members remain checked.

The actual observer installer changes only Controller.observe; the actual output-scanner installer changes only Controller.resources and its private scanner handle. Their complete original Refs are included in the proof/readset. Neither installer is executed in a historical context. The active c/S/external identities, globals, OUT, functions and resource constants are fingerprinted before/after construction and before/after every historical validator invocation. All remain unchanged.

## I1: original opt-in before source load

The future reviewed launch process must already have `DENSE090_EXTERNAL_OUTPUT_ENABLE=1`. The original install guard is retained, and v4 explicitly checks this before `owned_substrate.load`. `COMMANDS.model` supplying the variable at a later exec does not satisfy this earlier step. Real dispatch separately requires `BOLE_CONTINUATION_MAIN_ENABLE=1`, the exact current config/MAIN review and a genuinely frozen launcher. V4 does not inject or invent authorization.

Use a fresh process with the original unlimited CPU-time/file-size soft and hard limits. Do not inherit a short source auditor's 150-second CPU or 16-MiB FSIZE hard cap. The v2 guards remain: AS soft512MiB/hard infinite, CPU166, original phase3600/shared cleanup180/full prepare3780, MAIN lock inherited into the exact source command, and predispatch alarm cancelled before exec. The old report deadline remains unchanged at 2026-10-22 12:38:41 UTC.

## I2: retain every complete current inspect receipt

The saved successful v4 observation records six raw old-owner inspect stdout sizes totaling 28,138,794 bytes. V4 therefore retains complete current receipts in a lossless `zlib+base64` envelope. It preserves all original metadata and stores exact original UTF8 bytes/SHA, compressed bytes/SHA, and canonical complete-receipt bytes/SHA. Each envelope is strictly decoded and compared to the entire original receipt before publication.

The decoder bounds raw output by the existing 8-MiB per-command cap, uses strict canonical base64, limits decompression by the declared original size, requires EOF and rejects unused/trailing/concatenated data or unconsumed tail. It uses strict UTF8 and refuses a potentially lossy replacement character from the frozen CLI reader. Both check-only stdout and execute's exclusive predispatch receipt retain the **16-MiB whole-evidence cap**. Oversize evidence is rejected; nothing is truncated and no original limit is increased.

## Actual status and remaining work

MAIN's real source freeze and independent source audit have now completed with PASS_SOURCE_ONLY. Their exact source, commands, build, auditor and audit Refs are copied into `CONFIG.template.v4.json` from `continuation_actual/QUALIFIED_SOURCE_REFS.json`. This is distinct from a MAIN resource/dispatch approval. The template remains true; fresh snapshot/program/execution and authorization pins still need exact completion from the actual source and new observation. No old 12:14 snapshot is populated as a current lease.

`LOCAL_CONTROLS_V4.json` records eleven passing existing pure-data/default-OFF controls on v4. `CONTEXT_CODEC_CONTROLS_V4.json` records five passing new source-derived context/codec controls. The new controls use the actual seven helper texts supplied by MAIN, but use explicitly synthetic OWNED/inspect objects and local reference/path transports. They cover three historical sources × two roles, the original active-OUT rejection and private-context success, unchanged active fingerprints, original memory/device/environment/owner rejection, and corrupted/truncated/concatenated codec input. They do **not** prove the actual six raw historical chains or live MAIN integration have passed.

Before any real check, MAIN must finish independent final static review, bind final helper/launcher identities in a separately saved frozen version, supply a genuine exact resource review and immutable config, and acquire a fresh complete successful snapshot no more than 180 seconds old at entry and final dispatch. The real six chains and current controller must then pass their full exact checks. The source-owned controller still rechecks before every create. No NPU, numerical, paired-state, performance or accuracy qualification is granted by this package.

## Supported inner launch argv

The exact check-only sequence is `/usr/bin/env`, `DENSE090_EXTERNAL_OUTPUT_ENABLE=1`, `/usr/bin/python3`, `-I`, `-B`, the **final frozen launcher_ref.path**, `--check-only`, `--config-ref`, one complete serialized config Ref argument, `--review-ref`, one complete serialized genuine MAIN review Ref argument. The exact dispatch sequence adds `BOLE_CONTINUATION_MAIN_ENABLE=1` immediately after the first environment assignment and replaces `--check-only` with `--execute`. Pass structured argv; do not interpolate Ref JSON through a shell. Do not add a nonexistent `--mode MODEL` argument.

`LAUNCH_CONTRACT_V4.md` gives each argv item and all inherited limit/lock requirements explicitly. MAIN's new bounded one-shot unit must be based on the actual old terminal unit configuration, CPU166 and the original host/cgroup/phase/cleanup budgets. No unit timeout or CPU/FSIZE limit may substitute a short-auditor limit for the model owner. A fresh process must already have CPU and FSIZE soft/hard unlimited and AS hard unlimited; the launcher retains AS soft512MiB. No particular unobserved systemd unit settings are assumed here.
