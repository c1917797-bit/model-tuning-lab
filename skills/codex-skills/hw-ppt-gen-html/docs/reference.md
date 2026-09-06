# 能力展示

## 当前 Wrapper 可核验证据

以下证据来自当前 wrapper 的真实 forward-test 归档，链接指向可打开交付件或可复核记录，不再使用上游子仓示例作为能力展示依据。

## Wrapper 可提供的能力

- 先用 `humanize-ppt/` 把原始材料整理为 AST 大纲、逐页或逐章节意图、讲者意图与素材意图，再把明确的生产交接物交给最终生成阶段。
- Deck 模式生成以 `section.slide` 为页面单元的可翻页 HTML；可使用 `html-ppt-skill/` 的模板、布局、主题、运行时和演讲者模式。
- Report 模式生成不以 `section.slide` 为主结构的滚动 HTML 分析报告。
- [Deck 导出脚本（wrapper 固定提交）](https://github.com/MozhiJiawei/hw-ppt-gen-html/blob/a0578c54074669a3e8fdcf87e8e1e2a721794e97/scripts/render_html_ppt.py) 导出逐页 PNG，并检查多页键盘导航及非微型可见图片的缩放比例。
- [Report 导出脚本（wrapper 固定提交）](https://github.com/MozhiJiawei/hw-ppt-gen-html/blob/a0578c54074669a3e8fdcf87e8e1e2a721794e97/scripts/render_html_report.py) 导出桌面全页截图，并检查滚动结构、正文规模、横向溢出和破图等硬性问题。
- 导出通过后，独立视觉 checker 直接检查 PNG；渲染脚本通过不代表视觉 QA 通过。

## Wrapper 端到端 Forward-Test 证据

`rtx-spark-agent-pc-report` 是当前 wrapper 的 Report 模式 forward-test。它从 `forward-tests/rtx-spark-agent-pc-report/sources/web/` 的 NVIDIA 网页证据包开始，先运行 Humanize PPT 生成 AST 规划，再生成滚动 HTML Report，最后用本 wrapper 的 `render_html_report.py` 导出桌面长图并交给独立视觉 checker 审查。

- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/index.htm" target="_blank" rel="noopener noreferrer">打开归档 HTML Report</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/export/desktop-full.png" target="_blank" rel="noopener noreferrer">打开桌面长图 PNG</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/export/report-render-manifest.json" target="_blank" rel="noopener noreferrer">打开 Report 导出 manifest</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/visual-qa.md" target="_blank" rel="noopener noreferrer">打开独立视觉 QA 记录</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/delivery_mode.md" target="_blank" rel="noopener noreferrer">打开交付模式记录</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/humanize/ast_outline.md" target="_blank" rel="noopener noreferrer">打开 Humanize AST 摘要</a>
- <a href="/skill-static/hw-ppt-gen-html/showcase/rtx-spark-agent-pc-report/judgment.md" target="_blank" rel="noopener noreferrer">打开 forward-test 判断记录</a>

本次归档的 `report-render-manifest.json` 状态为 `succeeded`，检查到 `slideCount: 0`、`bodyWidth: 1920`、无横向溢出、无破图；`visual-qa.md` 给出 `Verdict: PASS`。这证明 Report 路线已经有一份当前 wrapper 真实运行、可打开、可复核的端到端证据。

## 能力边界与当前证据缺口

- 本 skill 交付静态 HTML、PNG、manifest 和视觉 QA 记录，不承诺生成 `.pptx`。
- wrapper 不负责把交付件部署到公网；在线发布需要单独的发布流程和权限。
- `render_html_ppt.py` 不会判断叙事质量、文字重叠、裁切、图表是否易读或视觉风格是否合适；这些由独立 checker 负责。
- `render_html_report.py` 的硬检查也不能替代对长图节奏、图文层级和证据可读性的视觉复核。
- 当前 wrapper 专属的公开 Deck + `render-manifest.json` + `visual-qa.md` 证据包仍待补齐；现有公开证据覆盖 Report 路线。

## Forward-Test 边界

forward-test 用于检验 wrapper 在真实输入下能否稳定调度制作、导出和视觉 QA，不是新的运行时能力。候选输出放在 `.tmp/html-ppt-runs/<case-id>/<run-id>/`，主 agent 判断放在 `.tmp/forward-tests/<case-id>/<run-id>/judgment.md`；judge、rubric 和 expected-example 不得发给生成子 agent。
