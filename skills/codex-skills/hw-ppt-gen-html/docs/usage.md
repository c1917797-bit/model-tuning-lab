# 使用方式

## 工作目录约定

本文中的 `<workspace-root>` 指包含 `skills/`、`docs/` 和 `.tmp/` 的 `Mozhi-s-AgentWorkspace` 根目录，而不是 skill 子仓目录。

- Skill 根目录：`<workspace-root>/skills/hw-ppt-gen-html`
- 原始输入：`<workspace-root>/.tmp/hw-ppt-gen-html/<task-name>/input/`
- 任务根目录：`<workspace-root>/.tmp/hw-ppt-gen-html/<task-name>/`
- Humanize 原始 AST 契约：`<task-root>/humanize/`
- 稳定规划交接物：`<task-root>/planning/`
- 最终 HTML：`<task-root>/final/index.html`
- 导出结果：`<task-root>/final/export/`
- 模式记录：`<task-root>/delivery_mode.md`
- 视觉 QA：`<task-root>/final/visual-qa.md`

用户明确要求保存为正式仓库文档或交付资产时，才把最终文件复制到指定正式位置；制作过程、截图、日志和 QA 中间物仍留在 `.tmp/`。

`humanize/` 是 Humanize PPT 实际运行后留下的原始 AST 契约目录；`planning/` 是主 agent 复核 `humanize/` 后，面向最终生成阶段整理或镜像出的稳定交接面。最终 HTML 生成前必须能追溯到 `humanize/`，但生成子 agent 可以只消费主 agent 明确批准后的 `planning/`、素材路径和输出路径。

## 可复制中文 Prompt

替换尖括号中的内容后可直接发给 Agent：

```text
请使用 hw-ppt-gen-html 制作一份 <主题> 的 <PPT/翻页 HTML/滚动 HTML 报告>。

workspace 根目录：<workspace-root>
输入材料：<workspace-root>/.tmp/hw-ppt-gen-html/<task-name>/input/
任务根目录：<workspace-root>/.tmp/hw-ppt-gen-html/<task-name>/
受众与用途：<受众、场景、时长或阅读方式>
语言与风格：<中文/英文；正式汇报/技术分享/论文分析等>
最终交付件：<Deck 或 Report；若不确定请先问我，不要同时生成两种模式>

请先读取 skills/hw-ppt-gen-html/SKILL.md、humanize-ppt/SKILL.md 和 html-ppt-skill/SKILL.md。
先在任务根目录写 delivery_mode.md，再用 Humanize PPT 生成 AST 大纲和逐页/逐章节意图，最终生成阶段只能消费已确认的规划交接物，不得绕过规划直接从原始材料生成最终 HTML。

我允许你为最终 HTML 制作启动一个有明确输入输出边界的生成子 agent，并允许在导出后启动独立 html_ppt_visual_qa_checker。checker 只做审查，不参与制作。若当前运行环境仍要求单独授权，请在启动前向我确认。

完成标准：最终 HTML 存在；只运行 delivery_mode.md 指定的唯一导出脚本且返回 0、无 [ERROR]；脚本生成 manifest 时其 status 必须为 succeeded；独立 checker 查看实际导出 PNG 并在 final/visual-qa.md 给出 PASS；若 FAIL，修复 HTML、重新导出并重新检查后再交付。请最终列出 HTML、导出图片、已有 manifest 和 visual-qa.md 的绝对路径。
```

## Deck 与 Report 的互斥判定

开始制作前必须在 `<task-root>/delivery_mode.md` 固化一次判定，后续步骤引用该文件，不能在导出时重新猜测或同时运行两个入口。

```text
# Delivery Mode

- mode: Deck | Report
- reason: <根据用户最终交付件作出的理由>
- final_html_contract: <Deck 使用 section.slide 翻页结构 | Report 使用滚动结构且不能以 section.slide 为主结构>
- export_command: <实际命令>
- export_outputs: <实际输出>
```

- 选 `Deck`：最终要 PPT、slides、deck、幻灯片、演示文稿、演讲稿页面、键盘翻页、speaker notes、presenter mode 或逐页 PNG。
- 选 `Report`：最终要 HTML 分析报告、论文分析报告、滚动长文网页，或明确不要翻页版。
- 同时出现冲突词时，以用户描述的“最终交付件”为准；仍无法唯一判断时先询问。

## 规划交接物消费契约

本 wrapper 不依赖仓库外或缺失的内容简报说明文件。最终生成阶段使用以下完整契约：

1. 主 agent 先让 Humanize PPT 产出 AST 规划。若 Humanize 生成 `<renderer>-production-prompt.md`，它是生成子 agent 的首要交接文件；同时保留 `deck_brief.md`、`ast_outline.md`、`slide_plan.json`、`speaker_intent.md`、`asset_manifest.md` 和 `style_brief.md` 作为可追踪依据。
2. Report 路线也必须提供等价字段：受众、目标、核心张力、章节顺序、每章进入状态/意图/离开状态、证据或素材用途、引用来源和风格原则。可以使用不同文件名，但这些字段不能缺失。
3. 生成子 agent 只接收 `delivery_mode.md`、规划交接物、已批准素材路径和明确的输出路径；不得重新从原始材料推导另一套故事线，也不得改变 Deck/Report 模式。
4. Deck 输出必须以 `section.slide` 作为页面结构并保留键盘导航运行时；Report 输出不得用 `section.slide` 伪装成长报告。
5. 生成子 agent 的交接物是最终 HTML 和其本地素材。导出、修复循环、checker 调度和最终验收仍由主 agent 负责。

## 从 skill 根目录运行导出

以下 PowerShell 命令都从 skill 根目录运行。先进入目录：

```powershell
Set-Location '<workspace-root>\skills\hw-ppt-gen-html'
```

Deck 模式只运行：

```powershell
python scripts\render_html_ppt.py '..\..\.tmp\hw-ppt-gen-html\<task-name>\final\index.html' all '..\..\.tmp\hw-ppt-gen-html\<task-name>\final\export'
```

标准多页 Deck 输出 `index_01.png` 等逐页 PNG 和 `render-manifest.json`。显式单页导出可传数字 `1`；脚本对单页不写 manifest，因此标准 Deck 验收应优先使用 `all` 对真实多页结构导出。

Report 模式只运行：

```powershell
python scripts\render_html_report.py '..\..\.tmp\hw-ppt-gen-html\<task-name>\final\index.html' '..\..\.tmp\hw-ppt-gen-html\<task-name>\final\export'
```

Report 输出为 `desktop-full.png` 和 `report-render-manifest.json`。发现 `section.slide`、正文过短、页面过矮、横向溢出或可见破图时脚本返回非零；不要切换到 Deck 入口绕过失败。

## 独立视觉 QA

导出返回 0 且没有 `[ERROR]` 后，主 agent 才能委派 `html_ppt_visual_qa_checker`。动态输入为：

```text
- HTML：<task-root>/final/index.html
- 导出图片（Deck）：<task-root>/final/export/*.png
- 导出图片（Report）：<task-root>/final/export/desktop-full.png
- 视觉 QA 记录：<task-root>/final/visual-qa.md
```

checker 必须直接加载图片，只审查，不修改 HTML、素材、脚本或模式判定。Deck 的 `visual-qa.md` 应包含 verdict、逐页 `Primary Visual Checks` 和原始检查记录；Report 应包含长图整体层级、关键章节和主视觉可读性检查。checker 返回 `FAIL` 时，由生成者修复 HTML，主 agent 重新运行同一模式的导出命令并再次委派 checker。

## 完成标准

- `delivery_mode.md` 存在且只选择一种模式。
- 规划交接物完整，最终 HTML 没有绕过它直接消费原始材料。
- 最终 HTML 与模式结构一致，引用的本地素材均存在。
- 唯一导出命令返回 0、无 `[ERROR]`；多页 Deck 或 Report 的对应 manifest `status` 为 `succeeded`。显式单页 Deck 以脚本返回值、PNG 和独立视觉 QA 为准，因为脚本不会为单页写 manifest。
- 独立 checker 已查看实际 PNG，`visual-qa.md` 最终 verdict 为 `PASS`。
- 交付时列出最终 HTML、PNG、manifest、`visual-qa.md` 和仍存在的证据或发布残项。
