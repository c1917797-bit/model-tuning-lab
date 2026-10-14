# 一手来源与版本边界

核查日期2026-10-14。以下是理解来源，不是本轮性能/任务验收。未来版本需重新核实；不能根据主分支函数证明当前image执行。

| ID | 一手来源 | 支持的用途 / 边界 |
| --- | --- | --- |
| S1 | [Gated Delta Networks v3](https://arxiv.org/html/2412.06464v3) | 递推、chunk/WY三角结构；非Qwen checkpoint运行证据 |
| S2 | [SSD/Mamba2](https://arxiv.org/abs/2405.21060) | SSM与attention代数联系；不保证GDN ABI相同 |
| S3 | [FlashAttention](https://arxiv.org/abs/2205.14135) / [FA2](https://arxiv.org/abs/2307.08691) | exact attention IO/并行路线；不外推GPU倍数到Ascend |
| S4 | [PagedAttention](https://arxiv.org/abs/2309.06180) | serving KV管理机制；不同于state压缩数学 |
| S5 | [稳定三角求逆](https://arxiv.org/abs/2605.21325) | MXR研究对象；官方实现溯源另绑定commit/许可证 |
| S6 | [Good Enough](https://arxiv.org/abs/2606.06034) | 量化GDN近似研究对象；FP32 NPU候选需单列差异 |
| S7 | [DeltaLog](https://arxiv.org/abs/2608.15533) | deferred recurrent state研究对象；构建成功不证明数值或E2E |
| S8 | [vLLM插件](https://docs.vllm.ai/en/latest/design/plugin_system/) / [graph设计](https://docs.vllm.ai/en/latest/design/cuda_graphs/) | 最新官方接口背景；私有接口/Ascend图按安装源码核验 |
| S9 | [vLLM-Ascend v0.23.0](https://github.com/vllm-project/vllm-ascend/tree/v0.23.0) | 发布源码参考；容器实际backport和loaded hashes优先 |
| S10 | [Ascend PyTorch](https://github.com/Ascend/pytorch) | torch_npu源码和官方迁移入口；pinned wheel/API另证 |
| S11 | [CANN/ops-transformer](https://gitcode.com/cann/ops-transformer) | 算子复用来源；并非不存在的Ascend GitHub同名仓库 |
| S12 | [CANN9.1流水同步](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/sync_control/intra_core_sync/intra_core_synchronization_capability_overview.md) | pipeline依赖背景；真实910B SDK编译/数值另证 |
| S13 | [CANN8.0 TQueBind](https://www.hiascend.com/doc_center/source/en/canncommercial/800/apiref/ascendcopapi/atlasascendc_api_07_0148.html) | 绑定队列概念；不能直接当CANN9.1 ABI保证 |
| S14 | [MegaGDN](https://github.com/huawei-csl/megagdn-pto) / [独立数值测试](https://github.com/huawei-csl/megagdn-pto/blob/main/tests/test_gdn_e2e.py) / [实际 hook](https://github.com/huawei-csl/megagdn-pto/blob/main/vllm_patch/install_hook.py) | GDN六阶段NPU、模型接入与参考方法；prefill不是固定1024整服务收益；安装脚本不能照搬修改原版runtime |
| S15 | [FLA GDN layer](https://github.com/fla-org/flash-linear-attention/blob/main/fla/layers/gated_deltanet.py) / [测试](https://github.com/fla-org/flash-linear-attention/blob/main/tests/ops/test_gdn.py) / [Ascend安装](https://github.com/fla-org/flash-linear-attention/blob/main/INSTALL.md#ascend-npu) | chunk/recurrent与完整状态接口；最新A2支持不证明image660已部署或全部serving资格 |
| S16 | [Mooncake论文](https://arxiv.org/abs/2407.00079) / [工程](https://github.com/kvcache-ai/Mooncake) / [Ascend后端](https://github.com/kvcache-ai/Mooncake/blob/main/docs/source/design/transfer-engine/ascend_direct_transport.md) / [910B异构](https://github.com/kvcache-ai/Mooncake/blob/main/docs/source/design/transfer-engine/heterogeneous_ascend.md) | 传输边界和缓存生命周期迁移；后端存在不等于原论文全部GPU收益在Ascend复现 |
| S17 | [TeaCache作者工程](https://github.com/ali-vilab/TeaCache) / [Ascend HunyuanVideo集成](https://gitcode.com/cann/cann-recipes-infer/blob/master/models/hunyuan-video/README.md) | 真实模型缓存接入、组合互斥、warmup/质量取舍；不能直接外推Qwen GDN |
| S18 | [CANN Qwen3.5-MoE实践](https://gitcode.com/cann/cann-recipes-infer/blob/master/models/qwen3_5/README.md) | 按芯片、算子、量化和软件版本限定支持；不是910B4/27B兼容或收益保证 |

## 已发现的知识错误与纠正

- `2406.02528`不是SSD/Mamba2论文；正确ID为2405.21060。查询核实后再引用，不靠记忆。
- 通用vLLM packed Triton decode存在，不能证明Ascend worker执行它；本轮image660 `gdn.py` SHA `d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816` 显示独立gating/l2norm/native recurrent路径。保存actual dispatch/trace后才作路径结论。
- 一份技能或旧交接称某任务已失败/停止，不是当前设备和算法结果；以实际原始证据和最新授权为准。

## 实测证据的使用

[案例索引](cases/EVIDENCE.json)保存小型Ref；原始inputs/state/logs留在受控cache，Git不保存大数据。验证器只核对引用身份和案例范围，不重算NPU、不证明论文成功。证据消失应报告不可审计，而不是伪造或悄悄引用不同输出。
