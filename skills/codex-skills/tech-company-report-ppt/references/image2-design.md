# Image2 Full-Slide Design

## Role

Image2 creates a complete 16:9 visual design draft for each slide. The draft is the composition reference for editable reconstruction. It is not the final slide and must not be used as a full-slide bitmap in the delivered PPTX.

## Inputs

Every design job receives:

- the exact slide contract from `deck_spec.json`;
- the selected template page render;
- the relevant Huawei visual rules;
- required official screenshots and user assets;
- previous and next slide titles for sequence awareness;
- language, canvas ratio, and output path;
- explicit provenance labels for official facts, report judgments, and scenario illustrations.

Do not launch a design job when a required asset or template render is missing.

## Prompt Contract

The prompt must instruct Image2 to:

- preserve the selected template's grid, hierarchy, title origin, and content boundaries;
- create the entire 16:9 slide composition;
- keep the contract title and body wording exact when text is rendered;
- use one main visual and no more than three support groups;
- maintain Huawei-style white background, dark text, coordinated structural colors and optional contract-defined emphasis, and medium-high density;
- leave official product screenshots unchanged except for placement and crop;
- avoid invented data, fake logos, fake UI, garbled text, placeholder copy, and source labels with no meaning;
- avoid dashboard card walls, decorative gradients, generic robots, speaker portraits, and unnecessary red panel fills;
- make every highlighted element's purpose visually evident.

## Text Policy

Rendered text in the draft may be non-editable because the draft is temporary. The final page uses the authoritative text from `deck_spec.json`. If unknown visual text must be inspected, the model reads it directly with local vision and records the result as transient geometry guidance. External OCR engines and editppt text hints are not part of this workflow.

If Image2 cannot reliably render dense copy, use shortened visual labels in the design draft while retaining complete final copy in the slide contract. The design review must record this planned reconstruction difference.

## Asset Policy

- Official screenshots remain original pixels; Image2 must not redraw them.
- Explanatory diagrams and scenario scenes may be generated when clearly treated as illustrations.
- User-provided logos, photos, and diagrams are strict assets. Do not replace them without recording a blocker.
- Complex visual backgrounds must still leave separable regions for final editable text and shapes.

## Jobs And State

One job represents one slide. Save:

```text
design-prompts/slide-XX.json
design-drafts/slide-XX.png
design-jobs.json
design-run-state.json
```

The main agent owns the content contract, template mapping, asset mapping, review, and selected result. A slide worker owns only its assigned prompt and candidate images.

## Iteration

- Local text or spacing defect: edit the existing draft.
- Incorrect composition, weak hierarchy, wrong case, or template mismatch: regenerate the page.
- Retain at most three candidates per page.
- A page that still fails after three candidates is marked `blocked`; it does not advance to editable reconstruction.

Use the deck `color_system` for categories, components, stages and chart series. These structural colors may appear in headings, icons, lines and light region fills without individual emphasis targets. Keep roles consistent across slides and peers equal in visual weight. Keep body text dark. The `emphasis` contract governs red or other attention-grabbing highlights only; an empty contract does not disable structural colors. Preserve original evidence-image colors. Avoid decorative red labels or an unsupported visual winner among peer alternatives.
