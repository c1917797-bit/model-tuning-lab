# 实际启动失败：observer 作用范围与纯文本配置分支的限定审查

## 当前结论

本次失败发生在真实整模型服务启动的 **multimodal encoder memory profile**，尚未取得两代诊断请求或 projection 结果。日志显示 chip4/5 的 AI Core 异步异常，在视觉 `rot_pos_emb` 的 1 MiB H2D copy 暴露；它没有定位真正出错的算子。不能据此判为 BOLE 数值错误、量化错误、硬件故障或 observer 根因。旧配对 FAIL 也未解除。

本审查只读本地日志和源码，未操作主机、执行 CPU controls、上 NPU、修改模型或生成新门禁。当前 owner 的终止、cleanup 和设备释放未由本审查独立观察。

## 实际证据与异常边界

日志镜像包含完整 65,484 UTF-8 bytes / 428 行，内容 SHA256 为 `7ba30529f202fee7401103e1cc650ac3c7d2ee4b71df7536dc40b38d54743edf`。原始路径、镜像 Ref3、全部输入 Ref3 见 `REVIEW.json`。native 六文件的本地全文尺寸与 SHA 均重新核对，并匹配 MAIN 提供的同 CID/image 两次 docker-cp 读取记录；本审查没有独立执行远端读取。

13:38:18 日志宣布 encoder budget 16,384 tokens，profile 一个最大特征尺寸 image；13:38:22 的实际栈是 `determine_available_memory → model_runner.profile_run → gpu_model_runner.profile_run → embed_multimodal → visual → prepare_encoder_metadata → rot_pos_emb → pos_ids.to(device)`。TP0 / guest PID3259 / chip4 报 L0B MTE 同地址读写冲突；TP1 / guest PID3260 / chip5 报 L0A 同类冲突。重复打印和 EngineCore 传播不计为新的独立故障。日志明确警告异步栈可能不准确。

已读原生 `qwen3_vl.py` 说明 `visual.forward` 在此 copy 前已执行输入转移和 `patch_embed`，随后 `prepare_encoder_metadata` 先执行 `fast_pos_embed_interpolate` 再调用 `rot_pos_emb`。因此故障可能来自更早提交的工作；本证据不能选定 patch embedding、位置插值、rotary 或其某一个后端作为根因。视觉 block 循环位于 metadata 返回之后，本次 Python 栈尚未到达该循环。

upstream profile 的本次执行先 MM encoder，后 language `_dummy_run`；Ascend 外层在 `super().profile_run()` 前另有条件 MC2 warmup 和 EPLB warmup，不能把 upstream 的顺序扩大成“整个启动以来未运行任何 language kernel”。原生源码中的 profile context 把 `in_profile_run=is_profile` 传入。日志已有 readonly plog 警告，它只说明该日志通道可能不完整，并非 AI Core 根因证明。

## observer 是否可能在 MM profile 阶段介入

**安装可以早于 MM profile。** 保存的 worker 包装链先调用原 `NPUWorker.load_model`，随后发现真实 language inner model 并调用 `after_load → service_runner.install → BP.create → PP.install`。BP 创建时立即注册 hooks，PP 立即替换同一个 GDN0 `out_proj` 实例的 `forward`。故不能说 profile 时 observer 尚未安装。实际四 worker 的 `G0-INSTALL` 仍需单独读取，不能用源码推导代替实际安装证据。

**安装不等于激活。** BP 初值 `scope=False`，hooks 只绑定实际 language layer0 的 gated norm、out projection、post-attention norm 和 MLP。scope False 时 hook 直接返回 None，PP 包装直接调用原 bound method；两个构造器的新增工作为 Python source/identity/accounting 检查与注册，没有发现新增 tensor 传输或数学调用。真正 D2H/hash、projection trace 只会在真实 C1 请求、131 tokens、按序 GDN0 原 core 返回后启用。

保存的 `prefill_tail.core` 在 `ctx.in_profile_run=True` 时直接回原 core；无合格 prefill metadata 时也回原 core。新 `boundary_delta` 没有修改这些 guard，只把 BP enter/return 接在通过原 guard 的真实 prefill 区间。PP `sys.settrace` 仅位于 `_invoke` 且在 `_scope` 验证之后；没有全局类级视觉 hook。

因此已读源码不支持“visual.rot_pos_emb 直接进入新 projection observer”的解释，但也不能从 Python 异常栈缺少 helper 名称推出 observer 完全无影响。它可能已经安装；更早执行或时序影响没有进行实证隔离。本审查使用的辅助 worker_bootstrap 是保留旧时钟的输入快照，rendered service_runner/prefill_tail 是历史渲染文件，只用于未变函数体与 delta 的静态推导，**没有冒充当前远端完整 runtime Ref3**。

## 原生 language-model-only 分支

对本轮明确的纯文本 GSM8K、HumanEval、MMLU，`--language-model-only` 在任务语义上适合作为**新的、明确声明的共用配置分支**。这是条件性工程判断，不是已通过执行的修复。实际 native CLI 会转发此字段，`MultiModalConfig.get_limit_per_prompt` 对所有 modality 返回 0。其含义与 `--skip-mm-profiling` 不同：后者跳过测量但保留 MM 支持及潜在 activation/cache 内存责任。

六文件尚不足以证明 zero limits 最终怎样影响本模型的 budget、dummy-item 生成、视觉塔实例化和权重加载。最小后续源码闭包为 `multimodal/encoder_budget.py`、`multimodal/registry.py`、实际 `models/qwen3_5.py`、`models/interfaces.py`；如 `_mark_tower_model` 委托占位模块或 AutoWeightsLoader，再读对应 `models/utils.py`。必须区分“源码支持/配置声明为 0”“本次有效预算为 0”“真正启动执行跳过视觉 encoder”三种事实。

若采用该分支，dense/candidate 必须冻结同一配置、模型和 prompt 规则，完整重过原真实 NPU 数值、多步状态与生命周期门禁，再进入同配置配对性能。原 numeric 阈值不变；早先失败证据保留。不能把节省 MM 启动或改变 KV 预算当成候选技术 ≥10% 生成吞吐收益，也不能宣称修好了底层 MM kernel。

## 最少进一步实际证据

1. 控制器终态 RESULT、primary/secondary、原 cleanup/OWNED/inspect 链及终止后的 fresh 设备/真实进程/FD/container 释放检查。当前日志快照不能代表实时占卡状态。
2. 四 worker 的 `BOUNDARY-Rn/G0-INSTALL.json` 或准确缺失，以及是否存在任何 G1/G2/projection 文件的不可覆盖 inventory；必要时补读当前 source-bound worker bootstrap / service runner / prefill tail / entry 和 worker identity。
3. 已存在的 chip4/5 CANN/device 错误记录，用 PID、时间、stream/task/operator/kernel/address 绑定。readonly plog 缺失应写为证据缺口。本审查不提议原样重跑或启用 blocking 环境变量。
4. 原生 text-only budget/tower 源码闭包，随后才设计可审的新配置；未获真实新启动证据前不声称分支已经生效。

本结果只完成失败边界定位和静态适用性审查，所有 numeric/state/lifecycle/paired/performance/accuracy 资格与准入标志均为 false。
