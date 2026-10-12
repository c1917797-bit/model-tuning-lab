# HYPIC 算法特性穿刺 · NPU0–3 终态负结果（含命令）

> 论文：*Hypic: Accelerating Hybrid-Attention LLM Serving with
> Position-Independent Caching*, arXiv:2607.01299v2。本文只评价
> vLLM-Ascend 派生实现的单副本 C1/C2 文本路径，不是作者 SGLang
> 实现的逐字节复现，也不是 C3 跨副本穿刺。
>
> 报告状态：**final negative result for the frozen r13 C1/C2 experiment**。
> 质量部署判定 `REJECT_OR_QUALIFY`，严格质量热路径判定
> `NOT_ACCEPTED_HOT_COVERAGE`；独立的性能筛选为
> `EFFECT_SCREEN_PASS`。本报告不宣称生产可部署、论文全量复现或
> 29 个 Skill 全部验收。

## Step 0. 环境准备与证据分类

目标为 chicaihong01 EulerOS/aarch64、物理 Ascend 910B4 NPU0–3
（NPU4–7 禁用）、单模型副本 TP4、端口 8223、CPU 集 112–191。
模型目录 `/cache/efim/Qwen3.6-27B` 的 `config.json` SHA256
`69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c`
表明实际架构为 `Qwen3_5ForConditionalGeneration`：64 层中
48 层线性注意力、16 层全注意力，BF16；名称中的“Qwen3.6”
不构成架构证据。模型索引 SHA256
`a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`。
服务镜像固定为
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`，
派生插件源码 commit
`c12060cd47e7575ead059983d7a8bb4704165c98`，仓库
`/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008`。
两个服务组均使用 41,984 上下文、GPU 利用率 0.85、CPU binding
关闭、3,584 MiB/10 段 material cache 上限。独立的同镜像 profiler
记录 `torch_npu 2.10.0.post4`、CANN 9.1.0；驱动与 vLLM
包版本的 r13 原始逐包清单未留存，镜像 digest 是本实验的运行时身份。

当前实测分为两把**不可混合**的尺子。质量尺：LongBench-v2 原始
127 样本，输入逐题不同，显式位置无关段边界，c8、自然 EOS、
最多 2048 输出、三轮。数据集 SHA256
`cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a`，
评分器 SHA256
`9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0`。
性能尺：共享前缀 16,384、输入 32,768、固定输出 1,024、
c16、每轮 40 个计分请求、三轮。质量的 2048 上限不能写成
性能的 1024 固定输出；两表的百分比也不能合并。

以下属于**当前实测**：r13 两组质量原始根、六个性能阶段、同源
HYPIC-only Prefill/Decode 诊断 profile。旧 c16/1024 性能
`performance-independent-audit.json` 的 22.3562% TPOT
降幅，以及 clean2 自然任务质量，只作**历史参考**，不进入当前
结果列。论文的作者加速数字未作为当前证据或验收阈值。
“性能机制有效但质量不可接受”是根据当前证据作的**解释**，
不是论文原文结论。

### 获取代码、预检与资源边界

经 AWMCP 新鲜解析 `chicaihong01/ma` 并证明直连后，执行前只读
预检包括 `git status --short --branch`、`npu-smi info`、
`docker ps`、`ss -lntp`。Docker 映射不等于物理卡占用；
每个阶段从启动前到结束都有 10 秒周期的实际物理 NPU0–3
外来进程守卫。出现外来 PID 或探测错误，该阶段失效，
仅清理精确属于本阶段的容器，不动外部任务。当前报告由
`/cache/cch/model-tuning-lab-hypic-e2e-20261006` 工作树
`work/hypic-npu03-cpu-binding-fix-20261007` 及其分支交接接管。
原始大文件、模型、数据集和 profile 不进入 Git。

## Step 1–3. 分组、拉起服务与测试命令

| 组 | 唯一服务开关 | 回答的问题 |
| --- | --- | --- |
| G1 no-cache | `VLLM_ASCEND_HYPIC_ENABLE=0` | 同身份关闭插件时的质量与速度 |
| G2 hypic-only | `VLLM_ASCEND_HYPIC_ENABLE=1` | 单副本 C1/C2 路径开启的部署效果与热路径 |

除开关和各组证据输出路径外，两组镜像、模型、源码选择、
容量、CPU/NPU、请求与评分配置按冻结契约相同。r13 质量先
G1 后 G2；性能六阶段依次 G1/screen、G2/screen、
G2/repeat2、G1/repeat2、G1/repeat3、G2/repeat3。
质量每题先执行两次一 token 预热，然后三次
`temperature=0, seed=0, thinking=false, ignore_eos=false`
计分请求。显式边界按冻结规则
`[min(16384,floor((prompt_tokens-2048)/16)*16),prompt_tokens]`；
启动后的首题先验证四个 worker 的计分热路径。

下列是**历史执行选择器**，用于核对运行方式，不得在已有根上
重跑。每次设备执行当时由 AWMCP 异步控制器和连续守卫管理；
认证值只在连接器字段中传递，不属于命令。

```sh
cd /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007
export HYPIC_HOTPATH_QUALITY_CAMPAIGN=cache10r13
export HYPIC_HOTPATH_QUALITY_MODE=full
export HYPIC_QUALITY_PLUGIN_REPO=/cache/cch/hypic_vllm_ascend-fallback-telemetry-20261008
export HYPIC_QUALITY_PLUGIN_COMMIT=c12060cd47e7575ead059983d7a8bb4704165c98
HYPIC_HOTPATH_QUALITY_ARM=no-cache python3 -B hotpath_quality_full.py
HYPIC_HOTPATH_QUALITY_ARM=hypic-only python3 -B hotpath_quality_full.py
```

第二条的控制器在全部 127 题、381 响应保存后，以
`candidate scored boundary/hot coverage incomplete` 退出 1；
这不是请求缺失，也不能改写成控制器成功。独立审计按预冻结
“部署全请求 / 严格四 worker”双口径保存有效负结果。
两组服务在各自阶段后停止，原始根分别为
`quality-context-41984-hotpath-cache10r13-full-baseline` 与
`quality-context-41984-hotpath-cache10r13-full-hypic`，
都位于 `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/`。

性能阶段使用已登记的同一源码、容量及隔离控制器，
两次一 token 并发预热后发送 40 个 c16 请求；
`temperature=0, seed=0, ignore_eos=true`，每条必须恰好
1,024 输出。原 benchmark 的首个 SSE request ID 由只观察不改变
请求的 `hotpath_request_id_benchmark.py` 记录；每阶段含预热
42 个唯一 ID，G2 的全部 120 个计分 ID 与四 worker 事件逐条关联。

```sh
python3 -B hotpath_cache10_matched_performance.py --arm no-cache --phase screen --run
python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase screen --run
python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat2 --run
python3 -B hotpath_cache10_matched_performance.py --arm no-cache --phase repeat2 --run
python3 -B hotpath_cache10_matched_performance.py --arm no-cache --phase repeat3 --run
python3 -B hotpath_cache10_matched_performance.py --arm hypic-only --phase repeat3 --environmental-retry21 --run
```

最后一条使用预登记、全新不可变 retry21 根；早期 retry
失败根未复用。实际容器启动命令、bind、镜像、源码、worker
映射见各阶段 `contract.json`、`service-start.json`、
`source-attestation.json` 和 `benchmark-command.json`，
不以此处简写替代原始收据。r13 G2 的源码证明记录实际
`/source-hypic:ro` bind、`/opt/hypic` 导入路径、
32 个 Python 文件的相同源树摘要
`0c6e64aca8f494c1a298cdb5c1d774d3c10ab5b0454bb2dd487ef544637e3633`；
它不证明编译二进制或所有传递依赖逐字节相同。

## 实测结果

### 性能：六阶段固定输出，不与质量分数混列

每行 40/40 有效计分请求，原始 `arm-result.json`、
`performance.json` 与总审计逐阶段对账。以下顺序和数值来自
SHA256 `d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062`
的独立六阶段 JSON。

| 轮次 | 组 | weighted TPOT ms/token | TPOT P95 ms | TTFT P95 ms | 吞吐 tok/s | 时长 s | 守卫样本 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| screen | G1 | 75.145144 | 112.036995 | 86628.571480 | 101.395092 | 403.964326 | 160 |
| screen | G2 | 58.643006 | 78.603832 | 45695.637440 | 133.451314 | 306.928413 | 150 |
| repeat2 | G2 | 58.498860 | 78.441900 | 45794.394730 | 133.685142 | 306.391566 | 150 |
| repeat2 | G1 | 73.372920 | 110.941315 | 85695.069490 | 102.926251 | 397.954841 | 162 |
| repeat3 | G1 | 74.727578 | 111.744995 | 86694.139190 | 102.754813 | 398.618798 | 164 |
| repeat3/retry21 | G2 | 58.896690 | 78.740563 | 45759.196170 | 133.329578 | 307.208653 | 164 |

三轮均值 ± 样本标准差：weighted TPOT G1
74.415214 ± 0.926484、G2 58.679519 ± 0.201413 ms/token；
TTFT P95 G1 86339.260 ± 558.848、G2
45749.743 ± 50.053 ms；吞吐 G1 102.358719 ± 0.838916、
G2 133.488678 ± 0.180703 tok/s。预冻结报告口径是
**三轮中位数**：weighted TPOT 74.727578→58.643006
ms/token，`(G2-G1)/G1=-21.5243%`，节省
16.084572 ms/token；TTFT P95 86628.571→45759.196
ms，节省 40.869375 s；吞吐 102.754813→133.451314
tok/s，即 1.298735 倍。配对三轮 TPOT 节省依次为
16.502137、14.874060、15.830888 ms/token。
三轮的预冻结门槛是 TPOT 至少节省 10 ms/token 且 TTFT P95
至少节省 10 s，故性能筛选 `EFFECT_SCREEN_PASS`。
这不是质量安全、C3 或跨负载推广的通过。

### 精度/质量：自然 EOS、max-2048

两组各 127 个唯一题目 × 三轮 = 381/381 有效计分响应；
没有将冷请求或长度受限请求后验排除。计分轮次正确数：
G1 `77,74,79`，G2 `69,73,77`，即三轮正确率均值
60.3675% ± 1.9816pp 对 57.4803% ± 3.1496pp
（样本标准差）。合计 G1 230/381 (60.3675%)，
G2 219/381 (57.4803%)，绝对差
`(219-230)/381×100 = -2.8871` **个百分点**。
配对翻转：19 个改善、30 个退化；达到输出上限的响应
G1 48、G2 60。预冻结质量门槛为候选正确数不低于
G1 且无分类断崖；G2 未通过，部署口径
`REJECT_OR_QUALIFY`。

逐 request ID 机制证明：G2 368/381 四 worker 热命中，
13/381 冷请求使严格口径 `FAIL`。原始 369 次汇总修复
计数不是 368 个唯一计分 ID，不可替换。13 个冷请求的
观察序列均为材料曾就绪、随后驱逐、规划时无 ready hash，
进入原生 partial-Prefill；其冷子集 7/13 正确对 G1
4/13，而热子集 G2 212/368 对 G1 226/368。
这些事后分层只描述现象，不能把总质量下降因果归咎于
冷路径或宣称热路径无损。r14 c1 诊断两组各 3/9 正确、
G2 9/9 热，改变了并发、样本和调度历史，亦不得改判 r13。
当前 r13 没有完整配对 GSM8K，也没有完整多模态/MTP
质量结论；未测不写成 0。

### 机制、Profiler 与资源隔离

候选性能 120/120 请求均具有显式边界和四 worker
post-repair 证明；质量只 368/381。单副本 TP4 的四个
worker 是张量并行 rank，**不是**论文 C3 的四个副本。
HYPIC-only 诊断 profile 单独捕获了四 rank Prefill
（281 个非空原始文件、每 rank 5,622 行详细 kernel）
和 Decode（441 个非空原始文件；每 rank
83,223 个真实 NPU compute kernel 位于 2.676525 s
采集窗内）。原始文件按 hash 不变，离线解析只在副本上做。
历史捕获入口为 `python3 -B hypic_profiler_capture.py --phase prefill --run`
（r2 版本）与 `python3 -B hypic_profiler_capture.py --phase decode --run`
（r6 版本）；两者的具体服务命令和 profiler 配置保存在各自
`contract.json`。当前工作树文件已演进到 r6，不能拿它在
r2 原始根上重放 Prefill；Prefill 捕获时控制器脚本的独立
Git blob 未在收据中固定，因而该脚本的逐字节可重建性仍有边界。
停止由捕获控制器以精确自有容器 ID 完成，而非手工停止其他任务。
首个 Decode 解析副本缺少共享管理节点，进程 exit 0
但 CANN export 内部失败；修正解析环境后四 rank 有效。
Prefill 原预登记 `>=47` 列数门槛实际只有 46，
该数值门槛保留为失败，不做事后改判。诊断 profile
没有配对 G1 profile，不能证明 CANN/HCCL 或某个算子
是 r13 质量下降根因。

质量 G1/G2 守卫分别 998/1080 次干净探测；性能
六阶段守卫依次 160/150/150/162/164/164 次，
均无外来进程或探测错误。六个阶段均证明精确自有
容器删除、NPU0–3 和端口 8223 释放；NPU4–7
未被本任务映射。被动映射与正在运行的外部容器不被
误判成物理 NPU 正在计算，但也不能用一次空闲快照
代替连续守卫。

## 与论文及同事历史结果分开比较

| 指标 | 论文报告 | 同事/历史实测 | 本次 r13 | 能否直接合并 |
| --- | --- | --- | --- | --- |
| HYPIC C1/C2 速度方向 | 作者声称加速；本报告不采用其数值 | 旧同卡 c16/1024 weighted TPOT 中位数下降 22.3562% | 本次 c16/1024 下降 21.5243% | 仅作方向/量级参考；缓存预算及活动路径不同 |
| max-2048 显式边界质量 | 本报告未取得同尺作者数字 | clean2 自然任务无 worker 热证明；r12 仅 G2 57 条诊断 | 230/381→219/381 | 不合并；只有 r13 是本次完整配对 |
| C3 跨副本 | 论文机制包含 C3 | 未在本机单副本路线证明 | 未实现 | 不可宣称复现 |

## Decision 与结论

| 门槛 | 当前判定 | 证据边界 |
| --- | --- | --- |
| C1/C2 架构可行性 | 限定可测 | BF16 混合注意力文本路径；非全纸 |
| 机制激活 | 性能 PASS、质量严格 FAIL | 120/120 vs 368/381 唯一 request ID |
| 性能收益 | `EFFECT_SCREEN_PASS` | c16/32768/1024 的三轮固定输出 |
| 质量安全 | `REJECT_OR_QUALIFY` | c8 LongBench-v2 127×3，−2.8871pp |
| profile 根因归属 | 未证明 | 候选诊断有效但非 G1/G2 成对 profile |
| C3/发布采用 | 未通过 | C3 缺失；质量门槛未过 |
| 跨模型/卡组/业务泛化 | 未测 | 本次仅一个模型、物理 NPU0–3、两个明确负载 |

**允许声称**：在冻结的单副本 C1/C2 性能负载上，
HYPIC 开关产生有激活证明的速度收益；
在另一把冻结的 max-2048 质量尺上出现退化并被拒绝。
**禁止声称**：无损、质量通过、HCCL/卡故障根因、
完整 HYPIC/C3 论文复现、生产发布、29 Skill 全部有效。
**仍未证明**：热请求答案差异的单一因果根、
GSM8K 完整配对及跨服务通用性。需要新研究时，
先冻结单变量因果设计，不改写或复用 r13/r14 根。

## 报错、失败尝试与排除

| 事件 | 可观察事实 | 分类及处置 | 是否进入正式结果 |
| --- | --- | --- | --- |
| r13 G2 控制器 exit 1 | 127/381 完整，但 13 个计分 ID 无四 worker 证明 | 实现/机制覆盖失败；保留所有质量响应 | 是，负结果 |
| 性能 retry4 | 外部 PID 3079008 进入物理 NPU1，16/40 部分响应 | 环境隔离失效；精确自有容器释放 | 否，16 条全排除 |
| 性能 retry19/20 | 外部 PID 分别在 NPU2/NPU3，均未到 health/计分 | 环境隔离失效；各零计分，自有容器释放 | 否 |
| 性能 retry6 | 20 秒 executor 超时，未形成可计分 benchmark | 控制器超时配置错误；不推断 HYPIC 性能 | 否 |
| profiler r1、Decode r2/r4/r5 | 外部 `Maxon4ick_vllm` 短时进入 NPU0 | 环境隔离失效；不停止外部任务，新根等空闲 | 否 |
| Decode 首次离线解析 | export 内部失败，尽管控制器 exit 0 | 解析环境缺共享管理节点；仅在原始 profile 副本上修复 | 原始采集有效，首解析结果无效 |
| Prefill 46/47 列 | 版本相关详细字段齐全但预登记数字未达 | 协议门槛失效，保留失败；未来另定版本化语义门槛 | 不倒填 PASS |

第六性能阶段最初根及 retry1–20 均未作为有效第六轮；
retry21 是唯一纳入六阶段审计的该轮原始根。部分尝试在
预检或控制器阶段就终止，没有 `arm-result.json`；
不能把“缺少该文件”自动解释为算法失败。其他环境
预检/重试的精确 PID、零计分与释放收据保留在
`task.json`、`HANDOFF_HISTORY.md` 和对应
`HOTPATH_CACHE10PERF_RETRY*_TERMINAL_AUDIT.md`；
它们不进入六阶段性能分母。r13 质量没有请求缺失，
冷请求全部保留；数据集范围未覆盖 GSM8K，不把
“未测”混成失败计分。

## 证据索引与精确交接

原始根为 `/cache/cch/hypic-npu03-cpu-binding-fix-20261007`。

| 证据 | 路径（相对原始根） | SHA256 | 证明/限制 |
| --- | --- | --- | --- |
| G1 quality contract/result | `quality-context-41984-hotpath-cache10r13-full-baseline/contract.json` / `arm-result.json` | `79ef620ab90a1f5925e6155b03b30de3c396ba1cb2e379108ec593f3a4661d23` / `d348af20d07dab5d34dfa3b2fbf68d310f716f1a9e6aecf91e1d467ad63a5449` | 381 基线响应 |
| G2 quality contract/result | `quality-context-41984-hotpath-cache10r13-full-hypic/contract.json` / `arm-result.json` | `d7a169d11e8ddfaf7c3e865cc86874b5609c6b175863b25c4a3548443622ed9a` / `f4ef1e4f3c2367b41121a6f49209d4d229adaa8eecdb52b050cfad1ebc97329a` | 381 候选响应及 exit 1 |
| 独立质量双口径审计 | `hotpath-quality-cache10r13-dual-audit.json` | `f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b` | 分数、逐 ID 热证明、隔离与释放 |
| 独立六阶段性能审计 | `hotpath-cache10r13-matched-performance-audit.json` | `d8f710f6ccd79ad79a31a36926963eac650761c921924d08b4fb0d2a1a206062` | 6×40 响应、三轮效应 |
| G2 r13 source attestation | `quality-context-41984-hotpath-cache10r13-full-hypic/hypic-only/source-attestation.json` | `d2169d9b36561aa59c1fdcded08df9c98f7fee6a145e7aca1290986c1a92a687` | 服务中 Python 源码，不是全部二进制 |
| Prefill/Decode 诊断 | 仓库 `HYPIC_PROFILER_PREFILL_AUDIT_20261009.md` / `HYPIC_PROFILER_DECODE_AUDIT_20261009.md` | `9e5822afbdbc482a8a9deb3ca3fb96bc192ad4fcccb12f523491f104fcba6556` / `41821d170eae98dd512a990d4e027774213e47cb1b4917b832d5853870cd2d40` | 候选诊断，非质量根因 |

旧实验、原始 profile 和所有失败重试均不覆盖或删除。
以下命令只读回放已有证据，不重新拉起服务：

```sh
cd /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007
python3 -B verify_paper_to_ascend_reproduction_case.py
python3 -B verify_hotpath_cache10_matched_performance.py
python3 -B verify_hypic_profiler_prefill.py
python3 -B verify_hypic_profiler_decode.py
python3 -B verify_ascend_source_map_case.py
git status --short --branch
npu-smi info
ss -lntp
```

本次自有服务已精确释放，**没有可执行的旧容器停止或同根续跑步骤**；
手工 `docker rm/kill` 外部容器不是恢复手段。未来新实验须先按
`chicaihong01-host-maintenance` 重新解析目标、证明物理 NPU0–3
与 8223 真正空闲、预登记新根和接受规则，再以新控制器运行，
并以外来进程守卫失败或质量不达标为停止条件。
