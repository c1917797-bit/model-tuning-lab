# 性能推理、因果实验与路线去留

## P1. 先建立本机瓶颈模型

**本文推导**：某算子的理想时间下界近似为 `max(FLOPs/有效算力, bytes/有效带宽)`；launch、sync、通信、访存粒度和pipeline约束还会增加成本。峰值规格是下界参数，不是实际性能。算术强度低时减少FLOPs可能无收益；减少HBM也可能新增解码/flush成本。按prefill/chunkwise、decode、cache-hit分开核实。

对于固定工作量，若关键路径可加速部分占p、该部分加速s、新增串行成本c（按原总时间归一化），则理想总speedup为 `1/(1-p+p/s+c)`。要吞吐≥1.10，则 `p*(1-1/s)-c ≥ 1-1/1.10≈0.090909`。s=4.3、c=0时p至少约11.85%。这是有强假设的可行性估计，不是从kernel时间加总得到的严格paper no-go。

**反例**：rank-mean kernel累计55ms+通信120ms不可当作同一串行关键路径；重叠、重复launch、批次和CPU空档会使总和失真。profiling确定路径/机会，关闭profiling后才做正式比较。只有证明critical-path比例、 workload可比且新增成本受控时，Amdahl才有淘汰力度。

## P2. 指标的对象和公式

固定请求集合时整体输出吞吐=`Σ真实输出tokens / 整段measured makespan`，不是各请求tokens/s的平均。TTFT是请求发出到第一个输出token；非queue prefill时间。请求TPOT常用 `(最后token时间-第一token时间)/(输出tokens-1)`，单token需明确不适用；逐请求均值、加权均值、p分位不混用。

固定1024输出是性能协议，正常EOS/上限2048是任务精度协议；强制生成满长度不能混入最终accuracy。记录输入token分布、prefix长度/复用、并发、40请求还是其他样本、实际错误/超时、冷/热和图模式。并发请求输入32768不保证某次worker packed batch≤32768，scheduler aggregation需要实查。

匹配dense/candidate：同checkpoint、tokenizer、镜像、stack、input IDs、seed/sampling、并发、batch预算、dtype、TP、cache状态、graph/commonopts；只改变论文delta。common优化两边同时施加。改任一重要定义生成新ID，不覆盖旧结果。基线可以冻结复用，仅在完整fingerprint/协议一致且无重大时变混杂时使用；性能声称需同期对照，不能无限复用历史常数。

三轮配对保留各轮差异和离散程度，按预注册顺序控制热机/时序偏差；有限样本未观察到下降不等于统计证明无损。异常只按先定规则排除。组合需要实际D/A/B/A+B，不加百分数；检查两hook的缓存/图/生命周期冲突。

## C1. 归因决定下一步，不只贴分类

| 证据定位 | 下一次动作 | 允许的结论 |
| --- | --- | --- |
| 环境/设备/UDA/资源不合格 | 只读定位exact owner与mapping，授权范围内修复 | 尚未有效测试算法 |
| 源码/CLI/ABI/装载/输入/报告契约缺陷 | 修复已证实接口，实际入口回归，新packet | 当前适配/实验失败 |
| controller先失败，child结果完整 | 独立审计原child+release；不改旧owner exit | child限定范围可复用，parent仍失败 |
| NPU比独立参考差，CPU候选也同样差 | 隔离近似域/公式/缩放，再改算法参数 | 当前算法实现/配置不正确 |
| CPU候选正确、NPU有局部持久字节错 | copy/layout/sync/alias因果控制 | 当前NPU适配缺陷或pending |
| 整模型配对有效但收益不足 | 按热点/新增开销选择有依据修复或关闭该配置 | 当前配置无收益/未达标 |
| 任务差异超限 | 查输入/scorer、数值累计、cache语义；有证据才恢复 | 当前候选任务精度未过 |

第一异常和secondary cleanup分开。根因报告包含竞争假说、证据支持/反驳、信心、最小鉴别实验、适配修改与回归范围；unknown不能改名为算法根因。严禁读一段grep就改controller：完整函数上下文可能已有guard。

## C2. 有效冒烟与递进

先测真实入口和小而可辨别的case，而非全量后发现基础契约缺失：同镜像无卡真实CLI/依赖闭包→装载schema/owner+canary→NPU独立参考、多个heads/非零state/tail→全state多步+slot生命周期→整模型短语义冒烟→固定1024单轮配对→有收益再三轮→任务smoke/full。实际交付启用graph时，进入对应整模型模式前必须过图回放；共同eager可以先进入整模型配对，graph能力标pending，不拿未使用的模式阻塞有效路线。

冒烟通过仅准入后续，不折抵长序列、图或整任务；失败需区分先决条件、算法和实现。官方源码不存在可以忠实实现，但应绑定论文公式并注明非作者原code；有官方源码也需核实实际执行分支和licenses。

保存原输入、原输出、nullable after、命令、bytes/hash、实际loading和独立判定。归因端允许重用有效原始数据，不重跑昂贵NPU仅填parent PASS；改变算法/源码产生新实验。结果目录不可覆盖。

## Q1. 任务精度与1%界限

当前用户选择GSM8K、HumanEval、MMLU，先固定smoke再full。GSM生成与答案抽取、HE生成与官方测试执行、MMLU本实验冻结的选项likelihood协议分别绑定scorer/prompt/sampling。MMLU likelihood的`max_tokens=1`不是生成2048协议，须显式声明任务评分分支，不能偷换成只看生成A/B/C/D，也不宣称likelihood是唯一官方形式。确认实际tokenizer/template关闭思考，不能给未知字段假定生效。

设baseline正确率a、candidate b：下降百分点=`100*(a-b)`，相对下降=`100*(a-b)/a`（a=0时未定义）。明确用户1%是哪个口径；未澄清前同时报告，双界限是保守解释而不是擅自改变授权。accuracy损失容忍不能覆盖NPU数值/确定性门禁失败。

HE生成代码是非可信执行，官方reliability_guard不等于安全沙箱；使用受限、无网络/设备、只读依赖和有CPU/RAM/PID/time预算的独立runner。人工pass/fail样例验证scorer ABI不算模型得分。数据/权重/原始响应留在受控外部目录，Git仅小摘要与hash。

## D1. 高效的证据DAG

各论文独立并行准备、MAIN资源准入、device节点有限持有lease。失败释放后转device-free修复；另一READY节点可推进。依赖同一失败结果的下游不算独立READY。明确CURRENT/NEXT/BACKUP和actual source/input/command/budget/output/verdict，避免“计划完了”被当作可运行。

优化目标是单位时间有效验收边的推进，不是agent数量或AICore满载。测ready等待、阶段耗时、交接缺陷、资源/准入空档；只有连续观测才计算利用率。时间窗不能自动重置；截止前没有完整验收就如实给未完成/限定结论，不补写成功。
