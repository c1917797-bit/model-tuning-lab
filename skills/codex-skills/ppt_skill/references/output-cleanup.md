# Output Cleanup

## Delivery Contract

After successful finalization and validation, `final/` contains only regular PPTX files by default. Remove JSON, Markdown reports, build scripts, previews, temporary PDFs, owner lock files and nested production folders even when they were accidentally written inside `final/`.

Keep a non-PPTX deliverable only when the user explicitly requested it. Pass its exact filename, relative to `final/`, with repeatable `--keep-deliverable`:

```sh
python3 scripts/huawei_ppt.py finalize /path/to/project --keep-deliverable report.pdf
python3 scripts/huawei_ppt.py cleanup /path/to/project --keep-deliverable source.png
```

Each requested file must already exist directly in `final/`. Directory names, wildcards, symbolic links and paths outside `final/` are rejected before cleanup deletes anything.

## Production Files

Put every temporary script, candidate image, scratch JSON/Markdown, preview and QA report in the project production directories: `work/`, `design-prompts/`, `design-drafts/`, `editable-run/`, or `qa/`. These directories and the workflow's root metadata (`brief.md`, `outline.md`, `deck_spec.json`, `template-map.json`, `project.json`, design jobs/state/reviews) are deleted after delivery. Never write a final Markdown summary or helper script as an extra user deliverable unless requested. Give the result link and short verification summary in chat.

## Safety

- Cleanup requires `project.json` with `stage: finalized` and at least one regular, non-symlink final PPTX; an arbitrary PPTX alone is insufficient.
- Never clean a failed or blocked project. A symlinked `final/` is refused, including before finalization copies its output.
- Keep original user inputs outside the workflow-owned production directories and reserved metadata names. Unknown root files and shared directories are preserved; cleanup never sweeps the parent folder, sample library, template assets or installed skill scripts.
- Production-directory links are unlinked, never followed. Preserve explicitly requested deliverables by filename rather than retaining whole workspaces.
- Use `finalize --keep-workfiles` only when the user explicitly asks to retain the production workspace; it skips automatic cleanup.
- Use `cleanup` for an already finalized project whose metadata still exists. Once cleanup has removed metadata, a repeated cleanup is refused rather than inferring authorization from a remaining PPTX.
