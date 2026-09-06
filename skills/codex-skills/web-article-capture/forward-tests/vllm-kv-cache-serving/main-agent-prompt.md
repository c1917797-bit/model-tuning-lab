# Main Agent Prompt: Run vLLM KV Cache Serving Web Capture Forward Test

Orchestrate one isolated child-agent run. Keep page extraction inside the child run. Before dispatch, read this case's `candidate/prompt.md` and `candidate/input/urls.txt`, choose a fresh `<run-id>`, and verify that the output directory does not exist.

Dispatch only:

Paste the URLs from `forward-tests/vllm-kv-cache-serving/candidate/input/urls.txt` into the `<assigned URLs>` slot. Do not include this file path in the child prompt.

```text
请使用仓库 `SKILL.md` 完成网页图文抓取任务：

目标网页：
<assigned URLs>

输出目录：
.tmp/forward-tests/web-article-capture/vllm-kv-cache-serving/<run-id>/

请生成每个网页的 `source.md` + `images/` source package，并生成 `review.html` 汇总原始链接、本地图片缩略图、正文摘录和 package 链接。
```

After completion, inspect the output and run:

```powershell
python scripts/validate_capture_package.py <run-output> --require-images when-referenced
```

Open or inspect `<run-output>/review.html` for a human-readable sampling pass: original links, local images, and正文 excerpts should line up for every source.

Write `judgment.md` under the run output directory. Include whether isolation held, whether the output directory was fresh, whether one child agent can reliably capture the roughly 10-source webpage set expected for deep research, and whether `review.html` made the result easy to inspect.
