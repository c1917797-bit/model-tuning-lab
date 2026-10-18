# BOLE：两轮实际 CPU 诊断与 FIA 重放停止点

日期：2026-10-18。最新现场观测：`2026-10-18T19:07:12Z`，operation `exec-000000000000171c`。完整小型 Ref3 与统计保存在同目录 `BOLE_EVIDENCE.json`；本记录不包含原始张量或完整容器 inspect。仓库保存位置为 `.agents/workstreams/qwen36-damp-ascend-20261006/continuation_20261018/`。

**两轮 CPU 诊断均完成并释放资源；后续 FIA 重放只完成 source binding，CPU preflight 和 NPU 重放均未启动。** BOLE 原 R6 的 FA 数值失败仍保留。原 R6 的 greedy identity、accepted-path writeback/restore 已通过，但 FA tree 的失败集合仍为 **22 / 64 个 rank-layer case**。完整模型、性能、任务及生产资格均未建立，scheduler 未提交。本轮未修改数值门槛，也未确定实际 FA 内核根因。原 `08:43:20 UTC` 执行截止已过。

## 1. 实际执行与证据入口

| 诊断 | 实际 operation | 同镜像 controls | owner whole elapsed | 结果 |
|---|---|---:|---:|---|
| FP64 累加与最终 BF16 表示能力 | `exec-00000000000016f0` | 4 / 4 PASS | 67.500635 秒 | 4 rank 完成，primary=null，secondary=[] |
| softmax 概率 BF16 单变量模型 | `exec-00000000000016fb` | 12 / 12 PASS | 13.373979 秒 | 3 case 完成，primary=null，secondary=[] |

两者均为 Devices=[]、CPU 1 核、guest 8 GiB、只读根文件系统、network=none，镜像 `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`。

释放的 exact CIDs：

- FP64/BF16：`7646db388fbead3a7e5e451a5cdf27af81fc5c9b0840fe4e491f181e7f9836c7`，容器结束于 `2026-10-18T06:58:22.81894048Z`。
- probability：`8ca0881c2d3fd01e8f809ed5e330b1fde3812c5b3c6b901f0af3ceffe2d23e2e`，容器结束于 `2026-10-18T07:30:35.07097103Z`。

两个 final inspect 均为 Running=false、Pid=0、ExitCode=0、OOMKilled=false、无 ExecIDs；owner 均记录 resource_release_verified=true、stopped_retained=true。每次执行的 source、RESULT、ATTRIBUTION、SOFTWARE、FINAL_INSPECT，以及第二次 PROBE 的完整路径/字节数/SHA256，见 `BOLE_EVIDENCE.json` 的两个 diagnostic 条目。

关键引用摘要：

| 记录 | 字节数 | SHA256 |
|---|---:|---|
| rounding SOURCE_BOUND | 3,917 | `47a9af8fd83f82677970efa8c5cb1897ccbdfaa9eef5381a9be0f960c0bdc9d8` |
| rounding RESULT | 855 | `4b262aca2d2e8237bda634b9694844494d412320ff5e4ecd1860296db7e359c0` |
| rounding ATTRIBUTION | 1,524 | `1bc14dae4bfd018eddefe742b2f27d00dde69708e58dff388b3ef07839bf5326` |
| probability SOURCE_BOUND | 4,286 | `d81e225e55621cc132f48524ad54e411177be6078fc6eb56c60400cf934ddb89` |
| probability RESULT | 876 | `c503213094f825302a3eeefd1c8d646d811bed7ccdca57a174eb7b234ad45b91` |
| probability ATTRIBUTION | 970 | `5b5d19604b670d03bdc7bd28f1a3a49abd580ae878d95932ac8331b2f0d1d4e1` |
| probability PROBE | 16,408 | `cdc83b676ebca404ac1db70d85df77738982d4fd1bad1bf3e07f9e980c94bd9d` |

## 2. 第一轮：排查 CPU 参考累加差异和最终 BF16 表示能力

诊断重开固定 R6 原 source/raw/rank reports，将普通 CPU64 参考与独立 compensated FP64 参考逐元素比较，并检查最近 BF16 可表示值能否满足原门槛：`abs(actual-reference) <= .001 + .01*abs(reference)`。

| 范围 | 输出块 | 元素数 | 失败元素数 | 失败输出块 | 失败 rank-layer case |
|---|---:|---:|---:|---:|---:|
| tree，3 node / case | 192 | 294,912 | 38 | 30 | 22 / 64 |
| native own inputs，4 step / case | 256 | 393,216 | 60 | 43 | 29 / 64 |
| 两组累计 | 448 | 688,128 | 98 | 73 | 并集 32 / 64 |

**元素、输出块和 rank-layer case 是不同计数单位。** 22 / 64 是原 R6 tree FA case 失败率，不能改称 22 个元素。两组 case 交集为 19 / 64；native 使用自身每一步的独立输入，不能把 tree/native 同 layer 视为完全相同的张量输入。

全部 448 块的 failed_set_changed=false；原 R6 float、double 与本轮 tree 失败的 case 集合精确相同。98 个失败点的 CPU64 与 compensated 参考差异最大为 `1.2490e-15`，而最小超门幅度为 `2.23744e-6`。因此，这两种参考算法的累加差异不足以解释已观察到的失败。

98 / 98 失败点均有满足原门槛的最近 BF16 值；最近 BF16 误差 / 门槛最大仅 `0.1310044`。因此，最终 BF16 格式本身的表示能力不足以强迫这些失败。该结论不覆盖 FA 内部中间计算、online softmax、近似指数、缩放、归约或真实算子内部实现。

## 3. 第二轮：概率 BF16 模型未获得支持

预先固定原 R6 rank 1 / layer 43 的三个 case：tree node 2、native path 2 / node 2，以及同层原先通过的 tree node 0。每个 case 都比较完整 1,536 维。

两路径共用独立 FP64 QK/softmax、PV 的 `math.fsum` 和最终 nearest-even BF16；唯一干预为 `P64 → nearest-even BF16 → FP64`，量化后不重新归一化。原 raw、producer/source、mask、scale 和原 rank 报告均保持绑定。

| case | 最终 BF16 路径与原 NPU 的 bitwise 相同元素 | 加概率 BF16 后 | 与原 NPU 的 L2 误差：原路径 → 干预 |
|---|---:|---:|---:|
| tree node 2 | 1,257 / 1,536 | 1,160 / 1,536 | 0.0599693 → 0.0755757 |
| native path 2 / node 2 | 1,244 / 1,536 | 1,123 / 1,536 | 0.0595689 → 0.0793910 |
| tree node 0，预先指定 pass control | 1,328 / 1,536 | 1,246 / 1,536 | 0.0668744 → 0.0846997 |

表中 L2 为到原 NPU 输出的绝对向量范数。三个 case 的 bitwise 相同元素均减少、L2 误差均增大。

两个原失败点都位于 head 2 / channel 61：

| case | 原 NPU | final-only BF16 | 加概率 BF16 |
|---|---:|---:|---:|
| tree node 2 | -0.0625 | -0.0595703125 | -0.05810546875 |
| native path 2 / node 2 | -0.0267333984375 | -0.029052734375 | -0.0294189453125 |

两个干预输出均未重现原 NPU 失败点，且向更远方向变化。final-only 对 compensated 参考的失败数为 0 / 0 / 0；概率 BF16 后为 1 / 2 / 1，失败位置也不同于两个原始 head 2 / channel 61 点，原 pass control 还出现一个新失败。

因此，**“其余计算采用当前 compensated 模型，仅在完整 softmax 概率上加一次 BF16 舍入”这一具体解释未获支持。** 不能据此排除所有中间 BF16 或真实融合算子的分块 softmax 策略，也不能推断 Ascend 硬件、集合通信或内核实现存在特定故障。

## 4. 实际调用源码已闭合；精确 FIA 重放包已冻结并绑定

已读取固定 R6 的 `model_entry.py`、`adapter.py`、`worker_entry.py`、`model_smoke.py`、`component_gate.py`、`independent_model.py` 及实际 attention 源码。`model_smoke` 把已绑定的 `adapter` 传给 Bridge；`component_gate` 再以正文 bytes/SHA 与实际完成的 paged component source 核对，并沿 numeric owner → stage → actual ABI 收据获取真实 dispatcher 身份。

两条原始路径确实调用同一 `torch_npu.npu_fused_infer_attention_score` 接口，但完整输入域不同：

| 参数或输入 | tree 原调用 | native path 2 / node 2 原调用 |
|---|---|---|
| query | BF16 `[1,6,3,256]`，全部三个 query | BF16 `[1,6,1,256]` |
| key / value | paged BF16 `[2,1,128,256]` | dense BF16 `[1,1,133,256]` |
| mask | bool `[1,1,3,256]`，True 禁止；含完整 padding | 未显式传入 |
| block_table / block_size | int32 `[[0,1]]` / 128 | 均未显式传入 |
| actual_seq_lengths / KV | `[3]` / `[134]` | `[1]` / `[133]` |
| sparse_mode / inner_precise | 1 / 2 | 0 / 0 |
| 共同参数 | BNSD，Q heads=6，KV heads=1，scale=.0625，pre/next=2147483647 | 相同 |

实际 ABI 为 5,425 字节、SHA `164f89472d6adecb55c8eeb76b23e04c774c4040dbfb8eaa3ad5d9fccd3815a2`，只声明 `int inner_precise=0`；已读取的 CANN 头文件同样只给出整数类型。**没有找到 0/2 的精度语义或适用域枚举。** 两个数值在原来的不同调用域中执行过，并不证明交换后各域都支持，也不允许命名为某种中间计算 dtype。实际 attention 源中 C8 路径的 `inner_precise=1` 不能外推到这两个 BF16 调用。

独立组件重放包 `bole-fia-fixed-frame-replay-renew24h-20261018-001` 已于 `08:15:56 UTC` 在本地冻结并完成审阅。共 **44 项本地纯 CPU controls** 通过且无 skip：probe 20 项，owner/ticket 24 项。本地没有运行 torch/raw/NPU 实验；这些控制不能替代同镜像 Devices=[] 的真实输入与 ABI preflight。

实际 binder `exec-000000000000171b` 以 exit 0 完成，耗时约 **4.688 秒**，记录 `full_readset=53`，生成：

- source：`/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-fia-fixed-frame-replay-renew24h-20261018-001/SOURCE_MANIFEST.json`
- 大小：**12,699 字节**；SHA256：`535848eb04738414f099c2d261ba372611c080577fb06c3e0ebcad01b702c5e1`。

此项是 source 绑定成功，尚无 CPU preflight、ABI ticket、NPU baseline 或参数干预结果。

固定设计如下：

1. 原 R6 rank 1 原始 raw、source、producer、rank report 均保持 Ref3 绑定。重构全部 tree paged tensors/full mask/table/padding，以及独立 native prefix/root/current-token dense tensors；H2D 后再核对完整字节、shape、dtype、stride。
2. 先执行 tree 原 `inner_precise=2` 和 native 原 `inner_precise=0`。分别要求全部 **4,608 / 1,536** 个 BF16 输出位复现原记录，并复现预先固定的 **tree node 2 失败 1 点、native node 2 失败 1 点、tree node 0 通过**；tree node 1 也保留为完整调用中的通过对照。不能裁成单个 tree query 后仍声称原调用重放。
3. **两条 baseline 都完整通过重放门后**，才分别执行 tree `2→0` 与 native `0→2`。每个分支其他 kwargs、输入、layout、mask、scale、seq length 全部不变。不支持的跨参数调用保留原异常，不回退或重写参数。
4. tree 数值判断直接调用已绑定原 `independent_model.attention`，保留其 float/double 门；逐点报告仍使用原 CPU64 公式。native own-input 的 CPU64 结果继续作为诊断，不升级为原 whole-model 新资格门。两轮 compensated CPU 结果不替换原参考。

即使参数切换改善固定输出，也只说明这个新重放域中的参数效应，不能独自确定原融合内核的内部精度、tiling 或硬件根因，不能让原 R6 model/performance/task 资格转为通过。

## 5. 本轮真正停止点与现场复核

171b 之后，准备调用的 source-audit 工具在**执行前**被工具目录变更中止，返回：

```text
tool call rejected because the catalog changed after codex_apps/awmcp.skill_run_write was prepared
```

该调用没有 operationId。它不是自动安全审批拒绝，也不是 CPU 测试失败；后续 mkdir、CPU owner 与 NPU owner 调用均未发出。因此不能把此前“即刻 CPU”的计划表述当作实际启动记录。

`exec-000000000000171c` 在主机 UTC `2026-10-18T19:07:12Z` 的 fresh 只读复核确认：

- replay 输出根 `/opt/host/vnf/austinov/run-bole-fia-fixed-frame-replay-MAIN-RENEW24H_001/replay` 不存在。
- 预期 `cpu/RESULT.json`、`numeric/RESULT.json` 均不存在，没有本轮 replay CPU / NPU 结果可消费。
- 所查两个 owned label 列表均为空；该观测只覆盖所查 owner，不代表整机没有其他任务。

独立组件原合同为 NPU whole 900 秒，原最晚完整入口为 `2026-10-18T08:28:20Z`；CPU preflight 也有其完整时间门。原授权截止 `2026-10-18T08:43:20Z` 在此次 fresh 观测时已过，不能继续使用旧窗口启动。

下一步应先取得新的明确执行窗口，并据此准备、审阅新的不可变后继 source，保留本轮 bound source 与所有历史失败。随后重新满足完整同镜像 CPU preflight、释放证明、ABI ticket、现场资源与 ARM 门，才可执行上述 baseline → 单变量设计。本记录不缩短整模型 3,600 秒门或组件 900 秒门，不自动延期。完整模型、任务和性能状态仍为 pending，原 FA 失败不作任何晋级。
