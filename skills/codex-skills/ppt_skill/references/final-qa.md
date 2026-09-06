# Final PowerPoint QA

## Production QA Artifacts

- final `.pptx`;
- rendered PDF;
- one PNG per slide;
- contact sheet;
- final validation report;
- optional design-draft versus editable-render comparison sheet.

## Structural Checks

- PPTX opens as a valid package.
- Slide count and order match `deck_spec.json`.
- Slide size matches the source template.
- Every image relationship resolves and media hashes match recorded provenance.
- Required notes are present; unrequested notes are absent.
- No full-slide design raster is used under editable overlays.
- Main text, tables, diagrams, connectors, and simple charts are native editable objects where required.
- Microsoft PowerPoint opens the file without a repair warning. A package that requires repair is not deliverable even when deterministic validation passes.

## Content Checks

- Titles and key copy exactly match the content contract.
- Sources correspond to the claims they support.
- Facts, report judgments, and scenario illustrations remain distinguishable.
- No prompt text, placeholder, OCR error, invented value, or production note appears.
- The sequence of titles still tells the approved story.

## Visual Checks

Render with PowerPoint or a PowerPoint-compatible engine, then inspect every page at presentation scale:

- no clipping, overflow, overlap, accidental crop, image stretch, or font substitution;
- no body text below the readability threshold;
- no unexplained red emphasis or pale-red panel fill;
- no low-value empty regions;
- screenshots are legible and show the intended evidence;
- charts and tables retain headers, labels, and alignment;
- recurring title, margin, footer, and page-number positions remain stable;
- page density and composition remain close to the accepted design draft.

## Comparison Review

Compare the final render with the accepted Image2 draft. Differences are allowed when they improve editability, text fidelity, or official-asset accuracy. Differences that weaken hierarchy, alter evidence, change the main case, or materially reduce density must be repaired.

## Completion Rule

Do not report completion while any required page is missing, blocked, unrecorded, or visually unreviewed. The final report states:

- output path and slide count;
- render and validation result;
- pages with accepted warnings;
- any content or asset limitation that remains.

These artifacts exist only while producing and validating the deck. After a successful finalization, apply [output-cleanup.md](output-cleanup.md): retain only the final PPTX and any additional final format explicitly requested by the user. Do not deliver or leave behind prompts, drafts, manifests, previews, contact sheets, validation reports, or QA directories.

If PowerPoint normalizes the assembled deck for compatibility, save that normalized copy as the same final artifact, reopen it once without a warning, and run the editppt deck validator again. This is a compatibility pass over the editppt output, not a second authoring path.

Before cleanup, finalized status requires both the project stage written by the unified finalizer and a passing `editable-run/final/validation.json` produced by `editppt run finalize`. After cleanup, the verified final PPTX in `final/` is the delivery artifact; intermediate validation evidence has intentionally been removed.
