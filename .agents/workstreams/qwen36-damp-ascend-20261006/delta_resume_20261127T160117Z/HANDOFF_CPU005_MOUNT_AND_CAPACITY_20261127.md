# DeltaLog · CPU005 挂载与预算交接

本轮截至 2026-11-27 17:41 UTC 已将 Qwen3.6-27B 的 DeltaLog 源码绑定到物理 2 卡配置。CPU005 在容器启动前退出。当前停在 CPU 控制阶段，下一项是用修复后的接入代码通过控制验证，再做物理 2 卡的 16 步数值验证。NPU 数值、整模型吞吐、TTFT、TPOT 及任务精度均未测。窗口截止 2026-11-29 16:01:17 UTC。[人工授权](WINDOW_AUTHORIZATION_20261127.json)

## 本轮实证

| 阶段 | 结果与证据 |
| --- | --- |
| 输入恢复 | 两个旧实验目录恢复只读挂载，484 个文件共 6,630,878,800 B 哈希匹配。[恢复回执](restore_035r2_r4_readonly_after_boot_20261127_v1/RESULT.json) |
| 源码绑定 | 014、015 两次真实采集分别绑定 R4、R5，绑定均退出 0。R5 的运行时校验回执也已读回。[014 采集](entry_prepare/native_capture_card2_v5/RESULT.json) · [R4 绑定](entry_prepare/native_bind_card2/RESULT.json) · [015 采集](entry_prepare/native_capture_card2_r5/RESULT.json) · [R5 绑定](entry_prepare/native_bind_card2_r5/RESULT.json) · [R5 运行时校验](entry_prepare/runtime_inverse_r5/S4_RUNTIME_INVERSE_LOCAL_PUBLICATION_RESULT.json) |
| CPU005 执行 | 在账本第 3 代写入整笔 1 GiB 预约后创建容器。39 对挂载应只有输出目录可写，实际 15 对可写。原检查拒绝启动，外层退出 3。观察时容器处于 `created`、PID 为 0，清理未确认。保留 6 个文件共 62,109 B。[原执行归因](EXECUTION_DELTA_CPU005_CREATED_MOUNT_MODES_BLOCKED_20261127.json) · [外层终态](entry_prepare/cpu005_main_owner_v3/TERMINAL.json) |
| 接入修复 | 两处赋值把字符串 `ro` 传给需要布尔值的可写标志。修复候选在相同 39 对路径上生成 38 只读、1 可写。原检查拒绝真实失败配置，并接受修正后的配置。修复后的真容器尚待验证。[原检查与候选对照](delta_source_prepare/r6_mount_contract_005_source_prepare/R5_CREATED_MOUNT_DEFECT_AND_CANDIDATE_CHECK.json) |

## 预算与接续

按原生扫描和已批准的 CPU003/004 关闭回执，保留 CPU005 全额时当前承诺为 1,074,725,386 B。新的 CPU 控制需要 1 GiB，N16 需要 33 GiB，其中 RAW 上限 32 GiB。存储协议登记的数据承诺为 34 GiB，原生写前实耗硬上限为 34 GiB 加 1 MiB。两项均执行时，计入新账本前至少超出硬上限 1,073,676,810 B。按当前格式估算两代新账本合计另需 6,339 B。2 MiB 控制元数据另行计量。[实际账本](../dual_resume_20261030T115104Z/delta_prepare/runtime_storage/STORAGE_LEDGER061.3.json) · [存储协议](delta_prepare/CURRENT_D_STORAGE_SCOPE_CARD2.json) · [控制元数据额度](delta_prepare/STRICT_CONTROL_METADATA_CURRENT_WINDOW_CARD2.json)

维持 CPU005 预约与原失败证据。待用户决定数据额度后，核对下一次运行的真实源码、工厂、编号、输出目录和剩余额度。CPU 控制实际成功、原容器终态与资源释放、独立资格结果齐全后，MAIN 再核物理 2 卡并提交 N16。R5 后继源码记录了 CPU005 的固定输入，若启用新编号，须绑定对应真实回执。[原后继的适用范围](entry_prepare/N16_R5_SUCCESSOR_SOURCE_ONLY_20261127.json)

## 维护经验

- 挂载检查应比较真实创建配置中每一对源、目标和可写布尔值。发生差异时先修生成参数的调用方，复用原检查做针对性回归。
- 在下一次 CPU 控制前，同时核算该次与紧随其后的 N16 预约、未跟踪文件和下一代账本。容器未启动时，已写入账本的预约仍须计入。
