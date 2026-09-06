# HTML PPT / HTML Report Skill Wrapper

本仓库把 `humanize-ppt/` 的叙事规划、`html-ppt-skill/` 的静态 HTML 视觉能力、Deck/Report 导出门禁和独立视觉 QA 接入当前 workspace。它不复制两个子仓的实现，也不把渲染成功等同于视觉验收通过。

## 逻辑视图

| 层 | 输入 | 责任 | 输出与边界 |
| --- | --- | --- | --- |
| 模式与任务控制 | 用户 prompt、最终交付要求 | 主 agent 固化 Deck/Report、任务目录、验收标准和 agent 授权 | `<task-root>/delivery_mode.md`；两个模式互斥 |
| 叙事规划 | 原始材料、受众与目标 | `humanize-ppt/` 形成 AST 大纲、逐页/章节意图、讲者与素材意图 | 规划交接物；不拥有最终 HTML |
| 最终生成 | 模式记录、规划交接物、已批准素材 | 生成子 agent 按 `html-ppt-skill/` 规则制作 Deck，或按滚动契约制作 Report | 最终 HTML 与本地素材；不得重新推导故事线或改变模式 |
| 硬性导出 | 最终 HTML | `render_html_ppt.py` 或 `render_html_report.py` 运行结构、截图和基础门禁 | PNG + manifest；不判断整体视觉质量 |
| 独立视觉 QA | 最终 HTML、实际导出 PNG | `html_ppt_visual_qa_checker` 只审查视觉结果 | `visual-qa.md` verdict；不参与制作或修复 |

核心数据流为：

```text
原始材料 -> AST 规划交接物 -> 最终 HTML -> 唯一模式导出 -> PNG/manifest -> 独立视觉 QA -> 交付
```

Deck 的结构边界是 `section.slide` 翻页页面；Report 是滚动 HTML，不能用 `section.slide` 作为主结构。`delivery_mode.md` 是两条路径共享的唯一模式判定来源。

## 运行视图

1. 主 agent 读取 wrapper、Humanize PPT 和 html-ppt 三份 Skill 说明，建立 `<workspace-root>/.tmp/hw-ppt-gen-html/<task-name>/`。
2. 主 agent 根据用户的最终交付件写 `delivery_mode.md`；冲突且无法唯一判断时先询问用户。
3. Humanize PPT 基于原始材料生成 AST 大纲和逐页/章节意图。最终生成阶段只消费规划交接物，不直接绕回原始材料另起故事线。
4. 如使用生成子 agent，主 agent 只交给它模式记录、规划交接物、已批准素材和输出路径；子 agent 返回最终 HTML 与素材清单。
5. 主 agent 按 `delivery_mode.md` 运行唯一入口：Deck 用 `scripts/render_html_ppt.py`，Report 用 `scripts/render_html_report.py`。失败时修复 HTML 并重跑原入口，不能切换模式绕过错误。
6. 导出通过后，主 agent 委派独立 checker 直接查看 PNG。checker 只审查，不修改 HTML；失败后的修复仍由生成者负责。
7. checker 最终 `PASS` 后，主 agent 汇总 HTML、截图、manifest、`visual-qa.md` 和残项再交付。

## 开发视图

| 路径 | 分层含义 | 修改边界 |
| --- | --- | --- |
| `SKILL.md` | workspace wrapper 的运行契约、模式判定和 QA 入口 | Agent 运行时资产，不是普通发布文档 |
| `humanize-ppt/` | 叙事规划子仓 | 由其上游子仓维护 |
| `html-ppt-skill/` | 模板、主题、布局、运行时和示例子仓 | 由其上游子仓维护 |
| `scripts/render_html_ppt.py` | Deck 截图、导航与图片缩放硬检查 | wrapper 代码资产 |
| `scripts/render_html_report.py` | Report 全页截图与滚动结构硬检查 | wrapper 代码资产 |
| `.codex/agents/` 与 `references/` | checker 声明和视觉 rubric | Agent/QA 运行资产 |
| `docs/` | 面向文档站发布的能力、用法、依赖和架构说明 | 本文档集；不承载运行逻辑 |
| `forward-tests/` | wrapper 调度的验证输入与判断资产 | 不进入正常生成子 agent 语境 |
| `<workspace-root>/.tmp/` | 每次任务的输入副本、规划、HTML、截图和 QA 记录 | 临时运行产物，不是能力来源 |

## 多 Agent 职责与禁止事项

### 主 agent

- 拥有用户沟通、模式判定、目录与权限边界、规划调度、导出命令、修复循环和最终验收。
- 向生成子 agent 提供有界交接物，向 checker 提供最终 HTML、PNG 和 `visual-qa.md` 目标。
- 禁止把 judge/rubric/expected-example 泄露给 forward-test 生成子 agent，禁止在 checker `PASS` 前宣称完成。

### 生成子 agent

- 只根据 `delivery_mode.md`、规划交接物和已批准素材生成指定模式的最终 HTML。
- 交接最终 HTML、本地素材和必要说明；不得改变模式、改写验收标准、跳过 Humanize 规划或自行宣称视觉 QA 通过。
- 若任务不需要或用户未授权启动子 agent，主 agent 可以承担生成工作，但职责边界仍保持不变。

### 独立视觉 checker

- 必须与生成者职责分离，直接加载导出 PNG，并用 HTML 辅助定位问题。
- 只审查，不修改 HTML、素材、脚本或模式记录；按约定留下 verdict 和检查记录。
- 返回 `FAIL` 时只说明问题和修复方向，不能自己修改后给自己复检。

涉及生成子 agent 或独立 checker 的任务，应在用户 prompt 中明确允许启动；若运行环境要求额外授权，主 agent 必须先取得授权。

## 发布边界

`docs/` 是文档源。修改源文件不会自动证明远端文档站已经更新；还需要主仓执行文档同步、发布和远端可访问性验收。远端页面仍显示旧内容时，应登记为同步/部署残项，不能通过继续改写子仓文档假装已经发布。
