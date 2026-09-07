# DRRQR 论文到昇腾实验室落地：Qwen3.6-27B 穿刺报告

## 受众、目标与结论边界

- 受众：模型推理优化维护者、算法研究人员、昇腾部署工程师。
- 目标：解释《The Key to State Reduction in Linear Attention: A Rank-based Perspective》中 DRRQR/Strong RRQR 状态降维方法的核心原理，并交付 Qwen3.6-27B 在 4×Ascend 910B4 上的完整实验结论、证据边界和恢复命令。
- 已完成结论：Dk64（50%）与 Dk96（25%）均结构正确、可在昇腾执行，但都未通过冻结的 GSM8K 基线波动门限，因此对当前 workload 的 adoption decision 是 rejected。
- 待完成结论：Dk112（12.5%）checkpoint 与结构审计已通过，但尚无 NPU smoke、quality、performance 或 profile 数据，decision 为 pending。

## 方法核心与原理

线性注意力/Gated DeltaNet 维护递归状态矩阵，状态的一条轴由 key 维度 d_k 决定。训练后 Q/K 表征往往存在有效低秩和冗余通道。Strong rank-revealing QR 在校准激活上选择更能保持列空间/有效秩的一组通道；随后对每个 GDN head 的 Q 和 K 同步删除其余通道，把 head_k_dim 从 128 缩小到 64、96 或 112。同步、结构化、轴对齐的剪枝保持 dense kernel 形态，同时缩小投影权重与 recurrent state，理论上减少状态存储、带宽和相关计算。它不同于非结构化稀疏，也不同于 HYPIC 的缓存复用。

公式化表达：原状态 S_t 属于 R^(d_v × d_k)。选择矩阵 P 保留 r 个代表性 Q/K 通道后，Q'_t=Q_t P，K'_t=K_t P，状态变为 S'_t 属于 R^(d_v × r)。目标是在 r<d_k 时尽量保持校准激活张成的子空间。RRQR 解决“保留哪些通道”，结构化切片解决“如何让部署栈真正变小”。

收益成立需要四条链同时成立：低秩假设成立；被删通道对任务精度不关键；运行时算子真的消费缩小后的 d_k；节省没有被全模型其他层、同步、调度和通信开销淹没。任何一条不成立，都可能出现结构成功但端到端收益弱或精度退化。

## 架构和实现适配

- 模型：Qwen3.6-27B。
- 结构：64 层，其中 48 个 GDN/线性注意力层、16 个全注意力层，模式为 3 个线性注意力层后接 1 个全注意力层。
- 原始 head_k_dim：128。
- 处理范围：48 个 GDN 层的 Q/K 对应张量，96 个 tensor；全注意力层保持不变。
- 官方代码：camail-official/LinearAttentionPruning，commit 919d8667d951c385e08510bc1267c2e7049a4f56。
- 官方 rrqr.py SHA256：fa4bacf516011ba1c88f2e0e92957bbe4513cc1bb6634912fdb0d06ba7821a62。
- 校准适配：LongBench-v2 源顺序前 16 条，每条冻结 2048 个目标模型 token；不是论文的 FineWeb-Edu，且与评测家族存在重叠风险，因此不能声称 paper-exact reproduction。

## 实验环境与隔离

- 设备：4×Ascend 910B4，host NPU4-7，容器内映射 0-3，TP4。
- CPU：0-95。
- 正式 Dk64/Dk96 服务端口：8225。
- 性能 workload：32768 input、1024 output、40 requests、concurrency 16、2 warmups、每 arm 3 runs。
- 质量 workload：LongBench-v2 127 条、GSM8K 1319 条；seed 0、temperature 0、thinking off、3 runs。
- CEval：按用户决定排除。NIAH+：缺权威文件，未用替代数据。
- 资源规则：不得把 host NPU4-7 误写为容器可见 4-7；不得触碰保护的 NPU0-3；使用前必须同会话重验进程、容器、端口和控制器。

## 处理结构证据

- Capture：48 layers × 4 ranks × 16 samples = 3072 个 .pt 文件。
- Dk64 manifest SHA256：2eaa9a14fffe3dc0cd37906e08bee857be7c9ce2ed761f693a99a0ef02d90c0d。
- Dk96 manifest SHA256：a8f8f162f15fb6e4717ed509927d93c549a2ef01eca4c88e45e75cdf900b16fc。
- 两个 checkpoint 均修改 48 层、96 tensors、6 个 shard；未改 shard 使用 hardlink。
- Dk96 real-weight smoke 返回精确 ASCEND_DRRQR_OK，并记录 head_k_dim=96。

## 性能结果

Baseline 三次均值：TTFT 38456.890090 ms；TPOT 73.628823 ms；output throughput 125.819134 tok/s；duration 325.902211 s。

Dk64 三次均值：TTFT 37411.854905 ms（-2.717%）；TPOT 71.699479 ms（-2.620%）；throughput 129.230504 tok/s（+2.711%）；duration 317.429595 s（-2.600%）。全部三次区间与 baseline 重叠，不能声称稳定收益。

Dk96 三次均值：TTFT 38302.675575 ms（-0.401%）；TPOT 73.302878 ms（-0.443%）；throughput 126.298149 tok/s（+0.381%）；duration 324.836207 s（-0.327%）。全部三次区间与 baseline 重叠，不能声称稳定收益。

## 精度结果和门限

门限：对每个数据集，baseline mean - treatment mean 不能超过 baseline 三次 accuracy range。

- Baseline LongBench-v2：45.669291%，range 3.937008 pp。
- Dk64 LongBench-v2：48.293963%，+2.624672 pp，pass。
- Dk96 LongBench-v2：49.343832%，+3.674541 pp，pass。
- Baseline GSM8K：96.310336%，range 0.151630 pp。
- Dk64 GSM8K：96.108163%，-0.202173 pp，fail。
- Dk96 GSM8K：96.007076%，-0.303260 pp，fail。

因此 Dk64、Dk96 均被拒绝。Profiling 按预注册规则跳过，因为 correctness/quality gate 已失败；没有 profiler 不是“算子没有收益”的证据。

## Dk112 改进回合

- 实验 ID：state-reduction-qwen36-dk112-quality-first-20260907。
- 剪枝比例：128→112，减少 16/128=12.5%，保持对齐。
- Checkpoint：/cache/cch/Qwen3.6-27B-gdn-drrqr-dk112。
- 构建 operation：exec-0000000000000cb7，exit 0，190904 ms。
- Manifest SHA256：033eac4d29e12e9f219b213f12a15ebd3217e183f353c43c2200bb47f149243a。
- 结构审计 SHA256：0d9efd2418d9b34e3ef16b78949c366d79992b587bc53cc6110b7fd058e6a12c。
- 结构审计：Dk112、48 layers、96 tensors、6 rewritten shards、9 unchanged hardlinked shards。
- 当前状态：只有 checkpoint/structure evidence；不允许声称精度保持或性能提升。
- 下一门：获得明确 NPU4-7 授权后，先 smoke，再 fresh baseline quality 与 Dk112 quality；两数据集都 pass 才运行 performance，最后视需要 profile。

## 与同事 HYPIC 成功案例的对比

同事 HYPIC v0.8.5 案例为 Qwen3.5-27B、2×Ascend 910C、TP2，机制是位置无关缓存/复用；报告的 TTFT -46.6%、TPOT -18.4%、throughput +38.5%、duration -27.8%。本环境 HYPIC 历史标尺复现也得到相近方向和幅度，但这不能作为 DRRQR 的预期值。DRRQR 缩的是 GDN state key dimension，端到端理论上只影响部分层和部分计算；当前 Dk64/Dk96 测到的全模型变化仅约 0.4%–2.7%，且区间重叠。二者方法、模型、硬件、卡数、TP 和 denominator 都不同，绝不能合并比较绝对值。

## 成功、失败和已知陷阱

成功：官方代码/哈希固定；采集数量审计；结构改动边界审计；真实权重 Ascend smoke；每 arm 三次性能；每数据集三次质量；逐条 JSONL、hash/count/index 独立审计；负结果保留；资源释放审计。

失败/陷阱：把校准适配冒充论文同分布；只看 mean 不看区间重叠；用 LongBench 校准后再把 LongBench 提升当作无偏泛化证据；质量失败后仍以性能均值宣称 adopt；把 host device ID 与 container-visible ID 混淆；启动脚本路径多写 scripts/ 导致 pre-runtime failure；把 HYPIC 大收益直接投射到 DRRQR；把“pass 观测门限”写成“无损证明”。

## 最终 decision

- Dk64：rejected for current frozen workload。
- Dk96：rejected for current frozen workload。
- Dk112：pending，尚未进入 NPU 运行门。
- 方法层：mechanism feasible on Qwen3.6/Ascend stack。
- 论文层：未完成 paper-exact reproduction。
- 收益层：未建立稳定 serving benefit。
- 采用层：当前不得采用 Dk64/Dk96；Dk112 要等新实验闭环。

## 精确恢复命令

Dk112 首个运行命令（仅在明确授权 NPU4-7 后）：

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/state_reduction_dk112_runner.py --arm drrqr-dk112 --phase smoke
```

Dk112 只读重审：

```bash
sha256sum /cache/cch/Qwen3.6-27B-gdn-drrqr-dk112/drrqr_manifest.json
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/cache/cch/Qwen3.6-27B-gdn-drrqr-dk112/drrqr_manifest.json')
x = json.loads(p.read_text())
assert x['target_head_k_dim'] == 112
assert x['changed_layers'] == 48
assert x['changed_tensor_count'] == 96
assert len(x['changed_shards']) == 6
print('Dk112 manifest structural gate: PASS')
PY
```

## 证据入口

- HANDOFF.md
- MAINTAINER_RETROSPECTIVE.md
- evidence-state-reduction-qwen36-formal-npu4-7-tp4.json
- decision-state-reduction-qwen36-formal-npu4-7-tp4.json
- experiment-state-reduction-qwen36-dk112-quality-first-20260907.json
- evidence-state-reduction-qwen36-dk112-quality-first-20260907.json
- decision-state-reduction-qwen36-dk112-quality-first-20260907.json
