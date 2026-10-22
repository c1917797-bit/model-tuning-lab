# Projection 内部观察器：本地最终源码审查

审查时间：2026-10-22T11:55:01Z。状态：**PASS_LOCAL_SOURCE_REVIEW_ONLY**。

本次完成最终 helper、父 observer 集成及 host 控件入口的本地源码审查。必要的16项 projection CPU 控件全部通过，容量计算通过。**没有执行远程操作、source freeze 或 NPU；不授予数值、多步状态、生命周期、ON/OFF配对、低观察开销路径、整模型性能或任务精度资格。**

## 本轮实际执行与证据

- 本轮重新执行 helper 的16项有针对性控件，退出0；真实 Python frame/trace 事件与 fake CPU tensor 用于控制验证，没有 Torch/NPU 导入或模型计算。
- 本轮执行 metadata capacity 计算，退出0。它明确标为 fabricated_bounds_only，不是NPU观测结果。
- 两个CPU子进程前后的17项审查输入完全一致。随后 MAIN 有意补齐 preparation 副本、evidence 和新 runner/README，本次最终审查另外登记19个最终文件Ref，不覆盖先前执行记录。
- 新四任务 host runner 的源码已经检查；**本地未调用这条远端路径固定的四任务入口，也未声称它已在host运行**。既有11+8项测试未在本次无意义地重复，原20项same-image控件保持独立且未被替代。

完整执行记录：[LOCAL_EXECUTION.json](sandbox:/workspace/scratch/e65c435145b1/projection_final_review_20261022T1150Z/LOCAL_EXECUTION.json)。完整最终来源与判定：[REVIEW.json](sandbox:/workspace/scratch/e65c435145b1/projection_final_review_20261022T1150Z/REVIEW.json)。父 observer 精确差异：[PARENT_DIFF.patch](sandbox:/workspace/scratch/e65c435145b1/projection_final_review_20261022T1150Z/PARENT_DIFF.patch)。

## 已核对的行为

1. **默认关闭。** 缺失、空或0的 `BOLE_NATIVE_PROJECTION_PROBE_ENABLE` 在接触owner前返回；开启必须是字面1和完全相同声明。模块只导入stdlib。
2. **真正的调用点身份。** 方法必须绑定实际对象，完整来源文件Ref、完整模块编译后code对象、receiver与module globals匹配。真实native作用域要求GDN0已返回、layer1尚未进入、131实际tokens、同一当前request和代际，以及原norm证据已产生而原projection证据尚未产生。
3. **原调用不变。** wrapper只安装到实际layer0投影实例，原bound forward恰调用一次并返回原对象。被记录的是实际输入、quant返回、原调用点前后的局部张量及原projection返回。
4. **分支诚实。** generic、Sequence inline-return、fused和no-reduce的CPU控制通过。融合分支不制造quant/local partial，不拆融合，不增加GEMM或collective；不可观测阶段明确absent。记录只能证明Python caller边界，通信callee与HCCL kernel未独立pin。
5. **所有权与恢复。** 既存trace/profile被保留并拒绝本次观察；运行中出现foreign trace也被保留并使本次失败。finally只移除自己的trace，部分安装失败回滚，失败粘滞。两代正确退休后恢复安装前instance forward属性的存在性和同一对象；foreign替换不会被覆盖。
6. **计费及闭包。** 新读取通过原owner._read/_finite，受2MiB单次、8MiB每代、16MiB总新增及原512MiB累计限制。有限性检查失败后已发生读取仍计入新增计数。新两份完整envelope进入原writer和retained_files，不建未计费目录、不增加raw。父级原148文件语义保留，新闭包150文件，COMPLETE索引149个前置Ref。

## 容量结果

| 项目 | 源级保守计算或fixture | 原/新增硬上限 |
|---|---:|---:|
| 全部文件 | 150，其中132 JSON、18 raw | 完整闭包150；索引149前置Ref |
| probe raw | 836,352 B | 原836,352 B，未增加 |
| probe metadata | 519,086 B | 原524,288 B；余5,202 B |
| D2H累计最坏量 | 531,997,248 B | 原536,870,912 B；余4,873,664 B |
| OTHER含原64KiB预留 | 3,088,982 B | 原3,145,728 B；余56,746 B |
| Sequence完整envelope fixture | 7,915 B | 新完整envelope硬上限8,192 B |

7,915字节是带六roles、五stage、64位地址、长Ref和一条异常的保守Sequence样例，**不能称为所有允许元数据组合的通用最大值**。代码在发布每份实际完整envelope前检查8192字节，超出会失败，不截字段。未来真实分支兼容性仍待真机核验。

## 最终本地准备状态

MAIN已补齐第五helper、16项测试、README及5份固定snapshot，最终19文件的完整Ref登记在REVIEW.json。新runner明确要求这些依赖，按旧probe11、integration8、新projection16、capacity四任务执行；保留每子进程30秒、总120秒、输入前后全Ref核对和独占输出。

| 关键文件 | bytes | SHA-256 |
|---|---:|---|
| projection_probe_v1.py | 30248 | `4c442d86077efcb64e0d7f845d77accabe9b310e844c88a2a9731b2c3b450765` |
| test_projection_probe_v1.py | 21696 | `c042973efc22e4505dcd852d9dbefbbcec4837931c7b6292b6e1f9711ab2a010` |
| 父boundary_probe_v1.py | 31338 | `14c69907adffb9ed5661f6ffd6023f85ab58730af69232b9a54a4ff6883e4bdf` |
| run_boundary_controls.py | 8050 | `ee5dc91dd568ed1f4c1b27ecfcec7f6081c4de33f34c8d2850194c1866e8eeb2` |
| PROJECTION_README.md | 12599 | `a78cacf68fa83fc9c3c99f78ef3183e195ca8a4c108e64efec84e61908031574` |

## 未完成事项及时间边界

本审查不证明远程新控件执行、MAIN review、冻结SOURCE/COMMANDS、独立新source audit、实时资源与上卡准入、真实NPU内部记录、独立150文件reader消费或最终目标已经完成。也没有重新核实远端当前空闲/运行/释放状态；历史快照不能代替实时检查。

硬截止保持 **2026-10-22 12:38:41 UTC**。原prepare和auditor要求剩余完整3780秒，当前时间已超过其最晚可用起点11:35:41 UTC；原phase3600秒及其中cleanup180秒没有缩短。当前只允许本地源码/证据收尾，不能把此审查当作新实验许可。后续真实实验需要可容纳原预算的新明确授权窗口与新的source/output身份，再依次补齐审计和真机门禁。

本次未发现所审固定源码中的阻断性实现问题；这项结论只适用于登记的字节及上述源码/CPU验证范围。所有资格字段保持false。
