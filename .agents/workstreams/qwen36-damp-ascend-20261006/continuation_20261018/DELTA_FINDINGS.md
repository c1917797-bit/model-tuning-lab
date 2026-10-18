# DeltaLog：R36 / R37 实际停止点与 R38 只读准备核验

日期：2026-10-18 UTC。最近资源现场观测：`2026-10-18T19:07:12Z`，operation `exec-000000000000171c`；其后实际只读准备核验为 `exec-000000000000171f`。只记录小型引用、必要标量与判读；不包含 raw、完整 inspect 或整段运行日志。精确小型引用见 `DELTA_EVIDENCE.json`；尚未取得独立 operation receipt 的项明确标为 pending。仓库保存位置为 `.agents/workstreams/qwen36-damp-ascend-20261006/continuation_20261018/`。

**本轮尚未完成新的模型阶段。** R36 正式绑定被原 storage061 门拒绝；R37 完成 cheap 检查和 early source 绑定，但实际 early CPU 入口仍固定旧 R36 路径，退出于 payload 和软件 suite 之前。R37 容器已停止并释放，不能把源码检查、source 绑定或资源释放记为数值通过。R38 已冻结审阅并通过 20 项本地准备/传输控制；归档准备器的实际只读预演 **171f 通过全部 193 份 Python 文件的语法与身份检查**。R38 model/early 执行源码树仍未部署，实际 CPU/model 未启动。原 `08:43:20 UTC` 执行截止已过。

## 实际执行与边界

| 阶段 | operation | 实际结果 |
|---|---|---|
| R36 正式 model bind | `exec-00000000000016f5` | 约 207.5 秒后失败于 `capture_closed2.validate → prior_policy → storage061.check`；未进入 NPU / 模型输出 |
| R37 cheap gate | `exec-0000000000001711` | PASS；检查 **281 个 own_files**，不能当作模型 suite 已执行 |
| R37 early source bind | `exec-0000000000001712` | 产生新 early manifest：3,678 字节，SHA `97075fae32d3fe0bd9a1650a4aa0e4ff8379051dc406b09888ffdf41d3b8f1a7` |
| R37 实际 early CPU | `exec-0000000000001716` | 主控 operation exit 3；容器 exit 1；原 26 项 payload 与模型 suite 均未到达 |
| R37 终态核验 | `exec-0000000000001717` | Running=false、Pid=0、ExitCode=1、OOMKilled=false、Devices=[]、resource_release_verified=true |
| R38 归档准备器只读预演 | `exec-000000000000171f` | exit 0；内存拼装计划通过 193 份 Python syntax/identity 检查；没有容器、新执行源码树或 bound source |

R37 exact CID：`953ec2a8a3c091873fbddb0e79a28c83fa7fa94db981c52f0beb66f0b333fa95`。容器结束于 `2026-10-18T08:10:58.15851638Z`，实际配置为 guest 1 GiB、CPU 1 核、cpuset 145。其 582,204 字节 FINAL_INSPECT 的 SHA 为 `3ce77e723cdee2d0e0eeeba4942e176db393a3f38800ea7537a68161b5384e7c`；完整 inspect 留在外部证据目录。

RESULT 路径为 `/opt/host/vnf/austinov/run-dl-R37admission-early-software-MAIN-RENEW24H_001/software/consumer/RESULT.json`，**703 字节**，SHA `7c9c59343ce7613d9cd95167f68f8d3bb148a513ced34410e3b7a0593fd7aec9`。同目录的 `FIRST_FAILURE.json`（609 字节）与 `child.stderr`（689 字节）也已固定精确 Ref3，记录在 JSON 中。随后 `exec-0000000000001719` 的 fresh 检查确认所查两个 owned label 列表均为空；这个观测不被外推为整机无其他任务。

## R37 的具体入口问题

已只读检查现场 R37 `recover.py` 副本。它仍定义：

```python
MODEL_ROOT = '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001'
```

随后同时要求 `m['root'] == MODEL_ROOT`、模板路径等于该根下 `SOURCE_TEMPLATE.json`。当前传入的是 R37 模板，所以这个断言在写 `CHILD_IDENTITY.json`、等待 MAIN_ARM、调用 payload26、调用 `prebind_software22.py` **之前**失败。此轮没有新软件测试结果、模型 decode 结果或数值资格可提升。

这也说明，R37 early owner 名称、模板 Ref 和闭包编译通过，尚不足以证明所有实际入口常量完成继承。后继应在新 source 中完整更新并检查 recover/model/owner/模板命令的活动路径；保留旧 R37 失败与 frozen source，不原地改写历史证据。

## R36 storage 问题与 R37 修复范围

先前完整 metadata scan 给出的实际占用为 `45,898,518,779` 字节，即约 `42.7463266803 GiB`；文件系统 free 约 `142.73574066 GiB`。原 closed2 的两个历史 33 GiB 承诺，实际完整已封存 payload 分别为 `1,131,358,910` 与 `8,879,581,752` 字节。旧 prior-policy 仍按未折减承诺计算，可导致约 `103.422526 GiB` 的 committed 值被 **80 GiB** 门拒绝。

R37 新 `readonly_closed_admission` 的设计是先完整验证 closed2 的 source/typed receipts/全树字节、已停止 owner 与无 writer，再使用原 `model_snapshot_budget.adjusted` 规则折减历史两项、加入新的完整 32 GiB 预留，最后仍调用未经改写的原 `storage061.check` 并继续原 closed15 验证。按此前固定 scan 算得 committed `84,552,810,402` 字节，即约 `78.745941 GiB`，剩余约 `1.254059 GiB`。这只是该 scan 下的账务可行性，**不是 R37 实际 binder 通过**；现场仍需重扫。

80 GiB 上限、100 GiB free 门、历史文件、旧 ledger 均未因此放宽或删除。R34 retained payload 仍计入实际全树占用，不能把旧 32 GiB 承诺余量冒充新模型的完整 32 GiB 预留。新 helper 的实际 admission 尚不能由本次 early 失败推定成功。

## R38 已完成的准备与未完成的实际门

R38 的新生成器以原 R36 冻结闭包和已审阅的四份 storage-admission 补丁为输入，保留 R37 model template、已绑定 early source、early template 和实际失败 RESULT 四份精确前驱 Ref。它只在真实 `recover.py` 中替换一个完整 `MODEL_ROOT` 字面量，然后按依赖顺序重算 early own Refs/template、model 侧 owner/template 镜像、model template 与最终命令票据，并扫描完整双树 `.py` 的旧活动身份。独立只读审阅没有发现具体静态阻断。

本地 **8 项准备控制 + 12 项传输/复制控制 = 20 项 PASS，无 skip**。这些是准备工具控制，不进入实际软件计数；原 full 255、early 253 与 payload 26 门保持。原 storage 80 GiB 上限、100 GiB free 门及新模型完整 32 GiB 预留要求保持，未改旧 ledger 或历史 payload。

MAIN 已将三份准备程序归档到本 checkpoint 的 `source/deltalog_r38_preparation/`，随后从该归档目录调用 `transport_emit_r38.py --receipt`。实际 operation **171f exit 0**：重新读取原冻结 source 与实际 R37 失败 Ref，在内存拼装完整计划，全部 **193 个 Python 文件**通过语法与身份检查，`active_stale_identity_tokens={}`。计划文件数为 model **282**、early **12**；这是文件计数，不能写成软件测试数。full 255、early 253、payload 26 保持，实际同镜像门仍未运行。

该次 package ID 为 `6f56bf205070968b0bf18d5375a9e31083e9afc163a9a3b1b43b7531681f3d3d`，返回下列**仅存在于内存计划中的模板 Ref**：

| 计划模板 | 字节数 | SHA256 |
|---|---:|---|
| model `SOURCE_TEMPLATE.json` | 297,848 | `35e5a6f3016df8d2efc474e3ffc58033a6fde9f0d37afacc95ece21d24a2bc50` |
| early `SOURCE_TEMPLATE.json` | 3,862 | `ae66b2ed2f14f491bd910b3aa3977c63bc268ce38c295fa63cc25718d242ee33` |

完整 small receipt 由 MAIN 保存为同目录 `R38_READONLY_PREPARATION.json`。171f 没有调用 copy/prepare，没有创建容器、R38 model/early 新树或 bound source。仓库中的归档准备程序不等于活跃的 R38 模型执行源码。

拟用远端 model root 为 `/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair38-closed-admission-identity-20261018-001`。171c 在 `2026-10-18T19:07:12Z` 确认该根不存在；171f 仅作只读内存预演，新 model/early 执行树仍未创建。本轮没有 R38 实际 cheap/early CPU、真实 model bind、模型或消费者结果。171c 所查两个 owned label 均为空，观测范围不外推为整机空闲。

## 下一阶段与时间门

新的模型/消费者仍继承 `time.time() + 3600 <= 1792313000`，本窗口最晚入口为 `2026-10-18T07:43:20Z`。原授权截止 `2026-10-18T08:43:20Z` 在最新现场复核时也已过去。较短的 early CPU 阶段或其他已注册组件不能替换这个整模型门。

下一步需先取得新的明确执行窗口，准备和审阅绑定该窗口的不可变后继，保留 R36 / R37 实际失败与 R38 冻结准备证据。之后应顺序完成远端源闭包核验、实际 cheap、early bind、同镜像 early 253 + payload 26、释放证明、原 closed15 / storage / component binder 与完整模型准入。本文不自动延长窗口，不把准备器预演通过写成 early、模型或数值阶段通过；模型、任务、性能资格继续 pending。
