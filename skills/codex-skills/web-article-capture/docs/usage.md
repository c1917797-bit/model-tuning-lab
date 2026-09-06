# 使用方式

请在 prompt 中明确目标 URL 和输出目录，并要求 Agent 使用 `$web-article-capture`。工作区内的临时交付统一写到 `.tmp/web-article-capture/<任务名>/`。

## 可复制 prompt

```text
请使用 $web-article-capture 抓取以下网页的正文和正文图片：
- https://example.com/article
- https://example.com/product-announcement

输出到 .tmp/web-article-capture/my-capture/。
请为每个网页生成 source.md + images/ source package；同时生成 review.html，汇总原始链接、抓取模式、正文与尾部摘录、package 链接及本地图片缩略图。交付前运行 validator，并报告受阻页面、fallback 和校验结果。
```

普通抓取不需要子 Agent 或独立 checker；主 Agent直接控制 Codex in-app Browser、生成交付物并完成结构与语义复核。只有用户明确要求运行 `forward-tests/` 时，才需要允许启动隔离子 Agent。

## 输入与输出

- **输入**：一个或多个可访问 URL、输出目录，以及是否需要 `review.html`。
- **每页输出**：`<output-root>/<source-slug>/source.md` 和 `<output-root>/<source-slug>/images/`。
- **可选检查页**：`<output-root>/review.html`，用于集中检查原始链接、正文边界、图片和 fallback 风险。
- **临时目录**：从工作区根目录执行时使用 `.tmp/web-article-capture/<任务名>/`；不要把临时抓取结果写进 skill 子仓。

抓取时，Agent应选择包含标题和正文的最小范围，在相关推荐、评论、支持/联系模块和页面 chrome 之前结束；图片应放在其支持的正文附近。Browser 部分可用或受阻时，应记录抓取模式、受阻阶段和 fallback 来源。

## 校验命令与工作目录

优先从工作区根目录 `Mozhi-s-AgentWorkspace/` 执行，完整命令为：

```powershell
python skills/web-article-capture/scripts/validate_capture_package.py .tmp/web-article-capture/my-capture --require-images when-referenced
```

如果当前目录已经是 skill 根目录 `skills/web-article-capture/`，使用：

```powershell
python scripts/validate_capture_package.py ../../.tmp/web-article-capture/my-capture --require-images when-referenced
```

校验单个、目录内直接含有 `source.md` 的 package 时，同样传入该 package 路径：

```powershell
# 工作区根目录
python skills/web-article-capture/scripts/validate_capture_package.py .tmp/web-article-capture/my-capture/example-article

# skill 根目录 skills/web-article-capture/
python scripts/validate_capture_package.py ../../.tmp/web-article-capture/my-capture/example-article
```

validator 检查 package 是否只有 `source.md` 和 `images/`、本地图片引用是否存在且留在 package 内、图片扩展名是否支持，以及文件名是否疑似截图。它不检查正文是否完整、尾部是否越界、图片是否真正属于正文，也不验证原始 URL 或 fallback 的可靠性。

## 完成标准

- 每个目标 URL 都有 source package，或在最终说明中明确记录受阻阶段。
- `source.md` 包含来源 URL、抓取日期、可读正文、抓取模式与必要的可靠性说明。
- 正文图片保存在 `images/`，在相关正文附近引用，并记录原始图片 URL 或上下文；无正文图片时保留空目录并说明原因。
- validator 通过；若无法通过，交付说明列出具体错误和未完成项。
- 主 Agent人工检查正文起止边界、图片归属、`review.html`（如要求）和 fallback 风险。
