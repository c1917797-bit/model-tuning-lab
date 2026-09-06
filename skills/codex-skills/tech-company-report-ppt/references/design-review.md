# Automated Design Review

## Agent Review Input

After viewing every selected draft, the reviewing agent writes
`design-review-input.json`. Each slide must set all fourteen checks to `true`; an
absent review is a blocker even when the PNG dimensions are valid.

```json
{
  "slides": [{
    "slide_number": 4,
    "checks": {
      "contract_match": true,
      "no_pseudo_text": true,
      "required_assets_present": true,
      "information_density": true,
      "red_discipline": true,
      "structural_color_clarity": true,
      "no_dashboard_wall": true,
      "no_crop_overlap_or_drift": true,
      "template_match": true,
      "no_simulated_official_ui": true,
      "no_redundant_copy": true,
      "visual_semantics_explicit": true,
      "distinct_views_and_states": true,
      "asset_decomposition_feasible": true
    },
    "observed_emphasis_targets": [],
    "notes": []
  }]
}
```

## Output

Run `scripts/review_designs.py` to combine deterministic image checks with the
agent review and write `design-review.json`. It does not approve a page solely
because the PNG exists.

## Review Dimensions

### Content Fidelity

- title and key labels match `deck_spec.json`;
- core message is visually dominant;
- primary case and required assets are present;
- no invented number, source, logo, product UI, or claim;
- no placeholder, lorem ipsum, production note, or garbled text;
- title, body, and conclusion do not repeat the same sentence.

### Template Fidelity

- composition follows the selected template's page role, grid, title position, and content regions;
- recorded adaptations match `template-map.json`;
- the slide does not revert to a generic blank-canvas layout.

### Huawei Visual Quality

- medium-high information density without unreadable text;
- one dominant visual and no more than three support groups;
- inspect the image and list every attention-grabbing highlight (red or another color), excluding ordinary structural category/stage/series colors in `observed_emphasis_targets`, using the contract identifiers; include unauthorized objects with descriptive identifiers rather than omitting them;
- `structural_color_clarity` checks that the deck palette distinguishes roles consistently, peers have equal visual weight, text contrast is sufficient, and color is paired with labels. A neutral page passes when structure is already clear; neither grayscale nor added color is rewarded for its own sake;
- the observed inventory must match `emphasis.targets` exactly; without an emphasis contract it must be empty. The script checks this inventory, not pixel semantics, so visual inspection remains mandatory;
- reject decorative red labels (such as “分析”), arbitrary winner-like route highlighting, or color spreading from a declared phrase to its entire row; original evidence-image colors are excluded;
- verify the reason is a substantive difference/change/recommendation supported by the content. “Important” or “main path” alone does not pass;
- no default pale-red panels, dashboard card wall, decorative icon wall, heavy shadow, gradient, or marketing hero treatment;
- no accidental empty block, clipping, overlap, stretched image, or drifting alignment;
- official screenshots remain readable and are not redrawn.

### Reconstruction Feasibility

- text regions can be recreated as native text;
- tables, cards, flows, connectors, and simple charts have clear object boundaries;
- complex images can remain separate replaceable image objects;
- the layout does not depend on an inseparable full-slide bitmap effect.
- every visual region has an explicit semantic purpose and identifiable evidence;
- distinct viewpoints, product states, devices, and time steps use distinct assets;
- complex assets can be separated without replacing them with generic shapes.

## Result Shape

```json
{
  "deck_id": "apple-on-device-ai",
  "passed": false,
  "slides": [
    {
      "slide_id": "slide-04",
      "candidate": "design-drafts/slide-04.png",
      "status": "repair",
      "scores": {
        "content_fidelity": 0.95,
        "template_fidelity": 0.88,
        "visual_quality": 0.82,
        "reconstruction_feasibility": 0.91
      },
      "blocking_issues": ["Official screenshot was redrawn"],
      "repair_mode": "regenerate",
      "repair_instructions": "Place the supplied screenshot unchanged in the left visual region."
    }
  ]
}
```

## Status Rules

- `accepted`: no blocking issue and all required dimensions pass.
- `repair`: a localized or structural issue has an actionable correction.
- `blocked`: a required asset, factual decision, or viable composition is unavailable after the allowed iterations.

Only `accepted` slides advance. A deck passes only when every expected slide is accepted.

## Repair Policy

- Use Image2 editing for localized spacing, cropping, or emphasis problems.
- Regenerate for wrong structure, missing evidence, fake product UI, weak primary message, or template mismatch.
- Do not hide a problem by shrinking text or adding labels that merely describe the design.
- Do not lower the bar because the slide has already consumed three attempts; record the blocker.
