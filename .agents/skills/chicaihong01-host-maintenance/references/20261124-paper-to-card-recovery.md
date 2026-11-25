# Paper-to-Ascend：证据复用与接入失败经验（2026-11-24）

适用于 BOLE / DeltaLog 连续恢复、报告修复、当前源码准入与上卡排程。下列成功均为历史限定范围；本文件不是新的算法、模型或性能 PASS。

## 已验证经验

| 证据与结果 | 可复用的做法 | 必须补齐的下一门 |
| --- | --- | --- |
| BOLE真实NPU执行16次verify与16次commit；修复后的独立消费者128/128通过，58份原始文件哈希不变 | 数学未改且输入/输出完整时，修复判定器并重判原数据，保留旧FAIL | 真实模型调用、请求生命周期、长程及配对性能 |
| 原BOLE消费者128个内层指标通过但外层失败；上下文把checks建成list，却按字符串索引 | 验证完整初始化、返回值形状、调用对象与错误路径；数学AST相同不足以证明接线正确 | 经完整实际消费者复核后才更新阶段 |
| DeltaLog原生capture/bind完成；bind exit0、5.753秒，CPU/NPU未执行、账本未改 | 使用原生生成产物及真实消费者判定阶段；prepared_only=false或遗留NOT_BOUND标签都不能单独说明READY | 合法当前控制证据、设备准入和真实数值结果 |
| CPU004 guest pass_gate=true，外层因postverify:AttributeError失败；实际别名callee在V15已修返回类型 | 保留旧FAIL；先追踪实际导入别名、被调用文件及返回对象，再验证既有修复，不重复修已修部分 | V15当前运行结果仍未测；不能把旧owner改成当前released owner，需真实补判定及当前控制验证 |
| CPU004与V15的15项入口、oracle、consumer、ABI、构建及库字节一致，旧/新pin有效 | 复用未变化的软件证据，另验证授权和控制改动 | 此一致性不授予当前CPU数值资格或任何NPU资格 |
| 历史账本绑定旧scope，当前执行另有新AUTH | 分别核验历史不可变身份与当前执行权；修复角色误比较 | 不改历史账本、不贴新AUTH冒充旧任务的新执行 |

详细BOLE重判经过见 [state16经验](20261117-state16-rejudge.md)，此处不重复全部启动错误。

## 下一次执行时的决策规则

1. 每个准备节点只回答一个会阻止真实下游执行的问题，交付实际入口、输入/源码Ref、预算、唯一输出、独立判定与释放方式。未能给出下一真实消费者时，标记具体缺口。
2. 接线修改验证完整入口与实际容器环境，包括授权文件、目录、锁、只读挂载、真实调用对象和返回结构。沿实际import alias追踪callee和完整源码Ref；同名文件或15项数学字节相同不能证明控制模块相同。CPU004旧callee返回list，V15实际callee已返回含final_verify的类型；“V15必重现旧错”及“把seal改storage”假设已被反证，不再据此修代码。复用已验证的owner构造器；不要因每次续跑重写控制框架。
3. 同一轮先核完整生产者→消费者→模型入口的输入契约再绑定。只为新证据支持的变化派生新源码/输出；保留原失败。不能通过连续增加fixture、源码审查或重复旧CPU套件替代缺失的NPU/模型门。
4. 对数值/布局/状态缺陷，保存首个失败输入并做针对性独立对照。对报告/引用/启动缺陷，修该层并复用有效原数据。新Ascend算子或已证算子缺陷可走兼容的官方实现/CANNBot流程；已通过的内核不因接线问题重写。工具使用不等于算法验收。
5. 源复用须钉住原失败、原guest、原source、实际库/ABI及当前控制变化。普通严格准入分支保持；补判定不得伪改旧source/target_source/错误字段，不能用自造MAIN PASS补缺失上游。
6. 主机重启后重新核boot、确切PID/start、CID、物理映射和实际挂载。旧operation编号、STARTED、释放截图及旧stat.dev不能作为当前进程/资源证明。
7. 使用实际输出盘和DockerRootDir的可用容量。2026-11-24已测/cache正常挂载但f_bavail=0；f_bfree约100.8GiB不是可分配额度。先核本任务可归档项及剩余授权，不改ext4预留、服务或他人数据。 该事实采集于2026-11-24T08:01:57.430446+00:00，见[资源回执](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/RESOURCE_ADMISSION_20261124_V2.json)（1390B，SHA256 7fbce3089a52232f289fbfa7299e924e76d0ee46e7db21349379e0d3e74a7cad）；未来每次执行前重新采集，不能把此观测当作永久资源状态。
8. MAIN只调度真正READY节点；准备agent完成独立节点即续派下一有用节点，不等于自动上卡。四卡比较独占串行；独立单卡仅在设备、控制器和汇总预算兼容时并行。ready=0就修精确缺口，不用重复16/192或假负载填卡。
9. 只记录可证明的阶段起止、计算、必要启动/搬运、CPU和空档。缺连续证据时利用率/空档时长为未测。源码/文档阶段不能计为NPU利用率。
10. 当前协议规定的真实模型数值/状态门完成后，立即转同栈/同输入/同并发/同通用优化的32K、fixed1024、c1、profiling OFF配对筛选；正式重复及任务smoke→full仍按最新冻结合同执行。短组件通过不能借作模型、long160或最终性能精度通过。

## 证据索引（主机内）

根目录 O：`/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/dual_resume_20261117T060217Z`。

| O下相对路径 | 字节 | SHA256 |
| --- | ---: | --- |
| bole_f65_state16_run_v5/result/INDEPENDENT_RESULT.json | 55466 | ce145f0c99e7ac5baa9d417628c420245b9f1e089dfd2a67bdba0860f8e59677 |
| bole_f65_state16_rejudge_run_v2/result/INDEPENDENT_RESULT.json | 54690 | 944252e2bf8965093a79a874293d6343c7983b7dc8083f7b2e917453fedb2fec |
| bole_f65_state16_rejudge_prepare_v2/CONTROL_PROOF.json | 1877 | fc0c52a13c9d9e5860aa21987324dfb25a727a01f4bdc7e7c76276fef8f14bd7 |
| MAIN_STATE16_INDEPENDENT_PASS_FRESH_RELEASE_20261117.json | 26493 | 6fca953e8464df51170c2acd1a6cb5c6b6c2ca03a88df9421bc4fa333f53f2a9 |
| delta_prepare/native_bind_v15_execution_20261117/RESULT.json | 1385 | 5739df13fdc5b90bbc8e8252dda27201b1303096407781ee19be24439b243c47 |
| delta_prepare/CPU004_REUSE_CONTRACT_ANALYSIS_20261117.json | 18810 | a5c98df8477f24faa5274a9ca8020bdb7c8784d9e2ac4b9ea6ee2502e79f0766 |

这些哈希于11月24日独立只读核验。另见[实际别名与V15已有修复的归因纠正](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/delta_prepare/ATTRIBUTION_CORRECTION_20261124.json)（8220B，SHA256 a7ea0faefa44eb18f75855777bc29137d6b25a55400179d9b79d8fcd00db2552）；原分析保留，错误修复假设不再沿用。源码与RAW始终留在chicaihong01；没有新的NPU、整模型、正式性能或任务精度验收。

## November24 stage corrections with actual evidence

- The BOLE native comparison rejected five envelope scalar roles although all477 source files/Refs matched. Inventory window bounds and derived output/stream paths as well as source literals and Ref3 objects. Persist both full manifests and the exact typed diff before correcting a failed binding; current native bind then succeeded without repeating the matrix or math suite.
- A manifest declaration does not prove the real callee. Delta's actual guard loaded old V15 R3/R4 reader programs through five typed aliases despite m.files declaring current readers. Trace actual load/context/effective-budget calls and distinguish executable reader programs from immutable receipt/ledger/math basis. Evaluate pure constructors and the real callee closure before freezing. D.history(fresh=False) still performs bounded native observation writes: retain that writer in the declared capture phase under the original1MiB metadata cap, and require its genuine result before qualification; do not mock it or call the whole chain pure. This correction is preparing; do not claim its runtime gate passed.
- Freeze evidence input while observing it. The first absence observation had one new-source loader Ref change during parallel preparation. Preserve that report and use an immutable original loader for historical observer functions; the stable second observation verified all readset hashes before/after. Avoid attaching provenance observers to mutable preparation files or creating review/template Ref cycles.
- Validate actual argument types and the complete native input constructor, including audit dictionaries, before mkdir/output/STARTED. Original Q's CID ABI is exactly two ordered singleton groups, not a flat list; accept only that cardinality and phase mapping, never arbitrary flattening. Preserve failed flat comparison and old filename/loader errors as control failures.
- Recheck resources while preparing. Docker independently recovered from0 to~23GiB; cancel the unexecuted native-OCI workaround and use the original Docker environment. Eight genuine original CLI reports matched in245.045s and all CPU guests released. This is archive compatibility, not new algorithm/NPU/model success or proof of cleanup; no original directory has yet been moved or deleted.
- BOLE component160 was approved for one 2 GiB output after the 16-step run used a 256 MiB cap. Tie an increase to the specific run. Retain the complete step evidence and keep the DeltaLog storage budget separate.
- Derive all writable paths from the real owner and guest before dispatch. In BOLE, the raw results and seed used one root, the owner receipts used another, and an additional host-only admission file used `S/control`. All three needed new destinations on retry. Verify the original source and old output directories retain their bytes. Use Docker and kernel observations to distinguish a missing historical container, an active workload, and a failed control request.
- For a renewed DeltaLog package, resolve the actual caller’s output argument and each active observation writer. Compare any additional ledger-directory member to an original capture and bind receipt before admitting its exact hash. Keep the ordinary CPU and model acceptance branches intact when adding a narrow control-only validation.
- When an inverse proof stores code strings alongside metadata, parse it on chicaihong01 and construct a new response containing only the permitted counts, booleans, byte lengths, and hashes. Truncating a serialized object after transport can still disclose code.
- MA control/registration flapping is not an OS task terminal or proof of a credential failure. RGW can stay healthy while the peer disappears. A second peer's same-boot/repo/host-namespace read-only proof permits attribution, not silent write failover or bypass of approval. Keep original handles and verify actual receipts/PID/start/CID before a successor.

## BOLE 单卡设备枚举失败（11 月 24 日）

- 把容器启动、设备枚举、第一次算子调用和独立数值验收分别记账。e975 容器已启动，torch_npu 报告 ascend_hal 无法取得设备数；实际 verify 和 commit 都为零，数值结论记为未测。
- 当设备可见性断言合并多个条件时，分别留存可用性、设备数、各自的异常和警告。历史 16 步使用相同镜像和设备映射曾进入计算，驱动版本和命名空间归因仍需本次证据。
- 同镜像的有限设备诊断可以直接检验上述分歧。用确切容器 ID 核实退出，仅在资源与独立授权允许时执行。单次验证授权按实际 guest 启动记账。

## 原生资格发布与设备临界区（11 月 25 日）

- 原生 prepare 已正确生成当前窗口、receipt 和 STREAM 路径时，不重复套用旧包的“五角色修复”。先比较真实字段；仅缺资格 AUTH 时，只发布该字段并保留原 unsigned。复用发布 helper 时同时验证其真实 globals 和当前 producer 的序列化契约：先用主机内小样本实际执行 helper，再以真实输入运行完整入口至首次权威写入前截断。AST 编译或字段形状通过不能替代这条接缝验证。发布与 bind 成功仍不是模型数值或性能 PASS。
- CPU 释放时的设备快照不能覆盖随后 create/start 的竞态。以真实 create arm 区分设备阶段（可省略的 cpu 布尔不足以判定）；对当前明确授权的物理集合，在设备 create 前和 created/Pid0→start 前分别新鲜读取 UDA。created/Pid0 且没有正面 own-namespace 证据时仍要求该集合全无 holder；未知归属须拒绝，不能因 OWNED 文件存在而放行。保留原 exact-CID 身份、finally 清理和数值门，CPU arm 不增加设备访问；源码绑定及纯 metadata 回归不代表设备或模型已通过。

本轮主机证据：

- [单字段资格发布回执](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/bole_prepare/native_short8_physical47_deviceguard_prepare_v1/native_bind_authorization_publish_v1/PUBLISH_RECEIPT.json)（2619 B，SHA256 `d2f54281c68e0c9c6aaa125d07e11f4e168f475b2eac0363d88880f9ce5dcae5`）；[helper 实际回归](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/bole_prepare/native_short8_physical47_deviceguard_prepare_v1/NATIVE_QUALIFICATION_AUTHORITY_PUBLICATION_HELPER_REGRESSION_V2.json)；V3 原入口实际首写前截断为 MA `exec-000000000001138d`。
- [双边 UDA 守卫 V2](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/bole_prepare/physical47_device_guard_delta_v2/SOURCE_DELTA_REVIEW_INPUT.json)（8060 B，SHA256 `0c26f9ddd2dab11cee7a10bbcf7b5540b731b539121454be7c9820d47f653dd6`）；[created/Pid0 原清理合同](../../../workstreams/qwen36-damp-ascend-20261006/dual_resume_20261124T075410Z/bole_prepare/physical47_device_guard_delta_v2/CREATED_PID0_CLEANUP_CONTRACT.json)。

## 整模型失败帧与配对索引（11 月 25 日）

- 排查算子时，把已执行的 verify 调用、可见库身份和状态张量关联到同一请求、rank、层和槽位。库名或映射能够证明加载；原生派发指针若未采集，保留为未知。仅修改观察字段时，复用未变的组件数值证据。
- 在首次上卡前，对照生产者传入的真实 trial 编号与独立读数程序的索引规则。这条 BOLE 路线的单轮是 0，三轮是 0、1、2。最终读数使用同一物化目录中的程序和控制文件。
- 历史报告字段可沿用旧名称。核实独立程序实际比较的长度、真实 HTTP token、各 rank 状态与运行终态，再判断旧结果能否用于 160 步。
