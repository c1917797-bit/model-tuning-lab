# NVIDIA PC Web Article Capture Task

Use `SKILL.md` to extract article/main webpage text and original inline images from the URLs below:

```text
<paste URLs here>
```

Write one source package per page under:

```text
.tmp/forward-tests/web-article-capture/nvidia-pc/<run-id>/
```

Also write a review page at:

```text
.tmp/forward-tests/web-article-capture/nvidia-pc/<run-id>/review.html
```

The review page is for human inspection of the captured sources. Use one section per source with:

- page title and original webpage link;
- local images from the source package, shown as thumbnails with captions or nearby text;
-正文 excerpt from `source.md`;
- links to the local source package and `source.md`.

Final response should briefly state which source packages were generated, where `review.html` was written, and whether each `source.md` includes article/main text with the relevant original webpage images.
