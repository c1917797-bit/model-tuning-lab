# Exact idle, protected-card and old-owner supplement

Scope: local source inspection only; no remote action, NPU call, or change to the frozen `fresh_snapshot_v2.py`. The latter remains 17622 bytes, SHA256 `8530e4c98ff29da33b75aaffe997d7dd002f21e75ab52372076ba0e7c87572eb`.

## Newly verified source pins

| Local source | Bytes | Independently recomputed SHA256 |
|---|---:|---|
| `boundary_resource_input/full_matrix_host_v2.py` | 33743 | `ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86` |
| `boundary_resource_input/native016_safety_lifecycle.py` | 6865 | `4bbd492809c9ba1922fd3885b101f8cc6fe187884703c21e4a2d44acd1444b75` |

Both match the exact expected refs supplied by MAIN. This closes the named idle/protected predicate source gap in the preceding checklist. The old `legacy().process_rows` implementation remains a separately hash-bound dependency of the original controller; this supplement neither replaces nor weakens that parser.

## 1. The actual idle predicate

`full_matrix_host_v2.py:196–205`, called through the existing controller's `self.h.idle_one`, requires all of the following for each physical card 4–7:

1. SMI text contains the literal `No running processes found in NPU <physical>`.
2. `legacy().process_rows(text)` contains no row for that physical card.
3. A card line matches `\|\s*<physical>\s+910B4\s*\|` and contains the literal health substring `| OK `.
4. On the following line, the third pipe-separated segment has a first whitespace token exactly equal to the string `0`.
5. That same segment matches `\b28[0-9][0-9]\s*/\s*32768\b`.

The final expression is the original **2800–2899 / 32768 idle baseline**; it is not a generic “below 3 GiB” condition. The exact source searches the metrics segment for that ratio. It does not itself select a ratio by a freshly interpreted column name. Separately, original025 `safety_host.py:89–118` validates the precise header, chip and bus layout, parses the actual HBM ratio, and requires its 3072 MiB physical reserve. Both original checks remain applicable. The independent `/proc` actual device-holder check also remains: an empty SMI process list alone does not prove device release.

Do not broaden this predicate if a current driver reports a different idle baseline or text layout. Preserve the raw snapshot and let the original source gate fail with its actual reason.

## 2. The effective 0–3 protection predicate permits external churn

`full_matrix_host_v2.py:82–90` produces each observed protected-card row from the actual SMI process list plus `/proc`, with exactly the fields `physical`, `chip`, `pid`, `start_ticks`, `cgroup`, and `cmdline_sha256`.

The effective original025 wrapper delegates to `native016_safety_lifecycle.py:91–115`. It validates both baseline and observed rows:

- Each row list has at most 4096 rows; each row has exactly those six keys.
- Physical device is integer 0–3; chip equals 0; PID and start ticks are positive integers with PID >1; cgroup is a nonempty string; command-line hash is 64 lowercase hex characters.
- `(physical, chip, pid)` is unique within each list.
- No row may have a PID in the supplied `owned_host_pids`, and no row's cgroup may contain any supplied full owned CID.

The function **does not require `before == after`**. It preserves `external_added`, `external_removed`, and `external_changed`, and returns `own_on_protected=False` and `external_unchanged_claimed=False`.

This is the boundary used by original025 `safety_host.py:10–12,185–191,303–305`. The old H8/full-matrix `observe` functions also contain older direct-equality checks, but those are not the actual overridden TP4 `S.Controller.observe` path. Do not accidentally revive the earlier equality rule and treat another user's independent 0–3 process start/exit as evidence that this experiment interfered. Preserve external changes faithfully and reject any actual owned process on 0–3.

This process-membership predicate does not, by itself, prove every aspect of noninterference. The exact device mappings, nonprivileged container, actual FD observations, original lifecycle and source gates remain necessary.

## 3. Five exact labels and config binding

The required labels in frozen `fresh_snapshot_v2.py:271–275` exactly match the original TP4 `safety_host.py:38–40` producer schema:

| Config label | Derivation from an already verified original `OWNED.json` object `o` |
|---|---|
| `model-tuning-lab.arm` | `o['arm']` — e.g. actual role `dense` or `cpu-preflight`, not an inferred ON/OFF or candidate label |
| `model-tuning-lab.controller-sha256` | `o['host_sha256']`, required here to equal `20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30` |
| `model-tuning-lab.owner` | Original loaded `S.OWNER`: `bole-root-r6-20261017-001` (`owned_substrate.py:44`) |
| `model-tuning-lab.run` | `o['name']`, without the leading slash used by Docker inspect's Name field |
| `model-tuning-lab.source-manifest-sha256` | `o['source']['sha256']`, the appropriate original ON/OFF v2 manifest, never the new boundary child manifest |

For each of the four exact old CIDs, MAIN should reopen the historical OWNED Ref and its create receipt with the producer's real Ref schema: full SHA, and byte count when present. Do not require a nonexistent `bytes` field in an old path/SHA Ref. Before making the config entry, join:

1. `o['cid']` to the selected exact old CID; `o['image']` to the original fixed image; `o['host_sha256']` and its `sources['safety_host.py']` to the old controller SHA.
2. `o['source']` to the already bound corresponding original ON/OFF source and `o['name']`/`o['arm']` to the original create projection.
3. `o['create_receipt']` to the original create command/result: exit 0, returned full CID, exact `--name`, and the five original label arguments. The expected labels come from the old producer and receipt, not from whatever a fresh inspect happens to show.

After that independent proof, construct the config entry as follows; this is a mapping recipe, not an unverified projection of current Docker metadata:

```python
entry = {
    'id': o['cid'],
    'name': '/' + o['name'],
    'image': o['image'],
    'labels': {
        'model-tuning-lab.arm': o['arm'],
        'model-tuning-lab.controller-sha256': o['host_sha256'],
        'model-tuning-lab.owner': 'bole-root-r6-20261017-001',
        'model-tuning-lab.run': o['name'],
        'model-tuning-lab.source-manifest-sha256': o['source']['sha256'],
    },
}
```

Put all four entries in a **new** config's `old_containers` list. Verify their CID set equals the four previously selected `old_cids`. Keep the known lock, old-unit, deadline, source and output values. The frozen script chooses `old_containers` when present; retaining only `old_cids` deliberately produces `complete_historical_owner_identity_checked=False`. Preserve original OWNED/create refs in a separate binding receipt so that the new expected configuration has auditable provenance.

`inspect()` projects all `model-tuning-lab.*` labels, and `old_identity()` compares that projected mapping exactly to the expected five-key mapping (`fresh_snapshot_v2.py:202–203,217–230`). MAIN confirms the actual original containers have those five labels. If additional prefixed labels appear, retain the mismatch; do not discard an unexpected label just to make the observational check pass. The complete original owner validator remains authoritative for all resources, mounts and environment.

The three output booleans have different scopes. `expected_identity_matches` checks only CID/image; `complete_historical_owner_identity_checked` additionally checks the exact name and labels; `stopped_pid0_noexec_nooom_observed` is a state observation and does not itself require the full name/label match. MAIN must inspect all three for all four CIDs before and after, plus identity/state stability. Script `complete=True` only means collection completed. No one of these fields grants owner admission.

Original retained containers can have a nonzero init exit code after the owner's bounded stop. The existing cleanup predicate checks stopped/PID0/no ExecIDs/no OOM and the original cleanup/protected/release evidence; it does not require the sleep-container init ExitCode to be zero. Do not invent that extra requirement.

## Local checks performed

The two new source files' exact full hashes and the unchanged frozen snapshot hash were recomputed. The five label keys were compared directly against both producer and snapshot source. The existing unit-name pattern was evaluated against MAIN's two real unit names and accepts both. No remote resource assertion, active lock claim, device-idle claim or old-owner release claim is made by this supplement.
