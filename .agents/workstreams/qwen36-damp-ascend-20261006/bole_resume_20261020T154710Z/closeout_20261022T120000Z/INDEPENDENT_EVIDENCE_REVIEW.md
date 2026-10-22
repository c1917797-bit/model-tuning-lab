# BOLE 截止前证据收尾复核

## 结论

**本轮尚未达到用户要求的技术交付和最终验收。** 已完成的是原短程 ON/OFF 结果的只读比较、额外 ON 单臂真机边界诊断及其独立证据完整性检查。原配对门禁仍为 FAIL；低观察开销路径自身的真机资格、同配置固定 1024 输出的 dense/candidate 正式性能，以及 GSM8K、HumanEval、MMLU 精度验收均未完成。没有新的 ≥10% 整模型吞吐提升或正式 TTFT/TPOT 结论。[E1–E4]

本次复核只读取当前 workspace 中的已保存副本。没有连接远端、查询凭据、启动模型、操作容器或 NPU，也没有重新打开远端 7208 项原始文件。以下历史结果通过本地文件的完整 SHA、结构和相互引用复核；远端实况必须由 MAIN 另行确认。完整来源和本地输入前后 Ref 在 `FACTS.json`。

## 原配对结果：读取问题修复后仍未通过

旧 V3 的 cleanup 摘要读取错误发生在状态比较前，不能当作 ON/OFF 状态相等或不同的结论。后续 V4 保留严格哈希和清理谓词，按生产者的二字段摘要读取真实文件。保存的执行记录显示，读取器控制通过，实际 pair 退出 1，原输入不变。[E1]

保留诊断明确给出 **ON 36 个 rank-frame key、OFF 32 个，共同 32 个**。额外四项是每个 rank 的第一代第 4 帧；完整 key 集合不相等。不能取共同子集替代原完整配对门禁，也不能把两边各自 host primary=null 推进为配对成功。该 FAIL 未被后续 ON 内两请求比较覆盖。[E1–E2]

## 真实边界诊断确定了什么

ON 单臂、TP4、131 input tokens、两次不同请求、每次固定 8 output tokens 的模型诊断已在历史证据中完成。独立 reader V2 状态为 `PASS_READONLY_DIAGNOSTIC_INTEGRITY`，实际读取 7208 个完整 Ref、421892101 B，核验四个 rank 各 148 个 boundary 文件及前后身份不变。reader 未执行 NPU；退出 0 只证明这份模型诊断证据完整，不授予算法数值、状态配对、性能或任务精度资格。[E3–E4]

四 rank 的最早已观察差异都是 `RAW-layer0_out_projection`。精确区间是 gated norm 返回观察点，经原 reshape/rearrange 和 out_proj 内部执行，到 out_proj 返回观察点。两代 layer0 qkv/b/a、core 和 norm 的完整 131-token producer 哈希相同，core/norm 的保留末 8-token 原始切片比较也相同。[E4–E5]

输出投影保留末 8 tokens 的每个 rank，共 40960 个 BF16 元素，有 **5874** 个数值不同，全部有限；`max_abs=0.0625`，`RMS=0.0004381508352294257`，`L2_error / generation_1_L2_norm=0.002602792492276376`。这些数值只描述保存切片，没有新增容许阈值，不能解释成任务精度损失，也不能外推完整 131-token 数值幅度。本次仅重验投影中的这些记录及一致性，未重新读取远端 raw 二进制。[E5]

同一代内四个 rank 的 out-projection 末 8-token 原始字节一致，两代之间不同。每个 rank 的 norm/out-projection 已记录 geometry 跨代仅 `object`、`data_ptr`、`storage_ptr` 不同；shape、stride、offset、dtype、storage/logical bytes 相同。实际 matmul 输入、有效权重字节和后端私有格式尚无这轮内部观测证明。以上不能唯一归因到 GEMM、HCCL、布局或生命周期。[E5]

两代之间，每 rank 的 state、conv_full、conv_leading3 各 47/48 层从 layer1 起有不同哈希，layer0 相同。同一代内部保留的 native/registered/calibration/MTP/旧 STEP0 端点状态哈希相同；端点相同不能排除中间写入、恢复或异步行为，也没有证明两次请求初始状态相同。[E5]

## V4 证据投影修正已核对

V2 投影曾把原 reader 缺失的 `interval_contains_unobserved_work` 默认成 false，错误强化了结论。原 reader 本身没有错误声明 false。V3 增补时又因把 producer envelope 当成扁平 record 而读取失败。失败和旧投影应保留。[E5–E6]

本次对本地 V2/V4 直接比对，确认 HTTP、budget、gates、host、input 全部相同，rank 内容除 interval 修正外相同。**40 处缺失字段已改为 null/present=false；8 处原有 true 保持 true/present=true。** V4 额外保存的 16 项 producer 记录恰覆盖四 rank × 两代 × norm/out-projection。没有因这次修正重跑 NPU。[E5–E6]

## 新 projection reader 的准确完成度

新读取器、包装器与测试源码已在本地落盘，并有 **15 项 synthetic focused controls** 的保存执行记录。它们校验 stage 可观测性、callsite、Ref 映射、geometry、有限数、计费、闭包与未知值表示；本次逐项重开记录中的五份输入以及 stdout/stderr，所有长度和 SHA 匹配，没有重跑测试。保存状态仅为 `PASS_LOCAL_SOURCE_CONTROLS`。[E7]

目前源码仍明确设置 `REVIEWED_EXTENSION_FROZEN=False`，auditor 的 bytes/SHA 未填，五个 helper pin 全部是 `(None, None)`。包装器同样 `REVIEWED_WRAPPER_FROZEN=False`，reader/test 两个 pin 未填，主入口在执行前拒绝未冻结状态。保存记录的 `main_entry_executed`、`reader_frozen`、`wrapper_frozen` 和 `host_python_runtime_qualified` 均为 false。因此不能把本地控制称为远端冻结、实际结果读取或真机资格。[E7–E8]

设计上，新路径拟保留原 148 文件并增加两代完整 envelope，总计每 rank 150 文件，COMPLETE 引用 149 项；每份新 envelope ≤8192 B，每代新增 D2H ≤8 MiB、两代 ≤16 MiB，仍计入原 512 MiB。新阶段只在实际固定 Python 调用方边界观察，callee/HCCL 内核没有独立 pin，融合路径不可见的内部阶段必须明示。其实际部署、完整冻结、源审计、真实路径和新 reader 主入口均未由本次复核验证。[E8]

## 时间和实时状态边界

硬截止保持 **2026-10-22 12:38:41 UTC**。此次开始复核时是 11:50:39 UTC，原 prepare 要求完整 3780 秒已无法容纳；本报告不给予缩减预算、延长窗口或新实验授权。原 phase=3600 秒包含 cleanup=180 秒，外层 systemd=3900 秒及 stop=180 秒不能混算或以历史实际短耗时替代。

当前可读的最后保存释放巡检时间为 **2026-10-22 09:23:49.974442 UTC**：device FD holders 为空、proc_races=0、所属 unit MainPID=0/ExecMainStatus=0，状态 active/exited。这是历史时间点。不能据此说现在卡空闲、现在仍有任务运行或资源已经重新准入。当前物理设备映射、真实进程/容器、内存、磁盘、新输出目录和远端分支均不在本次本地复核范围。[E9]

## 最终验收缺口

| 用户要求 | 当前证据状态 |
|---|---|
| 非 HYPIC、免训练、显式 opt-in vLLM-Ascend monkeypatch 新技术 | BOLE 路径仍在诊断和准备阶段，没有本轮最终成功证明 |
| 候选真实 NPU 数值、多步状态、生命周期门禁 | 原完整 ON/OFF pair FAIL；低观察开销候选未获自身资格 |
| 同配置整模型 dense/candidate、固定输出 1024、吞吐 ≥10% | 无正式配对验收结果 |
| 分别报告 TTFT、TPOT | 无满足上述正式配对条件的可报告最终指标 |
| GSM8K、HumanEval、MMLU；关闭思考、max_tokens=2048、正常 EOS | 未完成最终任务精度验收 |
| 精度损失不超过用户允许的 1%，报告百分点与相对比例 | 缺少 dense/candidate 实测分数，不能填数或声称通过 |

下一项实验性工作仍应是明确实际输出投影分支及差异区间；若获得新的有效实验窗口，再完成源冻结、严格新准入、真实两代运行和独立新 reader。不能从本次本地源码控制直接跳到性能筛选。

## 证据索引

下表远端 Ref 是已保存证据所记录的身份；本次没有重新读取远端。`WS=/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z`。

| ID | 来源 | 身份与范围 |
|---|---|---|
| E1 | `/opt/host/vnf/austinov/run-bole-short-pair-reader-v4-20261022T070247Z/EXECUTION.json` | 3721 B；SHA `41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1`；本地副本 `review_input/EXECUTION.json` |
| E2 | `/opt/host/vnf/austinov/run-bole-short-pair-diagnostic-v1-20261022T072523Z/DIAGNOSTIC.json` | 4432793 B；SHA `3d615eeeb0d9ae010ba7ec2602f82567b7b772bce46d1a8bbde520f736dec30f`；本次读取其本地投影 |
| E3 | `/opt/host/vnf/austinov/run-bole-boundary-ON-v1-20261022T080000Z/RESULT.json` | 2389206 B；SHA `25b24adf212dc9ba93331b16d52e2a4c046f1b5aee9432f19dc4895acffa3a8c`；身份取自 checkpoint |
| E4 | `/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z/EXECUTION.json` | 4433 B；SHA `045062f159502e86838889c2db6aec565f39af31534c0cee3435e034eb8ed58b`；本地副本完整 SHA 一致 |
| E5 | `boundary_actual_review/BOUNDARY_PROJECTION_V4.json` | 220768 B；SHA `2a0ca57128b5b6ea421c926577055c144117cc9862d1e3e5656a50982e5840c7`；源完整诊断 5011374 B，SHA `c2260812c8bda323b4b0b363f770c6becb9a613ee1e1c850b456f6a9a852d9f2` |
| E6 | `boundary_actual_review/BOUNDARY_PROJECTION_V2.json`、`PROGRESS_AFTER_BOUNDARY_V1.md` | 保留旧投影以及失败/修正解释；本次不覆盖 |
| E7 | `projection_reader_v1_draft/LOCAL_CONTROL_EXECUTION.json` 与其 stdout/stderr | 15 项本地合成 controls；记录及输入完整 SHA 本次重验 |
| E8 | `projection_reader_v1_draft/read_projection_result_v1.py` 与 `run_projection_reader_once_v1.py` | reader 93803 B，SHA `17e3072fd7f7ecad89d0f1d6aacc731458a9065cb87674853a8c08b62e01b33e`；wrapper 27042 B，SHA `6a7c6f5ca6f3c2d75b084dd11f94396dfabb7849c978ac5b3cd9510e749aeabb`；未冻结 |
| E9 | `boundary_actual_review/POSTRUN_RELEASE.json` | 9780 B；SHA `d678e1edeeb08c1129874c5027402ac76fb3368575530512cde995694c072af8`；历史释放快照 |
