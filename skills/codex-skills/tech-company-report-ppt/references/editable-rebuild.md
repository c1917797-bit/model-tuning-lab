# Editable PowerPoint Reconstruction

## Objective

Rebuild each accepted design draft as an object-level editable PowerPoint page while preserving the selected Huawei template and the approved visual composition.

## Source Priority

1. `deck_spec.json` for all authoritative text, facts, numbers, and source IDs.
2. `template-map.json` and the source template page for geometry, masters, guides, and fixed elements.
3. The accepted Image2 draft for composition, hierarchy, relative sizing, and visual rhythm.
4. Original source assets for screenshots, photos, diagrams, and logos.

Never use visual text extraction to override known contract text. Read unknown labels directly with the model's local vision capability; do not call PaddleOCR, Tesseract, cloud OCR, or editppt text hints.

## Object Decisions

Rebuild as native PowerPoint objects:

- titles, body copy, captions, labels, and numbers;
- tables and table emphasis;
- cards, bands, dividers, arrows, connectors, and flow nodes;
- simple architecture diagrams;
- basic bar, line, scatter, and process charts when their data is known;
- page number, footer, source IDs, and conclusion strips.

Keep as separate replaceable images:

- official product screenshots;
- photos and video frames;
- complex generated illustrations;
- visual textures that cannot be reproduced faithfully with simple shapes.
- icons already present in the accepted effect image, when they can be cleanly extracted. Preserve each as an independent image object instead of redrawing or substituting it.

### Effect-Image Icon Priority

1. Inspect the accepted effect image for the exact icon.
2. If the icon can be isolated cleanly, extract it and place it as a separate replaceable image object.
3. Recreate it with native shapes only when extraction is not faithful or vector editability is explicitly required.
4. Never replace an available source icon with an unrelated library icon, emoji, or approximate symbol.

Forbidden final construction:

- a full-slide design PNG used as the page background;
- the full-slide PNG covered with editable text;
- flattened tables or diagrams when native objects are practical;
- low-quality vector tracing of a photo or complex illustration.

## Runtime Flow

Use the integrated `editppt` run model:

1. prepare the accepted design drafts and page contracts;
2. dispatch one worker per page when multi-agent execution is available;
3. reconstruct only inside the assigned page workspace;
4. write the page manifest and preview;
5. record only pages that pass deterministic validation;
6. finalize the deck from recorded manifests.

Before recording a page, write `visual-fidelity.json` in that page workspace. All checks in [visual-fidelity-gate.md](visual-fidelity-gate.md) must pass. A visually simplified redraw is blocked even when the PPTX is structurally valid.

The parent owns orchestration and final assembly. A page worker owns one page and must not edit deck-wide contracts or another page's files.

### No Parallel Authoring Path

After the editable run is prepared, `editppt` is the authoritative state machine and assembler. The parent must not create a separate deck directly from `deck_spec.json`, even when a generic presentation tool can produce valid editable shapes faster. That path discards the approved design geometry and makes the design review meaningless.

The only valid final deck is the output rebuilt from recorded page manifests by `editppt run finalize`. A `.pptx` created before all pages are recorded is a diagnostic artifact and belongs under `qa/`, never `final/`.

## Geometry And Text

- Use the source template's actual slide dimensions and guides.
- Record coordinates in a consistent slide coordinate system.
- Use Microsoft YaHei for Chinese and Arial for English/numbers unless the template requires a compatible installed substitute.
- Fit copy by editing line breaks and object dimensions before reducing font size.
- Preserve readable hierarchy; body text must not drop below the documented visual minimum.

## Page Manifest Requirements

Each page manifest records:

- source draft and hash;
- template page;
- slide dimensions;
- every native object and its coordinates;
- every image asset and provenance;
- text from the content contract;
- notes status;
- validation warnings and result.

Speaker notes are included only when requested. Notes must remain editable and must not be synthesized merely to fill the file.

## Acceptance

A page is recordable only when it can be independently rebuilt from its manifest, contains no forbidden full-slide raster pattern, and its preview passes the page-level checks in `final-qa.md`.

The deck is deliverable only when every page is `recorded`, finalization validation passes, and the final render is compared with the accepted design contact sheet. Package validity or lack of text overflow alone does not establish visual fidelity.
