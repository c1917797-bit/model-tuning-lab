# 线程枚举与回归准入经验 — 2026-10-08

## 本轮结论

这是维护知识的增量补充，不是新的论文穿刺成功。此前
[经验记录](EXECUTABLE_READINESS_LEARNING_20261008.md)及全部失败原件保留。
本轮通过了完整软件和同镜像无设备阶段，但真实四卡实验仍在模型启动前失败。
没有新增完整 NPU 数值、端到端吞吐或 LongBench-v2/GSM8K 精度验收结果。

## 六项已核实事实

1. MAIN1387：SparsePrefix v9 完整167项宿主软件与219源闭包通过；不是 NPU 测试。
2. MAIN138f：同镜像 Devices[] 完整167项及7条真实 CLI 通过；MAIN1393 独立
   consumer 通过，专用 CPU 容器已停止保留。该权威只适用于原 v9 源身份。
3. MAIN1397：物理4–7的四卡算术 canary 通过；随后 RSS owned-tree observer
   在 `thread.first-stat` 失败，PID3121095/TID3121130/errno2。模型没有启动。
   采样峰值约124MiB，限额512MiB；不证明未观测峰值，也不证明完整数值正确。
4. MAIN1399：独立消费失败证据、精确 own CID 停止保留、宿主子进程收割与
   4–7释放已核实。原1397仍为exit1；旧134d的缺失PID不能由本次记录补造。
5. MAIN13a7：ANN canonical 源41/自有31的身份和编译通过，但完整170软件
   仍有11失败、3错误。多项检查指向已迁移的旧文件/PA/FP32协议，须逐项核实，
   不能笼统称全部误报、更不能删除检查后直接上卡。
6. MAIN通用 harness 将 SparQ default-OFF 误设为exit1；其真实disabled入口
   按本项目约定正确返回0。应修正 harness，不应为迎合测试修改运行时。

## 可复用成功经验

- 真实聚合入口、完整依赖与同镜像挂载检查能够提前暴露软件缺口；helper
  PASS不能替代它们。结果生产者和独立consumer各自保留 source/terminal 权威。
- 第一次拒绝记录 syscall/PID/TID/errno，能够把控制器失败缩小到可修复边界；
  own-only cleanup与失败原件分别保留，避免把清理成功写成算法成功。
- 并行准备包按不可变版本交付；新版本不借用旧 manifest 的PASS，算法源、
  ABI、门限与固定截止时间保持可审计。

## 失败经验与下一次应做什么

| 触发 | 下一次行动 | 持久入口 |
| --- | --- | --- |
| 线程在枚举和读取间消失 | 保留同一parent/start及前后thread集合；只有严格离开证明成立才记录retired；完整重扫仍活线程的children，防止漏计收养子进程。权限、活体失读、reuse继续硬拒绝，不填零RSS。 | controller observation reference |
| 60秒准入Ref在慢API流程中过期 | 先完成静态审阅，再临近dispatch生成真实新凭证；按宿主时间计龄，保留原拒绝，不改时钟或放宽门禁。 | controller observation reference |
| 实现迁移后旧回归仍抓旧文件/协议 | 逐项映射到真实当前producer/consumer、独立oracle与原生ABI，补行为检查；保留旧失败，不跳过负例、不改数值阈值，不为generic harness更改正确的OFF行为。 | ranking reference |
| CPU/同镜像PASS后canary阶段失败 | 只推进已通过阶段；控制修复重走其源码版本的软件准入，随后一次新鲜上卡。不升级为paper-wide no-go，也不叫E2E成功。 | tuning-loop skill |

具体规则已写入已有维护者skill及其窄reference，不新建泛化大skill。
[结构化证据与原件SHA](THREAD_ENUMERATION_AND_REGRESSION_LEARNING_20261008.json)
记录触发、行动、目标文件及核验方法；大原始日志在宿主 /cache/cch 下，不入Git。

## 交接边界

SparsePrefix v10已由准备者冻结，12项新增真实线程与完整179软件尚未执行；
v9失败不可原样重跑。ANN canonical新回归仍待修复/验证，完整128/20480
NPU、长上下文/TP4/service与配对性能尚缺。SKVQ的输入采集/校准/packed-cache
服务准备不是官方完整算法或数值通过。所有待验证项仍默认关闭。

只使用物理4–7，不干扰0–3；32GiB HugeTLB释放权限已SPENT。
portfolio Oct9 11:17:31Z、SparsePrefix Oct9 07:09Z、SparQ Oct8 19:00Z
不重置。无新的至少10%端到端技术验收。此次只提交维护知识，不提交当前未通过
的软件实现或其他未跟踪文件；正常推送工作分支，不修改main/不强推。
