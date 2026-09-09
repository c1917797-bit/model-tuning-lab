# Qwen3.5 MTP-off：经验与接管入口

本包是经过文件和工件复核的维护交接，不是性能交付通过声明。
证据索引见 `evidence.json`；可复用经验的触发条件、下一次动作、落点和
验证方法见 `lessons.json`。原始数据、日志和未提交代码备份不进入 Git。

## 0. Status

- **性能目标尚未达成，T15 尚无完成的候选或跨测试集结果。**
- 主任务分支：`work/qwen35-performance-delivery`。
- 主任务工作区：`/opt/host/vnf/austinov/worktrees/qwen35-performance-delivery`。
- 原 task ID 保留为 `exp-20260904-qwen35-query-rewrite-3x-e2e`，其中
  `3x` 是历史标识，不是当前门槛；不要因此新建一个重复业务任务。
- 本经验交接分支：`work/qwen35-experience-ingestion-20260909`；其验证或
  完成状态不代表性能分支完成，也不代表已合入 `main`。
- 文件/备份快照时间：**2026-09-09T21:43:08Z**（UTC）。所有机器状态均需
  接管时重新查询，不能把快照当租约。

## 1. North Star

Qwen3.5-27B、Ascend 910B4、TP4/DP1、BF16；MTP/speculation 始终关闭，
不量化、不重训练。交付是在未修改的官方 vLLM-Ascend 0.23.0 镜像中加载的
可移除 runtime Python plugin，不用 source overlay 冒充最终交付。
自定义 OPP 只有在另行证明必要性、兼容性、正确性和只读加载边界后才可讨论。

c1/c5/c8/c16 每档分别取三轮的请求级 P95 再取中位数；TTFT 候选/基线
比值必须 <=0.60，TPOT 必须 <=0.80。P99 单独审查，P50 仅辅助。
这是延迟降低 40%/20%，不是“加速 1.4x/1.2x”。最终还需完整 357 行
配对语义无实质退化；不能拿 32 行 canary 或空答案字段声称通用准确率无损。

## 2. Current Focus

将 T15 限定为可泛化的 JIT/启动策略实验，不能拿测试集预跑充当优化。
TPOT 仍需独立的真实执行效率改进。当前只有既有实验复核，没有在本次交接
整理中启动模型、运行新 benchmark、停止容器或改变 NPU/内存配置。

比较口径必须显式登记，不能互换：

1. 历史 TP4 MTP-off 基线 `baselines/tp4dp1-npu03-ref-v1` 保留原始工件。
   它的 `baseline-summary.json` 是 P50 汇总，P95 要从三轮原始 JSON 读取。
2. `scripts/analyze_qwen35_candidate_vs_original.py` 还有哈希锁定的历史
   `tp4-dev-decodegraph/quick32-v3` 口径，不要误认为与前者相同。
3. 当前 `VALIDATION_PLAN.md` 要求环境实质变化后使用新的同环境配对 control。
   这用于当前 treatment 的因果比较；历史连续性参照仍保留，不得静默替换。
4. T12 control、T14 r1、T14 r2 都不是可随意替代上述口径的新“冻结基线”。
   新实验先记录采用的比较器、baseline ID、缓存状态和阈值，再采样。

## 3. Recent Progress — 成功、失败和不确定性

### 已证明可复用的成功

**交付机制可行，不等于性能过关。** T13 计划记录 T12 已在四个 TP worker
激活只读 runtime patch，保持官方镜像身份，并完成自然 EOS smoke。
这是加载和激活机制的成功；性能与最终语义门槛并未通过。[E-T13-PLAN]

**GDN projection fusion 是有历史实测支持的优化组成部分。** 原始 decision
保存了 c1/c5/c8/c16 三轮结果；TTFT 加速约 2.206/1.938/1.930/1.910，
TPOT 约 1.381/1.651/1.753/1.980。它使用 source overlay，且历史验收门槛
不同，因此不能直接算作当前 runtime-plugin 交付通过。[E-GDN]

**control 的冷暖差异已复现。** 本次找回了先前漏报的 T14 r2：

| 运行 | TTFT P95，ms | TPOT P95，ms | 完成/错误 |
|---|---:|---:|---:|
| T12 control，c1/r1 | 6502.636 | 31.754 | 32/0 |
| T12 candidate，c1/r1 | 5697.694 | 31.641 | 32/0 |
| T14 control，c1/r1 | 6461.675 | 35.405 | 32/0 |
| T14 control，c1/r2 | 840.460 | 28.969 | 32/0 |

T14 r2 的窗口文件记录 `.npubin` 数量从 25 到 25；这些都是 control，
不是 warmup treatment A/B。没有 r3 或跨集结果，不宣称正式优化收益。
DEBUG 日志、输出长度与执行顺序仍需作为潜在混杂因素处理。
[E-T12-CONTROL, E-T12-CANDIDATE, E-T14-R1, E-T14-R2]

### 已拒绝、不得原样重跑的路线

| 路线 | 有限证据与决策 | 合法后继条件 |
|---|---|---|
| bounded-MMAR t11 | 历史 c1 三轮约 TTFT 1.9128x、TPOT 1.2085x；TPOT 不过当前 1.25x 等价门槛 | 改变实质机制，先过精确 BF16 M=1 gate；不是原样再测 |
| T12 standalone | 单轮约 TTFT 降 12.38%、TPOT 降 0.36%；记录仅 16/32 响应哈希相同，不能晋升 | 配对语义审查与新的性能假设 |
| MMAR x3 residual | 直接复制 residual 会重复累加；语义保留版本正确，但几何平均加速仅 0.655224x，最差 0.635134x | 不重复添加逐层缩放/独立归一化的慢路径 |
| local SwiGLU FFN | 197.9728 -> 180.2859 us，约 1.0981x，未过预设 1.10x；细分块/单缓冲也已拒绝 | 新机制，不四舍五入改门槛；稀疏解析正确性不等于完整模型质量 |
| SwiGLU -> MMAR 边界消除 | 已记录的可见 gap 约 1.30–1.31 us/层，不足以单独支持 1.15x chain gate | 证明 MMAR 本体的额外可回收时间；不是只换 Python 包装 |
| online HCCL、buffer、NZ、ShortGPT、MMAR decomposition | T13 的关闭路线清单已有负结果 | 回读各自哈希/失败阶段，不把不同实现的失败合并成整个算法不可能 |

bounded-MMAR 的历史记录可用
`git show c71de549b3ee32030799d66198786d8619aba3c1` 查阅；其原判决包含历史
门槛，必须保留，不改写为今天的新实验。
[E-X3, E-SWIGLU, E-T13-PLAN, E-T13-BUDGET]

### 明确收回或降级的历史表述

- “TTFT 长尾全部由 JIT 导致”：改为有编译和慢请求同窗出现的相关性证据，
  尚缺逐请求完整归因。`.npubin` 总数不变也不单独证明整个编译链零开销。
- “GDN terminal RMS/gate 仅 5 us/token，所以无价值”：原过滤器没有识别
  完整 fused gated norm；不可据此关闭整个 Candidate A。
- “T14 已冻结，可替代旧基线”：不成立；只能作为具体 control 工件保留。
- “spawn ENOENT 说明没有到主机/整个 executor 坏了”：过度归因。
  本次直接目标已证明 `/bin/sh`、`/usr/bin/python3` 加绝对 cwd 可执行，
  旧故障根因仍未知，不能声称修复了某个已确诊的 NPU/网关故障。
- “没有代码改动”：性能工作区实际有 11 个 dirty tracked 文件；本次已备份，
  未对其作者、正确性或部署状态作未验证认定。
- “容器结束就是测试完成”：T15 control 正常退出且当前不在运行列表中，
  但被检查的工件目录没有完成的 benchmark JSON；实验仍不完整。

## 4. Current Action — 保护已有工作

性能分支 HEAD 为 `0ff5757798d1eb7e1c2fd15bf23e224fa97e7478`；
`0dbfc28` 和 `0ff5757` 保存 dense-tail 机会分析及边界路线关闭。
这不是全部运行时代码身份：T14/T15 都记录同一个 HEAD，但 patch SHA256
不同。接管时必须同时核对 dirty diff、launcher、plugin、镜像及挂载身份。

本次私有恢复备份：

```text
/cache/austinov/handoffs/qwen35-mtp-off-20260909T214308Z/
  preservation.json
  delivery-uncommitted.patch
  untracked/agentic/
  untracked/optimization-analysis/
  audited-sources.json
  baseline-p95-audit.json
  npu-smi.txt
  docker-ps.txt
  ports.txt
  git-worktrees.txt
```

备份权限限制在目标主机，未跟踪目录内共 6 个文件；没有把它们加入本经验
分支，原工作区也没有被 reset、clean、stash 或覆盖。清单和补丁哈希见
`evidence.json`。这是同机恢复备份，不等于异地备份。

本轮机器点查：NPU0-3 无设备进程，10010/8210/8220 无监听；唯一运行
容器 `drrqr_qwen38_energy_preflight_20260908` 声明物理 NPU4-7，必须保护。
NPU4 曾观察到 Python 进程。空闲率和 HBM 基础占用不构成资源授权。
用户已允许本任务使用 NPU 服务，但每次仍要获得实际独占租约，不能停止邻居。

## 5. Next Actions

1. 先用新解析的 `chicaihong01/ma` 进入正确主机，核对 Git、备份和当前卡占用。
   更新实际性能分支 HANDOFF 前先核实其所有权；本包不覆盖那个 dirty 工作区。
2. T15 先登记独立 synthetic/development shape 策略，冻结后不看最终测试集
   精确长度来补覆盖。分别检验未见内容、未见长度/分块组合及混合并发。
3. 分离 time-to-ready、首次未见 shape 和稳态指标。隔离编译缓存与 prefix KV
   cache；warmup 和测量使用不同 salt，并核实实际命中和编译事件。
4. 审计真实 specialization key。旧源码观察显示 T/B 已有 do_not_specialize；
   task_num/bh_step 等只是待验证线索，不应盲目去特化或移除安全检查。
5. 先做正确性及 c1/c16 screen，再按预声明 gate 决定是否扩到全矩阵；
   缺 c1/c5/c8/c16 各三轮和完整质量审查时，不标记最终 accepted。
6. TPOT 独立继续定位生命周期和真实关键路径，保留所有负结果；不要把
   重叠 AICPU/AI Core 时长相加，或把微基准百分比直接当端到端收益。

## 6. Validation Commands

在本经验交接工作区执行，不占用 NPU：

```sh
./scripts/validate-mst.sh
/usr/bin/python3 scripts/validate_qwen35_handoff.py
/usr/bin/python3 tests/test_qwen35_handoff.py
/usr/bin/python3 scripts/validate_qwen35_handoff.py --verify-artifacts
git diff --check
```

这些验证检查交接结构、证据文件哈希与错误结论防线，不代替模型性能测试。
最终验证/commit/push 状态以分支 `HANDOFF.md` 和 `integration-evidence.json`
为准；本材料不把本地 commit 自动视为已推送或已合并。

## 7. Do Not Do

不恢复 MTP；不把 source overlay、单轮、P50 或空答案当最终通过；不调低
门槛；不修改 HugeTLB 池；不关 TLS 校验；不对整个 dirty 工作区 git add；
不靠旧 PID/container ID 停服务；不无界重试同一个失败 collective。
凭据只传连接器 verify 字段，示例中仅称 AWMCP_VERIFY，绝不写入仓库。

## 8. Recovery / Resume Commands

连接器必须先 `topo tree/get` 解析当前 peer，再 `skill_get(host-development)`
和 `a_status` 证明直接目标。调用示例的语义是：
`command=/bin/sh`，`args=[-c,<命令>]`，`cwd=/` 或确实存在的绝对仓库路径；
不要把整段带空格的命令当可执行文件名，也不要复用历史 peer ID。

```sh
cd /opt/host/vnf/austinov/model-tuning-lab
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
docker ps --no-trunc
npu-smi info
ss -lntp
grep -E '^(MemTotal|MemAvailable|Hugetlb):' /proc/meminfo
cd /opt/host/vnf/austinov/worktrees/qwen35-performance-delivery
git status --short --branch
git diff --stat
```

如遇 spawn 错误，保留精确错误和 cwd/可执行路径，使用文件读取检查必要
路径；不要推断 NPU 故障。operation_not_found 则转查私有工件、退出码、
进程和容器，不要直接重发昂贵作业。

本轮另有 Git 网络命令在非登录环境下超时；改用 `/bin/bash -lc`、明确
`cd`、`GIT_TERMINAL_PROMPT=0` 后，远端引用查询和普通 push 已成功。
没有关闭 TLS 校验或改动凭据。具体环境差异未完成归因，不把这一可用
调用方式包装成已定位的网络根因。命令超时后先查 Git/远端状态，再决定
是否有必要继续，避免重复提交或强制推送。

如需恢复未提交工作，先核对 `preservation.json` 和补丁哈希，核实当前作者、
进程及 worktree budget，在指定 base 的干净恢复工作区做 `git apply --check`。
**不能把补丁直接重复应用到仍有这些改动的性能工作区。** 当前只做保存和
可接管准备，没有自动恢复或启动任何业务作业。
