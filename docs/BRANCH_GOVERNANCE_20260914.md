# Branch governance, 2026-09-14

## Steady-state branch set

The live branch namespace is intentionally identical locally and on
`origin`: `main` plus the six branches attached to active task worktrees.

- `main`
- `work/drror-objective-loop-skill-20260909`
- `work/qwen35-experience-ingestion-20260909`
- `work/qwen35-performance-delivery`
- `work/qwen35-sparse-prefix-reproduction`
- `work/qwen38-nvfp4-ascend-910b4-20260910`
- `work/sliminfer-qwen36-ascend-piercing-20260914`

Do not infer a new task from an archive tag. A restored experiment needs a new
task record, ownership proof, and a new work branch.

## Retired local branch recovery

The following removed local names are recoverable from exact annotated tags:

- `archive-local/qwen35-query-rewrite-20260909` ->
  `archive/qwen35-query-rewrite-pre-canonical-20260909`
- `archive-local/qwen35-shortgpt-20260909` ->
  `archive/qwen35-shortgpt-semantic-reject-20260909`
- `work/exp-20260904-dynamic-moe-paper-to-ascend` ->
  `archive/retired-20260912/exp-20260904-dynamic-moe-paper-to-ascend`
- `work/exp-20260904-qwen35-dense-mtp-paper-to-ascend` ->
  `archive/retired-20260912/exp-20260904-qwen35-dense-mtp-paper-to-ascend`
- `work/exp-20260904-qwen38-prefix-cache-general-eval-final` ->
  `archive/retired-20260912/exp-20260904-qwen38-prefix-cache-general-eval-final`
- `work/handoff-status-sync-20260904` ->
  `archive/retired-20260912/handoff-status-sync-20260904`
- `work/exp-20260903-qwen38-prefix-cache-general-eval` ->
  `archive/retired-20260914/exp-20260903-qwen38-prefix-cache-general-eval`
- `work/exp-20260904-qwen38-gdn-native-state-layout` ->
  `archive/retired-20260914/exp-20260904-qwen38-gdn-native-state-layout`
- `work/update-ascend-maintainer-skills-20260909` ->
  `archive/retired-20260914/update-ascend-maintainer-skills-20260909`

## Retired origin branch recovery

- `work/drrqr-dk112-handoff-20260907` ->
  `archive/retired-20260914/drrqr-dk112-handoff-20260907`
- `work/drrqr-paper-parity-lessons-20260911` ->
  `archive/consolidated-20260912/drrqr-paper-parity-lessons-20260911`
- `work/exp-20260903-qwen38-prefix-cache-general-eval` former remote tip ->
  `archive/retired-20260914/exp-20260903-qwen38-prefix-cache-general-eval-remote-tip`
- `work/exp-20260904-qwen38-gdn-native-state-layout` ->
  `archive/retired-20260914/exp-20260904-qwen38-gdn-native-state-layout`
- `work/update-ascend-maintainer-skills-20260909` ->
  `archive/retired-20260914/update-ascend-maintainer-skills-20260909`

The prefix-cache general-eval local tip was one commit ahead of its former
remote tip, so both exact tips have separate immutable tags.
