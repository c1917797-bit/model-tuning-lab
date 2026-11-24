# Paper-to-Ascend：证据复用与接入失败经验（2026-11-24）

适用于 BOLE / DeltaLog 连续恢复、报告修复、当前源码准入与上卡排程。下列成功均为历史限定范围；本文件不是新的算法、模型或性能 PASS。

## 已验证经验

| 证据与结果 | 可复用的做法 | 必须补齐的下一门 |
| --- | --- | --- |
| BOLE真实NPU执行16次verify与16次commit；修复后的独立消费者128/128通过，58份原始文件哈希不变 | 数学未改且输入/输出完整时，修复判定器并重判原数据，保留旧FAIL | 真实模型调用、请求生命周期、长程及配对性能 |
| 原BOLE消费者128个内层指标通过但外层失败；上下文把checks建成list，却按字符串索引 | 验证完整初始化、返回值形状、调用对象与错误路径；数学AST相同不足以证明接线正确 | 经完整实际消费者复核后才更新阶段 |
| DeltaLog原生capture/bind完成；bind exit0、5.753秒，CPU/NPU未执行、账本未改 | 使用原生生成产物及真实消费者判定阶段；prepared_only=false或遗留NOT_BOUND标签都不能单独说明READY | 合法当前控制证据、设备准入和真实数值结果 |
| CPU004 guest pass_gate=true，外层仍因postverify:AttributeError失败 | 保留guest有效证据和外层失败；按已证final_verify接收对象错误做最小修复 | 不能把旧owner改成当前released owner，需真实独立补判定及显式复用类型 |
| CPU004与V15的15项入口、oracle、consumer、ABI、构建及库字节一致，旧/新pin有效 | 复用未变化的软件证据，另验证授权和控制改动 | 此一致性不授予当前CPU数值资格或任何NPU资格 |
| 历史账本绑定旧scope，当前执行另有新AUTH | 分别核验历史不可变身份与当前执行权；修复角色误比较 | 不改历史账本、不贴新AUTH冒充旧任务的新执行 |

详细BOLE重判经过见 [state16经验](20261117-state16-rejudge.md)，此处不重复全部启动错误。

## 下一次执行时的决策规则

1. 每个准备节点只回答一个会阻止真实下游执行的问题，交付实际入口、输入/源码Ref、预算、唯一输出、独立判定与释放方式。未能给出下一真实消费者时，标记具体缺口。
2. 接线修改验证完整入口与实际容器环境，包括授权文件、目录、锁、只读挂载、真实调用对象和返回结构。复用已验证的owner构造器；不要因每次续跑重写控制框架。
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

这些哈希于11月24日独立只读核验。源码与RAW始终留在chicaihong01；没有新的NPU、整模型、正式性能或任务精度验收。
