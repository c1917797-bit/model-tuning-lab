# HYPIC Qwen3.6-27B TP4 · Paper-to-Ascend 穿刺进度报告

> 状态：progress，非终版；截至 2026-10-06 21:45 UTC。
> 实验 ID：hypic-qwen36-e2e-2048-20261006。
> 当前证据来自本次实验；历史 HYPIC 标签 paper-result/hypic-qwen36-tp4-adopted 仅作历史参考，不进入本次结果列。
> 本轮只支持“方向及部分组件机制复现”的讨论，不支持“论文完整性能复现”或“可采用”结论。

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

质量协议与性能协议分离：LongBench-v2 127 条、GSM8K 1,319 条；每组每数据集 3 轮、并发 32、最大输出 2,048、自然 EOS、温度 0、seed 0、关闭 thinking。LongBench 原始数据 SHA256 cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a；GSM8K SHA256 3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14；评测器 SHA256 9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0。质量契约 SHA256 fa7915cdab4c836869f867184de563dd407c237979a48b691098518aacc9373d，位于 quality-context-41984/quality-context-contract.json。单个 LongBench 长提示为 39,642 token，连同 2,048 上限共需 41,690；因此两组质量服务都使用 41,984 上下文，并与 40,960 性能服务分开比较。当前唯一运行控制器为 AWMCP exec-000000000000064a；严禁再启动第二个服务。

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

无缓存 LongBench-v2 基线 run1、run2、run3 分别为 71/127（55.9055%）、77/127（60.6299%）、74/127（58.2677%）；三轮均 127/127 成功，独立核验了完整索引、原始文件与逐行响应哈希、2,048 输出上限、41,984 上下文上限及汇总算术。三轮 JSONL SHA256 依次为 670832c4e063724bd08e1aab282a819a66dbfaa6f0e094b60f8d6850fa3183fa、e7ded491a9b7f995ca035c9c0d10011002eaf48e4a9aa84bed963b5160650031、a0391b097ca8734042d7855b629191fde68e5fe377b14c0056622a4fc57b4982。LongBench 三轮准确率均值 58.2677%，样本标准差 2.3622 个百分点；这是单组描述，不是配对质量结论。GSM8K 基线 run1 正在运行；完整六轮基线注册表尚未冻结，G2 配对质量与安全门禁均未判定。

原生设备 Profiling 在四个 TP rank 都捕获了 Prefill 与 Decode 原始数据；Prefill 完整导出，Decode 离线分析只覆盖 rank 0/1/3，rank 2 原始数据保存但离线导出不完整。匹配 rank 上 Prefill AllReduce 数量从 774 降到 387，但 Decode 增量数量两组均为 16,383。profile-diagnostic.json 是诊断证据，不是性能门禁；CANN 多流任务耗时不可相加推断可节约的端到端墙钟时间。

## 当前 Decision 与失败分类

| 门禁 | 当前状态 | 可允许的结论 |
|---|---|---|
| 环境和真实权重可运行 | 已验证 | 目标模型在 NPU0–3 TP4 可服务，Canary 匹配 |
| 论文组件激活 | 部分验证 | Prefill 机制与 TTFT 方向成立，C3 完整机制未证实 |
| 论文端到端性能收益 | rejected | 四项门禁仅一项通过 |
| 追加优化迭代 | rejected | 已完成一次真实测量迭代，但未达到采纳门槛 |
| 2048 配对质量 | pending | 不允许称无精度损失 |
| 全部证据独立审计 | pending | 不能声称实验闭环完成 |
| 最终资源释放与交接 | pending | 当前质量基线服务仍占 NPU0–3 |

已完成的回滚演练见 rollback-evidence.json：禁用请求通过、treatment marker 缺席、当时的两个自有容器与端口/NPU 均已释放。这不等于当前质量服务已释放。候选 G3 也已在质量开始前单独释放。当前真实质量基线容器中的四个 TP worker PID 与物理 NPU0–3 的 PID 对应；不得触碰 NPU4–7 的其他进程。

## 证据索引与恢复边界

- 冻结身份和协议：baseline-contract.json、baseline-registry.json、quality-context-41984/quality-context-contract.json。
- 当前性能判定：performance-gate.json；六份原始轮次文件 SHA256 见该文件的 run_sha256 字段。
- 原始 Canary 与回滚：canary-gate.json、rollback-evidence.json。
- 优化尝试：optimization-iteration.json；所有 G3 原始哈希记录在其 raw_sha256 字段。
- 设备诊断：profiles/profile-diagnostic.json；缺失的 rank 2 Decode 离线导出必须显式保留为限制。
- 当前精度：quality-context-41984/controller-status.json 与 quality/no-cache 下各轮 JSONL、summary、log。只在整轮完成后核验；不得从运行中样本推导终态。
- 实时恢复入口：先查 AWMCP exec-000000000000064a 是否仍在运行。活着时只轮询，绝不重复启动。若终止，则核验精确容器、NPU0–3 与端口 8223，再根据保留的 JSONL、registry 和 HANDOFF.md 分类或恢复。控制器自身的安全截止是 2026-10-07 11:24:37 UTC；实验目标截止是 11:39:37 UTC。

最终报告须在控制器终止并完成独立审计后重新核对所有结果、补齐质量配对表和终态分类，并证明当前质量容器及 NPU0–3 已释放。此进度报告不可作为采用或论文完整复现证明。
