# TECH PPT Skill

`tech-company-report-ppt` 用于制作华为风格的技术洞察、竞争分析、战略规划和管理层汇报。它把报告写作、模板选型、Image2 整页设计、自动复核和对象级可编辑 PowerPoint 重建合并为一条工作流。

English documentation: [README.md](README.md)

## 核心原则

设计稿和最终 PPT 承担不同职责：

- **Image2 设计稿**负责完整 16:9 页面构图，包括信息层级、视觉节奏、密度和素材位置。
- **可编辑 PPTX**按照通过复核的设计稿重建。标题、正文、表格、流程框、连线和简单图表使用 PowerPoint 原生对象；照片、产品截图和复杂插画作为独立、可替换图片保留。

整页设计图只能作为视觉蓝图，不能铺成最终页面背景。

## 工作流程

1. 生成并一次性确认完整大纲。
2. 将大纲转为权威内容契约 `deck_spec.json`。
3. 每页先从 `assets/huawei-template/PPT模板.pptx` 选择真实模板页，并写入 `template-map.json`。
4. 将模板渲染图、页面契约和指定素材一起交给 Image2，生成整页设计稿。
5. 自动检查文字、素材、密度、配色、布局和模板一致性；失败页面必须修复或阻塞。
6. 将通过复核的页面重建为对象级可编辑 PPT。
7. 实际渲染、对比设计稿并完成结构与视觉验收。

默认只在完整大纲阶段等待用户确认。大纲确认后自动完成后续页面，不再等待样张或逐页审批；用户明确要求检查点时除外。

## 命令入口

```bash
python scripts/huawei_ppt.py doctor
python scripts/huawei_ppt.py init --brief <input> --out <project>
python scripts/huawei_ppt.py prepare-design <project>
python scripts/huawei_ppt.py review-designs <project>
python scripts/huawei_ppt.py prepare-editable <project>
python scripts/huawei_ppt.py finalize <project>
python scripts/huawei_ppt.py status <project>
```

用户确认大纲后，将 `deck_spec.json` 顶层的 `outline_approved` 设为
`true`。`prepare-design` 会检查该门槛。运行 `scripts/install_skill.sh`
会安装仓库内置的 `editppt` 运行时，并将本仓库软链接到
`~/.codex/skills/tech-company-report-ppt`。

## 权威产物

```text
<deck-project>/
├── outline.md
├── deck_spec.json
├── template-map.json
├── design-prompts/
├── design-drafts/
├── design-jobs.json
├── design-run-state.json
├── design-review.json
├── editable-run/
├── qa/
└── final/<deck-name>.pptx
```

`deck_spec.json` 是页面文字和事实的唯一权威来源。最终重建不得从设计稿 OCR 猜测已有规范文案。

## 规范索引

| 主题 | 规范文件 |
|---|---|
| 故事线、标题与写作 | `references/writing-and-storyline.md` |
| 华为视觉风格 | `references/huawei-visual-style.md` |
| 模板选择 | `references/template-selection.md` |
| 页面内容契约 | `references/deck-spec-schema.md` |
| Image2 整页设计 | `references/image2-design.md` |
| 自动设计复核 | `references/design-review.md` |
| 可编辑重建 | `references/editable-rebuild.md` |
| 最终渲染与 QA | `references/final-qa.md` |

## 不可接受的结果

- 未记录模板页选择，直接从空白页自由发挥。
- 页面内容偏离或弱化已确认的核心观点。
- 出现占位符、乱码、虚构数据或 OCR 猜测文字。
- 需要官方证据时使用 Image2 仿造产品界面。
- 页面像 Dashboard 卡片墙、营销海报或原始 Excel 导出。
- 在整页源图上叠加少量可编辑文本冒充可编辑 PPT。
- 文字或图片裁切、字号不可读、无意义留白、元素漂移。
- 完成重建后没有实际渲染和逐页检查。

## 版权说明

工作流参考了 ningzimu 的两个 MIT 项目：[codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) 与 [image-to-editable-ppt-skill](https://github.com/ningzimu/image-to-editable-ppt-skill)。详情见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 和 `LICENSES/`。
