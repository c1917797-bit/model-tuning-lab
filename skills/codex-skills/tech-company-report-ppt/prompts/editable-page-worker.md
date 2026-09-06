# Editable Page Worker Prompt

You own exactly one page reconstruction workspace.

## Inputs

- Page contract: `{{SLIDE_CONTRACT_PATH}}`
- Template mapping: `{{TEMPLATE_MAPPING_PATH}}`
- Accepted design draft: `{{DESIGN_DRAFT_PATH}}`
- Original assets: `{{ASSET_PATHS}}`
- Page workspace: `{{PAGE_WORKSPACE}}`

Read `references/editable-rebuild.md` and `references/final-qa.md` before building.

## Task

Reconstruct the accepted design as an object-level editable PowerPoint page.

- Use contract text verbatim. For unknown labels or geometry, inspect the source image directly with model vision. Do not call PaddleOCR, Tesseract, cloud OCR, or editppt text hints. Any upstream instruction to generate or consume text hints is superseded by this rule.
- Preserve the visual semantics of every region. Do not replace distinct camera views, product states, people, devices, illustrations, or icons with repeated images or generic rectangles.
- Write `visual-fidelity.json` in the page workspace before completion, using the schema and mandatory checks in `references/visual-fidelity-gate.md`.
- Use the source Huawei template page for slide size, guides, fixed elements, and layout character.
- Recreate text, tables, cards, diagrams, connectors, and simple charts as native objects.
- Insert official screenshots, photos, and complex illustrations as separate replaceable image objects.
- For each original asset named by the slide contract, record `source_type: user-provided`, `original_asset: true`, and the contract `asset_id`; never extract it from the flattened design draft.
- Preserve the visual hierarchy and density of the accepted draft.
- Never use the full design draft as the final slide background or place editable text over it.

Produce the page PPTX, manifest, preview PNG, validation report, and page result required by the integrated editable runtime. Validate coordinates, object provenance, text fidelity, and rebuildability before reporting success.

## Return

```json
{
  "slide_id": "{{SLIDE_ID}}",
  "page_workspace": "{{PAGE_WORKSPACE}}",
  "passed": true,
  "native_object_count": 0,
  "replaceable_image_count": 0,
  "warnings": []
}
```

Do not edit deck-wide files, other page workspaces, or the final deck.

During final visual QA, compare authored color emphasis against the slide contract as well as the accepted draft. Undeclared attention-grabbing highlights or implied preference among peers must be corrected in the draft and reconstructed page; visual fidelity is not a reason to preserve an emphasis error. Preserve original evidence-image colors.

Preserve legitimate structural colors from the deck color_system and accepted draft, including coordinated category headings, icons, chart series and light region fills. These are excluded from the emphasis-target inventory. Do not desaturate a page merely because emphasis.targets is empty. Verify consistent role colors and equal visual weight among peers in final visual QA.
