# Light QA

Default QA is intentionally small. Use this checklist after building the deck.

## Required Checks

- PPT page count matches `page-contracts.json`.
- Every page title is editable PPT text.
- Every bottom conclusion is editable PPT text and matches `page-contracts.json`.
- Every table-like structure resolves as a native PowerPoint table rather than an image.
- Comparison matrices, schedules, roadmaps, KPI grids, legends, key numbers, and decision criteria are editable PowerPoint objects.
- No message-critical or revision-prone content exists only inside a bitmap.
- No fact, comparison row, KPI label, legend, explanatory sentence, or conclusion is duplicated between a bitmap and an editable object.
- Diagram text is limited to identifiers necessary to read the mechanism.
- Middle images exist for all image pages.
- Middle images are not placeholders.
- Middle images fill the reserved middle canvas without small-island centering, obvious white borders, obstruction, or subject-cropping.
- Middle images do not generate the PPT title, page number, or bottom conclusion.
- Middle images contain no placeholder, lorem ipsum, garbled text, or obvious typo.
- Contact sheet is generated.
- Missing middle images make the build fail; missing-image placeholder PPTs are not allowed.
- Temporary outputs and smoke-test artifacts are cleaned.

## Not Default

Do not run these unless the user explicitly asks for a formal defense deck:

- formal defense pack
- source register
- presenter notes
- draw.io
- golden sample alignment
- full profile QA
- complex component regression QA
