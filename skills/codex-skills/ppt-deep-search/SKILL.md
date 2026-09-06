---
name: ppt-deep-search
description: >-
  面向 PPT 生成前置阶段的人机协同来源理解审阅。用于把论文、网页、Markdown、仓库分析、PDF、笔记或原始材料解析成可审阅的 Source Understanding HTML，
  帮助人类在进入 PPT-GEN 前确认技术理解、来源证据、图片材料和证据边界。
  不用于演示文稿终稿渲染。
---

# PPT Deep Search

构建有来源支撑的 Source Understanding 审阅产物，不制作幻灯片，不生成 PPT 故事主线或内容简报。负责来源选择、来源解析、Source Understanding HTML 制作和审批 gate。
稳定子 agent 角色定义放在本 skill 子仓的 `.codex/agents/*.toml`；本 Skill 只负责在运行时补全动态占位、执行 HITL gate 和回收子任务结果。

最终交付文件：

- `review/source_understanding_review.html`：对“不了解该技术的技术小白”解释技术原理。
- `review/source-understanding-images/`：Source Understanding HTML 导出截图。
- `review/visual-qa.md`：独立视觉 QA 记录。
- `baselines/015-source-understanding.md`：已审批的来源理解 baseline。
- `sources/**`：网页 source package 或论文解析结果。

## HITL 交互

- 默认用中文与用户交互。
- 向用户提问时，输出当前问题，并按gate中的回答模板整理备用答案，并等待用户回复确认。
- 必须遵循 HITL。

## Workspace Skill 索引

- 这些SKILL都是配套委派子agent使用的，主agent禁止加载查阅细节
- 网页来源抓取使用 workspace skill：`web-article-capture`。
- 论文解析使用 workspace skill：`grobid-docling-pdf`（仓库路径：`skills/grobid_pdf_skill/SKILL.md`）。
- Source Understanding HTML deck 生成使用 workspace skill：`hw-ppt-gen-html`。
- 优先使用工作区中的现有文件，无法在工作区中找到些SKILL时，通过git将子skill clone到 .tmp目录下来使用
  - https://github.com/MozhiJiawei/web-article-capture
  - https://github.com/MozhiJiawei/hw-ppt-gen-html
  - https://github.com/MozhiJiawei/grobid_pdf_skill

## 工作流程

### 制作 Source Understanding 审阅 deck

加载 `references/source-understanding-html-ppt.md`，按其中的 Codex custom agent 与动态占位约定委派子 agent 做内容解析和 HTML deck 制作。
用户批准 Source Understanding 后，本 skill 的职责结束。后续是否生成 PPT 由用户另行请求 PPT-GEN。

## 工作区

- 运行开始时确定一个 `workspace-root`。如果用户或父级 dispatch 提供输出目录，使用该目录；否则使用 `.tmp/ppt-deep-search/<task-name>/`。
- 将草稿笔记、source map、baselines、QA 文件和临时资产放在 `<workspace-root>/` 下。
- 最终 Source Understanding HTML 必须位于 `<workspace-root>/review/source_understanding_review.html`。
