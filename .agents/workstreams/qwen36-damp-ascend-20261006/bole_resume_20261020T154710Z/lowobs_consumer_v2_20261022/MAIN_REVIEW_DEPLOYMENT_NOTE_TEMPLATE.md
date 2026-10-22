# MAIN review / source-only deployment record — template

This is a separate record. Do not rewrite the preceding `SOURCE_ONLY_MANIFEST.json` or the three reviewed runtime files.

## Review already reported by MAIN

MAIN reviewed both v2 consumers, their exact diff, the unchanged helper and source-invariant logic. The role-bound cleanup read seam is acceptable. No actual model-result `consume()` invocation is authorized by this record. The old short ON/OFF pair FAIL remains unchanged.

Runtime identities remain:

| File | bytes | SHA256 |
|---|---:|---|
| `read_short_results_v2.py` | 4850 | `48bf3d952a932d0733c620bcc09a5d5f1a4f19e52d97512759b9597b42a07f69` |
| `consume_pair_v2.py` | 8828 | `cee870a32b8f2087d63bb3c9f2d3dbd81efa6a317ad0eb044f86478f5943c0c0` |
| `cleanup_summary.py` | 3957 | `1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687` |

Previous manifest: 5416 bytes, SHA256 `e8d9244c1865d1d596e0616c657aa52595e412290c4c4d5866497015b47f6686`.

## Exact deployment and validation scope

Package:

```text
/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/lowobs_consumer_v2_20261022
```

Fresh exclusive output:

```text
/opt/host/vnf/austinov/run-bole-lowobs-consumer-source-check-20261022T080000Z
```

Deploy the pinned runtime three files, `test_cleanup_boundary.py`, `verify_source_invariants.py`, unchanged old manifest, both exact original ON-v2 fixture files, and the separately reviewed `remote_validate_source_only_v1.py`. Keep the fixture relative paths under `fixtures/original_ON_v2/{cpu-preflight,dense}/cleanup.json`.

The runner checks all pinned inputs before executing children. It confines the unchanged seven-control suite to an exact-copy zone inside the fresh output; the tests' temporary files cannot alter the deployment package. Source invariants read the deployed consumers and the exact absolute frozen R3 baseline. The final two children use `--help` only. All four children use `-I -B -S`, standard-library-only imports, a 25-second child cap, a 90-second whole cap, bounded logs, and inherited address-space/CPU/file limits. A timeout kills only the runner's newly created child process group. It preserves exclusive raw stdout/stderr and source/control input Refs before/after.

Invocation for MAIN through the already required host-development contract:

```text
python3 -I -B -S /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/lowobs_consumer_v2_20261022/remote_validate_source_only_v1.py --execute
```

No verify value belongs in this command, any file, any log or Git. The existing fixed output is never overwritten or resumed. No Torch, owner, container, NPU or model-result consumer is invoked by the four reviewed child commands.

## Fill only from actual deployment / runner evidence

- MAIN deployment operation and UTC: **NOT EXECUTED IN THIS TEMPLATE**.
- Runner deployed bytes/SHA verified: **PENDING**; use the separate prepare record's exact Ref.
- Actual source-check operation / exit code / UTC: **PENDING**.
- Exact `RESULT.json` Ref: **PENDING**.
- Raw child stdout/stderr Refs: **PENDING**.
- Source and control inputs before/after equality: **PENDING**.
- Project `./scripts/validate-mst.sh` evidence for the checkpoint: **PENDING**.

Any `PASS_SOURCE_ONLY` is limited to seven reader-boundary controls, source invariants and two CLI help checks. `numerical_qualification`, `paired_gate_pass`, `performance_admitted`, `formal_performance`, `task_accuracy` and `technology_success` remain false. This record neither changes the failed old pair nor extends the hard report deadline of 2026-10-22 12:38:41 UTC.

## Preserve raw independent reviews alongside the checkpoint

MAIN preserves the original files; do not replace them with this template's paraphrase or modify the other agent's draft.

- Readiness / cleanup ABI source review: `/workspace/scratch/e65c435145b1/lowobs_review_notes/READINESS_SOURCE_REVIEW.md`; 18468 bytes; SHA256 `2d4e8771f7861e539d0e0b0f00d25a12fc780ca5ffe664602143de83ba4e243c`.
- Independent causal source review (exact Ref supplied by MAIN): `/workspace/scratch/e65c435145b1/old_runtime_review/source_review.md`; 15445 bytes; SHA256 `92fab207a06a78d5d190c80230dfade5b39b9d1d7b56f9dad2028336e3312bd5`.

No remote execution or deployment has occurred merely because these prepared files and placeholders exist.
