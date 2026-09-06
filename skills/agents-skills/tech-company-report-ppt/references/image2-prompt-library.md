# Image2 Prompt Library

Use these templates when writing `image2-prompts/slide-XX.md`. Prompts must generate only the middle canvas, not a full slide.

## Base Middle-Canvas Template

```text
Create a polished wide infographic panel for the middle area of a technology-company internal report slide.
Canvas role: middle content only.
Aspect ratio: exactly 2.37:1 wide panel, optimized to fill a PowerPoint middle canvas. Do not create a 16:9 full slide.
Do NOT include a slide title, footer conclusion, page number, logo, speaker portrait, placeholder, lorem ipsum, or garbled text.
Style: white background, restrained red accents for key points, blue/gray capability cards, light-gray section backgrounds, thin grid lines, compact executive-report density.
Language: <Chinese / English>. Use concise readable labels.
Topic: <page topic>.
Required content: <exact short labels / modules / flow nodes>.
Visual layout: <architecture / pipeline / matrix / evidence cards / roadmap>.
Text density: medium.
Output should fill the panel edge-to-edge with minimal empty top and bottom margins.
No red warning boxes. No red lightbulb. No decorative hero image. No speaker-only screenshot.
```

## Capability Map / Multi-Layer Architecture

```text
Visual layout: five-layer horizontal architecture.
Layers from bottom to top: <layer 1>, <layer 2>, <layer 3>, <layer 4>, <layer 5>.
Each layer contains 3-5 compact capability modules.
Use small line icons, thin dividers, and subtle blue/gray cards.
Add one small "official evidence / source anchor" card if source image is provided, but do not fake official evidence.
```

## Dual-Lane Overview

```text
Visual layout: two main lanes with supporting capability bars.
Left lane: <system capability -> apps>.
Right lane: <apps -> system intelligence>.
Bottom supporting bars: <developer tools>, <performance engineering>, <spatial / cross-device>.
Use clear directional arrows and numbered nodes.
```

## Call Chain / Mechanism Chain

```text
Visual layout: left-to-right call chain.
Nodes: <user input> -> <semantic indexing> -> <intent matching> -> <tool/API call> -> <app execution> -> <result attribution>.
Use compact cards and arrows.
Highlight key interfaces in red.
```

## Agent Loop

```text
Visual layout: closed-loop engineering cycle.
Loop nodes: objective -> profile/observe -> locate bottleneck -> modify -> verify -> regress/learn.
Use circular or rectangular loop with metrics panel.
Show "goal-driven" as the organizing idea.
```

## Opportunity Table Middle Canvas

```text
Visual layout: dense editable-like table style, but if table text needs future revision, prefer PPT editable table instead of image2.
Columns: <capability>, <platform change>, <planning direction>, <department opportunity>.
No priority column unless requested.
Use red emphasis on key phrases only.
```

## Left Image + Right Cards

```text
Visual layout: large evidence image area on the left, 3 numbered insight cards on the right.
Bottom of the panel may include a small neutral note strip, but not the final slide conclusion.
Do not generate a full slide title or footer.
```

## Chapter Synthesis / Integrated Judgment

```text
Visual layout: 3-4 large conclusion cards with small evidence tags.
Focus on synthesis, not long explanation.
Use one bottom internal map or capability chain if useful.
No exaggerated strategy slogans.
```
