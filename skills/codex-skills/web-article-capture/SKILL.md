---
name: web-article-capture
description: >-
  Extract article/main webpage text and original inline images into compact source packages for downstream agents. Use when Codex needs browser-rendered webpage capture for source grounding, media-rich official pages, article text, webpage image assets, or reusable web source packages.
---

# Web Article Capture

Use Codex in-app Browser to extract each target page's article/main正文图文. Produce one compact Markdown source package per page for downstream agents.

## Browser Entry

Before browser work, read `browser:control-in-app-browser`. Browser is usually controlled through Node REPL with `agent.browsers.get("iab")`.

## Capture Principles

First understand the rendered page, then choose the extraction approach that fits that page.

The target is the page's正文 reading experience: the main text plus the original images that belong inside that正文 flow. Preserve the relationship between paragraphs, headings, captions, charts, diagrams, and nearby images.

Use dynamic page-specific extraction when needed. A product page, docs page, blog post, keynote page, and live blog may each need a different DOM path or asset strategy. Let the rendered page structure decide the capture logic.

Before extracting, identify the smallest rendered content scope that contains the page title and正文 flow. Do not use a broad `main`/page wrapper if it also contains post-body modules. Stop the正文 at the first semantic transition into non-article material such as previous/next links, related content, recommendations, comments, product/contact/support panels, newsletter/social modules, author-more lists, or site chrome.

Audit the tail before writing `source.md`: the final headings and blocks should still read as part of the article/main content. If the tail has shifted into non-article modules, tighten the extraction boundary and rerun the media pass.

Prefer images that a reader would naturally treat as part of the article/main content: hero images, body figures, charts, diagrams, tables rendered as images, and image/caption pairs tied to nearby正文. Keep image references near the text they support.

For each media candidate, check ownership before downloading: nearest heading/text, caption, container semantics, dimensions, link target, and whether ancestors look like article body rather than navigation, footer, sidebar, recommendation, comments, support, social, language, or decorative UI. Reject placeholders, tracking pixels, logos, avatars, icons, language/UI glyphs, support/contact graphics, and recommendation thumbnails unless they are clearly discussed by the正文. When uncertain, mention the uncertainty in capture notes instead of silently treating it as complete.

Screenshots of the rendered page are not source images. A page with no正文 images can have an empty `images/` directory and a note in `source.md` saying whether visible media was absent or rejected as non正文.

## Browser Recovery

Treat Browser failures as page-specific states to investigate before changing approach.

- When navigation times out in a batch run, retry that URL in a fresh tab before deciding it is blocked.
- When a page uses lazy-loaded figures, scroll to the正文 figure/chart area and let the rendered page load real image assets before collecting `currentSrc`, `srcset`, `data-src`, or equivalent asset URLs.
- When Browser access remains blocked after focused retry, record the blocked stage in `source.md`: browser setup, tab creation, navigation, load state, DOM snapshot, or image asset loading.
- Use official source fallbacks only after Browser recovery fails. Label the capture mode in `source.md` as rendered capture, rendered partial, or official-source fallback; include the fallback URL or repository path and any version mismatch risk. Do not present fallback capture as equivalent to rendered-page capture.

Use the validator before handing off.

## Output

For each page, write one directory:

```text
<output-root>/<source-slug>/
  source.md
  images/
```

`source.md` is the downstream-facing file. Include:

- source URL, title, captured date, publisher/date/author when available;
- article/main正文 in readable Markdown structure;
- local image references such as `![caption](images/image-01.jpg)` near the related text;
- original image URL and caption/nearby text below each image;
- brief capture notes when they help a later agent judge reliability, including capture mode, blocked stage or fallback source,正文 boundary/tail notes, and kept/rejected/uncertain media summary when relevant.

`images/` contains the original webpage images referenced by `source.md`.

When asked for a `review.html`, make it an inspection surface: one section per source with original link, capture mode, package link,正文 excerpt, tail excerpt or boundary note, local image thumbnails with captions/nearby text, and media warnings when important figures may be missing or non正文 candidates were rejected.

Run the validator before handing off:

```powershell
python web-article-capture/scripts/validate_capture_package.py <output-root> --require-images when-referenced
```
