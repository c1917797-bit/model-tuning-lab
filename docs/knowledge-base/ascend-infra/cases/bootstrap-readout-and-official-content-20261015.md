# 2026-10-15：真实启动链与参考语义的反例

本条是当前 Qwen3.6/image660 的实测经验，不是论文成功、整模型性能或任务精度结论。详细 Ref 和未完成项见工作流 `NEW48H_BOOTSTRAP_READOUT_AND_OFFICIAL_CONTENT_20261015.json`；大数据与原始日志留在实验目录。

## 正常框架初始化也是算子契约

GE060 实际上卡后，先导入 device_op 导致 ops.__init__→MoE selector→部分初始化 DeviceOperator 的循环导入。GE061 改为真实 package-first 后导入通过，但 native l2norm 在首个数值样本前又因缺 init_device_properties_triton 失败。这两次是 probe 接入缺陷，不是论文算法失败。

下次必须从真实 worker 的初始化链倒推独立 probe：平台/原生包装载、设备选择、动态 Triton device-properties 初始化、真实通信组及 forward context。不得 hardcode core 数、fake sys.modules 或删原生检查。无卡同镜像的软件测试只证明软件控制；不能宣称实际 native imports 或完整模型启动已通过。相关 bootstrap 变更用新实验保存完整初始化追踪，原失败不覆盖。

## 独立参考与原生实现都要审计

DeltaLog004 B16 第4步仍未过原 .00303 输出门禁。005 真正消费保存帧发现两臂输出/状态完全相同；最大差位于 BF16 舍入中点附近，且该点候选比原生更接近独立 FP64。不同 CPU 累加树可改变舍入，不能据此断言实际 CANN 指令顺序已被证明。

可迁移规则：小 state 误差不自动证明 output 正确；native/candidate 不同也不自动证明候选数学错误。需保存逐点/ULP/独立参考/状态与读出归因。CPU 重投影是诊断，不是 NPU 正确性资格。保留原门禁，不因一个更准的点、单ULP或任务1%容忍而放行；下一次只测试有新证据支持的单因素修复。

## 官方输入协议不能用自写解析器替代

旧 MMLU 字面 CSV 审计在一条选项 `None` 上失败。实际作者 pandas 默认解析得到 `nan`，与冻结输入一致。新004用同镜像 pandas3.0.5、原作者 formatter 及全部 GSM8K1319/HumanEval164/MMLU14042 内容独立核对成功；未改输入、未 fillna、未重分词。这修复的是参考/测试缺陷，不能说模型精度已通过。

同时区分评测形式：GSM8K/HumanEval 是关闭思考、上限2048、正常EOS生成；MMLU 当前作者协议为下一token四选项 likelihood，max1。两者不可混称相同生成长度，也不能把输入审计 PASS 写成任务分数。

## 预算更新不是放宽旧门禁

64GiB guest cap 加 reserve 导致73GiB旧整模型准入线，而普通可用内存约59–60GiB。真实15个 safetensors 分片与 lazy tensor loader 说明64GiB并非已证明的必要CPU驻留量；这只支持准备新的更小 cgroup 硬上限实验，不证明48GiB足够。原门禁不改；新实验必须同步 create/inspect/准入、保留主机reserve、记录真实容器peak/OOM/退出，并将OOM限制在自身。不得把CLI RSS当guest峰值、重复释放已用完的大页预算或干扰0–3。

## 接下来必须接上完整模型

当前真实 trace 只有阶段诊断聚合，不能拿 kernel sum 当关键路径或固定1024的整请求权重。相关数值通过后立即用现有同配置整模型 pair 筛当前实现；完整三轮与最终任务评测仍是成功必要条件。每个失败按环境/调度、适配实现、参考测试、方法配置限制或未知归因，只有有效证据才能决定路线去留。
