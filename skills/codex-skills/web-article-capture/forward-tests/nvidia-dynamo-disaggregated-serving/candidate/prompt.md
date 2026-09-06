# NVIDIA Dynamo Disaggregated Serving Web Capture Task

Use `SKILL.md` to extract article/main webpage text and original inline images from the URLs below:

```text
<paste URLs here>
```

Write one source package per page under:

```text
.tmp/forward-tests/web-article-capture/nvidia-dynamo-disaggregated-serving/<run-id>/
```

Also write a review page at:

```text
.tmp/forward-tests/web-article-capture/nvidia-dynamo-disaggregated-serving/<run-id>/review.html
```

The review page is for human inspection of the captured sources. Use one section per source with original webpage link, local image thumbnails,正文 excerpt from `source.md`, and links to the local source package.

Final response should briefly state which source packages were generated, where `review.html` was written, and whether each `source.md` includes article/main text with relevant original webpage images.
