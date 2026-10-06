# HYPIC Qwen3.6 TP4 2048-token E2E validation

## Objective

Complete a fresh HYPIC Paper-to-Ascend validation on physical NPU0-3 within
24 hours. The historical 1024-token quality evidence is reference-only; this
workstream owns a new 2048-token baseline and treatment.

## Frozen resources

- Branch: `work/hypic-qwen36-e2e-2048-20261006`
- Clone: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`
- Artifact root: `/cache/cch/hypic-qwen36-e2e-2048-20261006`
- Physical devices: NPU0-3 only
- CPU set: 112-191
- Service port: 8223
- HCCL port range: 27000-27100
- NPU4-7 and their containers are protected.

## Commands

Static no-side-effect gate:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh --self-test
```

Resumable full controller:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh
```

The controller validates existing units before skipping them. Do not delete or
overwrite partial JSONL files; incomplete indexes are the resume boundary.

## Current state

Planned. No NPU workload has been launched from this workstream yet.
