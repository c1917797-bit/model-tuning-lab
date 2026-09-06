# Output Contract

This skill creates compact source packages for downstream agents.

## Directory Shape

```text
<output-root>/<source-slug>/
  source.md
  images/
```

## `source.md`

`source.md` is the default file for downstream agents to read. It carries source metadata, capture mode, article/main text, local image references, original image URLs, and reliability notes in reading order.

Use this shape:

```md
# Page title

Source: https://example.com/article
Captured: 2026-06-04

## Source Notes

- Publisher: Example
- Date: 2026-06-04
- Capture mode: rendered capture
- Selected content: smallest article/main scope; stopped before related/comments/page chrome
- Media summary: kept body figures; rejected non正文 UI/decorative images
- Capture notes: brief reliability notes when useful

## Content

Article paragraph...

![Image caption or nearby text](images/image-01.jpg)

Image source: https://example.com/original-image.jpg
Caption: Original caption when available.

Article continues...
```

## Images

Save original webpage images referenced by `source.md` under `images/`.

Name images predictably:

```text
images/image-01.jpg
images/image-02.png
```

Put enough context around each image in `source.md` for a later agent to understand why the image belongs there: nearby heading, paragraph, caption, chart title, diagram label, and original image URL.

Before saving a media file, confirm it belongs to正文. Reject placeholders, tracking pixels, logos, avatars, UI icons, language glyphs, support/contact graphics, recommendation thumbnails, and decorative assets unless the article/main text clearly discusses them.

When the page has no正文 images, keep `images/` empty and record whether visible media was absent or rejected as non正文.

## Fallbacks

Prefer rendered Browser capture. If Browser access remains blocked after retry, a package may use an official source fallback such as repository Markdown or a documented source endpoint.

When using fallback capture, record:

- the blocked Browser stage;
- the fallback URL or repository path;
- any version or rendering mismatch risk;
- whether images are complete, partial, or unavailable.
