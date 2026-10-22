# BOLE 原 24 小时窗口封账报告

**当前结论：用户要求的最终技术交付、整模型性能和任务精度验收尚未达成。** 原完整短程 ON/OFF 配对仍为 FAIL。后续真实 ON 单臂边界诊断与独立 reader 的 PASS 只证明已保存诊断证据的完整性，不能替代候选数值、多步状态、生命周期或正式性能门禁。[R1–R6]

## 时间、授权与复核范围

原 24 小时窗口的硬报告截止保持 **2026-10-22 12:38:41 UTC**，不延长、不重写旧时钟。11:50 的本地复核时，原 prepare 要求的完整 3780 秒已经无法容纳。

MAIN 于约 12:00 UTC 转达用户明确新指令“可以继续穿刺一直到成功”。后续授权记录为 `explicit_user_continuation_20261022T1200Z`；已另立 `continuation_20261022T120055Z` 批次，内部有界时段为 **12:00:55–18:00:55 UTC，共 21600 秒（6 小时）**，使用新的 source/output 身份。此内部批次不改变旧窗口的验收事实、截止或失败证据，也不代表已获资源或数值资格。本摘要独立复核者没有远程操作或启动 NPU。

本报告汇总已保存的真实执行证据、独立本地复核，以及 MAIN 本轮远端只读复验与源码保存回执。MAIN 已重新解析拓扑、加载完整 host-development contract，并在安全会话中完成所需核验；本报告不包含验证值。原始 R1–R7 本轮已重新打开、全文 SHA 不变；R6 的 7208 个输入 Ref、共 421892101 B 逐项 streaming SHA 与 stat/lstat 稳定校验通过。这是证据重验，不是新的 NPU 执行。[F1、F3]

本地解析副本供本报告内容复核；其字节 SHA 与远端序列化回执分别记录，未冒称相同。远端精确身份以下列 F 表为准，本地输入身份另见 FINAL_STATUS.json。

## 已核实结论

1. **原配对 FAIL 保留。** cleanup 摘要读取格式问题已经按实际生产者格式修复，后续比较确实执行；保存记录显示原输入不变。完整 rank-frame key 集合为 **ON 36、OFF 32、共同 32**，ON 每 rank 多一项 `(rank, generation=1, frame=4)`。不得仅取共同子集放行，也不得用后续 ON 单臂诊断覆盖此 FAIL。[R1–R2]
2. **真实边界诊断完成，独立读取完整性通过。** 历史 ON 单臂 TP4 诊断使用 131 input tokens、两个不同请求、每次固定 8 output tokens；reader 为 `PASS_READONLY_DIAGNOSTIC_INTEGRITY`，校验 7208 个 Ref、421892101 B，四 rank 各 148 个 boundary 文件。reader 自身没有执行 NPU。[R3–R6]
3. **首个已观察差异位于 norm 返回至 out_proj 返回之间，根因未知。** 四 rank 都在 `RAW-layer0_out_projection` 首次出现已观察差异；之前 layer0 core/norm 的完整 131-token producer 哈希一致。实际区间包含原 reshape/rearrange 与 out_proj 内部执行，尚未观测实际 matmul 输入、有效权重字节和后端私有格式，不能唯一归因为 GEMM、HCCL、布局或生命周期。[R6、L1–L3]
4. **保存切片的差异已量化。** 每 rank 的 out_proj 末 8-token 切片共 40960 个 BF16 元素，其中 **5874 个不同**，均有限；max_abs=**0.0625**，RMS=0.0004381508352294257，relative L2（以第一代范数为分母）=**0.002602792492276376**。这是切片数值差异，没有新增容差，不是任务精度损失，也不是完整 131-token 数值幅度。同一代四 rank 的保留投影字节一致。[R6、L3]
5. **多步状态仍未获资格。** 两代之间每 rank 的 state/conv_full/conv_leading3 各 47/48 层从 layer1 起不同，layer0 相同；已保存的同代转换端点哈希一致，不能排除端点之间的写入、恢复或异步行为，亦未证明两次请求初始状态相同。[R6、L3]
6. **V4 纠正了投影中过强的默认值。** 40 处原缺失 interval 字段改为 null/present=false；8 处明确 true 保持 true/present=true。原 reader 本身没有将缺失字段宣称 false。旧 V2 投影与 V3 读取失败保留，未为该修正重跑 NPU。[L1–L3]

## 新 v2 与 continuation v3 包仅完成准备

本地 prepare/validator 静态审查覆盖五 helper/profile、沿用的五个 runtime Ref、historical original auditor 的 pinned readset 和不变的 clock/budget；未发现确定的新依赖遗漏或放宽原门禁。control Ref 的哈希与归属检查不能自行证明控制结果语义为 PASS。

新 reader 有 15 项已保存本地合成 controls 通过记录，但 reader/wrapper 仍未冻结；auditor、五 helper、reader/test 的必要 pin 未完成，主入口和远端真实结果读取未执行，host Python runtime 未获实际资格。不能将静态审查或本地 controls 计作真机资格。低观察开销路径自身的真实 NPU 资格尚未完成。[L1–L2]

新授权下的 continuation v3 已完成 **22 个核心文件的限定独立本地源码审查**：6 小时为 21600 秒，父源保持 `a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f`，原数值、Ref/hash、清理和数据限制未放宽；phase=3600 秒、cleanup=180 秒、完整 prepare budget=3780 秒不变。六 clock 的固定祖先选择与 renderer 仅完成静态检查，新六正文实际生成及原 validator/独立 auditor 验证仍待执行。20 项 same-image test 的源码审查不等于真实运行。host controls、真实 builder、独立 source audit、freeze/pins、资源准入和 NPU 执行仍 **pending**。新 reader 也未 freeze，未填虚构 pins 或 PASS。[L5–L6]

## 最终目标缺口

| 验收项 | 当前结论 |
|---|---|
| 非 HYPIC、免训练、显式 opt-in 新插件技术交付 | 尚无本轮最终成功证明；HYPIC 不计本轮新成果 |
| 候选真实 NPU 数值、多步状态、生命周期 | 原完整 pair FAIL；低观察开销候选未获自身资格 |
| 同配置 dense/candidate 整模型，固定 1024 输出，吞吐 ≥10% | 无正式配对验收结果，提升值不可填 |
| 正式 TTFT、TPOT 分别报告 | 尚无满足上述配对条件的最终指标 |
| GSM8K、HumanEval、MMLU，关闭思考、max_tokens=2048、正常 EOS | 未完成最终验收 |
| 精度损失 ≤用户允许的 1%，同时报告百分点及相对比例 | 缺少 dense/candidate 实测分数，不能声称通过 |

## 本轮真实资源观察：不构成准入

MAIN 的只读快照观测区间为 **2026-10-22 12:14:03.107435–12:14:11.523487 UTC**。原始快照 2086573 B，SHA-256 为 `b1e2067767a65976684e7934c58980d81df7f0c8356063df59f992ccb869306f`。18 个 mount 数组、5928 个 unique member 已独立完整还原；成员值、顺序及重复均相等。该完整性结果不授予实验资源资格。[F2、F7]

| 观察项 | 本轮记录 | 解释边界 |
|---|---|---|
| 物理 NPU4–7 | SMI 未列运行 PID，AICore 均为 0；HBM 读数依次 2868、2872、2868、2867（工具表标 MB） | HBM 非零，不能写成卡空闲或已经准入 |
| 实际进程扫描 | 未观察到目标设备 FD holder；扫描期间 7 个 PID 消失并保留记录 | PID 为 3359455–3359461；未将扫描竞争抹成“无异常” |
| 受保护设备 | NPU1 上外部 PID 3356831，python3，显存读数 944（工具表标 MB） | 保持保护，不触碰物理 0–3 |
| 六个历史容器 | 前后观察均 Running=false、Pid=0 | 只说明这些 CID 的本次状态 |
| 三个旧 systemd unit | MainPID=0、ControlPID=0、Result=success、ExecMainStatus=0、active/exited | 不等于新任务已获得 owner 或锁 |
| 主机可用内存 | MemAvailable=72924064 kB | 只对应快照时间点 |
| 磁盘 | `/opt` 可用 152365334528 B；`/cache` 可用 10923728896 B | `/cache/docker` 共用后者，需新执行前再核余量 |

六个历史容器的 OWNED/source/create/cleanup 核心记录已另行全文 SHA 重读；这一跟进并未重开其嵌套 inspect 原件。快照中最新两个容器的 saved-inspect historical join 仍为 false，不能扩写为完整历史链 PASS。完整 CID 与核心 Ref 保存在 FINAL_STATUS.json，并引用独立回执。[F3]

快照没有启动或修改容器，没有取得新 owner 或执行锁；resources_admitted=false。新 continuation v3 输出目录的独占创建与资源准入尚未由此快照证明。后续上卡前须重新核实，不能将上述时间点的无 PID 列表沿用成当前空闲声明。[F2]

## 源码保存、Git 与项目校验

源码提交 **C1 `dfb6938ed36fa25d2a161e3b44ffd6fb27bfabad`** 已正常 push，MAIN 独立 `ls-remote` 核对分支 `work/qwen36-damp-ascend-20261006` 指向同一提交。权威仓库为 `/opt/host/vnf/austinov/model-tuning-lab`。本报告只记录这个已有源码提交；封账报告自身后续 C2 提交的回执存于外部，避免自引用。[F4–F5]

`./scripts/validate-mst.sh` exit=0，**20 个维护者 skill 的结构校验通过**，stdout 为 59 B；源码 compile PASS。完整 `git diff --check` 的四处固定源码副本 EOF 空行 warnings 已记录；这些字节与已审查、固定哈希的原件相同，其余文件检查 PASS，未声称全树无警告。三个旧 tracked dirty 文件 SHA 保持原样，旧 untracked 文件未清理；没有将历史工作树状态伪写成 clean。这些项目与源码检查不构成 NPU 数值或整模型验收。[F4、F6]

## NEXT：在新明确授权下独立继续

原窗口按本报告已有事实封账，截止仍为 **12:38:41 UTC**，最终目标未达成。后续已获明确继续授权，不等待重复授权；在独立批次 `continuation_20261022T120055Z` 的内部 **18:00:55 UTC** 上限内，完成新 source/output 身份、真实 host controls、builder、原 validator 与独立 auditor、冻结及新的资源准入后，才探测实际投影调用路径以缩小未知根因。保留已有 FAIL，不原样重跑已知失败，不降低原数值门禁。物理设备仍限定 NPU4–7，保护 0–3。

只有低观察开销候选自身通过真实 NPU 数值、多步状态和生命周期门禁后，才能进行同配置固定 1024 输出的整模型 dense/candidate 配对及 TTFT/TPOT；之后按既定协议完成三项任务精度，报告原始分数、百分点损失及相对损失。

## 原始证据身份

以下七个原始远端身份已由 MAIN 本轮重新全文 SHA 核验，不变。独立摘要复核者没有远端操作；完整本地复核与限制见 L1/L2，MAIN 实读回执见 F1、F3。

| ID | 路径 | bytes | SHA-256 |
|---|---|---:|---|
| R1 | `/opt/host/vnf/austinov/run-bole-short-pair-reader-v4-20261022T070247Z/EXECUTION.json` | 3721 | `41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1` |
| R2 | `/opt/host/vnf/austinov/run-bole-short-pair-diagnostic-v1-20261022T072523Z/DIAGNOSTIC.json` | 4432793 | `3d615eeeb0d9ae010ba7ec2602f82567b7b772bce46d1a8bbde520f736dec30f` |
| R3 | `/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v1-20261022T080000Z/SOURCE_BOUND.json` | 1630998 | `702e3feba7de9e4365b472189c9bf0662fdc35f1e08e0e535c863b62e132dbdc` |
| R4 | `/opt/host/vnf/austinov/run-bole-boundary-ON-v1-20261022T080000Z/RESULT.json` | 2389206 | `25b24adf212dc9ba93331b16d52e2a4c046f1b5aee9432f19dc4895acffa3a8c` |
| R5 | `/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z/EXECUTION.json` | 4433 | `045062f159502e86838889c2db6aec565f39af31534c0cee3435e034eb8ed58b` |
| R6 | `/opt/host/vnf/austinov/run-bole-boundary-reader-v2-20261022T080000Z/BOUNDARY_DIAGNOSTIC.json` | 5011374 | `c2260812c8bda323b4b0b363f770c6becb9a613ee1e1c850b456f6a9a852d9f2` |
| R7 | `/opt/host/vnf/austinov/run-bole-boundary-ON-v1-20261022T080000Z/dense/cleanup.json` | 1201 | `3d006528440dbf6412c5b5e07a4068f0c80e020e8045af9f2b2bc0fc9a17c6cf` |

## 本地独立复核身份

| ID | 相对工作区路径 | bytes | SHA-256 |
|---|---|---:|---|
| L1 | `final_evidence_review_20261022T1150Z/REPORT.md` | 9863 | `c5f1c2569a189158abdca4d232bf617e92650fe2f308fb76482ad1a117b06db3` |
| L2 | `final_evidence_review_20261022T1150Z/FACTS.json` | 21325 | `6eb2071f968ead5bcf12c979d8769b91cb0e87288ac77d7b1161753bc27f0efd` |
| L3 | `boundary_actual_review/BOUNDARY_PROJECTION_V4.json` | 220768 | `2a0ca57128b5b6ea421c926577055c144117cc9862d1e3e5656a50982e5840c7` |
| L4 | `boundary_actual_review/POSTRUN_RELEASE.json` | 9780 | `d678e1edeeb08c1129874c5027402ac76fb3368575530512cde995694c072af8` |
| L5 | `new_v3_independent_review/REPORT.md` | 11749 | `05ec2d3be2c8c060b7a6351851c4c153598f06a16185365861177d2c0dc1c7fc` |
| L6 | `new_v3_independent_review/MAIN_SOURCE_REVIEW_SUMMARY.json` | 8936 | `01ab29a9e35796185ca040dac4772b862602f74c9e4a2ac8342a29ad3ed34192` |

## 本轮远端复验与保存回执身份

| ID | 路径 | bytes | SHA-256 |
|---|---|---:|---|
| F1 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/REF_VERIFICATION.json` | 9334 | `5745a8157a02fc2edf7540b035027f7298a5db274e9afc0df1ab4f848e651f30` |
| F2 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/SNAPSHOT_V4_VERIFIED_PROJECTION.json` | 124635 | `675bef0d5cf6a54e1e891881ccba55158113e6ebcdba07d1911da194bc2d6790` |
| F3 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/HISTORICAL_OWNER_CHAINS.json` | 26976 | `787ca7babe25e6d0c2fa9f9c3988226a0464fa679df8b2773f12694f7edb739c` |
| F4 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/SOURCE_COMMIT_PUSH.json` | 15682 | `fdf8452659e69a02620f5cba003b4f0ea30ba1423ec49cc3314f6a20049d9a93` |
| F5 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/SOURCE_REMOTE_REF_VERIFICATION.json` | 380 | `2d763ef6d728805cfd19ea0b74da6a5455c3f63b249ecccb103a4e2cf1430ac0` |
| F6 | `/opt/host/vnf/austinov/run-bole-final-closeout-20261022T120000Z/VALIDATE_MST.stdout` | 59 | `a0de6af6505edc59ef401af2e2e67a0a0cdc3124d04d84332fadbd7529bcae80` |
| F7 | `/opt/host/vnf/austinov/run-bole-final-closeout-snapshot-v4-20261022T121700Z/SNAPSHOT.json` | 2086573 | `b1e2067767a65976684e7934c58980d81df7f0c8356063df59f992ccb869306f` |
