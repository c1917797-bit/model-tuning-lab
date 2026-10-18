# 本轮工作状态：BOLE / DeltaLog 论文穿刺

日期：2026-10-18。主机现场状态核对于 19:07:12 UTC（22:07:12，Europe/Moscow），operation `exec-000000000000171c`。随后仅执行了源码归档和 R38 准备器只读预演 `exec-000000000000171f`。

**两篇论文均尚未达到最终验收。** 本轮有两项实际 BOLE CPU 诊断结果、一个真实 DeltaLog early 失败与已释放证据，以及可供下轮审阅的固定源码。新 BOLE FIA 重放、DeltaLog 四 rank 模型、匹配性能和任务准确率仍待完成。

## BOLE：已完成的实验与当前停止点

- `16f0`：同镜像 Devices=[] CPU 诊断完成，4 / 4 控制通过。核对 4 个 rank 的 688,128 个输出元素，原失败为 tree 38 点、native 自身输入 60 点。tree 的原失败仍覆盖 22 / 64 个 rank-layer case。全部 98 个失败点均有满足原误差门的最近 BF16 值；CPU64 与补偿 FP64 参考的差异不足以解释失败。该结果排除了最终表示能力不足和这两种参考累加方式的差异，未证明真实内核根因。
- `16fb`：同镜像 CPU 诊断完成，12 / 12 控制通过。固定 3 个各含 1,536 元素的 case，“完整 softmax 概率额外舍入为 BF16”这一具体模型在三个 case 中都降低了与原输出的逐位一致数、增大了 L2 误差，未复现两个原失败点。其他中间计算策略仍未排除。
- 两个实际诊断容器均已停止、保留且验证释放。
- 新 FIA 重放包的 44 项本地控制通过；`171b` 已完成 53 个引用的 source binding，实际 manifest 为 12,699 bytes / `535848eb04738414f099c2d261ba372611c080577fb06c3e0ebcad01b702c5e1`。
- 随后的 source-audit 工具因目录变更在执行前拒绝，没有 operationId。CPU owner、NPU owner及新实验输出目录创建都未发出。此事不是 CPU 测试失败，也不是自动安全审批拒绝。
- 新探针要求原完整 tree 4,608 / native 1,536 个 BF16 输出元素先全部逐位复现，再分别只改变 `inner_precise` 的 2→0 / 0→2。任一 baseline 不符即禁止全部变体。原数值门、输入和失败保持。

具体统计与精确引用见 [BOLE_FINDINGS.md](BOLE_FINDINGS.md) 和 [BOLE_EVIDENCE.json](BOLE_EVIDENCE.json)。

## DeltaLog：工程修复与未完成的验证

- R36 正式 binder `16f5` 被原存储门拒绝。已定位：完整 closed2 校验和历史承诺折减发生在原 prior-policy 核算之后。新 helper 先验证原封存证据，再按原规则核算；保留 80 GiB 承诺上限、100 GiB free 门、完整 32 GiB 新预留和原 closed15 检查。基于此前 scan 的可行性计算约为 78.746 GiB，尚无实际新 binder 通过。
- R37 `1711` 通过 281 个 own_files 的源码检查，`1712` 完成 early source binding。`1716` 实际运行在 `recover.py` 仍引用 R36 根路径时退出；payload26 与软件 suite 均未到达。容器已停止且验证释放。源码检查数量不是测试通过数量。
- R38 已修正实际 child 的完整根路径，并级联重算 owner、模板、镜像和命令引用。20 项本地准备与传输控制通过。`171f` 从归档准备器进行实际只读预演，完整拼装内容的 193 份 Python 源码通过语法与活动身份检查，残留旧活动身份集合为空。full255 / early253 / payload26 保持。
- `171f` 没有创建新 R38 model / early 执行树，也没有创建 bound source、容器或实验结果。其模板 Ref 是内存计划身份，不能作为已经落地的来源消费。完整只读 receipt 保存在 [R38_READONLY_PREPARATION.json](R38_READONLY_PREPARATION.json)。
- 独立 geometry consumer 修复及 48 项纯 CPU 控制、3 个 R34 元数据 fixture 已保留在 `source/deltalog_consumer/`。该 consumer 仍固定 R36 身份；它没有消费本轮新的 all4 原始模型证据，也不能直接接收 R38 身份。

具体停止点与引用见 [DELTA_FINDINGS.md](DELTA_FINDINGS.md) 和 [DELTA_EVIDENCE.json](DELTA_EVIDENCE.json)。

## 资源、时间与续跑条件

现场 `171c` 确认 BOLE 新实验输出根不存在、所查 `qwen36.owner` 与 `model-tuning-lab.owner` 运行列表均为空。该结论只覆盖本轮所查 owner，没有将其外推为整机无其他任务。

原授权文件 `RENEW24H_AUTHORITY_20261017_084320.json` 的截止为 **2026-10-18 08:43:20 UTC / 11:43:20 Moscow**，当前已经过期。原模型 whole3600、独立 FIA whole900 与 CPU whole1000 均未缩短或延期。

下一轮先取得新的明确执行窗口并准备相应的新不可变来源。随后：
1. BOLE 完整同镜像 CPU controls / 原保存帧 / 实际 ABI → 精确释放与 ticket → 单卡原 baseline → 条件允许时单参数对照。
2. DeltaLog 新执行树落地及 exact closure → cheap / early bind → 同镜像 early253 + payload26 → 完整 closed15 / storage / component binder → 四 rank 模型和匹配消费者。
3. 数值与状态资格建立后，再做既定匹配性能和任务准确率验收。

本目录归档只包含自有源码、准备清单、小型结果引用和统计。原始张量与完整 inspect 留在主机原证据位置。Git 检查点按既有 named work 分支保存；远端发布沿用已知 HTTPS 认证阻断下的本地保存状态，未建立新的 push 成功证据。
