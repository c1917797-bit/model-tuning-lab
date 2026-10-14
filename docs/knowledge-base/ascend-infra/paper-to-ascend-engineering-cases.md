# 论文机制迁移到真实 Ascend：可复用工程经验

核查日期：2026-10-14。类型：外部工程案例与设计推导，不是本轮实验验收。

## 使用条件与证据边界

在选择迁移接口、复用已有实现、设计缓存生命周期、组合技术或排查适配失败时阅读。本页不替换实验合同、独立数值参考或实际设备证据，也不授予资源与系统修改权限。

证据标记：`来源事实`是论文、官方源码或项目文档公开内容；`工程推导`是据此提出的本项目设计要求；`待验证`是当前环境尚无实际结果。主分支链接是理解入口，不是不可变部署身份；执行前仍须冻结 commit、许可证、源码、依赖及加载 binary 的哈希。

“存在真实 Ascend 后端/模型集成”不等于“完整复现原论文全部收益”，更不等于本项目的 Qwen3.6-27B/910B4/v0.23、固定1024输出、三轮配对与最终任务精度已通过。别人和历史 HYPIC 的成果不能算本轮新成果。

## E1：MegaGDN / 稳定三角求逆——算法与硬件数据流一起迁移

来源事实：Huawei CSL 的 MegaGDN 项目为 Ascend 实现 chunk GDN 六阶段：`chunk_cumsum`、`scaled_dot_kkt`、`solve_tril`、`wy_fast`、`chunk_h`、`chunk_o`，并提供合并执行、vLLM 接入、prefill 和任务评测入口。NPU 测试用非零初始状态，比较独立 CPU 双精度参考的输出及最终状态。官方 README 报告约15% prefill加速；不能称其为固定1024输出的整服务吞吐收益。

环境边界：官方 patch 文档覆盖 vLLM0.18/0.19；prefill 图标明单卡 Atlas A2，kernel 图标明910B2。CANN8.5–9.0 在 A2/A3 的验证和 A5/CANN9.1 实验支持不能替代当前 v0.23/910B4 的实际资格。

不变量：保留 gated delta 递推、初始/最终状态、变长边界与数值稳定性。可适配：Cube/Vector 分工、分块、数据搬运、阶段融合和后端绑定。

实际接入细节：官方 `install_hook.py` 处理 worker 初始化以及静态导入引用，但会写已安装上游文件。本项目只借鉴调用绑定与初始化顺序，改用默认关闭、显式 opt-in 的插件；不能照搬它修改原版 runtime。

最小鉴别实验：证明每个实际 worker 到达候选；在真实局部 head/shape 下，对同一输入检查输出和完整状态；随后进行相关完整数值覆盖和 profiler/observer-off 整模型配对。没有 hit、回退未计数或只通过求逆矩阵，都不能判断整模型收益。

当前应用：MXR 必须通过实际 GDN 接入，而不是把求逆单算子 PASS 当部署；短序列、长 packed 输入和推理元数据资格分别记录。待验证：本项目整模型吞吐与任务精度。

来源：[官方工程](https://github.com/huawei-csl/megagdn-pto)、[NPU/CPU 数值测试](https://github.com/huawei-csl/megagdn-pto/blob/main/tests/test_gdn_e2e.py)、[真实安装接口](https://github.com/huawei-csl/megagdn-pto/blob/main/vllm_patch/install_hook.py)、[稳定三角求逆论文](https://arxiv.org/abs/2605.21325)。

## E2：FLA / Gated DeltaNet——语义不变，执行阶段与状态接口分开

来源事实：FLA 的 Gated DeltaNet layer 具有 chunk/recurrent 路径，并维护 recurrent state、卷积 state 与 offset；官方测试有朴素递归参考并检查输出及最终状态。最新 INSTALL 提供 Ascend `[npu]` 路径，文档列出在 A2 测试的 CANN9.1/torch2.9/torch_npu2.9.post6/triton-ascend3.2.2 栈。安装支持不是当前 image660、全部算子或 vLLM serving 资格。

不变量：同一递推、head映射、归一化、卷积历史、位置、请求与槽位归属。可适配：chunk/recurrent 调度、内核实现及缓存接口；不得因统一接口而抹去不同执行阶段的状态需求。

最小鉴别实验：非零初始状态的多步递推、真正 B1/B16、请求加入/退出、槽位复用和 inactive 状态；按实际使用的图模式另测回放。参考不能调用候选的关键状态恢复或更新函数。

当前应用：DeltaLog/DASC 不只验证单个状态矩阵；还要审计 conv state、位置与复制接口。测试本身也须符合当前算子的 flush/reset 契约。待验证：当前插件完整 runtime 生命周期与整模型接入。

来源：[作者论文](https://arxiv.org/abs/2412.06464)、[实际 layer](https://github.com/fla-org/flash-linear-attention/blob/main/fla/layers/gated_deltanet.py)、[独立测试](https://github.com/fla-org/flash-linear-attention/blob/main/tests/ops/test_gdn.py)、[Ascend 安装边界](https://github.com/fla-org/flash-linear-attention/blob/main/INSTALL.md#ascend-npu)。

## E3：Mooncake——保留系统机制，替换硬件传输边界

来源事实：Mooncake 的 KVCache-centric 分离服务工程公开 Ascend transport，并记录 vLLM-Ascend 的传输引擎及 KV pool 接入。Ascend Direct 基于 CANN ADXL/HIXL 等能力；设备初始化、内存注册、传输完成及释放都有显式接口。910B→GPU 的异构文档说明将小块聚合后流水传输；该路径当前文档仅支持 WRITE，不能推断 READ 也支持。

不变量：缓存对象身份、有效字节、传输顺序、完成通知、生命周期与失败恢复。可适配：传输后端、块聚合、对齐和异步流水；不必重写论文的全部调度机制。

最小鉴别实验：核对同一缓存对象的实际注册/发送/完成/消费/释放，验证全部字节与请求归属，再测完整路径开销。仅测 RDMA 带宽，或未等完成就消费，不能证明 serving 收益与正确性。

当前应用：缓存论文应复用经过身份核验的原生复制/传输 primitive，开发论文特有的生命周期边界；没有分离部署机会时，不强行把 Mooncake 当当前单实例加速候选。待验证：原论文 GPU 收益是否在某个具体 Ascend 系统复现。

来源：[论文](https://arxiv.org/abs/2407.00079)、[官方集成记录](https://github.com/kvcache-ai/Mooncake)、[Ascend Direct](https://github.com/kvcache-ai/Mooncake/blob/main/docs/source/design/transfer-engine/ascend_direct_transport.md)、[910B 异构适配](https://github.com/kvcache-ai/Mooncake/blob/main/docs/source/design/transfer-engine/heterogeneous_ascend.md)。

## E4：PagedAttention → vLLM-Ascend——迁移缓存管理到实际后端

来源事实：PagedAttention 论文一起实现分页 kernel、block manager、scheduler 和 worker 元数据传递。其消融报告分页 attention kernel 比 FasterTransformer 延迟高20–26%，但服务端到端更快。vLLM-Ascend 的后端实现接收 block table、slot mapping、序列长度，调用 NPU 分页 attention/FIA，并处理图捕获与参数更新。

不变量：逻辑块与物理块映射、所有合法读写者、共享块的写入隔离、请求退出与复用。可适配：算子接口、布局和图参数；不能只移植 attention 公式而遗漏管理链。

最小鉴别实验：审计实际 allocator→writer→metadata→reader→replay→release 全链；用同栈同输入控制测整服务。缓存容量/调度方法不能仅因单 kernel 较慢而淘汰，也不能把增加候选并发包装成同配置速度提升。

当前应用：复用当前框架已有分页机制，不再把它算新增收益；DeltaLog/DASC 需要证明自己的增量。待验证：本项目缓存候选的完整生命周期、物理分配变化与配对性能。

来源：[论文及消融§7.1](https://arxiv.org/pdf/2309.06180)、[Ascend 后端参考源码](https://github.com/vllm-project/vllm-ascend/blob/v0.23.0/vllm_ascend/attention/attention_v1.py)。参考 tag 不证明容器 backport/实际选中分支相同。

## E5：TeaCache / TaylorSeer → Ascend HunyuanVideo——组合需要真实接入设计

来源事实：CANN 的 HunyuanVideo 模型集成提供 Ascend 单/多卡完整生成入口，`CacheManager` 接入 TeaCache、TaylorSeer 等方法，并公开 warmup、阈值、跳算/重算、cutoff/offload 参数。文档明确稀疏 attention 与 DiT Cache 会替换相同 block forward，直接同时启用会覆盖，部分配置因此互斥。

不变量：方法规定的误差估计、重算时机、缓存更新、CFG 分支和时间步归属。可适配：缓存管理与后端计算；不能把 hook 覆盖当两个技术均生效。

最小鉴别实验：检查每种机制的实际 hit、状态更新及互斥行为，再作 D/A/B/A+B 同配置完整输出与质量比较。近似方法的任务质量是单独门禁，不能用中间差异阈值替代。

当前应用：学习显式组合设计，不把视频扩散缓存直接迁移到 Qwen GDN；组合 MXR/DeltaLog 时同样要检查 hook、状态、图键与 materialization 相互作用。待验证：该视频模型的质量与倍数在本项目未独立复跑，不借作 LLM 验收。

来源：[TeaCache 作者工程](https://github.com/ali-vilab/TeaCache)、[真实 Ascend 模型集成及组合约束](https://gitcode.com/cann/cann-recipes-infer/blob/master/models/hunyuan-video/README.md)。

## 可执行设计检查：学经验，不增加无效准备

| 触发问题 | 下一步必须改变什么 | 如何反证 |
| --- | --- | --- |
| 候选始终停在组件 | 从真实模型消费者倒推接口；准备完整调用、输入、原始输出和独立判定链；相关数值通过后尽早作插件短模型冒烟 | 明确尚缺 worker/生命周期/模型消费者，不能称 READY |
| 自研算子很多、模型没收益 | 先复用实际可用的开源 primitive，仅开发论文特有差异；记录包含拷贝/同步/回退的完整成本 | 相同组件但 full path 更慢，或实际 hit=0 |
| 准备/控制器反复失败 | 公共底座保持稳定，版本化最小接口修复；CPU/数值/模型分别按真实预算准入 | 实际 CLI/同镜像入口和生产者→消费者交接仍失败 |
| 怀疑论文数值错误 | 对照公式、独立参考、实际 native 与候选；先核验输入、dtype、flush/reset语义 | 参考或测试契约与源代码矛盾，则原判断未成立 |
| 单项不足10% | 保留合法小收益组件，明确组合接口，再测 D/A/B/A+B | hook覆盖、未生效、状态不一致或实际组合无增益 |

浮点重排不等于逐bit相同；无损复制、inactive/guard字节、身份与生命周期仍按其精确契约检查。不能将别人的浮点容差移植为本轮新阈值。能力差异也不等于论文无价值：例如 CANN Qwen3.5-MoE 文档对 ChunkGDR、量化和芯片分别设边界；A3/950结果不自动适用于910B4。[具体能力边界](https://gitcode.com/cann/cann-recipes-infer/blob/master/models/qwen3_5/README.md)

使用者每次提交一张设计卡：实际模型/阶段；论文不变量；可复用代码及不可变身份；必要适配；新增成本；独立判定；最小模型闭环；下一完整门禁；失败分类和固定预算。通过知识/文档检查不授予 NPU、E2E、任务精度或跨环境 PASS。

## 最小实作能力：学习后必须能做出的六个练习

1. 算法语义：按实际 state 布局手算一头两步 GDN，写独立 FP64 递推，解释 chunk/recurrent 等价条件。辨别数学改变、浮点舍入和状态归属错误。入口：[架构与数值](architecture-and-numerics.md)。
2. 硬件成本：画出一个候选的 Cube/Vector、GM/片上存储读写和同步关系；估算包含打包、搬运、同步和 materialization 的完整成本。实际 profiling 反证估算，不能按算子时间相加宣称吞吐。入口：[硬件与运行时](ascend-and-runtime.md)。
3. 请求状态：画出 prefill→decode→加入/退出→reset/reuse→copy/cache-hit→release 的状态机；注明每个 tensor 的 reader、writer、owner、slot/epoch 和实际启用的图模式。不能把客户端并发等同真实 batch。入口：[硬件与运行时](ascend-and-runtime.md)。
4. 独立正确性：构造非零初态、刷回边界、inactive、复用和变长的反例；证明参考不调用候选关键算法。先确认测试契约与实际算子一致，再解释首个失败。浮点输出和精确复制字节使用各自冻结的判定，任务1%不是tensor容差。
5. 端到端归因：写出相同栈/输入/并发/通用优化的 OFF/ON，解释 TTFT、TPOT、吞吐和任务质量为何不能互代。分别估计 prefill/decode 机会，能力或容量收益单独报告；组合方法必须实际测 D/A/B/A+B。入口：[性能与因果验证](performance-and-causal-validation.md)。
6. 工程闭环：从真实模型消费者倒推一个可执行迁移包，完整运行真实CLI、同镜像装载、实际worker、相关NPU门禁、整模型冒烟与后续配对。失败给出证据、分类、最小修改和可反证预测；不把修改报告或 test 数量当可用技术。入口：[实测因果案例](cases/CASES.md)。

学习优先顺序是1→3→4，随后2→5，最后把6实际做通；不是等读完知识库才上卡。相关准备与实际实验并行，留足最终性能和任务评测时间。知识背景提高判断力，不保证某篇一定有≥10%机会；本项目工程执行责任仍由维护者承担。
