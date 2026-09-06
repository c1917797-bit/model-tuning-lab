---
name: tech-company-report-ppt
description: Use when creating or revising technology-company internal report PPT decks for insight reports, technical analysis, competitive analysis, strategy reviews, opportunity analysis, or executive briefings.
---

# Tech Company Report PPT

## Core Principle

Build report decks with three stable zones: **editable title**, **middle canvas**, and **editable bottom conclusion**. Use image2 only for visually complex diagrams or source imagery. Keep all message-critical and revision-prone content as native editable PowerPoint objects.

## Editability Contract

- Build tables with native PowerPoint tables. Never rasterize tables into image2.
- Build comparison matrices, schedules, roadmaps, KPI blocks, legends, decision criteria, and key numeric callouts with native tables, charts, shapes, or text.
- Keep labels editable when users are likely to rename modules, adjust wording, or update values.
- Use bitmap middle canvases only for complex topology, architecture, mechanism, screenshot, or illustrative content that does not require routine text editing.
- If an image contains a useful diagram plus a table, crop the table out and recreate it as a native PowerPoint table.
- Treat text embedded in an image as decorative or explanatory only; never place the sole copy of a critical claim, number, decision, table value, source, or conclusion inside a bitmap.

## Content Ownership And Deduplication

- Assign every visible fact, label, comparison, number, or conclusion to exactly one owner: editable PowerPoint object or bitmap.
- Before generating an image, create a content ownership list for the page. Put mechanism and topology in the bitmap; put comparison, interpretation, metrics, legend, and conclusion in editable objects.
- Do not repeat editable table headers, comparison rows, KPI labels, explanatory sentences, or conclusions inside the image.
- Allow only minimal identifiers inside diagrams when necessary for comprehension, such as `GPU 0`, `Router`, `Expert 1`, or `Stage 2`.
- If image output repeats editable content, regenerate the image with the duplicated labels explicitly banned. Cropping is acceptable only when it removes the complete duplicated region cleanly.

## Default Workflow

When the user says “I need a PPT about X”, run the full chain by default:

1. **Understand the brief**: infer topic, audience, page count, language, and output folder when not specified.
2. **Create `page-contracts.json`**: each page needs role, title, core message, key points, bottom conclusion, middle visual type, and source/evidence note.
   Add a content ownership map that lists `editableObjects` and `bitmapContent` without duplication.
3. **Initialize the project**: create `image2-prompts/`, `image2-middle/`, `preview/`, `qa/`, and `workflow-notes.md`.
4. **Generate per-slide prompts**: write `image2-prompts/slide-XX.md` for every standard/synthesis image page.
5. **Generate or source middle canvases**: use image2/image generation for complex diagrams only; save each result as `image2-middle/slide-XX.png`. Route tables and revision-prone content to native PowerPoint objects.
6. **Assemble the PPT**: use editable titles, conclusions, tables, matrices, legends, labels, and decision content. Place static middle images only where editability is not required.
7. **Light QA**: export slide PNGs/contact sheet and check practical blockers.

The user should not need to ask separately for page contracts, prompt files, image files, or contact sheet; they are default artifacts.

## Template Rules

- Read `references/template-v1.md` before building a deck.
- Read `references/style.md` before choosing page tone, density, typography, and emphasis.
- Read `references/page-roles.md` before creating the outline or choosing page types.
- Read `references/page-contracts.md` before writing `page-contracts.json`.
- Read `references/image2-middle-canvas.md` and `references/image2-prompt-library.md` before writing image2 prompts.
- Read `references/dependencies-and-fallbacks.md` before deciding how to produce middle canvases.
- Use `references/light-qa.md` for the default verification pass.
- Keep agenda and section pages editable.
- Use native editable tables for every table-like structure, not only opportunity summaries.
- Do not rebuild complex image2 diagrams with low-quality PPT boxes unless the user explicitly asks for fully editable diagrams.

## Middle Canvas Rules

- The middle image must fit the reserved content area and avoid large white margins.
- Generate the middle image at the reserved middle-canvas ratio, about `2.37:1`; do not use a generic 16:9 full slide unless it will be cropped into this middle area.
- It may include medium-density body text, but title and bottom conclusion must stay outside the image.
- Prompts must explicitly ban: slide title, footer, page number, placeholder text, lorem ipsum, garbled text, fake evidence, and speaker-only screenshots.
- If image2 produces wrong text, too much empty margin, a too-small center diagram, or a full-slide layout, regenerate with a tighter middle-canvas aspect ratio instead of shrinking it inside PPT.
- Crop only safe top/bottom whitespace when the generated ratio is slightly off; never crop the subject or duplicate title/conclusion zones inside the image.
- Do not ask image2 to generate tables, comparison rows, KPI grids, roadmaps, or legends that contain content users may revise. Build those with native PowerPoint objects.

## Light QA

Default QA is intentionally small:

- PPT page count matches the page contract.
- Every page title is editable text.
- Every bottom conclusion is editable text and matches the contract/user wording.
- Every table, comparison matrix, schedule, roadmap, KPI grid, legend, and key number is a native editable PowerPoint object.
- No critical or revision-prone table content is trapped inside a bitmap.
- Middle images exist for all image pages and are not placeholders, blank, tiny, cropped incorrectly, or dominated by low-value screenshots.
- Middle images fill the reserved canvas and do not duplicate PPT titles, page numbers, or bottom conclusions.
- Middle images do not duplicate editable tables, matrices, legends, metrics, labels, or explanatory copy.
- Contact sheet exists and shows no obvious overlap, title clipping, or conclusion clipping.

Do not run formal evidence packs, source registers, draw.io, speaker notes, golden-sample alignment, full-profile QA, or complex component regression QA unless the user explicitly asks for a formal defense deck.

## Default Output Structure

```text
<output-project>/
  page-contracts.json
  workflow-notes.md
  image2-prompts/
  image2-middle/
  preview/
  qa/
  final.pptx
```

`workflow-notes.md` should record topic decomposition, page role choices, middle-canvas visual intent, generation or fallback method, QA result, and known risks.

## Failure Conditions

A deck is not acceptable if:

- the middle visual is a low-quality script-drawn box diagram instead of image2 or a useful source image;
- the middle visual looks like native PPT block art rather than an image2/source-image middle canvas;
- a standard content page is built with a missing-image placeholder;
- title or bottom conclusion is trapped inside a bitmap;
- a table, comparison matrix, roadmap, KPI grid, editable legend, critical number, or decision criterion is trapped inside a bitmap;
- the same material information appears both in a bitmap and in an editable PowerPoint object;
- image2 rewrites the bottom conclusion;
- image2 fabricates or rewrites a bottom conclusion not present in the page contract;
- the middle image covers, repeats, or conflicts with title or conclusion zones;
- the middle image uses the wrong ratio, making the subject too small or cropped;
- the main visual is a decorative or speaker-only screenshot;
- the visual uses red warning boxes, red lightbulbs, exclamation-style risk icons, or excessive left red bars;
- contact sheet is missing;
- pages look sparse, unstyled, or like raw spreadsheet exports;
- temporary scripts, `tmp-smoke`, or test outputs are left behind after generation.

## Useful Scripts

- Initialize project folders/prompts: `scripts/init_three_zone_project.js <page-contracts.json> <output-project-dir>`
- Build a v1 deck: `scripts/build_three_zone_deck.js <page-contracts.json> <output.pptx>`
- Smoke-test the skill: `scripts/smoke_test_v1.js`
