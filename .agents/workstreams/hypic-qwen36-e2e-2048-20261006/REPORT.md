# HYPIC Qwen3.6-27B TP4 · Paper-to-Ascend 穿刺终态报告

> 状态：rejected / fail-fast，终态；截至 2026-10-06 22:06 UTC。
> 实验 ID：hypic-qwen36-e2e-2048-20261006。
> 当前证据来自本次实验；历史 HYPIC 标签 paper-result/hypic-qwen36-tp4-adopted 仅作历史参考，不进入本次结果列。
> 本轮只支持“方向及部分组件机制复现”的讨论，不支持“论文完整性能复现”或“可采用”结论。

## 追溯归因修正（2026-10-07；不改冻结门禁）

本轮确实在物理 NPU0–3 测了无缓存性能基线三轮，也测了同卡同协议
HYPIC 三轮；不存在“漏测 0–3 性能基线”。但原终态报告把服务百分比
门禁的拒绝放在最显眼的位置，没有量化技术本身的同卡绝对效应，
容易被误读为 HYPIC 的作用没有复现。以下从六轮原始 JSON 重新计算，
是**事后诊断**，不追改预注册 performance-gate.json 或 2048 精度状态。

| 三轮均值；同卡无缓存减 HYPIC | 2026-09-06 成功：NPU4–7 | 本轮：NPU0–3 |
|---|---:|---:|
| TTFT mean 绝对节省 | 17,609.82 ms | 17,830.56 ms |
| TPOT weighted 绝对节省 | 14.15 ms/token | 13.69 ms/token |
| 40 请求批耗时绝对节省 | 88.17 s | 91.02 s |
| 无缓存 TPOT weighted | 74.51 ms/token | 413.10 ms/token |
| TPOT weighted 相对改善 | 18.99% | 3.31% |
| 无缓存输出吞吐 | 123.77 tok/s | 29.48 tok/s |
| HYPIC 输出吞吐 | 168.40 tok/s | 31.54 tok/s |

9 月 5 日另一次 NPU0–3 的同形状无缓存三轮均值为 TPOT weighted
411.91 ms/token、输出吞吐 29.54 tok/s；和本轮的 413.10/29.48
高度接近。该早期服务的 max-num-seqs 为 32，本轮为 16，故它只用于
诊断稳定的慢底座，不并入任一正式 A/B 分母。两次正式 A/B 的镜像 digest、
HYPIC 源码 commit、压测脚本 SHA256、模型路径和性能流量形状一致；
物理卡组、CPU 绑定和时间不同，不能直接池化原始性能。

技术归因应改述为：**在已测延迟和批耗时指标上，HYPIC 的同卡绝对
效应在两组卡上近似重现；本轮没有通过预注册的相对服务门槛。**
公共慢项使百分比缩小，并因吞吐是固定 40,960 输出 token 除以批耗时，
使吞吐百分比也缩小。这不是“未测基线”，也不是 HYPIC 效应消失。
尚未证实公共慢项的底层来源；不能仅凭此表指认 HCCL、NUMA 或坏卡。
三轮样本不足以事后证明统计等效，未来若以“绝对效应等效”为正式
成功标准，必须预注册容差与重复次数。2048-token 配对质量仍不完整，
所以完整论文采纳结论仍为否。独立负向审计中的
`paper_algorithm_accepted=false` 仅指**完整采纳未通过**，不等于
“技术作用未发生”。

可复核命令（只读）：
`python3 .agents/workstreams/hypic-qwen36-e2e-2048-20261006/analyze_cross_lane_effect.py --successful-root /cache/cch/hypic-qwen36-formal-npu4-7-tp4-budget40960-20260906 --current-root /cache/cch/hypic-qwen36-e2e-2048-20261006 --earlier-baseline-root /cache/cch/hypic-qwen36-historical-reproduction-20260905`。

## Step 0. 环境准备

- 目标主机：chicaihong01，物理 Ascend 910B4 NPU 0–3，TP4；NPU 4–7 为受保护邻居资源。
- 模型权重：/cache/efim/Qwen3.6-27B；模型索引 SHA256 a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b。
- 镜像 digest：sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1。
- HYPIC 实现：v0.8.5，源码 commit 3ad0967589304cd8fc4e7cff02f48ecc6125c89f。
- 工作树：/cache/cch/model-tuning-lab-hypic-e2e-20261006，分支 work/hypic-qwen36-e2e-2048-20261006；原始大型证据根目录：/cache/cch/hypic-qwen36-e2e-2048-20261006。
- 服务端口 8223、CPU 112–191、HCCL 端口 27000–27100。真实权重 Canary 两组响应 SHA256 均为 0fa5e875f58b181ddb6ac6890d15b5e4b6c1b29c58f6d8034e981b988f8d0498；详见 canary-gate.json。
- 基线环境与原始数据指纹见证据根目录的 baseline-contract.json、baseline-registry.json 和 environment-and-container-snapshot.txt；当前质量测试使用另行冻结的 41,984 上下文身份，绝不冒充原 40,960 上下文性能基线。

## Step 1–3. 分组、部署与评测

| 组 | 问题 | 相对于无缓存基线的声明差异 |
|---|---|---|
| G1 no-cache | 不启用原生 prefix cache 或 HYPIC 的服务基线 | 无 |
| G2 hypic-only | 论文方法在本次端到端服务中的作用 | VLLM_ASCEND_HYPIC_ENABLE |
| G3 candidate | 独立的证据驱动优化尝试，不归因于论文原法 | 在 G2 上另启用 VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE=1 |

原始性能协议：32,768 输入 token，16,384 共享前缀，固定 1,024 输出 token，40 请求、并发 16、每组 2 个预热请求、3 轮；ignore_eos=true。每一轮均为 40/40 成功且固定输出长度得到原始行校验。规范入口和实际环境变量在本工作流 run_hypic_e2e_2048.sh；相同配置服务的真实容器记录与命令在证据根目录的环境快照和各组 service-start/service-stop 文件。

质量协议与性能协议分离：LongBench-v2 127 条、GSM8K 1,319 条；计划每组每数据集 3 轮、并发 32、最大输出 2,048、自然 EOS、温度 0、seed 0、关闭 thinking。LongBench 原始数据 SHA256 cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a；GSM8K SHA256 3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14；评测器 SHA256 9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0。质量契约 SHA256 fa7915cdab4c836869f867184de563dd407c237979a48b691098518aacc9373d，位于 quality-context-41984/quality-context-contract.json。单个 LongBench 长提示为 39,642 token，连同 2,048 上限共需 41,690；因此质量服务采用独立的 41,984 上下文身份，绝不冒充 40,960 性能分母。唯一控制器 AWMCP exec-000000000000064a 已于 22:00 UTC 以退出码 2 结束；不得重复启动或把部分质量数据称为配对结论。

## 实测性能：三轮原始值与冻结门禁

以下每行依次为 TTFT P95 ms / TPOT P95 ms / 输出吞吐 tok/s / 批耗时 s。原始请求、预热、配置与哈希在 no-cache/performance.run1-3.json 和 hypic-only/performance.run1-3.json；门禁在 performance-gate.json。每组各 120/120 测量请求成功。

| 组/轮 | TTFT P95 | TPOT P95 | 吞吐 | 时长 |
|---|---:|---:|---:|---:|
| no-cache 1 | 92633.55 | 457.29 | 28.94 | 1415.47 |
| no-cache 2 | 81137.27 | 447.08 | 29.74 | 1377.15 |
| no-cache 3 | 80874.35 | 446.63 | 29.75 | 1376.99 |
| hypic-only 1 | 51456.74 | 420.43 | 31.42 | 1303.60 |
| hypic-only 2 | 49153.90 | 420.70 | 31.59 | 1296.49 |
| hypic-only 3 | 49169.50 | 421.30 | 31.59 | 1296.45 |

三轮算术均值 ± 样本标准差（n=3，仅描述波动，不替代门禁中位数）：

| 指标 | no-cache | hypic-only |
|---|---:|---:|
| TTFT P95 ms | 84881.73 ± 6714.56 | 49926.71 ± 1325.06 |
| TPOT P95 ms | 450.33 ± 6.03 | 420.81 ± 0.44 |
| 输出吞吐 tok/s | 29.48 ± 0.47 | 31.54 ± 0.10 |
| 批耗时 s | 1389.87 ± 22.17 | 1298.85 ± 4.12 |

正式预注册门禁使用三轮中位数：TTFT P95 改善 39.40%，通过 30% 门槛；TPOT P95 改善 5.90%，未达 10%；吞吐改善 6.22%，未达 20%；时长改善 5.86%，未达 15%。因此 G2 作为完整服务候选被拒绝，不能以 TTFT 单项通过替代整体通过。独立 G3 候选对 G1 的 TTFT 改善 43.05%，但 TPOT 6.42%、吞吐 6.78%、时长 6.35% 仍未达相同门槛；对 G2 吞吐只改善 0.53%。G3 的三轮 40/40 请求、Canary、回收证据与哈希见 optimization-iteration.json；其终态为 rejected，原 G2 门禁不变。

## 精度与机制证据边界

无缓存 LongBench-v2 基线 run1、run2、run3 分别为 71/127（55.9055%）、77/127（60.6299%）、74/127（58.2677%）；三轮均 127/127 成功，独立核验了完整索引、原始文件与逐行响应哈希、2,048 输出上限、41,984 上下文上限及汇总算术。三轮 JSONL SHA256 依次为 670832c4e063724bd08e1aab282a819a66dbfaa6f0e094b60f8d6850fa3183fa、e7ded491a9b7f995ca035c9c0d10011002eaf48e4a9aa84bed963b5160650031、a0391b097ca8734042d7855b629191fde68e5fe377b14c0056622a4fc57b4982。LongBench 三轮准确率均值 58.2677%，样本标准差 2.3622 个百分点；这是单组描述，不是配对质量结论。

GSM8K 基线 run1 于 21:43:15 UTC 启动，到约 22:00 UTC 仅完成 80/1,319 条。服务持续约 35–43 token/s；按观测速率，完整单轮会明显超过预设 2 小时上限。由于论文性能门禁已失败，执行 fail-fast：只向该轮评测子进程发送 TERM，让控制器的失败处理与 `finally` 释放自有容器。80 条部分 JSONL 完整保留，SHA256 4732761d2a59a95fb10051cb7783fd5f393730bad0bc5d92019d3529edc5d215；独立审计检查唯一索引、逐响应哈希、成功状态、2,048 输出上限和 41,984 上下文上限均通过。部分正确数不作为准确率报告。完整六轮基线注册表未冻结，HYPIC 治疗组未运行，因而不能判定质量无损、回归或通过。

原生设备 Profiling 在四个 TP rank 都捕获了 Prefill 与 Decode 原始数据；Prefill 完整导出，Decode 离线分析只覆盖 rank 0/1/3，rank 2 原始数据保存但离线导出不完整。匹配 rank 上 Prefill AllReduce 数量从 774 降到 387，但 Decode 增量数量两组均为 16,383。profile-diagnostic.json 是诊断证据，不是性能门禁；CANN 多流任务耗时不可相加推断可节约的端到端墙钟时间。

## 当前 Decision 与失败分类

| 门禁 | 当前状态 | 可允许的结论 |
|---|---|---|
| 环境和真实权重可运行 | 已验证 | 目标模型在 NPU0–3 TP4 可服务，Canary 匹配 |
| 论文组件激活 | 部分验证 | Prefill 机制与 TTFT 方向成立，C3 完整机制未证实 |
| 论文端到端性能收益 | rejected | 四项门禁仅一项通过 |
| 追加优化迭代 | rejected | 已完成一次真实测量迭代，但未达到采纳门槛 |
| 2048 配对质量 | incomplete-fail-fast | 仅完成三轮 LongBench 基线和 80 条 GSM8K 部分行；不能称无精度损失或回归 |
| 独立负向证据审计 | passed | 六轮性能、三轮完整 LongBench、部分 GSM8K 和当前资源释放证据一致；这不等于算法通过 |
| 完整 18 单元配对/采纳审计 | not-evaluable | 缺完整基线与治疗组；正式闭环检查保持失败 |
| 最终资源释放与交接 | passed | 精确质量容器已移除，8223 无监听，NPU0–3 无进程，早于截止时间 |

已完成的回滚演练见 rollback-evidence.json：禁用请求通过、treatment marker 缺席、当时的两个自有容器与端口/NPU 均已释放。候选 G3 也已在质量开始前单独释放。本轮质量容器的 service-start/service-stop 收据与独立实时检查进一步证明其四个 TP worker 曾对应物理 NPU0–3，且现在精确容器被移除、端口及 NPU0–3 已释放；未触碰 NPU4–7。

## 证据索引与恢复边界

- 冻结身份和协议：baseline-contract.json、baseline-registry.json、quality-context-41984/quality-context-contract.json。
- 当前性能判定：performance-gate.json；六份原始轮次文件 SHA256 见该文件的 run_sha256 字段。
- 原始 Canary 与回滚：canary-gate.json、rollback-evidence.json。
- 优化尝试：optimization-iteration.json；所有 G3 原始哈希记录在其 raw_sha256 字段。
- 设备诊断：profiles/profile-diagnostic.json；缺失的 rank 2 Decode 离线导出必须显式保留为限制。
- 已完成与部分精度：quality-context-41984/controller-status.json、no-cache/service-start.json、no-cache/service-stop.json、quality/no-cache 下三轮 LongBench 的 JSONL/summary 和 GSM8K run1 的 80 条部分 JSONL。只对整轮 LongBench 计算描述值；不得从部分 GSM8K 推导准确率。
- 独立负向审计：fail-fast-independent-audit.json，SHA256 93fdb954f186cfd2ec3d892c0f445b57b8c2f045c033366e5f44b47c09261bf4，`evidence_integrity_ok=true` 且零错误；`paper_algorithm_accepted=false`、`quality_classification=incomplete-fail-fast`。正式 e2e-closure-audit.json 的 `ok=false`，缺项为 baseline_registry_quality、performance_gate_pass、independent_18_unit_audit_present、quality_context_audit_present。这些是诚实的负向闭环边界。
- 控制器与资源：AWMCP exec-000000000000064a 已终止，退出码 2；质量容器 ID eeb65fd29e054783ce8ba6f9165ea54d38a2575f170225ddf11b3e7584b9f12a 的 stop 收据时间为 2026-10-06 22:00:04 UTC。独立实时核对确认精确容器不存在、8223 无监听、NPU0–3 无进程，早于 2026-10-07 11:39:37 UTC 截止。

结论：本次端到端穿刺以 **论文性能门禁未通过** 收束。真实权重、可回滚交付、性能负向证据、一次测量优化迭代、部分 2048-token 质量基线、独立负向审计和资源回收均有证据；但完整 HYPIC 论文性能目标及配对质量安全未被证明。不可将本轮标为 adopted；未来若要完成完整配对质量，应另行规划足够时长并冻结新的匹配实验身份，不能复用本轮未完成基线充当通过证明。
