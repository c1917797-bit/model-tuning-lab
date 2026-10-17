# 昇腾论文迁移：本轮因果案例（范围受限）

本条目是经验知识，不是论文排行榜或技术成功声明。每项区分实际测量、源码确认和待验证假说。源证据索引见 EVIDENCE.json；不复制大型张量。所有验收门禁保持原值，任务精度≤1%不等于允许中间状态误差1%。

## GE：近似阶数不适用，不能归罪 Ascend

实测 GE005：真实 rank0 捕获矩阵，N3S8 的 NPU、CPU32、CPU64 相对 Frobenius 误差分别约 .003637068477/.003637039588/.003637068606，超过原 .002；NPU 对 CPU32 约2–3e−7。rank2约 .00124944通过。

结论：当前 N3S8 在该输入域不足；排除“唯一问题是NPU后台”的解释，不排除其他输入/集成错误，不推出整篇论文无价值。

鉴别：同一原始输入、同一公式在 CPU32/CPU64 重算，与独立 FP64 三角求逆比较；不能复用候选关键逻辑作为参考。下一次应改有理论动机的有限阶数/修正配置，不放宽门禁、不无限搜索。本轮预注册 N3S11/N3S15，四rank CPU32/64 共16行均通过（GE007），但CPU筛选不代表NPU或整模型收益。

反例：仅 rank2 或无NaN通过不能放行；N3S11九次Matmul不意味着端到端更快。GE008真实四rank×三重复×三tile矩阵与bitwise通过，但仍缺独立恢复消费者/完整GDN/配对性能和任务精度。

## DeltaLog：输出正确不代表持久状态正确

实测原v9第二个B1轨迹第54次更新：candidate状态误差 .291826879，独立CPU64对native约1.10e−7；只有共享keyhead0的heads0–2异常，其余约6e−8；末K日志与当前key最大差 .375，U日志约3–4e−8正确，当前输出接近参考。

结论：该候选持久K日志写回存在实际异常，不能以当前输出小误差放行；不能据此判论文数学失败。独立重构排除了此次CPU-first参考重构误判。

源码确认：StoreKLog将VECIN队列的MTE2搬运结果直接给MTE3写回，队列还复用于旧log读取。实际CANN9.1 TQueBind<VECIN,VECOUT>实现建立MTE2→MTE3和MTE3→MTE2复用事件。这是具体适配缺口。

假说：缺失DMA依赖导致旧K缓冲写回；旧a369二进制与当前源码HEAD关系未证实，所以不能宣称源码审阅已经证明旧二进制唯一根因。DCCI风险是另一个独立假说，不可用增加延迟掩盖DMA问题。

鉴别：同工具链冻结 fresh baseline/KDMA-only 两份源/库，独立命名opt-in，保持数学、输入、阈值和host stream一致。完整006编译成功只证明构建可用。pair007先54→160 B1保存每步input/state/K/U/metadata/pointers，独立CPU64重新消费；再按依赖进入graph/B16/长链/mixed，全模型门禁不能省略。

反例：一次160步append通过不覆盖slot状态路径；a369历史失败被fresh baseline复现与否均需报告。只修DCCI后偶然通过不能建立KDMA因果。

## 构建：头文件找不到可能是路径发现失败

实测 KDMA004 configure未停止，但torch_npu路径发现子进程因libascend_hal.so缺失导入失败，变量为空，compile argv出现-I/include，最终NPUStream.h找不到。

结论：是构建配置的失败传播/包路径发现缺陷，不是证明实际SDK缺头文件或算子数值失败。修为不执行包的find_spec定位、验证include/lib存在、检查子进程返回码和非空值；fresh baseline/KDMA各臂相同修改。

反例：给编译容器挂NPU设备来让import“碰巧成功”不是必要修复；baseline编译成功但owner中断的partial005产物不能冒充完整双臂构建RESULT。

## 资源保护：不干扰0–3不等于外部PID永远不变

实测 GE008矩阵成功、owner因外部0–3静态PID身份变化在cleanup失败；原owner保持FAILED。新独立释放审计确认原CID停止/Pid0，再用CPU-only recovery原消费者消费保存raw，不重跑NPU、不改旧owner。

实测 KDMA005外部PID两次同start_ticks、stateZ、cmdline空、cgroup根，旧observer误拒绝；不是PID复用证明。新observer只在freshSMI不列PID、复采同startZ或全missing时确认外部终止；权限错误、仍SMI列出、复用、ownedPID/CID/祖先/FD越界仍拒绝。

鉴别：持续保存raw SMI/进程证据再判定。针对外部退出/加入、owned越界、PID复用、权限错误和Z仍SMI列出做负向回归。不能将Z的零RSS当资源充分依据，也不能凭一次快照宣称30分钟无空档。

## MXR056：设备关联尚未闭合，不编故事

目前只收到MAIN定位摘要：Docker设备6→0、guestPID7/start10234921/canary通过，末SMI物理5 PID1120558、物理6无PID。原始完整Ref尚待MAIN交付。

状态：未测/未闭合归因；logical mapping、物理ID关联和PID归属都需鉴别，不能写成“已证实argv错误”或宣称PID1120558是owned。需要exactCID Dockerinspect/top、namespace PID链、start_ticks/cgroup/argv和同期物理SMI关联；禁止为继续运行放松物理证明。

## 回归复用方法

新增：[10月17日真实入口与阶段契约](entrypoint-and-stage-contracts-20261017.md)。区分导入/清理、提前测试DAG缺陷与算法数值失败；记录实际172项提前检查通过，同时保留最终完整174项门禁。

先运行 verify_cases.py --evidence-root 真实本地交接目录 --execute，验证证据字节及限定结论的可机读反例；这只审计保存证据，不是重跑数值。实际CPU/NPU重放使用各已封存owned包的原独立消费者和fresh结果目录，保持权威时钟、源码哈希和资源预算。最新失败不能覆盖历史失败，新的成功不能自动升级到整模型落地。

## 10月15日后继：真实绑定与单因子反例

[运行时绑定、观测顺序、归约反例与任务shape覆盖](runtime-binding-and-single-factor-evidence-20261015.md)：保留实际失败与未知归因，禁止由启动或组件证据升级整模型结论。
