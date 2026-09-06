# Template Selection

## Source Of Truth

Use `assets/huawei-template/PPT模板.pptx` as the template library. `assets/huawei-template/template-catalog.json` records the 42 source pages and their layout characteristics. Do not start a slide from a blank canvas before evaluating the catalog.

`template-map.json` records the final choice for every slide.

## Real-report examples

Also consult [the curated reference guide](../assets/insight-reference/GUIDE.md) and `assets/insight-reference/优秀洞察报告精选参考.pptx`. Its 24 pages supplement the 42 editable template pages. `catalog.json` records source filenames, PDF physical page numbers, checksums, page roles, and the value of each layout.

Set `insight_reference_id` on a deck-spec slide to select R01–R24 explicitly. `prepare_design_jobs.py` includes the chosen reference and its preview in `template-map.json` and the design prompt; without an explicit ID it uses the first role match. Inspect the preview and change the ID when another example fits the content better. A missing role match is acceptable: use the base template alone.

Keep the base template's typography and margins while borrowing the example's evidence organization. PDF-derived sample pages are image references, not editable layouts. Rebuild native text/tables/diagrams for the new content; do not use the full-page image in a delivered report. Source claims and future predictions have not been independently verified. Do not copy branding, confidentiality footers, or historical numbers into new work.


## Selection Order

Match in this order:

1. **Page role:** cover, agenda, section, overview, mechanism, evidence, comparison, table, synthesis, or appendix.
2. **Content structure:** one dominant visual, left/right split, asymmetric split, three columns, full-width process, matrix, or dense table.
3. **Asset type:** official screenshot, generated illustration, architecture, chart, table, or text-led argument.
4. **Information density:** low, medium, medium-high, or high.
5. **Sequence fit:** the layout must vary appropriately from adjacent slides while retaining a coherent deck rhythm.

## Required Mapping

Each slide entry includes:

```json
{
  "slide_id": "slide-04",
  "template_page": 18,
  "layout_type": "large-image-right-analysis",
  "density": "medium-high",
  "reason": "The page has one official product image and three interpretation groups.",
  "preserve": ["title_origin", "content_margins", "footer_position"],
  "adapt": ["image_crop", "column_ratio"],
  "rejected_pages": [
    {"page": 7, "reason": "Too many equal cards for one primary case."}
  ]
}
```

## Adaptation Rules

- Preserve the selected template's grid, not necessarily its original copy or artwork.
- Replace content slots according to the page contract; do not force content into irrelevant placeholders.
- Small changes to column width, image crop, or row height are allowed when the reason is recorded.
- If no exact template exists, choose the nearest role and structure, then document the adaptation. Do not invent an unrelated visual system.
- Use at least four layout families in a deck longer than eight pages unless the material genuinely requires repetition.

## Template Review

Reject a selection when:

- the main case becomes secondary;
- text would need to fall below the minimum size;
- the template creates empty decorative regions;
- the page becomes a generic dashboard;
- the layout duplicates both adjacent pages without narrative reason;
- the source template relies on an asset type unavailable for the slide.

## Template Asset Notice

The Huawei template is a user-provided internal asset. Its inclusion and use do not inherit the licenses of third-party workflow projects. See `assets/huawei-template/NOTICE.md`.
