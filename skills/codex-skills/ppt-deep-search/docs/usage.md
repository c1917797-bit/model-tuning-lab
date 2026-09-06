# 使用方式

`ppt-deep-search` 是生成 PPT 前的来源理解审阅流程。它不生成 PPT、不规划页数目录、不产出内容简报；做到 `source_understanding_review.html` 并完成审批后结束。

## 适用场景

使用这个 skill 处理以下任务：

- 从论文、网页、Markdown、仓库分析、PDF、笔记或原始材料中整理技术理解。
- 在正式生成 HTML 演示文稿之前，先确认来源证据、关键机制、可用图片和证据边界。
- 把网页 source package、论文解析结果、Source Understanding HTML、截图和视觉 QA 记录留在同一个运行目录中，便于后续人工审阅或另起 PPT-GEN 任务。

不要用它做演示文稿视觉渲染、版式模板、字体配色、导出 PPT、页数规划、目录规划、SCQA 或逐页观点生成。这些属于下游 PPT-GEN。

## 可直接复制的启动 prompt

```text
请对以下材料进行“PPT深度研究”，先完成来源理解审阅，不要直接生成正式 PPT：

- 主题：<填写主题>
- 原始材料：<粘贴 URL、PDF 路径、Markdown 路径或仓库路径>
- 任务名：<task-name>

请使用 workspace 根目录下的 `.tmp/ppt-deep-search/<task-name>/` 作为本轮唯一运行目录。
我允许你按 skill 契约启动必要的子 agent，包括网页来源抓取 agent、论文解析 agent、Source Understanding deck maker，以及独立视觉 QA checker；每个 agent 只处理分配给它的来源或交付物。
请先向我确认原始来源和对照方案，待我批准后再继续。完成后交付 `review/source_understanding_review.html`、导出截图、`review/visual-qa.md`、`sources/**`，并等待我审批后再写入 `baselines/015-source-understanding.md`。
```

若任务不包含网页或论文，对应的来源处理 agent 不需启动；deck maker 和独立视觉 QA checker 仍是 HTML 审阅交付链的组成部分。

## 标准流程

默认走 human-in-the-loop：

1. 确认 Source Understanding 的信息来源，包括原始来源和必要的同类方案。
2. 对网页来源调用 `web-article-capture`，对论文来源调用 `grobid-docling-pdf`，把结构化来源产物写入 `<workspace-root>/sources/`。
3. 基于来源产物制作 `review/source_understanding_review.html`。
4. 导出 Source Understanding PNG 到 `review/source-understanding-images/`。
5. 委派独立视觉 QA checker，写入 `review/visual-qa.md`。
6. 请求用户审批 Source Understanding，并保存 `baselines/015-source-understanding.md`。

审批通过后，本 skill 的职责结束。后续是否生成 PPT，由用户另起请求交给 PPT-GEN。

## 工作目录

一次运行只使用一个 `workspace-root`：

- 默认路径：`.tmp/ppt-deep-search/<task-name>/`
- forward-test 路径：`.tmp/forward-tests/<case-id>/<run-id>/`
- 用户指定输出目录时，以用户指定目录为准

所有临时笔记、baseline、资产和 QA 输出都放在这个目录下。

最终要求产物：

- `<workspace-root>/review/source_understanding_review.html`
- `<workspace-root>/review/source-understanding-images/`
- `<workspace-root>/review/visual-qa.md`
- `<workspace-root>/baselines/015-source-understanding.md`
- `<workspace-root>/sources/**`

## 校验命令

下列命令均从 workspace 根目录运行。在本仓库默认位置下，可完整复制：

```powershell
Set-Location "D:\Agent Repo\Mozhi-s-AgentWorkspace"
python skills/ppt-deep-search/verify_dependencies.py
```

Source Understanding HTML 写完后，把示例中的 `demo` 替换为实际任务名，再运行：

```powershell
Set-Location "D:\Agent Repo\Mozhi-s-AgentWorkspace"
python skills/ppt-deep-search/scripts/validate_source_understanding_html.py ".tmp/ppt-deep-search/demo/review/source_understanding_review.html" all ".tmp/ppt-deep-search/demo/review/source-understanding-images"
```

## 完成标准

- 所有来源产物和审阅产物都位于同一个 `workspace-root`，且来源与结论可追溯。
- HTML 审阅页已导出 PNG，且目标校验命令通过。
- 独立 checker 已写入 `review/visual-qa.md`，其发现的阻断问题已处理。
- 用户已审阅 HTML；只有审批通过后才保存 baseline。
- 未在本流程中提前生成 PPT 页数、目录、SCQA、逐页观点或正式演示文稿。
