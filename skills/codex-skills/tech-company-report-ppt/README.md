# Tech Company Report PPT Skill

`tech-company-report-ppt` defines a unified workflow for Huawei-style technology insight and executive report decks. It combines disciplined report writing, page selection from a real Huawei template library, full-slide Image2 design drafts, automated draft review, and object-level editable PowerPoint reconstruction.

Chinese documentation: [README_zh.md](README_zh.md)

## Design Principle

The design draft and final PowerPoint serve different purposes:

- **Image2 draft:** establishes the complete 16:9 composition, hierarchy, density, visual rhythm, and asset placement.
- **Editable PPTX:** reproduces the accepted composition with native text, tables, shapes, connectors, and simple charts. Photos, product screenshots, and complex illustrations remain separate replaceable image objects.

A full-slide image may be used as a review reference, never as the final slide background.

## Workflow

1. Create and confirm one complete outline.
2. Turn the outline into `deck_spec.json`, the authoritative content contract.
3. Match every slide to a page in `assets/huawei-template/PPT模板.pptx` and record the decision in `template-map.json`.
4. Generate a complete Image2 design draft for every slide using the selected template render, approved content, and required assets.
5. Review drafts for copy fidelity, visual quality, information density, asset correctness, and template alignment.
6. Rebuild accepted pages as editable PowerPoint objects.
7. Finalize, render, compare, and validate the deck before delivery.

After outline confirmation, the default workflow continues automatically. It does not pause for a sample slide or per-slide approvals unless the user explicitly requests checkpoints.

## Command Entry Point

```bash
python scripts/huawei_ppt.py doctor
python scripts/huawei_ppt.py init --brief <input> --out <project>
python scripts/huawei_ppt.py prepare-design <project>
python scripts/huawei_ppt.py review-designs <project>
python scripts/huawei_ppt.py prepare-editable <project>
python scripts/huawei_ppt.py finalize <project>
python scripts/huawei_ppt.py status <project>
```

After the user approves the outline, set top-level `outline_approved` in
`deck_spec.json` to `true`; `prepare-design` enforces this gate. Running
`scripts/install_skill.sh` installs the vendored `editppt` runtime and links
this repository to `~/.codex/skills/tech-company-report-ppt`.

## Authoritative Files

```text
<deck-project>/
├── outline.md
├── deck_spec.json
├── template-map.json
├── design-prompts/
├── design-drafts/
├── design-jobs.json
├── design-run-state.json
├── design-review.json
├── editable-run/
├── qa/
└── final/<deck-name>.pptx
```

The content in `deck_spec.json` is authoritative. Generated slide text must not be recovered from Image2 output through OCR when the contract already supplies the correct text.

## Documentation Map

| Concern | Specification |
|---|---|
| Story, titles, and writing | `references/writing-and-storyline.md` |
| Huawei presentation style | `references/huawei-visual-style.md` |
| Selecting a template page | `references/template-selection.md` |
| `deck_spec.json` contract | `references/deck-spec-schema.md` |
| Full-slide Image2 design | `references/image2-design.md` |
| Automated draft review | `references/design-review.md` |
| Editable reconstruction | `references/editable-rebuild.md` |
| Final render and QA | `references/final-qa.md` |

## Quality Bar

A deck is not complete when any slide:

- uses a generic layout without a recorded template choice;
- contradicts or weakens the approved page contract;
- contains placeholder, garbled, invented, or OCR-guessed text;
- uses an Image2 imitation where official product evidence is required;
- looks like a dashboard card wall, marketing poster, or raw spreadsheet;
- contains a full-slide source raster under editable text;
- clips text or images, uses unreadable type, or leaves accidental empty regions;
- has not been rendered and visually checked after editable reconstruction.

## Attribution

Workflow concepts are adapted from the MIT-licensed projects [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) and [ningzimu/image-to-editable-ppt-skill](https://github.com/ningzimu/image-to-editable-ppt-skill). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and `LICENSES/`.
