# 架构概览

`ppt-deep-search` 是正式 PPT 生成前的“来源理解审阅层”。它不决定页数、目录、SCQA 或逐页观点；它的职责是把原始材料转换为可追溯、可视化、可由人审批的 Source Understanding 结果。审批后的 review 与 sources 可作为下游 PPT-GEN 的证据输入，但下游生成不属于本 skill。

## 逻辑视图

```text
用户材料 + 来源选择
          |
          v
来源处理层
  - 网页 -> 逐页 source package
  - 论文 -> 结构化解析与图表
  - 本地材料 -> 按原路径作为证据输入
          |
          v
Source Understanding 建模层
  - 技术心智模型
  - 来源、图片与结论的可追溯关系
  - 已知事实、归纳判断与证据边界
          |
          v
评审层
  - HTML 渲染与 PNG 导出
  - 独立视觉 QA
  - 人类审批 gate
          |
          v
已审批 baseline + sources + review
```

核心输入是用户给定的论文、网页、PDF、Markdown、仓库或笔记，以及在第一个 HITL gate 中确认的原始来源和对照方案。核心输出是 `review/source_understanding_review.html`、导出截图、独立 QA 记录、`sources/**` 和审批后的 baseline。

边界有两条：来源处理 helper skill 对单个来源包的真实性和结构负责；`ppt-deep-search` 对来源选择、跨来源理解、审阅产物和人类 gate 负责。任何 agent 都不能用无来源的补写代替缺失证据。

## 运行视图

1. 主 agent 读取用户 prompt，确定唯一 `workspace-root`，并将原始来源和对照方案写入 `sources/source-selection.md`。
2. 主 agent 向用户发起来源确认 gate；未批准前不进入大规模抓取或制作。
3. 对每个网页，主 agent 分别委派 `web_source_capturer`，产物落在 `sources/web/<source-slug>/`；对每篇论文，分别委派 `paper_source_parser`，产物落在 `sources/papers/<source-slug>/`。
4. 来源就绪后，主 agent 把与当前报告相关的 source paths 交给 `source_understanding_deck_maker`。主题报告与最多两份对照报告可由不同子 agent 并行制作，但不得混入无关来源。
5. deck maker 产出 HTML，导出截图，再由独立视觉 QA checker 检查并将结果写入 `review/visual-qa.md`。制作者根据 QA 结果修复，不得自行宣告通过独立审查。
6. 主 agent 向用户提交 HTML 审阅。只有用户批准后才写入 `baselines/015-source-understanding.md`；至此本 skill 结束。

任何一步遇到来源不可访问、解析不完整、证据冲突、渲染失败或 QA 阻断问题，都应保留边界说明并停在对应 gate，不应通过猜测补齐。

## 开发视图

| 分层 | 主要资产 | 面向的问题 |
| --- | --- | --- |
| 运行入口 | `SKILL.md` | 何时触发、必须交付什么、HITL 在哪里结束 |
| 编排契约 | `references/source-understanding-html-ppt.md` | 何时启动哪个 agent，以及每次委派要填入的动态来源和输出目录 |
| 稳定角色 | `.codex/agents/*.toml` | 单网页抓取、单论文解析、Source Understanding deck 制作的静态职责 |
| 可执行 gate | `scripts/validate_markdown_size.py`、`scripts/validate_source_understanding_html.py`、`verify_dependencies.py` | 文档大小、HTML 渲染/截图、本地依赖与必需文件 |
| 发布资料 | `docs/`、`docs.manifest.yml` | 向人类说明能力、用法、依赖和架构，并声明可发布入口 |
| 行为回归 | `forward-tests/ppt-deep-search/` | 主 agent 编排、HITL、来源追溯和 Source Understanding-only 边界是否仍成立 |

`SKILL.md` 应保持短小；稳定 agent prompt 留在 TOML，当次 URL、PDF、source slug、来源列表和输出目录由主 agent 按 reference 动态补全，不得固化到 TOML。可机器检查的规则应由 validator 承担，不只写在说明文字中。

## 多 Agent 职责边界

| 角色 | 负责 | 交接物 | 禁止事项 |
| --- | --- | --- | --- |
| 主 agent | 管理 `workspace-root`、来源选择、HITL gates、子任务拆分、产物回收和最终审批 | `source-selection.md`、带动态占位的 dispatch、已审批 baseline | 不越过用户批准；不要求子 agent 制作正式 PPT 规划 |
| `web_source_capturer` | 每次抓取和校验一个网页 source package | `sources/web/<source-slug>/` | 不合并多页任务；不写跨来源结论 |
| `paper_source_parser` | 每次下载、解析一篇论文并整理 XML/图表资产 | `sources/papers/<source-slug>/` | 不代替主 agent 选择证据；不处理多论文综述 |
| `source_understanding_deck_maker` | 仅根据分配的 sources 制作面向技术小白的 HTML review，并导出截图 | 主报告或单个对照报告的 HTML 与图片 | 不引入未交接来源；不规划下游 PPT |
| 独立视觉 QA checker | 检查渲染、可读性、溢出、缺图、导航和主要视觉问题 | `review/visual-qa.md` | 不参与 HTML 制作；不因内容主张取代来源/人类审批 |

## 产物与维护契约

一次运行只使用一个 task root，通常是 `.tmp/ppt-deep-search/<task-name>/` 或 `.tmp/forward-tests/<case-id>/<run-id>/`。必需产物为：

- `review/source_understanding_review.html`
- `review/source-understanding-images/`
- `review/visual-qa.md`
- `baselines/015-source-understanding.md`
- `sources/**`

不要新增额外的 PPT 内容简报、页数规划、目录规划、SCQA 或逐页观点交接物。运行规则改变时，应同步复核 `SKILL.md`、reference、agent TOML、validators 与 forward-test judge expectations；本页面只解释已存在的行为契约，不替代它们。

子仓依赖与契约检查从 workspace 根目录运行：

```powershell
Set-Location "D:\Agent Repo\Mozhi-s-AgentWorkspace"
python skills/ppt-deep-search/verify_dependencies.py --skip-services
```
