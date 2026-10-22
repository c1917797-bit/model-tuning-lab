# BOLE 首轮 native boundary 诊断后阶段 checkpoint

## 阶段结论与验收边界

ON 单臂、两次请求、每次固定输出 8 tokens 的 TP4 边界诊断已真实完成。独立 reader V2 实际退出 0，状态为 **PASS_READONLY_DIAGNOSTIC_INTEGRITY**：重验原 host/单臂证据、四 rank 各 148 个 boundary 文件（共 592 个），完整 7208 项输入前后不变。reader 自身未执行 NPU 操作；这是已完成模型诊断结果的只读完整性验收。

**独立算法数值、paired-state、model-ready、性能及任务精度均未准入，原因尚未确定。** 原 short ON/OFF pair 的完整集合断言 FAIL 保留，未被本次 ON 内两代比较替换或重新放行。当前仍无新的 ≥10% 整模型吞吐提升、正式 TTFT/TPOT 或最终 GSM8K/HumanEval/MMLU 精度结果。

## 首次差异及其含义

四 rank 的最早已观察哈希差异均在 `layer0_out_projection` 返回记录。准确区间为：**gated norm 返回观察 → 原 reshape/rearrange → out_proj 内部执行 → out_proj 返回观察**。两代 native0 qkv/b/a、core 输出及 gated norm 的完整 131-token producer 哈希相同；core/norm 保留末8 tokens 的原始值独立解码也相同。不能跳过中间未观察区间而把根因直接命名为 GEMM、HCCL、布局或生命周期问题。

out-projection 末8 tokens 每 rank 有 5874/40960 个 BF16 数值不同，全部有限；max_abs=0.0625，RMS=0.000438150835，L2_error/第一代L2_norm=0.002602792492。这些指标仅覆盖保留切片，没有新增阈值，也不是任务精度损失。完整131-token哈希为绑定源代码的生产者见证，不能从末8原始值重算全文哈希。

V4 补证确认：每一代内四 rank 的 out-projection 末8原始字节相等，完整131-token SHA 也一致；两代之间仍不同。norm/out-projection 已记录 geometry 的跨代差异恰为 object/data_ptr/storage_ptr，shape、stride、offset、dtype、storage/logical bytes 均相同；未观察真正 matmul 输入、有效 weight 内容和后端私有格式。

跨代各 rank 的 47/48 层 state、conv_full、conv_leading3 自 layer1 起不同，layer0 相同。每代内部各已保留 native/registered/calibration/MTP/旧STEP0端点的所选状态哈希相同；端点相同不能排除中间写入后恢复或异步行为。相同 prompt/payload/seed 也不等于已证明相同初始 state。

## 投影修正与证据保留

- **V2 投影问题**：把原 reader 未提供的 `interval_contains_unobserved_work` 默认成 false，错误强化为没有未观察工作。**原 reader 本身没有错误声明 false。**
- **V3 读取失败**：增补 producer 详情时按扁平结构解析，实际字段位于 envelope.record，触发 KeyError。失败由 MAIN 保留；未完成的投影不作为诊断结论。
- **V4 修正完成**：缺失字段保留为 null，并设 interval_field_present=false；原 MTP→STEP0 的明确 true/present 保持。新增16份 producer 记录精确覆盖4 rank×2代×norm/out-projection，来自原 readset Ref，补齐完整 geometry、full/raw SHA及同代跨rank原字节比较。

独立本地核对表明，V4 对原有 HTTP、budget、gate、host、input 与 rank 信息除上述 interval 修正外没有改变。V2、V3失败证据、原 host 结果、原完整诊断及冻结 reader 均保留；没有重跑 NPU 来替换结果。审查使用取回副本与 MAIN 已完成的原 Ref 复验，不冒称本地重新打开了远端全部7208个文件。

## 下一步范围、预算与生命周期

实际 projection dispatch 路径取证进行中，须绑定本轮真实 Ascend 类、custom_op、quant_method、有效权重形式及 collective 分支。若实际路径为融合 mm-all-reduce，Python 层可能没有 local-partial 观察点，不能拆融合后称为原路径的纯观察。**下一轮尚未通过 MAIN 源/准入审查**；先完成已有源代码和配置取证，再确定最少 hash-only 观察。

| 原约束 | 本轮实际情况及含义 |
|---|---|
| OTHER 3 MiB/rank | 最坏2,906,375 B；余239,353 B，保留原64 KiB headroom后仅173,817 B |
| probe metadata 512 KiB/rank | 实际379,797 B，余144,491 B；新记录及COMPLETE引用文字均需计费 |
| probe raw 836,352 B/rank | 已满声明上限；不能直接追加新raw |
| device reads 512 MiB/rank | 已核算最坏剩21,650,880 B；weight读回不能免费化 |

假设有效 weight 为 BF16[5120,1536]，一次完整读取即15,728,640 B，两次31,457,280 B超过现余量；实际dtype/shape/格式还须核实。原单次读取上限2 MiB也保持。新观察须重算最坏容量、完整引用闭包及异常残留；不能以旧实际文件较小为由放宽硬预算。

新增路径仅允许原函数恰执行一次、输入/返回对象不替换、默认OFF、精确实例/代际绑定，并保留部分安装回滚、粘滞失败、退休后恢复与实际清理。测试只增加对应的新风险控制，不把重复13项reader控制当作新路径真机资格。数值与生命周期原门禁不降低。

释放巡检只代表 **2026-10-22 09:23:49 UTC** 的状态：观察到 owned 容器停止并保留、PID为0、设备FD holders为空、proc races=0；它不能替代下一轮设备映射、真实占用、资源及清理的实时核实。

硬报告截止仍为 **2026-10-22 12:38:41 UTC**。原 phase=3600秒本身包含cleanup=180秒；原prepare要求剩余3780秒，外层systemd=3900秒及stop=180秒均保持。各层预算不能混算或以本轮较短耗时替代，截止不得自动延长。

## 关键文件 Ref

`R=/opt/host/vnf/austinov`；`WS=R/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z`。R/WS条目指远端原证据；V4明确列为本地审查副本，归档时不得冒称已有远端地址。

| 文件 | 路径 | bytes / SHA-256 |
|---|---|---|
| 原source绑定 | `WS/bound-boundary-ON-v1-20261022T080000Z/SOURCE_BOUND.json` | 1630998 / `702e3feba7de9e4365b472189c9bf0662fdc35f1e08e0e535c863b62e132dbdc` |
| actual host RESULT | `R/run-bole-boundary-ON-v1-20261022T080000Z/RESULT.json` | 2389206 / `25b24adf212dc9ba93331b16d52e2a4c046f1b5aee9432f19dc4895acffa3a8c` |
| actual reader EXECUTION | `R/run-bole-boundary-reader-v2-20261022T080000Z/EXECUTION.json` | 4433 / `045062f159502e86838889c2db6aec565f39af31534c0cee3435e034eb8ed58b` |
| 完整独立diagnostic | `R/run-bole-boundary-reader-v2-20261022T080000Z/BOUNDARY_DIAGNOSTIC.json` | 5011374 / `c2260812c8bda323b4b0b363f770c6becb9a613ee1e1c850b456f6a9a852d9f2` |
| V4本地投影副本 | `/workspace/scratch/e65c435145b1/boundary_actual_review/BOUNDARY_PROJECTION_V4.json` | 220768 / `2a0ca57128b5b6ea421c926577055c144117cc9862d1e3e5656a50982e5840c7` |
| 原short pair FAIL | `R/run-bole-short-pair-reader-v4-20261022T070247Z/EXECUTION.json` | 3721 / `41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1` |
| 本轮dense cleanup | `R/run-bole-boundary-ON-v1-20261022T080000Z/dense/cleanup.json` | 1201 / `3d006528440dbf6412c5b5e07a4068f0c80e020e8045af9f2b2bc0fc9a17c6cf` |

所有性能和精度目标继续按原要求：非HYPIC、免训练、显式opt-in；候选自身先过真机门禁，再做同配置dense/candidate固定1024输出配对；最终精度关闭思考、max_tokens=2048、正常EOS，按用户允许的1%损失同时报告百分点与相对比例。
