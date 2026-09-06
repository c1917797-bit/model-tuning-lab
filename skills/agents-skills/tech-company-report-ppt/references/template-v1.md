# Template V1

## Canvas

- Slide size: 16:9, `13.333 x 7.5 in`.
- Background: white.
- Title zone: top `0.85 in`.
- Middle canvas zone: `x=0.45 in`, `y=1.02 in`, `w=12.45 in`, `h=5.25 in`.
- Bottom conclusion zone: `x=0.55 in`, `y=6.58 in`, `w=12.25 in`, `h=0.58 in`.

## Page Types

| Page type | Purpose | Required editable text | Middle visual |
|---|---|---|---|
| Cover | Open the report | title, subtitle, date/owner if needed | optional light cards |
| Agenda / section | Separate chapters | agenda items, current highlight | none or light divider |
| Standard content | Main analysis page | title, bottom conclusion | image2 or source image |
| Table / opportunity | Editable summary table | title, table, bottom conclusion | optional small icons |
| Synthesis | Final judgment | title, bottom conclusion | image2 synthesis map |

## Standard Content Layout

Use the same structure across the deck:

```text
editable title
thin divider
[ image2 middle canvas: architecture / flow / matrix / cards / screenshot wall ]
editable bottom conclusion bar
```

The middle image should be generated to this visual ratio: about `2.37:1` (`12.45 / 5.25`). If the generator only supports 16:9, ask for a wide central infographic with minimal top and bottom whitespace, then crop carefully.

## Agenda Rules

- Agenda pages should be simple: one line per chapter or subchapter.
- Highlight only the current chapter or current subtopic.
- Do not add explanatory subtitles unless the user asks.

## Table Rules

- Use editable PPT tables when the user may revise text.
- Keep table text short and use red only for key terms.
- Avoid priority columns unless explicitly requested.

