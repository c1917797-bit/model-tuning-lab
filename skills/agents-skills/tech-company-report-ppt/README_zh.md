# TECH PPT Skill

`tech-company-report-ppt` 是一个用于制作科技公司内部汇报 PPT 的 Codex skill，适合洞察报告、技术分析、竞品分析、战略复盘和机会点汇报。

English documentation: [README.md](README.md)

## 用途

这个 skill 会把用户输入的简短主题转成结构化 PPT 工作流，默认采用固定三段式页面：

- 顶部标题可编辑。
- 中间为固定尺寸的 `image2` 静态图片画布。
- 底部结论可编辑。

这样可以把关键信息保留为可编辑文本，同时把复杂主体视觉交给高质量生图工具或可靠素材完成。

## 核心工作流

1. 用户只输入主题或简短需求。
2. Codex 先生成 `page-contracts.json`，定义每页角色、标题、核心观点、要点、底部结论、中间视觉类型和证据备注。
3. `scripts/init_three_zone_project.js` 创建项目目录，并为每个图片页生成 `image2-prompts/slide-XX.md`。
4. 使用 `image2` 生成中间画布，保存到 `image2-middle/slide-XX.png`。
5. `scripts/build_three_zone_deck.js` 组装 PPT，标题和底部结论保持可编辑，中间画布为静态图片。
6. 导出 contact sheet 做轻量 QA。

默认输出结构：

```text
<output-project>/
  page-contracts.json
  workflow-notes.md
  image2-prompts/
  image2-middle/
  preview/
  qa/
  final.pptx
```

## 能力范围

除了基础 PPT 组装，这个 skill 还会约束报告结构和视觉执行：

- 报告结构：封面、目录、一页总览、能力全景、机制拆解、证据页、机会点表、章节收束和总结页。
- 视觉执行：克制的内部汇报风格，紧凑网格、低圆角卡片、细分割线和少量红色强调。
- 中间画布 prompt：覆盖架构图、双主线总览、调用链、Agent loop、机会点表、证据卡和综合判断页。
- 内容控制：page contracts 保证标题和底部结论可编辑，image2 只接收中间画布生成要求。
- 轻量 QA：检查页数、标题/结论可编辑性、中图存在、中图区铺满、文字错误和 contact sheet 输出。

## 三段式页面结构

标准内容页必须遵循以下结构：

- 标题：可编辑 PPT 文本。
- 中间视觉：固定中间区域内的静态图片。
- 底部结论：可编辑 PPT 文本。

中间视觉必须只生成“中间内容”，比例约为 `2.37:1`，不得重复生成标题、底部结论、页码或其他外层幻灯片元素。

## 视觉素材策略

`image2` 是中间画布的首选来源。也可以使用官方截图、用户素材或其他生图工具，只要它们能产出有价值的中间视觉。

如果没有生图能力，也没有可用素材，必须显式标记 `visual fallback`。fallback 只是草稿级降级方案，不是默认质量路线。

## 失败条件

以下情况视为不可接受：

- 标准内容页缺少中间图却仍然生成。
- 缺图时静默生成占位 PPT。
- 标题或底部结论被锁进图片。
- 中间图重复生成标题或底部结论。
- 中间图包含页码、placeholder、lorem ipsum 或乱码。
- 主视觉是脚本方块图，而不是 image2 或有效素材。
- 页面稀疏、缺少设计感，或像低质脚本生成的 PPT 方块。

默认情况下，`scripts/build_three_zone_deck.js` 在缺少中间图时会直接失败。只有显式设置 `ALLOW_VISUAL_FALLBACK=1` 时，才允许生成降级草稿。

## 示例效果

以下两个已审核示例展示了默认三段式结构：可编辑标题、静态中间画布、可编辑底部结论。

![Google I/O 2026 核心洞察](docs/showcase/google-io-2026-core-insight.png)

![Apple WWDC 26 核心洞察](docs/showcase/apple-wwdc-26-core-insight.png)

## 仓库内容

- `SKILL.md`: Codex skill 指令。
- `agents/openai.yaml`: Agent 配置。
- `references/`: 模板、风格、页面角色、page contract、prompt 模板、中间画布、fallback 和轻量 QA 规则。
- `examples/`: 最小 page contract 和示例中间画布。
- `scripts/`: 初始化、组装 PPT 和 smoke test 脚本。
- `docs/showcase/`: README 使用的审核通过示例图。

## Smoke 测试

运行：

```bash
node scripts/smoke_test_v1.js
```

该测试会在 `tmp-smoke/` 下初始化临时项目，复制示例中间画布并生成测试 PPT。验证后应删除 `tmp-smoke/`。
