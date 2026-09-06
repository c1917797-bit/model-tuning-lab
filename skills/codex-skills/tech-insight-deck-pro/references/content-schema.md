# `spec.json` 内容结构

同一份 UTF-8 JSON 同时驱动 Markdown/HTML 预览和最终 PPT，避免预览与成稿内容漂移。

## 目录

1. [完整示例](#完整示例)
2. [硬性规则](#硬性规则)
3. [单项技术页版面预算](#单项技术页版面预算)
4. [兼容字段](#兼容字段)

## 完整示例

```json
{
  "review": {
    "status": "draft",
    "version": 1,
    "review_note": "首次内容预览"
  },
  "title": "主题技术洞察",
  "department": "部门",
  "author": "作者",
  "date": "2026-07-24",
  "topic": "需要回答的核心技术与业务问题",
  "trend_insight": {
    "title": "技术趋势洞察",
    "time_horizon": "未来 12–24 个月",
    "stages": [
      {
        "stage_id": "T1",
        "period": "当前",
        "label": "主题相关的阶段名称",
        "technical_change": "这一阶段发生的具体技术变化",
        "example": {
          "kind": "practice",
          "title": "与该阶段直接对应的系统、项目、标准或论文",
          "organization": "机构或团队",
          "date": "2026-06",
          "fact": "可核验的技术机制、指标或工程事实",
          "source": "原始来源名称",
          "source_url": "https://example.org/source-1",
          "figure": "C:/absolute/path/example-1.png",
          "figure_caption": "原图及其技术含义"
        }
      },
      {
        "stage_id": "T2",
        "period": "未来 6–12 个月",
        "label": "主题相关的阶段名称",
        "technical_change": "工具链、系统集成或可靠性方面的技术变化",
        "example": {
          "kind": "paper",
          "title": "Paper or Project Title",
          "organization": "University / Research Lab",
          "date": "2026-05",
          "fact": "机制与带条件的实验结果",
          "source": "Conference/Journal/arXiv",
          "source_url": "https://example.org/source-2",
          "figure": "C:/absolute/path/example-2.png",
          "figure_caption": "架构图或关键实验图"
        }
      },
      {
        "stage_id": "T3",
        "period": "未来 12–24 个月",
        "label": "主题相关的阶段名称",
        "technical_change": "标准、生态与跨平台能力方面的技术变化",
        "example": {
          "kind": "standard",
          "title": "Standard or Ecosystem Project",
          "organization": "标准组织或开源社区",
          "date": "2026-04",
          "fact": "接口、兼容性或生态方面的具体变化",
          "source": "官方标准或项目页面",
          "source_url": "https://example.org/source-3",
          "figure": "C:/absolute/path/example-3.png",
          "figure_caption": "标准或项目原图"
        }
      }
    ],
    "viewpoint": "由上述技术变化自然引出的一句洞察观点"
  },
  "directions": [
    {
      "direction_id": "D1",
      "name": "方向名称",
      "category_label": "技术清单中的大类",
      "summary": "带立场的方向总结",
      "trend_link": {
        "stage_id": "T1",
        "claim": "该方向如何承接趋势判断"
      },
      "technologies": [
        {
          "technology_id": "P1",
          "name": "技术名称",
          "brief": "技术价值简述",
          "title": "English Paper or Technology Title",
          "reference": "Conference/Journal, year, DOI or arXiv",
          "reference_url": "https://example.org/source",
          "supporting_sources": [
            {
              "type": "Paper",
              "name": "独立核验来源 1",
              "url": "https://example.org/source-1"
            },
            {
              "type": "Official Blog",
              "name": "独立核验来源 2",
              "url": "https://example.org/source-2"
            },
            {
              "type": "Standard",
              "name": "独立核验来源 3",
              "url": "https://example.org/source-3"
            }
          ],
          "background": {
            "current_state": "当前系统、流程或能力已经做到什么，包含对象、场景和约束",
            "pain_point": "承接上一句，说明在什么条件下出现什么瓶颈、损失或风险",
            "research_question": "由此明确本页课题需要解决什么问题以及必须满足的约束"
          },
          "trend_link": {
            "stage_id": "T1",
            "claim": "本页验证或挑战的趋势判断",
            "evidence": "论文提供的关键机制或实验",
            "decision": "证据对产品或技术路线的含义"
          },
          "tech_detail_figures": [
            "C:/absolute/path/architecture.png",
            "C:/absolute/path/key-mechanism.png"
          ],
          "tech_detail_summary": "用一句适合人读的完整话说清楚核心思想：解决了什么问题、用了什么整体思路，可以比分点略长；不含冒号标签，「核心思想：」前缀由 build_deck.py 自动加粗添加",
          "tech_detail_points": [
            "关键技术一名称：该关键技术的机制或作用简述，写成自然流畅的一句话",
            "关键技术二名称：该关键技术的机制或作用简述，写成自然流畅的一句话"
          ],
          "experiment_method_header": "实验方法（Experimental Setup）",
          "experiment_method_points": [
            "实验设计：一句话说明想验证或对比什么",
            "平台与基线：具体运行环境、模型规模与对照系统",
            "数据与变量：具体数据规模、负载特征或受控变量"
          ],
          "experiment_figures": [
            "C:/absolute/path/result.png"
          ],
          "experiment_result_summary": "用一句适合人读的完整话说清楚这组实验总体证明了什么，可以比分点略长；不含冒号标签，「实验总结：」前缀由 build_deck.py 自动加粗添加",
          "experiment_result_points": [
            "具体指标名称一：带条件和数字的结果表现，写成自然流畅的一句话",
            "具体指标名称二：带条件和数字的结果表现，写成自然流畅的一句话"
          ],
          "figure_quality_checks": [
            {
              "path": "C:/absolute/path/architecture.png",
              "source_ref": "Figure 3",
              "complete": true,
              "clean_crop": true,
              "legible": true,
              "crop_note": "完整保留架构边界、箭头、图例和节点标签；已排除相邻正文"
            },
            {
              "path": "C:/absolute/path/key-mechanism.png",
              "source_ref": "Figure 4",
              "complete": true,
              "clean_crop": true,
              "legible": true,
              "crop_note": "完整保留子模块与标签；已排除页眉、页码和正文段落"
            },
            {
              "path": "C:/absolute/path/result.png",
              "source_ref": "Figure 7",
              "complete": true,
              "clean_crop": true,
              "legible": true,
              "crop_note": "完整保留坐标轴、图例和关键数值；已排除无关文字"
            }
          ],
          "takeaway": "相比现有基线，该机制首次把压缩与调度合并为单一阶段，端到端延迟更低；但目前仅在小规模集群验证，尚未在生产环境规模化，工程化仍需处理状态漂移。对当前系统而言，可优先在负载可预测的场景试点，并借鉴其压缩与调度合并的设计。"
        }
      ]
    }
  ],
  "overall_summary": "摘要页的一句话总体判断",
  "academic_resources": {
    "title": "学术资源洞察",
    "universities": [
      {
        "name": "高校名称",
        "school_lab": "学院 / 实验室",
        "focus": "主要研究方向",
        "strength": "与本主题最相关的长期积累",
        "url": "https://example.edu/lab"
      },
      {
        "name": "高校名称二",
        "school_lab": "学院 / 实验室",
        "focus": "主要研究方向",
        "strength": "与本主题最相关的长期积累",
        "url": "https://example.edu/lab-2"
      },
      {
        "name": "高校名称三",
        "school_lab": "学院 / 实验室",
        "focus": "主要研究方向",
        "strength": "与本主题最相关的长期积累",
        "url": "https://example.edu/lab-3"
      }
    ],
    "faculty_projects": [
      {
        "faculty": "教师姓名",
        "title": "教授 / 副教授",
        "university": "高校 / 实验室",
        "research_focus": "研究方向",
        "project": "代表课题名称",
        "period": "2025–2027",
        "profile_url": "https://example.edu/faculty",
        "project_url": "https://example.edu/project"
      },
      {
        "faculty": "教师姓名二",
        "title": "教授 / 副教授",
        "university": "高校 / 实验室",
        "research_focus": "研究方向",
        "project": "代表课题名称",
        "period": "2025–2027",
        "profile_url": "https://example.edu/faculty-2",
        "project_url": "https://example.edu/project-2"
      },
      {
        "faculty": "教师姓名三",
        "title": "教授 / 副教授",
        "university": "高校 / 实验室",
        "research_focus": "研究方向",
        "project": "代表课题名称",
        "period": "2025–2027",
        "profile_url": "https://example.edu/faculty-3",
        "project_url": "https://example.edu/project-3"
      }
    ],
    "viewpoint": "对高校与教师课题分布的一句学术观点"
  },
  "overall_viewpoint": {
    "title": "技术洞察观点",
    "viewpoint": "压缩前文后的一句话观点",
    "sections": [
      {
        "title": "与主题直接相关的小标题一",
        "points": ["具体观点"]
      },
      {
        "title": "与主题直接相关的小标题二",
        "points": ["具体观点"]
      },
      {
        "title": "与主题直接相关的小标题三",
        "points": ["具体观点"]
      }
    ],
    "unresolved": [
      "仍未解决的具体技术问题"
    ],
    "suggestion": "一条明确、可执行、有先后顺序的建议"
  }
}
```

## 硬性规则

- `review.status` 只能为 `draft` 或 `approved`
- `review.version` 为大于等于 1 的整数
- `trend_insight.stages` 必须包含 3–4 个阶段，`stage_id` 必须唯一
- 每个阶段都必须包含一个 `example`；`kind` 可为 `practice`、`paper`、`project` 或 `standard`
- 每个 `example` 必须包含来源 URL、真实图片、图注、机构、日期和具体技术事实
- 趋势页使用 `viewpoint` 作为底部一句洞察观点，不使用 `thesis` 或 `decision_implication`
- 每个 direction 和 technology 都必须包含 `trend_link.stage_id`
- 所有 `trend_link.stage_id` 必须引用已有趋势阶段
- 每个 direction 至少包含一个 technology
- 每个 technology 的 `supporting_sources` 至少包含 3 个独立权威来源
- 每个 technology 的 `background` 必须包含 `current_state`、`pain_point` 和 `research_question`
- 三个背景字段只用于保证内容完整；页面会把它们合成连续自然段，不得在字段内容前写“现状：”“痛点：”“问题：”等标签
- `current_state` 写对象、场景与当前约束，`pain_point` 承接说明瓶颈、损失或风险，`research_question` 再引出课题需要解决的问题
- 每个 technology 必须包含 `tech_detail_summary`：一句适合人读的「核心思想」完整表述，可以比分点略长，本身不含冒号标签，加粗的“核心思想：”前缀由 `build_deck.py` 自动添加
- 每个 technology 的 `tech_detail_points` 必须包含 2–3 个「关键技术」分点，每项写成「关键技术名称：简述」，技术名称会自动加粗，渲染时每项前会自动加上「• 」项目符号，并统一置于固定的“关键技术：”小标题之下
- 每个 technology 的 `experiment_method_points` 必须包含 3–4 项，并按「实验设计→平台与基线→数据与变量」从整体到细节分层组织：第 1 项标签固定为「实验设计」「验证目标」或「总体设计」之一，第 2 项标签固定为「平台与基线」「环境与基线」或「实验环境」之一，其余项标签固定为「数据与变量」「关键变量」「数据与负载」或「负载与变量」之一
- 每个 technology 必须包含 `experiment_result_summary`：一句适合人读的「实验总结」完整表述，说清楚这组实验总体证明了什么，可以比分点略长，本身不含冒号标签，加粗的“实验总结：”前缀由 `build_deck.py` 自动添加
- 每个 technology 的 `experiment_result_points` 每项都必须写成「具体指标名称：结果表现」；标签必须是被测的具体指标（如吞吐量、延迟、显存占用、准确率），不得使用“关键数据”“实验数据”“效果展示”等空泛词；结果表现必须包含具体数字、百分比或倍数；渲染时统一放在“关键指标：”小标题下，每项自动加“• ”项目符号
- 不要设置 `experiment_result_header`：该分区在模板里已经有固定的“实验结果”标签，内容里再写一遍会重复；直接提供 `experiment_result_summary` 和 `experiment_result_points` 即可
- 每个 technology 必须包含 1–2 张技术图和至少一张实验图
- 技术细节只有一张图时自动扩展；两张图时固定横向排列，并按原图长宽比分配宽度
- 两张技术图必须内容互补且路径不同，不得重复使用同一图片
- `figure_quality_checks` 必须覆盖全部技术图和实验图；每项都要标明原图编号或来源位置，并确认 `complete`、`clean_crop`、`legible` 为 `true`
- 截图长边至少 1000 px、短边至少 350 px；不得缺失图框、图例、坐标轴、标签或关键对比项
- 截图不得包含页眉页脚、页码、相邻正文段落或与当前论点无关的区域
- 阶段图片、技术图和实验图路径可以相对 `spec.json` 所在目录，也可以使用绝对路径
- 学术资源至少包含 3 所高校和 3 位教师及其代表课题；高校、教师主页与课题 URL 不可缺失
- `overall_viewpoint.sections` 必须包含 3 个按主题命名的部分，`unresolved` 不可为空
- 生成 Markdown/HTML 预览前，全部图片必须存在并通过分辨率与质量校验
- 构建 PPT 时，`review.status` 必须为 `approved`

## 单项技术页版面预算

`validate_spec.py` 用“版面单位”估算模板字号下的文字占用：中文和全角字符约为 1，
半角英文、数字和标点按较小权重折算。不要手工猜测是否能放下，以校验脚本结果为准。

“关键技术”“关键指标”这两个区域的上限不是凭感觉定的，而是按模板实际盒子尺寸换算的物理容量：
11pt 字号、1.2 倍行距下，一行大约能排 36–37 个版面单位；每个分点都是独立段落，哪怕内容很短
也会独占一行，所以“单项上限”按能在一行内排完来定（34），避免多出的换行吃掉一整行的高度；
“总项上限”（115）再按“关键技术/关键指标”标题 + 最多 3 个分点的行数总和来定。总结句允许
换行，但上限（70）按最多 2 行估算。构建阶段还会动态收紧或放宽实际图片区域：如果图片实际渲染
得比预留空间矮（例如偏宽的柱状图），多出的高度会自动让给下方文字，而不是留成空白；这个动态
调整不会改变下面表格里的版面上限，上限始终按"图片需要更多空间"的最差情况计算，保证任何一张
图片都不会把文字挤到上限以下。

| 区域 | 内容要求 | 版面上限 |
|---|---|---:|
| 技术背景 | 三个字段合成一个自然段，不手工换行 | 118 |
| 核心思想 | `tech_detail_summary`：1 句完整表述，含“核心思想：”前缀一起计算 | 70 |
| 关键技术 | `tech_detail_points`：2–3 项，每项含“• ”符号一起计算，且单项必须能在一行内排完 | 合计 115；单项 34 |
| 实验方法 | 3–4 项，按「实验设计→平台与基线→数据与变量」分层，加方法标题一起计算 | 合计 150；单项 56 |
| 实验总结 | `experiment_result_summary`：1 句完整表述，含“实验总结：”前缀一起计算 | 70 |
| 关键指标 | `experiment_result_points`：2–3 项，标签为具体指标名称且含数字，每项含“• ”符号一起计算，且单项必须能在一行内排完；不设 `experiment_result_header` | 合计 115；单项 34 |
| 洞察启示 | 连续自然段；至少 3 个完整分句 | 合计 110 |

`tech_detail_summary`、`experiment_result_summary` 都至少需要 20 个中文字符，写成完整、
适合人读的一句话，而不是电报式短语；可以比各自的分点略长，让核心思想或实验总结读起来自然顺畅，
但不要接近 70 的上限还硬塞进更多从句——留一点余量，避免换行超过 2 行。

洞察启示改为聚焦三件事，不再要求复述机制或实验细节：

- 至少 70 个中文字符
- 先进性：与现有方案或基线相比的具体优势
- 成熟度：当前处于研究原型、小规模验证还是可规模化落地
- 借鉴意义：对当前系统或工程实践的具体指导

任何区域超过上限都必须改写内容。不得通过自动缩小字号、压缩行距、覆盖形状或裁切文字
绕过校验；生成后还要运行 `check_ppt_text_overflow.ps1` 测量 PowerPoint 中的实际文本边界。

## 兼容字段

技术图支持：

- 首选：`tech_detail_figures`
- 兼容：`tech_detail_figure`、`tech_detail_figure2`

实验图支持：

- 首选：`experiment_figures`
- 兼容：`experiment_figure`

新项目应使用列表字段。

旧版字符串 `background` 仅用于读取历史 spec；新建或更新 spec 时必须改为包含
`current_state`、`pain_point` 与 `research_question` 的对象。
