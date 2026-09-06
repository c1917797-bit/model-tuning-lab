# Page Contracts

Create `page-contracts.json` before writing prompts or building the deck.

Each standard page contract should contain at least:

```json
{
  "type": "standard",
  "title": "Editable slide title",
  "coreMessage": "Core message of this page",
  "keyPoints": ["Short point 1", "Short point 2", "Short point 3"],
  "bottomConclusion": "Editable bottom conclusion from the outline or user confirmation, not rewritten by image2",
  "visualType": "architecture / call-chain / matrix / evidence-cards / agent-loop",
  "middleImage": "image2-middle/slide-XX.png",
  "sourceNote": "official screenshot / generated visual / user asset / web source"
}
```

For every page, also declare revision-prone content explicitly:

```json
{
  "editableObjects": ["table", "legend", "key metrics", "module labels"],
  "bitmapContent": ["complex topology diagram"],
  "deduplicationRule": "Each content item has one owner only"
}
```

## Rules

- The title must come from the page contract. Do not rewrite it during build.
- The bottom conclusion must come from the page contract or the user's original wording.
- Image2 prompts may use `coreMessage` and `keyPoints`, but must not invent or rewrite the bottom conclusion.
- If content is not enough to fill a page, mark the gap instead of padding with AI-flavored filler.
- Do not force opportunities into every page; prefer chapter synthesis pages or summary pages.
- For pages tied to external facts, prefer official screenshots or sourced assets. Generated visuals must not replace factual evidence.
- Any table, matrix, schedule, roadmap, KPI grid, legend, key number, or decision criterion must appear under `editableObjects` and be built as a native PowerPoint object.
- `bitmapContent` must never be the sole holder of revision-prone or message-critical text.
- `editableObjects` and `bitmapContent` must not contain the same fact, label, comparison row, metric, or conclusion. Minimal diagram identifiers are the only exception.
