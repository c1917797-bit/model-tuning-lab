# ppt-deep-search 效果展示

`ppt-deep-search` 是一个面向“PPT 生成前来源理解审阅”的 Skill：它先做来源解析，再生成可审阅的 Source Understanding HTML、导出截图并完成视觉 QA。这个页面展示最近一轮 forward-test 的公开样例，重点看三件事：

- 候选 agent 是否能把来源证据读透，而不是只摘关键词。
- HIL 审批、来源理解审查、视觉 QA 是否形成闭环。
- `source_understanding_review.html` 是否能让不了解该技术的人理解原理、证据和边界。

## 展示方式

本页只引用 `docs/showcase/latest/` 下的发布副本。forward-test 的运行目录只作为刷新来源，文档中不直接依赖临时运行产物。

每个样例只归档 Source Understanding HTML 及其必要静态资源。过程记录、检查记录和临时运行文件不进入展示目录。

| 样例 | 任务主题 | 最新结论 | 最终交付件 |
| --- | --- | --- | --- |
| Aegaeon GPU Pooling | 云 GPU 池化与 broker 架构 | Source Understanding 通过，视觉 QA 曾需多轮修复 | <a href="/skill-static/ppt-deep-search/showcase/latest/aegaeon-gpu-pooling/source_understanding.html" target="_blank" rel="noopener noreferrer">HTML</a> |
| RTX Spark Agent PC | NVIDIA DGX Spark 与 Agent PC | Source Understanding 通过，官方来源边界更清楚 | <a href="/skill-static/ppt-deep-search/showcase/latest/rtx-spark-agent-pc/source_understanding.html" target="_blank" rel="noopener noreferrer">HTML</a> |
| Stochastic KV Routing | Moonshot AI 的随机 KV 路由 | Source Understanding 通过，技术链路与图表复建更稳定 | <a href="/skill-static/ppt-deep-search/showcase/latest/stochastic-kv-routing/source_understanding.html" target="_blank" rel="noopener noreferrer">HTML</a> |

## Aegaeon GPU Pooling

这个样例要求 agent 将 Aegaeon 论文与项目材料重构成来源理解审阅材料。最新结果已经能把 broker 协调、GPU worker、客户端应用和基准曲线放进同一条解释链，并保留来源图表证据。

最终交付件：

- <a href="/skill-static/ppt-deep-search/showcase/latest/aegaeon-gpu-pooling/source_understanding.html" target="_blank" rel="noopener noreferrer">来源理解 HTML</a>

## RTX Spark Agent PC

这个样例检查 agent 面对厂商网页、平台介绍和生态材料时，能否区分“官方确定信息”和“行业解读”。最新结果把 DGX Spark、RTX PRO、Blackwell、AI Workbench、NVIDIA Blueprint 等材料归入清晰的证据层级，避免把网页营销语直接写成无来源判断。

最终交付件：

- <a href="/skill-static/ppt-deep-search/showcase/latest/rtx-spark-agent-pc/source_understanding.html" target="_blank" rel="noopener noreferrer">来源理解 HTML</a>

## Stochastic KV Routing

这个样例围绕 Moonshot AI 的随机 KV 路由论文，要求 agent 把算法动机、公式、表格和实验图重新组织为技术理解审阅材料。最新结果已经能把 `distributional equality`、随机路由器、容量受限调度、chunk prefill 与 Decode-Context Parallelism 之间的关系讲清楚。

最终交付件：

- <a href="/skill-static/ppt-deep-search/showcase/latest/stochastic-kv-routing/source_understanding.html" target="_blank" rel="noopener noreferrer">来源理解 HTML</a>

## 最新验证结论

- 来源理解审查已经能稳定暴露“只读摘要、不读图表”的弱点，并通过 HTML 与截图保留可复查证据。
- HIL 交互还需要更严格：候选 agent 问选择题时，应在同一条消息里列出完整选项文本。
- 文档展示区必须是发布副本。刷新时先定位最新 forward-test 结果，再只把最终 HTML 及其必要图片/CSS/JS 依赖复制进 `docs/showcase/latest/`，最后更新本页链接。

## 刷新规则

刷新本页时只替换 `docs/showcase/latest/` 的内容，不恢复旧样例目录，也不让文档链接到运行缓存。若新增样例，需要同时更新本页表格、样例章节、来源理解 HTML 和必要静态资源；不要归档内部过程产物。
