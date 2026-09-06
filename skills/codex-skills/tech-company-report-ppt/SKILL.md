---
name: tech-company-report-ppt
description: Use when creating or revising technology-company internal report PPT decks for insight reports, technical analysis, competitive analysis, strategy reviews, opportunity analysis, or executive briefings.
---

# Tech Company Report PPT

## Purpose

Create Huawei-style internal report decks whose conclusions, evidence, layout, and editable objects remain aligned from outline through final PowerPoint.

## Required Workflow

1. Build `outline.md` and `deck_spec.json`. Confirm the complete outline once; after confirmation, continue without per-slide approval.
2. Select a real page from `assets/huawei-template/PPT模板.pptx` for every slide and record the mapping in `template-map.json`. Also inspect matching pages in the [real-report reference library](assets/insight-reference/GUIDE.md): 24 selected pages from MWC and Google IO reports. Use `insight_reference_id` (R01–R24) to select a specific example; design preparation otherwise attaches a matching page by role. These PDF-derived examples teach evidence organization and are not editable finished slides.
3. Generate a complete 16:9 Image2 design draft for every slide. Treat it as the visual blueprint, not the final slide.
4. Review every draft against the content contract, template, assets, density, and visual rules. A failed page must be repaired or blocked.
5. Rebuild accepted drafts as object-level editable PowerPoint pages. Keep photos, product screenshots, and complex illustrations as separate replaceable images; do not use a full-slide screenshot as the finished page.
6. Render the final PPTX with PowerPoint-compatible tooling, pass structural and visual-fidelity QA, then remove production workfiles before delivery.

## Editable-Stage Ownership Gate

The accepted Image2 drafts are the visual specification. Once `prepare-editable` starts, the integrated `image-to-editable-ppt` / `editppt` workflow exclusively owns slide construction and final assembly.

- Run every page through `editppt prepare -> page worker -> editppt run record`.
- Build the deck only with `editppt run finalize` after every expected page is recorded.
- Do not use `artifact-tool`, PptxGenJS, python-pptx, Open XML, PowerPoint UI automation, or another presentation generator to create a parallel editable deck from `deck_spec.json`.
- Generic presentation tooling may be used only inside a page worker to produce that page's declared native objects, or after finalization for rendering and QA.
- Do not place any `.pptx` in `final/` before `editppt run finalize` succeeds.
- PowerPoint compatibility normalization is allowed only after `editppt run finalize`, only on that exact assembled deck, and only to repair package compatibility. It must not redesign pages or replace the editppt build. Re-run the editppt validator after normalization.
- A structurally valid but visually simplified manual redraw is a failed reconstruction, not a fallback.
- If page workers cannot run, keep the project blocked at `editable_prepared`; report the blocker instead of bypassing the workflow.

## Read Before Each Phase

- Outline and copy: [writing-and-storyline.md](references/writing-and-storyline.md)
- Huawei visual system: [huawei-visual-style.md](references/huawei-visual-style.md)
- Template selection: [template-selection.md](references/template-selection.md)
- Content contract: [deck-spec-schema.md](references/deck-spec-schema.md)
- Full-slide Image2 drafts: [image2-design.md](references/image2-design.md)
- Draft review: [design-review.md](references/design-review.md)
- Editable reconstruction: [editable-rebuild.md](references/editable-rebuild.md)
- Final acceptance: [final-qa.md](references/final-qa.md)

Worker handoffs use [design-worker.md](prompts/design-worker.md) and [editable-page-worker.md](prompts/editable-page-worker.md).

## Non-Negotiable Rules

- Use white backgrounds and dark body text with a coordinated structural palette for categories, stages, components and chart series. Establish a deck-level `color_system` and reuse role colors across pages. Reserve red and other attention-grabbing emphasis for `emphasis.targets`; an empty target list permits normal structural color. Review both unjustified emphasis and whether color helps readers understand the structure.

- Titles are conclusions; reading titles alone must reveal the story.
- One slide carries one main point, one primary case or visual, and no more than three support groups.
- Vendor facts, report judgments, and scenario illustrations must be visibly distinguishable.
- Image2 designs the whole slide. It does not replace official screenshots or become the final full-slide bitmap.
- Final text comes from `deck_spec.json`, never OCR guessed from a design draft.
- When text must be read from a visual source, use the model's local vision capability directly. Do not invoke PaddleOCR, Tesseract, cloud OCR, or `editppt` text-hint OCR.
- Main text, tables, diagrams, connectors, and simple charts are editable PowerPoint objects.
- Final editable renders must remain materially faithful to the accepted Image2 drafts in hierarchy, geometry, density, and visual rhythm.
- Visual meaning must survive reconstruction: distinct viewpoints, states, assets, and roles cannot be replaced by repeated images or generic placeholder shapes.
- If an icon exists in the accepted effect image, extract and reuse that exact icon first as a separate replaceable image object. Recreate it natively only when faithful extraction is impossible or the user explicitly requires vector editability; never substitute an unrelated generic icon.
- Do not revive the legacy editable-title/static-middle-image/editable-conclusion workflow.

## Default Deliverables

Create a dedicated production project, never use the source-report folder, skill repository, or a shared document folder as the production project. During production, keep the outline, contracts, design drafts, reconstruction state, and QA artifacts inside the project. Put one-off Python/JS/shell scripts and temporary exports in `work/`, never alongside the delivered PPTX. After a successful finalization, delete them by default. Do not generate a final Markdown report, JSON summary, helper script, or README as an extra deliverable unless requested. Give the completion message in chat. The delivered project contains only `final/<deck-name>.pptx` plus any PDF, PNG, or source file the user explicitly requested. Use `finalize --keep-workfiles` only when the user explicitly asks to retain production files.

Read [model-vision-text-extraction.md](references/model-vision-text-extraction.md), [visual-fidelity-gate.md](references/visual-fidelity-gate.md), and [output-cleanup.md](references/output-cleanup.md) before editable reconstruction and delivery.

Third-party attribution is recorded in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
