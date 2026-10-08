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
