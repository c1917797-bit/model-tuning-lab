# Model Tuning Lab

**面向昇腾的论文复现、推理性能优化与证据驱动的维护者 Skill 库。**

本仓库把论文分析、模型适配、源码定位、实验验证、运行时补丁交付和经验沉淀组织成可接手、可追溯的工作流程。目标不是“生成一段代码”，而是在真实模型与设备上证明修改生效、收益成立、质量满足约定，并能安全回退。

当前 `main` 的核心是 **29 个仓库级 Skill**、实验与交接规范、证据校验工具及补丁模板。它不是开箱即用的训练框架或模型服务；具体模型实现和尚未通过验收的候选由各自实验分支维护。

## 能支持哪些工作

| 工作 | 主要内容 | 能力入口 |
| --- | --- | --- |
| 论文理解与复现 | 分析完整方法链、适用条件、参考实现和复现口径，区分原方法、忠实迁移与派生方案 | [Paper-to-Ascend](.agents/skills/paper-to-ascend/SKILL.md)、[论文分析](.agents/skills/paper-ingestion/SKILL.md)、[复现验证](.agents/skills/paper-to-ascend-reproduction/SKILL.md) |
| 昇腾适配与优化 | 核对真实模型架构和运行路径；从瓶颈证据选择配置、调度、缓存、通信或算子层修改 | [架构适配](.agents/skills/ascend-architecture-fit/SKILL.md)、[源码定位](.agents/skills/ascend-source-map/SKILL.md)、[性能优化](.agents/skills/ascend-performance-optimization/SKILL.md) |
| Profiling 诊断 | 抓取、读取和解析真实运行数据，关联时间线、算子、Kernel、数据搬运与 HCCL，再定位修改点 | [CANN / Profiler 分析](.agents/skills/ascend-cannbot-profiler/SKILL.md) |
| 性能与质量验证 | 冻结对照条件、证明实际执行路径、重复测量，分别判定服务性能和模型质量 | [性能证据](.agents/skills/ascend-benchmark-evidence/SKILL.md)、[模型质量](.agents/skills/ascend-model-quality-evaluation/SKILL.md) |
| 可移除补丁交付 | 通过独立 monkeypatch / 插件加载修改，绑定源码与补丁哈希，验证各 Worker 激活、关闭对照和重启回退 | [运行时补丁交付](.agents/skills/runtime-monkeypatch-delivery/SKILL.md) |
| 经验复用与任务接手 | 将成功、失败和证据不足转成带触发条件的规则、验证案例和交接状态，支持续跑 | [经验沉淀](.agents/skills/mst-experience-ingestion/SKILL.md)、[维护者交接](.agents/skills/mst-maintainer-handoff/SKILL.md) |

这些入口是 Agent 执行工作的规范与可复用资产，不等于一个已经全自动运行的多智能体平台。`cannbot-skills` 是算子与 CANN 分析的外部参考；引用其经验仍需在目标环境验证，不能替代本地证据。

## 工作循环如何运行

1. **分析论文与适用条件**：从洞察得到的候选论文或已观测瓶颈出发，梳理实现规格和完整方法链；核对模型是 Dense、MoE，还是启用了 MTP 等路径，避免优化不存在的机制。
2. **建立基线与定位热点**：确认模型、镜像、源码、硬件和工作负载；测量 Prefill / Decode，并依据 Profiling 计算可改善的端到端空间。
3. **复刻实现与昇腾适配**：优先复用准确匹配的上游能力；针对实现缺口或优化目标提出可验证候选，并明确区分上游复用与本地增量。本地运行时修改以独立 monkeypatch 加载；需要自研算子时，另行确认芯片、公开 API、构建环境与授权范围。
4. **分层验证**：先做数值、状态和敏感语义校验，再进行真实服务对照。补丁激活、算子变快、模型性能提升和质量通过是不同层级的证据。
5. **判定与交付**：按预先约定的性能、质量、稳定性及回退门槛，记录 `accepted`、`rejected`、`inconclusive` 或 `failed`；只交付通过完整门槛的精确版本。
6. **诊断、反思与复用**：未通过时定位首个失败环节，保留证据并恢复安全代码；将可重复的经验沉淀到 Skill、验证案例或规则中，再指导下一轮候选选择。

性能和精度使用独立测试口径。性能需覆盖任务要求的并发、上下文、输出长度和多轮对照；质量需冻结数据、提示词、评分器、停止条件与采样参数。质量 Skill 默认采用每组、每数据集三轮和 2048-token 自然停止上限；具体任务可以冻结更严格的规则。GSM8K、MMLU、HumanEval 等测试应按任务和模型能力选用，不应把某项历史验收当成所有任务的固定配置。

### 经验如何转化为能力

“自进化”是受验证约束的知识更新：**真实执行反馈 → 提炼可复用经验 → 更新最小 Skill / 规则 / 验证案例 → 校验与复测 → Git 版本化 → 后续任务按条件检索复用**。

不是将所有日志写成规则，也不是自动接受 Agent 的每次反思。新规则必须说明何时触发、下次行为如何改变、证据在哪里、如何验证；一次失败不能被泛化成某篇论文或某类模型永远无效。参见 [Skill 治理](.agents/skills/mst-skill-governor/SKILL.md) 和 [迭代循环规范](.agents/skills/mst-loop-engineering-framework/SKILL.md)。

## 主分支包含什么

```text
AGENTS.md                         维护者职责、边界和必读入口
.agents/
  skills.registry.yaml            Skill 注册表与选择规则
  skills/                         29 个 Skill 及相关参考、工具、模板
  HANDOFF.md                      已合入的交接信息
  git-policy.yaml                 工作分支、检查点与合入规则
  experiments/                    实验说明与记录模板
  evals/                          维护规则的验证案例
  workstreams/                    已入仓的任务记录、复现工具与证据索引
docs/                             操作手册、经验与分支治理记录
scripts/
  validate-mst.sh                  Skill Tree 结构校验
  bootstrap-host-test-env.sh       目标主机 CPU 单测环境准备
pyproject.toml                    Python 版本与测试依赖声明
configs/                          配置目录及待安装插件清单
src/、tests/                      主分支通用源码与测试目录，目前为占位
```

实验专用校验器和历史复现脚本位于相应 `.agents/workstreams/` 中，不是通用模型服务 API。补丁模板位于 [runtime-monkeypatch-delivery/assets/template](.agents/skills/runtime-monkeypatch-delivery/assets/template)；它需要实现具体修改并填充真实清单，不能直接当作已验证优化启用。

<details>
<summary>完整 Skill 清单：15 个昇腾 / 论文 / 交付 Skill，14 个维护治理 Skill</summary>

### 昇腾、论文与交付

- `chicaihong01-host-maintenance`
- `ascend-npu-environment-orientation`
- `paper-ingestion`
- `ascend-architecture-fit`
- `ascend-source-map`
- `ascend-canary-implementation`
- `ascend-performance-optimization`
- `ascend-cannbot-profiler`
- `ascend-inference-tuning-loop`
- `ascend-benchmark-evidence`
- `ascend-model-quality-evaluation`
- `runtime-monkeypatch-delivery`
- `paper-to-ascend-reproduction`
- `paper-to-ascend-reporting`
- `paper-to-ascend`

### 维护治理

- `mst-agentsmd-authoring`
- `mst-experience-ingestion`
- `mst-git-checkpoint-policy`
- `mst-loop-engineering-framework`
- `mst-maintainer-handoff`
- `mst-parallel-workstreams`
- `mst-practice-iteration-planning`
- `mst-repo-onboarding`
- `mst-repo-transformation`
- `mst-runtime-skill-boundary`
- `mst-skill-governor`
- `mst-skill-tree-design`
- `mst-tool-adapter-boundary`
- `mst-transformation-verification`

完整路径、状态及选择规则以 [Skill 注册表](.agents/skills.registry.yaml) 为准。这里列的是仓库级维护者 Skill，不是本机所有个人 Skill 或插件的安装清单。

</details>

## 开始使用

```bash
git clone https://github.com/c1917797-bit/model-tuning-lab.git
cd model-tuning-lab
git status --short --branch
git worktree list --porcelain
sh scripts/validate-mst.sh
```

先读 [AGENTS.md](AGENTS.md)、[当前交接](.agents/HANDOFF.md)、[Skill 注册表](.agents/skills.registry.yaml) 和 [接手手册](docs/RUNBOOK.md)，再按任务选取最小 Skill 组合。结构校验通过只证明维护者资产满足结构规则，不代表模型性能或精度已通过。

可给接手 Agent 这样的指令：

> 先读取 AGENTS.md、.agents/HANDOFF.md 和 .agents/skills.registry.yaml，按 mst-repo-onboarding 核对当前分支、工作树及任务状态。继承已有证据和续跑点，不重新开始历史实验；机器相关工作按 chicaihong01-host-maintenance 在目标主机执行。任务是：〈填写具体任务及验收标准〉。

Clone 可以带走 Skill、治理规则和已入仓证据，但不会自动安装 AWMCP / 外部插件、准备模型数据或建立设备权限。[插件清单](configs/maintainer-plugins.md) 是待安装参考，不是当前安装状态。

### 主机上的 CPU 单测

仓库要求 Python 3.10 或更新版本。`chicaihong01` 的系统 Python 3.9 不满足要求，CPU 单测使用仓库提供的 uv / Python 3.11 环境：

```bash
./scripts/bootstrap-host-test-env.sh
```

随后使用脚本打印的 `PYTHONPATH=... python -m pytest` 命令，在拥有实际测试的工作分支中执行。共享环境位于 `/cache/cch/python-envs/model-tuning-lab-py311`，缓存与工具链位于 `/cache/cch/toolchains/uv/`；不要把它误用成 NPU 运行环境。设备测试需进入任务冻结的 Ascend 容器及配套 CANN / torch_npu / vLLM-Ascend 环境。

## 在 chicaihong01 上维护代码

机器相关开发和设备验证的规范入口为：

```text
/opt/host/vnf/austinov/model-tuning-lab
```

兼容路径为 `/cache/austinov/model-tuning-lab`。本机 Clone 便于阅读和准备材料，不能替代目标主机的代码与设备证据。

- 按 [主机维护 Skill](.agents/skills/chicaihong01-host-maintenance/SKILL.md) 动态解析 AWMCP 拓扑。默认规范节点是 `chicaihong01/ma`；其他节点需明确授权并重新核实目标身份，不能硬编码旧 peer ID。
- 远程操作前加载 `host-development`，确认目标 peer 和直接路由证明。认证值只通过连接器的 `verify` 字段传入，不写进仓库、示例、日志或交接。
- 分配设备前同时核对 Docker `HostConfig.Devices.PathOnHost`、物理 `npu-smi` 进程与协作锁。容器内逻辑 `0,1,2,3` 可能映射到其他物理卡，不能单独作为占用证据。
- 卡号、端口、内存和容器状态是实时事实；旧交接中的快照不是当前资源授权。不要停止他人服务或调整 HugeTLB、驱动等共享资源来“排除阻塞”。

## 如何读实验结果与交接状态

`main` 保存已合入的维护知识；具体实现、正在进行的验证和未接受的候选，应查看其所属实验分支以及分支内的 `task.json`、`HANDOFF.md` 和结果记录。分支已推送、代码能运行、单个算子通过，都不等于最终交付通过。

仓库已有一个可追溯的历史正例：**HYPIC-only 对无前缀缓存基线**，在冻结的 Qwen3.6-27B / TP4 / 4×910B4 / 40960 token 调度预算下完成 18 个计划单元及独立审计；记录的平均 TTFT 降低 43.6345%、TPOT 降低 18.9911%、输出吞吐提升 36.0663%。LongBench-v2 和 GSM8K 均值分别变化 -0.2625、-0.1516 个百分点，落在当时观测的基线三轮波动范围内，结论仅为该冻结配置下未观察到实质质量回退。

这是历史测试口径，不是当前 Qwen3.5 性能任务的 P95 验收，也不证明任意模型或流量均无损。其历史质量上限为 1024 token，不能改写成新的 2048-token 结果。参见 [完整决策](.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/decision-hypic-formal-npu4-7-tp4-b40960.json) 和 [完成审计](.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/COMPLETION_AUDIT.md)。同一方法的其他配置仍可能被拒绝或证据不足，不应混用分母或汇总收益。

接手和追溯入口：

- [已合入交接信息](.agents/HANDOFF.md)
- [工作流索引](docs/ACTIVE_WORKSTREAMS.md)：其中日期化任务和资源信息需与所属分支及实时主机状态核对
- [成功与失败经验](docs/LESSONS_LEARNED.md)
- [模型切换测试经验](docs/QWEN_MODEL_SWITCH_TESTING_LESSONS.md)
- [实验记录模板](.agents/experiments/TEMPLATE.yaml)
- [结果报告模板](.agents/skills/paper-to-ascend-reporting/references/report-template.md)

按 [Git 策略](.agents/git-policy.yaml)，非简单变更使用独立工作树和命名 `work/*` 分支，先推送起始检查点，验证后提交并立即推送当前分支；只有串行集成完成后才成为 `main` 的已合入事实。数据集、模型权重、原始响应、完整 Profiling 和大型构建产物保留在仓库外，Git 只记录必要配置、摘要、路径、哈希与决策。
