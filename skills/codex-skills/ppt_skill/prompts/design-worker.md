# Design Worker Prompt

You own exactly one slide design job.

## Inputs

- Slide contract: `{{SLIDE_CONTRACT_PATH}}`
- Selected template render: `{{TEMPLATE_RENDER_PATH}}`
- Required assets: `{{ASSET_PATHS}}`
- Huawei style reference: `{{HUAWEI_STYLE_PATH}}`
- Previous/next titles: `{{SEQUENCE_CONTEXT}}`
- Output candidate: `{{OUTPUT_PATH}}`

## Task

Create one complete 16:9 Image2 design draft. Follow the slide contract exactly and use the selected template page as the grid and composition reference.

If the design job has `template_reference.insight_reference`, inspect its local preview for evidence organization and read its reuse value. Keep the base template visual system and current slide contract; the historical sample is not a factual source or a finished slide.

The page must contain one dominant point, one primary case or visual, and no more than three support groups. Preserve supplied official screenshots and user assets; do not redraw product UI. Use white background, dark text, coordinated structural colors with restrained contract-defined emphasis, strong alignment, and medium-high information density.

Do not invent facts, numbers, logos, interfaces, citations, or body copy. Do not add placeholder, prompt, production, or source-PPT language. Avoid dashboard card walls, generic robots, decorative gradients, unexplained red text, and pale-red panel fills.

## Output

Return only:

```json
{
  "slide_id": "{{SLIDE_ID}}",
  "candidate_path": "{{OUTPUT_PATH}}",
  "backend": "image2",
  "asset_usage": [{"asset_id": "...", "status": "used"}],
  "self_check": {
    "contract_match": true,
    "template_match": true,
    "required_assets_present": true,
    "no_invented_content": true,
    "reconstructable": true
  },
  "notes": "Short factual note"
}
```

Do not edit deck-wide contracts, template mappings, another slide, or the final PPTX.

Use the deck `color_system` for categories, components, stages and chart series. These structural colors may appear in headings, icons, lines and light region fills without individual emphasis targets. Keep roles consistent across slides and peers equal in visual weight. Keep body text dark. The `emphasis` contract governs red or other attention-grabbing highlights only; an empty contract does not disable structural colors. Preserve original evidence-image colors. Avoid decorative red labels or an unsupported visual winner among peer alternatives.
