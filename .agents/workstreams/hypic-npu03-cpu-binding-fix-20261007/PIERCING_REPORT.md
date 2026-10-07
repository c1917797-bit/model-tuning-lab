# HYPIC C1/C2 NPU0–3 算法特性穿刺 · 进行中报告（2026-10-07 17:00 UTC 更新）

报告状态：**progress**。当前证据支持同环境 HYPIC 热复用路径的性能收益，尚不支持配对质量通过、生产采用或整篇论文复现。本文只列本次主机实测；同事历史 TP2 和论文 SGLang 数字不与本次 TP4 绝对值合并。CPU-binding 原因与修复的独立阶段结果见 `REPORT.md`。

质量尝试 1 在 16:52:55 UTC 因外部 NPU3 占用使隔离门槛失败；尽管六个 no-cache 单元均完成并通过逐行审计，**它们不是正式质量对照分母**，HYPIC 质量臂没有启动。原始数据保留于 `quality-context-41984`；新一轮完整 12 单元配对将写入 `quality-context-41984-clean2`，不混合两个尝试。归因、进程和清理证据见 `QUALITY_RESOURCE_CONFLICT.md`。

## Step 0. 环境与算法边界

- 目标：`chicaihong01` 物理 NPU0–3（910B4），TP4，HCCL AIV，FULL_DECODE_ONLY 图模式；容器 cpuset `112-191`，服务端口 `8223`。NPU4–7、其他容器和脏的主检出不在操作范围。每次服务启动和释放均由精确容器身份与物理 worker/端口检查约束。
- 模型目录 `/cache/efim/Qwen3.6-27B`，BF16；配置实际为 `Qwen3_5ForConditionalGeneration`，64 个文本层中 48 个 linear attention、16 个 full attention。本次只检验文本推理，不检验多模态或 MTP。模型索引 SHA256 `a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`。
- 官方服务镜像 `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`；HYPIC v0.8.5 衍生实现本地 Git HEAD `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`。作者原版 SGLang 的精确 Git commit 尚未建立，不能把该衍生实现叫作原版完整复现。
- 论文 C1（线性注意力段状态复用）和 C2（全注意力 KV 重定位/边界修复）的单实例文本路径与该模型匹配；C3（多副本冷段分布式调度）在本衍生实现和单 TP4 实例中缺失。正反两种源码范围审计与限制见 `PAPER_ARCHITECTURE_FIT.md`。

## Step 1–3. 配对部署与测试

| 组 | 服务变量 | 共同条件 | 要回答的问题 |
| --- | --- | --- | --- |
| G1 no-cache | `VLLM_ASCEND_HYPIC_ENABLE=0` | 同一镜像、模型、源码、TP4、NPU0–3、cpuset、容量、评测器，且两组均设 `enable_cpu_binding=false` | 修复后同槽位分母 |
| G2 HYPIC-only | `VLLM_ASCEND_HYPIC_ENABLE=1` | 同上；仅证据输出路径随组变化 | C1/C2 热复用贡献及质量风险 |

正式性能测试由 `binding_off_service.py` 的 `screen`、`repeat2`、`repeat3` 三个独立服务生命周期执行，每组各三轮；固定 32768 输入、16384 共享前缀、1024 固定输出、c16、40 请求、2 次预热、忽略 EOS。全部六轮 40/40、0 失败、精确 1024 输出。`audit_binding_off_performance.py` 从逐请求原始行重算 weighted TPOT、nearest-rank P95、TTFT、吞吐和哈希，并核对跨组命令、镜像、源码、设备、清理凭据。性能比较不混入先前 CPU-binding-on 组或 NPU4–7 历史组。

质量测试采用独立的 natural-EOS 协议：41984 上下文、2048 最大输出、c32、seed 0、temperature 0、thinking off、每组每数据集三轮。LongBench-v2 127 条（数据 SHA256 `cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a`）；GSM8K 1319 条（`3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`）；评测器 SHA256 `9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0`。质量尝试 1 的已执行入口是 `python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/binding_off_campaign.py --run`，AWMCP 作业 `exec-0000000000000c6d` 已以 exit 1 结束。尝试 2 使用同一脚本及 `HYPIC_QUALITY_ATTEMPT=clean2` 环境变量，增加物理 NPU0–3 外来 PID 监测；任何冲突或探测错误均使尝试无效。测试契约和恢复前提见 `QUALITY_PLAN.md` 与 `HANDOFF.md`。

## 本次实测结果

### 性能（每轮 40 个有效请求；三轮中位数为汇总）

| 轮次 | G1 weighted TPOT ms/token | G2 weighted TPOT ms/token | G1 TTFT P95 ms | G2 TTFT P95 ms |
| --- | ---: | ---: | ---: | ---: |
| 1 | 77.5641 | 60.2596 | 80775.49 | 43279.89 |
| 2 | 77.8308 | 60.1658 | 81806.77 | 43209.90 |
| 3 | 77.0052 | 60.2237 | 78932.28 | 43176.41 |
| 中位数 | 77.5641 | 60.2237 | 80775.49 | 43209.90 |

G2 相对 G1 的 weighted TPOT 中位数低 `17.3404 ms/token`，即下降 `22.3562%`；TTFT P95 中位数低 `37.5656 s`；输出吞吐中位数从 `117.2930` 升至 `166.8247 token/s`，比值 `1.4223×`。这些数字和公式来自 `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-independent-audit.json`，SHA256 `de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1`。这是预登记性能门槛通过，不是质量或整篇论文门槛通过。

### 质量尝试 1（G1 六单元原始结果；隔离失败，不进入正式对照）

| 数据集/轮次 | 有效/应有 | 正确 | 准确率 | 达 2048 上限 |
| --- | ---: | ---: | ---: | ---: |
| LongBench-v2 1 | 127/127 | 76 | 59.8425% | 15 |
| GSM8K 1 | 1319/1319 | 1276 | 96.7400% | 10 |
| LongBench-v2 2 | 127/127 | 75 | 59.0551% | 15 |
| GSM8K 2 | 1319/1319 | 1275 | 96.6641% | 11 |
| LongBench-v2 3 | 127/127 | 73 | 57.4803% | 18 |
| GSM8K 3 | 1319/1319 | 1277 | 96.8158% | 9 |

上述六单元逐行重算了索引、样本/答案、响应哈希、原始评测器计分、token 用量及摘要算术；同数据集重复间逐样本 prompt-token 数一致。各 JSONL、摘要、receipt 的路径与 SHA256 在 `HANDOFF.md`，原始数据在 `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984/quality/no-cache/`，不入 Git。最后一轮的尾部可能与外部 NPU3 算子任务重叠，且清理时整条卡道不空闲；不能把这六轮当作隔离合格的正式对照。G2 质量尚未开始，因此没有配对精度差、质量通过或退化结论。

### 激活、归因与未完成门槛

G2 的三轮正式性能日志满足插件构建、scheduler 与 worker 热路径激活，独立审计要求每轮 `worker_hot_path >= 4` 且无缺失事件；相同修复后的 G1/G2 只有 HYPIC 开关作为算法变量。CPU-binding-off 是两组共同修复，不被记为 HYPIC 收益。质量臂还必须在它自己的服务中重新证明插件构建、四个 worker 热路径、scheduler 激活和精确释放；性能臂证据不能替代质量臂证据。现有 Decode profile 的 rank-2 离线导出限制仍需单独标注，不能将性能差额全归因为论文所有组件。

| 决策门槛 | 当前状态 | 允许的结论 |
| --- | --- | --- |
| 可运行性与性能六轮 | 通过 | 修复后 NPU0–3 同槽位 C1/C2 热复用性能收益成立 |
| 性能热路径激活 | 通过（仅正式性能臂） | 不是仅靠容器名推断激活 |
| 12 单元配对质量 | 尝试 1 隔离失败；clean2 需重新完成 12/12 | 不宣称精度无损/回归 |
| 质量服务激活与两组释放 | 未完成 | 不宣称最终资源门槛通过 |
| 论文 C3 与原版系统广度 | 未实现/未测试 | 不宣称整篇 HYPIC 复现 |
| 生产采用/泛化 | 未审定 | 不宣称发布就绪 |

## 失败经验与证据索引

先前 one-wave HYPIC smoke 的外层进程曾因把正式 40 请求才需满足的 `native_decode_scheduler_passthrough` 事件门槛错误套到四请求窗口而退出 1；保留原失败记录，语义 canary/核心事件另行审计，正式三轮继续严格要求完整热路径。另一项已确认问题是 NPU0–3 的共享 Decode CPU-binding floor；用官方支持的禁绑开关同时修复两组后再测 HYPIC 差值，而不是把 CPU 影响归给算法。P95 审计必须按基准程序的 nearest-rank 定义复算。这些已沉淀到对应现有 Skill 与 registry，新的外部 NPU3 冲突证明仅启动前验槽不足；尝试 2 添加运行期 PID 守卫并重新做完整配对，不能挑选尝试 1 已通过算术校验的分数来规避隔离失败。详细证据在实验 YAML、`QUALITY_RESOURCE_CONFLICT.md` 和 `HANDOFF.md`。

证据根：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007`；主账本：`.agents/experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml`；逐项 Skill 状态：`SKILL_VERIFICATION.md`。下一步在 0–3 卡与端口预检空闲后启动 clean2 完整配对，审计其全部 12 单元、双组激活与释放，再把本报告升级为 final 或有证据的 negative/inconclusive。不得把尝试 1 的基线与 clean2 治疗臂混算。
