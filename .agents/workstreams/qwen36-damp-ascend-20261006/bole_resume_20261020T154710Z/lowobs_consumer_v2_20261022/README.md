# Low-observation cleanup consumers v2 — prepared for MAIN review

Status: source-only draft. No remote deployment or runtime result comparison occurred. The old short ON/OFF pair failure remains unchanged and does not admit any NPU experiment.

## Exact change

The frozen producer writes cleanup summaries as `{path, sha256}`. Both old consumers passed those summaries to a strict `{path, bytes, sha256}` reader, so successful retained cleanup evidence could not reach the actual comparison.

`read_short_results_v2.py` and `consume_pair_v2.py` change only the release-summary read seam to a dedicated cleanup reader. The required paths are derived from the source-bound output root and exact role:

| Summary key | Expected file |
|---|---|
| `model_release` | `out/dense/cleanup.json` |
| `CPU_release` | `out/cpu-preflight/cleanup.json` |

`cleanup_summary.py` is copied unchanged from the verified actual v4 helper: 3957 bytes, SHA256 `1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687`. It checks the exact Ref2 shape, canonical absolute role path, ordinary ancestors/file, 4 MiB cap, complete SHA and stable file identity. It parses the same checked bytes and never rewrites the producer summary.

Each consumer reads at most 3958 helper bytes, verifies the exact helper length/SHA, and compiles those checked bytes in a fresh private namespace. It does not resolve a `cleanup_summary` module alias or use a cached module of that name. The original generic Ref3 reader and all original cleanup, state, HTTP, coverage, performance and qualification predicates are retained. The state comparator and its pinned source Ref are unchanged.

`PATCH.diff` is the exact diff against the two SHA-pinned original R3 files. `verify_source_invariants.py` checks that every original arm statement/predicate is unchanged after normalizing only the declared cleanup read call; it also checks unchanged complete function source, original short source Refs, original short main except its result filename, and exclusive result writes.

## Output identities

Both outputs are siblings of the new consumer scripts, with exclusive `xb` creation. They do not target the frozen R3 v1 output:

- `LOWOBS_SHORT_NPU_COMPARE_v2.json`
- `LOWOBS_FIXED131_PAIR_SCREEN_v2.json`

The screen CLI still prints the same result object as the old CLI; it additionally retains that object in the exclusive v2 file with flush/fsync. No runtime result output exists in this draft. Neither consumer was called on model results during this preparation.

## Source-only validation

Seven focused controls passed under `python3 -I -B`. Their positive controls read the exact retained ON-v2 CPU and model cleanup JSON bytes supplied by MAIN (1245/1213 bytes), verified against the real producer SHA. Only the fixture Ref path is rebased to its local copy; these files are never described as a new experiment or new numerical/state result.

The controls cover: real producer bytes without rewriting; unchanged generic Ref3 rejection of Ref2; bad SHA; cross-role path mismatch; rejection of a Ref3 alias at the strict cleanup-only seam; cached helper alias poisoning; and changed helper bytes. Source invariants and both isolated CLI help checks also passed. All 12 recorded validation inputs remained byte-identical. Raw stdout/stderr, exact argv and exit codes are retained in `validation_v1/`.

These controls do not evaluate model mathematics, run the state comparison, measure throughput, or qualify NPU execution. `paired_gate_pass`, `performance_admitted`, `formal_performance`, `task_accuracy`, and `technology_success` remain false in the source-only validation record. The runtime consumers retain their original false qualification flags.

## Review/deployment boundary

MAIN review is pending. No frozen source, original result, remote file, host process or NPU was changed. The runtime package consists of the two v2 consumers plus the unchanged sibling helper. The fixture and validation files are review evidence, not runtime model inputs. Any later deployment must use a fresh assigned directory and preserve this source identity; actual lowobs qualification and same-configuration performance remain gated by the original prerequisites and the fixed authorization deadline. Project validation was not run in this scratch-only preparation.
