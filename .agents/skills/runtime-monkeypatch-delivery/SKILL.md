---
name: runtime-monkeypatch-delivery
description: Use when packaging, validating, or promoting a local inference-runtime technique as a removable Python plugin or monkeypatch against an unchanged official image; require hash-bound identity, per-worker activation, disabled control, rollback, performance, and quality gates.
---

# Runtime Monkeypatch Delivery

## Purpose

Turn a canary-level runtime change into a reproducible, removable delivery
candidate without editing framework files in place or rebuilding the official
serving image.

## Boundary

Use this skill for local Python/runtime adapters, import hooks, operator bridges,
and plugin-delivered inference changes. Prefer an existing configuration switch
or supported upstream hook when it expresses the treatment exactly.

Do not label upstream capability as local contribution. Native ABI changes,
image rebuilds, framework forks, or changes that cannot be disabled cleanly
need an explicit experiment decision explaining why monkeypatch delivery is
inapplicable; they are not silently exempt.

## Delivery policy

- New local inference-runtime techniques are disabled by default and delivered
  first as a removable plugin or monkeypatch against the pinned official image.
- Keep the candidate on its owning work branch until every promotion gate
  passes. Main may receive the reusable rule, not unaccepted active code.
- One package represents one primary treatment. Do not bundle unrelated wins.
- Bind the package to exact live source, image, patch bytes, experiment, and
  commit identities in `MANIFEST.json`.

## Workflow

1. Require source mapping and a passed canary with a frozen baseline.
2. Resolve the module, object, package version, and source bytes imported inside
   the live container; record their hashes before patching.
3. Copy the template under [assets/template](assets/template) into the owning
   workstream and implement only the declared treatment.
4. Use one explicit environment switch. Disabled mode must leave official
   behavior intact; uninstall must require no image or framework repair.
5. Emit bounded structured activation evidence from every relevant worker,
   rank, and engine process. Run the disabled control and prove the treatment
   marker disappears while requests still succeed.
6. Validate the package with
   `scripts/validate_monkeypatch_package.py <package-dir>`.
7. Run exact-shape numerical or task oracles and sensitive semantic tests before
   performance work.
8. Run the preregistered c1 fail-fast, then the complete repeated performance
   matrix only if every progression gate passes.
9. Run the independent paired quality contract. Performance-first is the
   default efficiency order, not a correctness dependency: a separately
   authorized quality study may proceed after valid performance regression.
   Preserve both decisions; promotion still requires both gates to pass.
10. Exercise disable, uninstall, restart, and resource-release rollback.
11. Record the terminal state and evidence hashes. Remove rejected hooks from
    the safe runtime tree while preserving their commits and artifacts.

## Promotion gates

A package is promotion-ready only when all applicable gates pass:

- official baseline image and live source contract are unchanged and proven;
- manifest, patch, native extension, and launch-wrapper hashes resolve;
- enabled and disabled controls differ only by the declared switch;
- every required process proves activation and no required event is missing;
- exact-shape, stress, semantic, and physical-NPU checks pass;
- full TTFT/TPOT/throughput gates pass with comparable repeated evidence;
- paired quality gates pass with no material regression;
- rollback restores official behavior and releases owned resources;
- A/B/C attribution separates official image, upstream capability, and local
  increment.

Read [references/delivery-contract.md](references/delivery-contract.md) when
creating the manifest, activation ledger, terminal decision, or PR handoff.

## Terminal states

- `accepted`: all gates pass; eligible for removable delivery and PR.
- `partial-component`: useful bounded component, not a release candidate.
- `rejected`: measured gate failed; preserve evidence and remove active hook.
- `failed`: execution or tooling failed; do not convert it to algorithm truth.
- `inconclusive`: evidence cannot support a decision.

## Verification

- Package validator exits zero.
- Enabled and disabled controls are both recorded.
- Patch identity and activation evidence cover every relevant process.
- Performance and quality conclusions use their dedicated skills.
- Rollback is executed, not merely described.
- `./scripts/validate-mst.sh` and `git diff --check` pass.
