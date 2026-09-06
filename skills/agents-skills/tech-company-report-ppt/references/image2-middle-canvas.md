# Image2 Middle Canvas Prompts

## Size And Crop Rules

- Standard PPT pages are 16:9.
- Three-zone layout:
  - editable title zone at the top;
  - middle canvas at fixed ratio `2.37:1`, approximately `12.45 x 5.25 in`;
  - editable bottom conclusion zone.
- Image2 must generate the middle-canvas ratio, not a complete 16:9 slide.
- If the generated image has too much top/bottom whitespace, regenerate instead of shrinking it into the PPT.
- If the ratio is slightly wrong, crop safe top/bottom whitespace only.
- Never crop the subject content.
- If cropping hides or damages the main content, regenerate with a tighter ratio instruction.
- Do not let the middle image duplicate the PPT title.
- Do not let the middle image duplicate the PPT bottom conclusion.

## Prompt Shape

Use this structure for each standard content page:

```text
Create a polished wide infographic panel for the middle area of a technology-company internal report slide.
Canvas role: middle content only.
Aspect ratio: exactly 2.37:1 wide panel, optimized to fill a PowerPoint middle canvas. Do not create a 16:9 full slide.
Do NOT include a slide title, footer conclusion, page number, logo, speaker portrait, placeholder, lorem ipsum, or garbled text.
Style: white background, red accents for key points, blue/gray capability cards, thin grid lines, compact executive-report density.
Topic: <page topic>.
Required content: <exact short labels / modules / flow nodes>.
Visual layout: <architecture / pipeline / matrix / evidence cards / roadmap>.
Text density: medium; use concise English or Chinese labels as requested.
Output should fill the panel edge-to-edge with minimal empty top and bottom margins.
No red warning boxes. No red lightbulb. No decorative hero image. No speaker-only screenshot.
```

## What Goes Into Image2

- Mechanism diagrams
- Architecture maps
- Flow charts
- Capability matrices
- Screenshot walls
- Product/UI concept cards
- Medium-density explanatory labels

## What Must Not Go Into Image2

- Tables or comparison matrices
- KPI grids or key numeric callouts
- Roadmaps, schedules, or decision criteria
- Legends whose labels may change
- Critical claims, conclusions, or source notes

If a source or generated image combines a useful diagram with any item above, crop the revision-prone region and rebuild it with native PowerPoint tables, shapes, charts, or text.

## What Stays Editable In PPT

- Slide title
- Chapter/agenda labels
- Bottom conclusion
- Opportunity summary tables that need later editing
- Critical numbers or decision asks that the user may revise

## Regeneration Triggers

Regenerate the middle image when:

- content is centered as a small island with too much whitespace;
- the aspect ratio causes visible cropping;
- the generator returns a full-slide layout with empty title/footer areas instead of a middle-panel image;
- generated text contains typos, placeholder words, or mixed language errors;
- the visual uses warning boxes, decorative icons, or speaker footage without technical value;
- the image duplicates the PPT title or bottom conclusion.
