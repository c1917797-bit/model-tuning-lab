---
name: hw-ppt-gen-html
description: HTML PPT / HTML Report Skill 的 workspace wrapper。用于制作 PPT、slides、deck、HTML 演示文稿、幻灯片、演讲稿、中文分析报告、论文分析报告、可滚动 HTML 报告时接入工作区；先用 humanize-ppt 生成 AST 大纲和逐页/章节意图，再按最终交付件选择 Deck 或 Report 导出入口，并完成 PNG 导出和独立视觉 QA。
---

# HTML PPT / HTML Report Skill Wrapper

本仓库作为 `html-ppt-skill` 的 workspace 接入 wrapper，并将 `humanize-ppt` 作为前置叙事规划子仓。

- `humanize-ppt/`：负责先产出 AST 大纲、逐页/章节意图、内容计划和素材意图。
- `html-ppt-skill/`：负责最终 HTML 视觉生成能力。
- `scripts/render_html_ppt.py`：Deck 模式导出和硬性 QA。
- `scripts/render_html_report.py`：Report 模式导出和硬性 QA。

执行任何 PPT、slides、deck、HTML 演示文稿、HTML 报告或截图导出任务时，先读取并遵循：

```text
html-ppt-skill/SKILL.md
humanize-ppt/SKILL.md
```

## 标准流程

1. 先根据用户最终交付件推断交付模式，并写入 `<task-root>/delivery_mode.md`。后续步骤必须引用这个文件，不要重新隐式判断。
2. 实际运行 `humanize-ppt`，将原始材料生成的 AST 契约写入 `<task-root>/humanize/`；执行humanize_ppt_v2.py，完成对brief生成的检查
3. 生成最终 HTML 前，先读取并审阅 `<task-root>/humanize/` 中的 AST 契约，再以这些文件作为叙事与逐页/章节规划依据。允许生成者根据 Deck 或 Report 的实际表达需要调整页面合并、拆分和视觉组织，但不得绕过 Humanize、仅凭原始材料另起一套叙事。
4. 按 `delivery_mode.md` 选择唯一导出入口。两个入口互斥，不要同时调用。
5. 导出通过后委派独立视觉 QA checker。checker PASS 后再交付。

## 语言要求

中文

## 交付模式判定

在接到任务后，先写 `<task-root>/delivery_mode.md`：

```text
# Delivery Mode

- mode: Deck | Report
- reason: <从用户最终交付件推断的理由>
- final_html_contract: <Deck: section.slide 翻页结构 | Report: 滚动式 HTML，不能使用 section.slide 作为主结构>
- export_command: <Deck 使用 `python scripts/render_html_ppt.py <final-html-path> all <export-output-dir>`；Report 使用 `python scripts/render_html_report.py <final-html-path> <export-output-dir>`>
- export_outputs: <Deck: 逐页 PNG + render-manifest.json | Report: desktop-full.png + report-render-manifest.json>
```

判定规则：

- 选择 `Deck`：用户要 PPT、slides、deck、幻灯片、演示文稿、演讲稿页面、翻页版 HTML，或需要键盘翻页、speaker notes、presenter mode、逐页 PNG。
- 选择 `Report`：用户要 HTML 分析报告、论文分析报告、可滚动报告、长文网页报告，或明确说最终交付件不是翻页版、不是 PPT/deck。
- 若用户同时出现冲突词，以“最终交付件”优先；仍不清楚时先询问，不要猜。

## 导出与 QA

### 导出

完成 HTML 后，运行 `delivery_mode.md` 中记录的唯一 `export_command`。`<final-html-path>` 使用实际完成的 HTML 文件；`<export-output-dir>` 使用该 HTML 所属交付目录下清晰命名的导出目录。

如果导出命令非 0 或输出 `[ERROR]`，必须修复 HTML 后重跑同一个导出命令，直到命令通过且无 `[ERROR]`。不要改用另一个入口绕过错误；导出脚本报错通常说明 HTML 结构和 `delivery_mode.md` 不一致。导出成功只代表截图已生成并通过硬性渲染检查，不代表视觉 QA 已完成。

### 独立视觉 QA

导出命令通过后，必须委派 Codex custom agent `html_ppt_visual_qa_checker` 作为独立视觉 QA checker。checker 已内置通用视觉 QA rubric；主 agent 只补充本次任务的动态输入，不要重复 checker 的完整规则。

给 checker 的动态补充：

```text
- HTML：<final-html-path>
- 导出图片：<exported-png-glob-or-file>
- 将视觉 QA 记录写入：<final-html-directory>/visual-qa.md
```

其中 `<exported-png-glob-or-file>` 按模式填写：

- Deck：`<export-output-dir>/*.png`
- Report：`<export-output-dir>/desktop-full.png`

checker 返回 `PASS` 后，生成者再进入交付或审批。
checker 返回 `FAIL` 时，修复 HTML，重新运行对应模式的导出命令刷新截图，并重新委派 checker。
