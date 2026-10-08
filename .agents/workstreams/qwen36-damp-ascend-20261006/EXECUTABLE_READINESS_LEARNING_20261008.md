# Executable readiness and controller lessons — 2026-10-08

## 本轮结论

本记录是新增成功/失败经验，不是论文验收报告。没有新的完整 NPU 数值、
端到端吞吐或最终任务精度 PASS。HYPIC 仍是历史成功样板，不能算本轮成果。
原失败、源文件和论文/组合截止时间不回改；只有新的验证可以推进对应阶段。

## 实际成功与失败

| 实际证据 | 结果 | 允许得出的结论 |
| --- | --- | --- |
| SparsePrefix v8 同镜像软件检查 | 已通过；实际 CPU 权威保留 | 软件与源闭包有效，不是 TP4 模型通过 |
| MAIN134d，物理4–7 | failed；四卡 canary 通过后，被我方 RSS observer 中断 | 当前实现/控制阶段失败，不能判论文无效或获益 |
| 独立 MAIN1352 / 原 cleanup | exact CID stopped/retained，owned children reaped | 可重新检查资源；不能伪造原 operation terminal |
| MAIN1367，ANN v1 | 15 tests，1 error；dataclass 模块查询失败 | 真实入口缺陷，不是 NPU 或算法精度失败 |
| MAIN136f，v9 tree core | 14 项真实短生命进程及负例通过 | 核心修复的软件证据；完整 host167/同镜像/NPU 尚缺 |
| MAIN1373，ANN v2 | 25 tests、43-source closure、两条 default-OFF 入口通过 | 模块注册修复和源码检查通过；canonical/native/model 尚缺 |

134d 原错误为 `ValueError('unknown vanished process is not zero RSS')`。
采样峰值为130076672 bytes（约124 MiB），限额512 MiB；不能据此界定未观测峰值。
原记录没有被拒绝样本的确切 PID/系统调用，不能武断认定是某个 SMI 或 Docker
子进程。32条稳定命令记录与原 exception 已保留；停止来自本轮失败清理，
不是算法正常结束。

## 沉淀到已有 skills 的规则

1. 准备就绪必须是实际可执行，而非“Agent 已写好”。完整真实 CLI、依赖闭包、
   同镜像挂载、报告 consumer 和资源预算要有证据；UNRUN 保持待验证。
   串行上卡时应维护已验证的接续任务，不能用 Agent 数量替代就绪队列。
2. RSS 的枚举与读取之间有进程生命周期竞争。登记 actual owned Popen 与
   PID/start/parent，再采样；未知、活体失读、权限和 PID reuse 必须硬拒绝。
   第一次拒绝保存原 PID/操作/errno。真实进程测试不能被 mock 测试替代，
   核心测试也不能替代完整控制入口。
3. 官方 AST 原字节/结构一致不等于参考程序能运行。共同 globals 覆写
   ModuleType 的 `__name__` 后，会破坏已注册的 `sys.modules` 对应关系。
   修复模块装载边界，不删作者 dataclass，不改算法 AST。
4. 数值 oracle 必须忠实于作者的离散 selector dtype/顺序。BF16 top-k 与
   FP64 重选可能选择不同支持集；各自 q/rq 独立执行原作者 selector，再用
   原始完整 q/K/V 重算 FP64 输出、alpha/均值。FP64 重选保留为诊断，
   不共享 candidate selector、不取消 non-tie/输出/多步反馈检查。
5. 失败权威、成功子阶段和清理权威分别记录。失去 operation registry 后，
   先核实 exact output/CID/PID，不能重启未知工作或补造 terminal。
   无新的机制证据不原样重跑，控制问题不能升级为 paper-wide no-go。

对应参考文件：
[controller observation](../../skills/ascend-inference-tuning-loop/references/controller-observation-and-quiescent-results.md)、
[portfolio admission](../../skills/ascend-inference-tuning-loop/references/portfolio-preparation-and-serial-admission.md)、
[ranking and snapshots](../../skills/ascend-inference-tuning-loop/references/ranking-and-packed-snapshots.md)。

## 当前交接与未完成项

- v9 完整167软件、同镜像 Devices[]、真实 TP4/all48 GDN/conv/六类请求生命周期待验证。
- ANN v2 private25通过；canonical整合、同镜像算术、完整128/20480 NPU、
  长上下文/TP4/service接入和配对性能仍待验证。
- SKVQ loader/capture 为准备阶段，不能叫量化部署或作者完整算法落地。
- 当前没有新增“至少10%吞吐 + 最终任务精度”合格技术。
- 继续训练/蒸馏免除的算法相关适配，复用开源算子，插件显式 opt-in；
  不转向无关算子调优或 dummy load。
- 用户最新任务精度容忍需同时报告百分点与相对百分比，不用作 tensor 门限。
- 四卡闲置应报告实际准备/控制阻塞；正常切换开销不同于长期未就绪空档。
- 固定 portfolio Oct9 11:17:31Z 与既有 paper cutoffs 不重置；
  32GiB HugeTLB 权限已 SPENT，不再释放，不干扰0–3。
- 当前工作分支 `work/qwen36-damp-ascend-20261006`，基准 HEAD `f815419f910b41dba45a37fe1d721e359f2759cd`。
  仅在该分支正常推送，不 main/force；认证、推送成功需独立证明。

## 可复现原件

精确 path/bytes/SHA、actual operation IDs、coverage 和阶段界限在
[结构化证据](EXECUTABLE_READINESS_LEARNING_20261008.json) 中。
大原始工具输出仍在 `/cache/cch/qwen36-paper-preparation-20261007/`，不入 Git。
请核对 source 与 terminal，不能把本记录中的计划当执行证据。
