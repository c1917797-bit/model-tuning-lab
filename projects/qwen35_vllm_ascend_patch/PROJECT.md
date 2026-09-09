# Qwen3.5 vLLM-Ascend runtime patch project

This directory contains the standalone, opt-in Python runtime monkeypatch for
Qwen3.5-27B on Ascend 910B4 with vLLM-Ascend 0.23.0.

## Provenance

- Source repository:
  `https://github.com/c1917797-bit/qwen35-vllm-ascend-patch.git`
- Imported branch: `feature/qwen35-validated-runtime-patch`
- Imported commit: `c61f5f984e13e2ca37fd410783b7e97f960a57f3`
- Imported tree: `64eb17532737d46e1ea825cb7d75468ea2f91630`
- Import merge: `d62a79ca208370604cb91a697f9f2d7c164d5d65`
- Source history: all 3 commits are retained because the exact source commit
  is the second parent of the import merge. This is not a squash or a file-only
  copy.

The source checkout was clean and synchronized with its source branch before
import. All 10 tracked source files were imported byte-for-byte. No uncommitted
or untracked source content was included, and no tracked source file was
modified during import.

Two monorepo governance files are additions rather than source-tree content:
this `PROJECT.md` and the adjacent `AGENTS.md`. The root
`projects/registry.yaml` is also updated. These explicit additions are the
only expected project-tree differences from the prefixed source tree.

Inspect the retained original history with:

```sh
git log --oneline c61f5f984e13e2ca37fd410783b7e97f960a57f3
git show c61f5f984e13e2ca37fd410783b7e97f960a57f3:README.md
```

## Current evidence boundary

The imported source packages the t12/GDN projection-fusion monkeypatch. Its
device-free contracts and single-NPU operator microbenchmark passed in the
source project, but it is not a promoted final candidate. The current
same-protocol c1 service screen missed the long-term TTFT/TPOT gates, and the
c1/c5/c8/c16 three-repeat matrix plus all-357 paired quality gate remain open.
Repository import is not performance or accuracy acceptance.

## Follow-up adaptations

- The source README still shows the standalone checkout path
  `/cache/cch/qwen35-vllm-ascend-patch`; monorepo deployment guidance should
  later use this project directory or an explicit read-only mount.
- Run the project contract from this directory and add a root-level test entry
  if the monorepo adopts a unified test runner. The current direct contract
  invocation passed during import.
- Synchronize only a future candidate that passes the declared live
  activation, performance, and quality gates; do not silently copy experimental
  worktree bytes into this project.

The import intentionally does not copy root maintainer skills. Maintenance uses
`../../.agents/skills.registry.yaml` and the root Maintainer Skill Tree.
