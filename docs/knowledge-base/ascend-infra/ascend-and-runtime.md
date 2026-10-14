# Ascend硬件、算子与服务运行时

## H1. 从节省对象到映射方案

**适用**：GPU官方实现不能直接移植、算子融合、IO优化。

不要逐行翻译CUDA/Triton。先写数据依赖和字节/FLOP/通信账本，再映射GM(HBM)、UB、L1及Cube相关buffer，选择Vector/Cube/Scalar工作。DMA与计算有独立流水；单条搬运正确不保证整体依赖正确。[CANN9.1同步概览](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_synchronization_capability_overview.md)。实际本机SDK header/compiler/SoC限制优先于其他版本示例。

优先复用 vLLM-Ascend 和 [CANN/ops-transformer](https://gitcode.com/cann/ops-transformer) 对应数学/形状的实现；审计dtype/layout/stride/head/tail/alias/workspace，而非函数名匹配。cannbot可以辅助生成/构建，但生成物仍需完整review、独立NPU验证和实际装载证据；工具不保证算法忠实或正确。记录上游commit、许可证、局部差异、产物hash；不修改原始参考仓库/镜像。

## H2. DMA、队列与缓冲生命周期

**工程推导**：GM→UB→GM 的copy-only路径也有“读已完成，才能写”“写已完成，才能复用buffer”的前后依赖。将GM输入队列当作输出队列、过早FreeTensor或复用UB可能留下有限但错误的数据。`TQueBind<VECIN,VECOUT>`是可研究路径，不是所有kernel的万能修复；必须核实本机CANN9.1精确队列语义。[官方TQueBind说明（8.0，跨版本概念参考）](https://www.hiascend.com/doc_center/source/en/canncommercial/800/apiref/ascendcopapi/atlasascendc_api_07_0148.html)。

**鉴别实验**：保存copy前/后每个head和slot的原字节；用完全不改数学的独立copy-only控制，比较稳定错误是否集中在DMA位置；构建baseline/fix双产物，保持输入/seed/形状/数学不变。若日志K错误而U/decay正确，支持局部搬运假说，但不足以证明是哪条指令。修后完整state、output、多步、槽位退出重用和graph仍需通过。

尾部、对齐和stride是每个kernel的ABI，而不是全Ascend固定规则。DRRQR旧非16对齐Dk失效是特定原生CopyOutState padding问题；不能推广为所有算子只能16对齐，也不能放松门禁复活旧数据。

异步host调用要证明提交/读/写/释放的happens-before关系。Python变量还存在、record_event成功、没有NaN都不能证明NPU访问期间storage仍安全。正确策略可能是同stream排序、event wait、持有buffer到完成或图固定arena；正式计时不能靠每步全局synchronize获得“稳定”再声称正常性能。

## R1. 真实worker接入和薄适配

vLLM采用entry_points发现插件，有general/platform等不同组；多进程须各自加载。[官方插件文档](https://docs.vllm.ai/en/latest/design/plugin_system/)。最新文档不是v0.23全部私有接口保证；必须审计安装版本。前端打印ON、import成功或torch schema存在，不能证明四个worker实际调用候选。

交付分三层：算法核心（数学不变量和独立参考）；版本adapter（metadata/parser/operator签名）；注册和能力探测（默认OFF、显式opt-in、幂等安装、fail-closed未知ABI、可撤销）。不要猴补整个上游平台，也不要silent fallback后宣传加速。

实际证据：所有rank的loaded module realpath/hash、plugin入口、operator schema、实际映射opapi/binary及hash、按layer/phase的dispatch计数。短诊断允许保存输入/输出；正式计时移除诊断新增的`.cpu()`/`.item()`、state dumps和强制sync。候选算法必需的传输/同步不能删掉，须保留并计入候选开销；不强加给dense来制造公平。用计时外的worker快照统计测量区间增量。共同controller/client成本对dense/candidate一致。

## R2. 缓存、调度和图是算法的一部分

cache的逻辑状态至少含请求身份、slot、token position、dtype/layout、layer、压缩/flush参数、图/metadata epoch；分配/复用协议须与语义一致。arena view可节省分配不等于vLLM cache manager已集成。层间不同Dk需处理grouping、prefix identity、scheduler和graph key；不能只让native operator接受view就宣称完成异构缓存。

测试包含：batch变化、请求加入退出、chunk tail、非零初态、共享前缀命中/不命中、flush边界、slot复用、未选slot守恒。prefix-hit要恢复完整逻辑状态（含延迟日志、conv、decay/position），不是只恢复一个state tensor。

graph捕获固定地址和执行依赖；真实tensor可能是inference tensor，没有可用version counter。用明确metadata producer epoch/来源/生命周期协议，不以`id()`或地址一样推导内容没变。graph replay需验证输入更新、indices、state持久化、alias、跨batch key和释放。[vLLM graph设计](https://docs.vllm.ai/en/latest/design/cuda_graphs/)仅为接口背景；Ascend NPUGraph和本轮实现需另证。

## R3. TP、通信和设备身份证明

TP将权重/head/state分到rank，收益可能被allReduce、launch或同步抵消。global heads、local heads、HCCL group、PCP/DCP group不等价；一个world-size1测试不能代替TP4服务。异步collective需在使用输出前完成；改变层计算会改变通信重叠，应看关键路径。

容器逻辑0不是物理0；设备节点映射、可见环境、runtime逻辑枚举、宿主实际PID/start/cgroup/NSpid、NPU进程/HBM必须形成一致证据链。PID标题可能随worker生命周期改变，不能单凭旧argv或新昵称停止任务；也不能把仅映射设备当成占卡。身份门禁失败先保留每个predicate的原始证明，再做归因，不能只留下合并的异常字符串。

资源调度是多资源问题：普通RAM、HugeTLB、CPU cpuset/quota、disk、HBM分别入账。独立单卡任务可并行但需要ONE合并预算和合格controller；正式TP4配对独占。agent完成是提交READY候选，MAIN审阅/准入后才上卡。不要为了“满卡”启动无用负载，也不要拿单快照推算整30分钟无空档。
