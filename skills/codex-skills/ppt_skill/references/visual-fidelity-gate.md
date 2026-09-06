# Visual Fidelity Gate

Structural validity is necessary but insufficient. Every reconstructed page must preserve the accepted design's visual meaning, not merely its title and approximate boxes.

## Required Checks

Each page workspace must contain `visual-fidelity.json`:

```json
{
  "passed": true,
  "checks": {
    "visual_semantics_preserved": true,
    "region_geometry_preserved": true,
    "density_preserved": true,
    "distinct_views_and_states_preserved": true,
    "complex_assets_not_approximated": true,
    "icon_language_consistent": true,
    "typography_hierarchy_preserved": true
  },
  "regions": [],
  "blocking_issues": []
}
```

## Meaning-Preserving Reconstruction

- Record what each region communicates, its visual evidence, its distinct views or states, and invalid substitutions.
- Keep photos, product UI, people, devices, animals, complex icons, and illustrations as separate replaceable image or SVG assets.
- Rebuild text, tables, flow boxes, connectors, simple diagrams, and simple charts as native PowerPoint objects.
- Never reuse one image to stand in for different viewpoints, devices, moments, or states.
- Never replace a complex semantic asset with a generic rectangle, circle, emoji, or unrelated stock icon.
- Icons visible in the accepted effect image are first-choice source assets. Extract them as independent images whenever possible; native redrawing is secondary, and generic icon substitution is a blocking fidelity failure.
- Match the accepted design's hierarchy, region proportions, whitespace, density, and emphasis before matching tiny decorative details.

Any missing or false check blocks page recording and finalization.

During final visual QA, compare authored color emphasis against the slide contract as well as the accepted draft. Undeclared attention-grabbing highlights or implied preference among peers must be corrected in the draft and reconstructed page; visual fidelity is not a reason to preserve an emphasis error. Preserve original evidence-image colors.

Preserve legitimate structural colors from the deck color_system and accepted draft, including coordinated category headings, icons, chart series and light region fills. These are excluded from the emphasis-target inventory. Do not desaturate a page merely because emphasis.targets is empty. Verify consistent role colors and equal visual weight among peers in final visual QA.
