# Deck Spec Schema

## Authority

`deck_spec.json` is the authoritative content contract after outline approval. Design prompts and editable reconstruction consume it; neither phase may silently rewrite its claims, numbers, titles, or source mapping.

## Deck-Level Fields

```json
{
  "schema_version": "1.0",
  "deck_id": "apple-on-device-ai",
  "title": "Deck title",
  "language": "zh-CN",
  "audience": ["OS planning", "AI architecture"],
  "management_question": "The one question this deck answers",
  "storyline": "One continuous narrative",
  "outline_approved": true,
  "template_library": "assets/huawei-template/PPT模板.pptx",
  "slides": []
}
```

## Slide Contract

```json
{
  "slide_id": "slide-04",
  "page_number": 4,
  "chapter": "02 Capability Analysis",
  "role": "mechanism",
  "title": "Conclusion-style editable title",
  "core_message": "The single judgment the page must establish",
  "bridge_from_previous": "Input received from the previous page",
  "bridge_to_next": "Result handed to the next page",
  "primary_case": {
    "name": "Human-readable case name",
    "description": "What happens in the case",
    "nature": "official_fact"
  },
  "support_groups": [
    {"heading": "Capability", "points": ["Concise fact", "Concrete effect"]}
  ],
  "bottom_conclusion": "Optional conclusion used by templates that include a conclusion strip",
  "content_nature": ["official_fact", "report_judgment"],
  "required_assets": [
    {
      "asset_id": "asset-04-a",
      "path": "assets/official/session-frame.png",
      "kind": "official_screenshot",
      "source_id": "A11",
      "required": true,
      "usage": "Primary visual"
    }
  ],
  "source_ids": ["A11", "A14"],
  "editable_priority": {
    "native_text": "required",
    "native_tables": "required",
    "native_diagrams": "preferred",
    "replaceable_images": "allowed",
    "full_slide_bitmap": "forbidden"
  },
  "template": {
    "page": 18,
    "layout_type": "large-image-right-analysis",
    "content_regions": ["left_visual", "right_analysis", "footer"],
    "selection_reason": "Matches one main image and three support groups."
  }
}
```

## Enumerations

Recommended `role` values: `cover`, `agenda`, `section`, `overview`, `mechanism`, `evidence`, `comparison`, `table`, `synthesis`, `appendix`.

Allowed `nature` values:

- `official_fact`
- `developer_observation`
- `report_judgment`
- `scenario_illustration`
- `recommendation`

## Validation Rules

- `slide_id`, page number, title, core message, role, template page, and template reason are required.
- A content slide has one primary case or primary visual and no more than three support groups.
- Required assets must exist before design generation.
- Every factual claim that materially supports the core message has a source ID.
- `bottom_conclusion` may be empty when the template does not use one; it must not duplicate the title verbatim.
- `outline_approved` must be true before full-deck design jobs are prepared.
- Image2 may suggest visual arrangement but must not modify contract text or introduce factual numbers.

## Optional Color Emphasis

Omit `emphasis` when no special attention-grabbing highlight is needed; ordinary structural color remains available. Do not create emphasis merely to add color. If the content establishes a difference, change or recommendation, record the exact phrases or identifiable diagram objects and the content-based reason before design generation:

```json
"emphasis": {
  "targets": ["route-2: preparation stage", "route-3: preparation stage"],
  "meaning": "difference",
  "reason": "Compare where preparation occurs in both alternatives; neither is ranked as the recommended route."
}
```

Targets must identify visible objects unambiguously, not vague “key content”. Color only these targets, not surrounding rows, borders or labels. Use the same meaning across pages. The designer follows this contract and cannot invent extra targets. An empty `targets` list means no special highlight; it does not constrain the structural palette. Evidence images retain their original colors.

## Deck-Level Structural Color

Before generating individual pages, establish `color_system` once. It distinguishes roles without declaring a winner. Example for a technical architecture report:

```json
"color_system": {
  "structural_palette": ["#356A8A", "#438478", "#786493"],
  "role_colors": {
    "flow orchestration": "#356A8A",
    "application capability": "#438478",
    "model processing": "#786493"
  }
}
```

Adapt roles to the actual report; do not force these example roles onto unrelated content. Each design job receives the same deck palette. When no palette is supplied, preparation provides coordinated starting colors; record a shared role mapping before page workers run. Structural colors require no object whitelist. Use dark text and light fills; retain labels so color is not the only way to read the diagram.
