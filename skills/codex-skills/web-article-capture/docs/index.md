# 架构概览

`web-article-capture` 把浏览器中实际渲染的网页正文、正文图片及可靠性说明整理为下游 Agent 可复用的 source package。它面向的是网页资料采集，不是整页截图归档、通用爬虫框架或网页镜像工具。

## 逻辑视图

工作流由三类能力组成：

1. **渲染与取证**：主 Agent 通过 Codex in-app Browser 打开目标 URL，识别包含标题和正文流的最小 DOM 范围，并在需要时滚动以触发懒加载。
2. **内容与媒体筛选**：主 Agent 保留正文、图表、图注和附近文本，排除导航、页脚、推荐、评论、联系卡片、UI 图标及装饰图；若 Browser 持续受阻，才使用官方来源 fallback，并记录受阻阶段和版本风险。
3. **打包与结构校验**：每个页面写成 `<output-root>/<source-slug>/source.md` 和 `images/`。`scripts/validate_capture_package.py` 只检查目录形态、本地图片引用、扩展名和疑似截图文件名，不判断正文边界或图片语义归属。

输入是用户 prompt、目标 URL 列表和输出目录；输出是一个或多个 source package，可按需再生成供人工检查的 `review.html`。网页正文判断、fallback 决策和可靠性说明始终由主 Agent 负责，不能交给结构校验器代替。

## 运行视图

一次正常执行按以下路径进行：

```text
用户 prompt 与 URL
  -> 主 Agent 读取 SKILL.md，并加载 in-app Browser 操作规范
  -> Browser 打开渲染页面；主 Agent确定正文起止边界
  -> 主 Agent 收集正文及属于正文的原始图片
  -> 主 Agent 写 source.md、images/，按需写 review.html
  -> validator 检查 package 结构
  -> 主 Agent人工复核正文尾部、媒体归属和 fallback 可靠性
  -> 交付下游 Agent
```

导航超时、DOM 快照失败或图片懒加载不完整属于页面级状态。主 Agent应先在新标签页重试、滚动到媒体区域或改用只读页面求值；仍无法恢复时，在 `source.md` 标记 `rendered partial` 或 `official-source fallback`，而不是把 fallback 描述为完整渲染抓取。

## 开发视图

理解实现时可按以下分层阅读：

```text
SKILL.md                              运行时抓取规则与交付要求
references/output-contract.md        source.md 与 images/ 的详细契约
scripts/validate_capture_package.py  package 结构校验器及自测
verify_dependencies.py               本地依赖与协议文件检查入口
forward-tests/                       隔离运行的前向测试协议和案例
docs/                                面向文档站的展示、使用、依赖和架构说明
```

`docs/` 解释公开使用方式，不取代 `SKILL.md` 的运行时约束；`forward-tests/` 用于评估流程，不是普通抓取任务的输入或交付目录。

## 多 Agent 职责与边界

普通抓取流程**不要求**启动子 Agent、checker 或 reviewer：

- **主 Agent**：读取运行规范、控制 Browser、判断正文与图片归属、生成 package、运行 validator，并完成语义复核；不得把整页截图放入 `images/` 冒充原始正文图片。
- **Codex in-app Browser**：提供页面导航、渲染状态和 DOM/资源访问能力；它是工具，不是独立 Agent，不负责决定内容边界。
- **validator**：返回结构错误供主 Agent修复；它不是 checker Agent，也不证明抓取内容语义正确。
- **下游 Agent**：读取 `source.md` 和本地图片开展研究、写作或 PPT 制作；不应把未记录的页面内容推断成已抓取事实。

只有运行 `forward-tests/` 时，测试协议才要求主 Agent把候选抓取任务交给隔离子 Agent，并由主 Agent按 rubric 判定。该测试分工不应套用到普通用户抓取任务，也不应向候选子 Agent泄露 rubric、历史输出或判定提示。

## 能力边界

- 抓取 article/main 阅读流，而不是保存完整网站或绕过访问控制。
- 保存正文实际引用的原始网页图片，不以渲染截图替代来源图片。
- 对受阻、部分抓取、fallback 或无正文图片的情况留下可审计说明。
- 结构校验通过仍需人工检查正文尾部、媒体归属和来源可靠性。
