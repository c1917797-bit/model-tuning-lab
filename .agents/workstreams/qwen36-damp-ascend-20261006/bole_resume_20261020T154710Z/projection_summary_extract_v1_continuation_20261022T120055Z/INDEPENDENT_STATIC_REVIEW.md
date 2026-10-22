# Projection 摘要器独立静态审查

结论：**限定源码审查通过；没有真实诊断结果或任何准入结论。**

本审查只读本地稳定摘要器及 final reader 的对应接口，未运行摘要器 main、reader、远端命令、原15/6 controls或NPU。固定 source/audit Ref 与 MAIN 提供的本地索引相等；reader bytes/SHA与本地完整文件相等。未重新读取远端原件。

## 保留的解释边界

- 缺失、显式 null、显式 false 分开记录；未观测 stage 保留原因，不能当作相等。
- stage/joins 保留 shape、dtype、bytes、geometry；首哈希差异和首覆盖差异单列。形状不同的 hash 比较不能变成同一数值范围的差异。
- full131/projection hash 保留 producer witness 解释，数值幅度仅来自原已保留的 last8 BF16 slice。relL2 不是任务精度损失，也不引入阈值。
- 跨 TP rank 不要求相等；四路观测不齐时相等性保留 null。
- active、roles、calls、exceptions、reductions、五 runtime source 映射和 rank complete_ref 可追源。weight/bias metadata 不证明权重内容；alias/code SHA不独立 pin通信callee、HCCL或设备kernel。
- reader完整性 flags 明确为 saved_reader_flags。摘要器只验证诊断文件与自身的完整SHA/稳定身份；不重开嵌套证据，不接替独立reader。原12条limitations完整保留。
- 历史 full pair FAIL只引用固定历史Ref，明确未重开；不推翻或重跑该门禁。

## 执行边界

源码保留输入32MiB、输出256KiB、AS512MiB、CPU30秒和60秒显式时间检查；只新建排他输出，超限失败，不截断。静态审查未证明未来真实诊断输出一定能在上限内完成，也未读取任何本轮实际诊断。最终输出仍须由 MAIN 提供真实输入Ref并执行。

完整本地输入身份与逐项结论见 INDEPENDENT_STATIC_REVIEW.json。
