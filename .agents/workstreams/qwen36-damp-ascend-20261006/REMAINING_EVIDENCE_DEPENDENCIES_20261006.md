# DAMP 剩余证据依赖与最短执行队列 — 2026-10-06

状态：source/read-only preparation；等待 MAIN 全文审阅。本文件不是设备、校准、服务、性能或精度授权。唯一新增文档；未修改算法、冻结来源、原始回执或门禁，也未运行 Docker/Torch/NPU/Git。读取基线：HEAD `0efb81f418e459c1c9aadff6970f08b61b682f54`，MB03ef 在18:54:51Z确认本路径不存在、源文件哈希和 canonical HEAD。DAMP截止仍为 **2026-10-07T08:48:03Z**（当时剩13h53m）；portfolio截止2026-10-09T11:17:31Z，不替代单篇24h限制。

## 1. 先对齐已有证据，不重跑已经通过的原配置

- 主线是 DAMP 方程导出的混合精度 recurrent-state 存储和必要的 Ascend 量化/缓存适配，不是无关算子加速。无官方校准代码/精确 SR 网格已核实；项目网格必须保持诚实标签。
- 真正已通过：保存step45修复、production v1 B1/B16 restricted640步；MA03e5六个 native/reference bitwise anchors和四个 synthetic general-positive-FP32 SR640步。原始失败和原阈值保留。这些是实际 NPU 数值证据，不是最终192计划、真实缓存或任务零损失。出处：`projects/damp-ascend/operator/production_integer_compaction_v1/ACTUAL_GATES.md`。
- MA040d通过B1/B16 × SR1/power2的独立存储图四例；不能代替真实 shared arena、一般SR或服务图。
- 当前 MAIN **MA06a0** 是唯一 live 四卡 independent all-T 操作，源冻结。18:49 HANDOFF确认四片running；MAIN18:52补充观察24个 native split anchors均过，分片进度约261/160/107/76步。这是运行进度，**没有完整64case/四片终态 PASS**。仅 MAIN继续观察该同一操作，不重新启动。
- MA0670 selected isolated败于P1 singleton stride2仍可能contiguous的负例夹具；MA0674 native feedback败于decorated-callable来源绑定，均在正式数值case之前。它们不是DAMP算法失败，也不能当selected组件PASS。
- MA0455 full ON完成36×4096生成，但OFF/ON29个输出不同、7个相同，prompt哈希全部相同。真实静态原terminal completed/exit1/error=`exit code`，duration10739597ms≈2.983h；原SHA `aff014c739ba203210fdeea80d151353fc4edc0b3a9ffd6ca35292bb8a7bf38a`。失败父容器已由MAIN停止保留。不存在合法full SOURCE_LOCK、最终192计划、候选服务、E2E或任务结果。

## 2. 最短依赖图：禁止无关阻塞，也禁止越过相关门禁

```text
实际 native/SO/source/ABI + original parent terminal/stopped + fresh资源
  ├─ 当前 restricted allT + shared-arena + eager/graph      [MA06a0 running]
  ├─ 修正selected来源/夹具 → isolated + B1/B16 native反馈  [pending]
  │    └─ true P2–8 / P9–15 → all-P原始执行授权             [pending]
  ├─ synthetic general-SR同压缩算法数值                    [旧v1实际PASS；新ABI补证另列]
  └─ C1 fixed-admission OFF/OFF/ON短诊断                    [NEW准备；不是full校准]
          └─ 可信full TRAIN OFF/ON同token + raw全部覆盖
               └─ 合法SOURCE_LOCK + 成功parent finalize
                    └─ CPU fit/tune/frozen-validation的192真实计划
                         └─ CPU admission + same-dense预算
                              └─ final192四rank eager/graph独立数值 → aggregate
                                  └─ 一般SR真实T/P与实际192安装/缓存/48×4 lifecycle
selected/allP + allT + final192 + 真实cache/receiver/预算/source authority
  └─ checked真实TP4 mixed/continuation/reset/暂停/回收/异常数值
       └─ 另经验证的formal无hot-D2H/设备错误退休路径
            └─ 同协议dense/candidate固定1024配对性能（≥10%，TTFT/TPOT分报）
                 └─ normal-EOS2048 LongBench-v2/GSM8K及三次配对 → 最终验收
```

分支是证据关系，不是执行权。TP4采集/真实模型/所有性能与profiling均独占4–7；只允许MAIN在鲜检查后把独立正确性作业放到不重叠单卡。0–3永远保护；没有实际worker且HBM/AICore空闲的设备声明不算计算占用。

| 证据项 | 是否真正需要full SOURCE_LOCK | 现在可到哪一步，不能升格什么 |
| --- | --- | --- |
| identity/power2 trueT1–16 shared-arena/图 | 否 | 当前操作正在真实运行；不证明generalSR/final192/model |
| synthetic一般正FP32 SR +原始坐标误差/量化 | 否 | 原v1 B1/B16已过；一般SR不得使用BF16缩放native作唯一oracle |
| IEEE FP32 x/SR、selected pack、native chunk/unpack→own反馈、trueP2–15 | 否 | 需要真实native绑定/参考锚点、原始stage/operation授权；当前selected失败尚待修证 |
| C1 OFF/OFF/ON首次分歧诊断 | 否 | 可定位native采集非干扰问题；即使PASS也不是full36/4096 |
| CPU selector、真实192 CPU admission | **是** | 冻结代码会重验full原始parity与raw；不能从failed capture或smoke拟合正式计划 |
| 最终192 NPU eager/graph与aggregate | **是**，通过index/admission/原始validation初态 | 每个rank48plans；不会由syntheticSR或thin case count替代 |
| actual192 checked assembly/48×4真实缓存/服务 | **是**，且上述组件/预算/lifecycle | 配置缺权限即拒绝；只通过算子不可启动正式测量 |
| 形式化配对性能/任务精度 | 间接需要已验收候选完整依赖 | 不能把诊断状态同步/CPU oracle时间当10%收益 |

数学上独立测试一组synthetic SR无需全模型校准；本项目正式校准的来源门禁仍必须遵守。这两个事实不矛盾。真实T2–15的一般SR参考必须经过独立FP32reference的实际whole-vs-row锚点；当前identity/power2 native锚点不能自动扩大到它。

## 3. 五个已定位的可执行缺口

### A. selected来源/夹具：必要修复，不改算术

MAIN/operator已识别最小后继：P1索引负例改为**真实P2**的distinct indices、stride2，先验确认noncontiguous；decorated native来源证明要覆盖原body及已部署wrapper/alias/closure/code/backlink，仍调用原decorated外层，而不是绕过wrapper调用unwrap。helper/runtime/actual-image来源51/26等后继闭包必须实际落盘核验后统一更新；当前7ea等旧pin不能假装已修。

先运行实际同镜像源/fixture/CLI预检，再鲜单卡canary、完整isolated134case/57negative和native8case×160；保留47checks/44hostneg已执行范围和两个原失败。原矩阵、1e-5/.00303、partial-write全call退休规则不变。两个完整组件授权后，才允许trueP中间批次引用它们。

### B. all-P与assembly桥：不是补一个ready=true

实际 `integration/service_assembly_v1/damp_checked_assembly/authority.py:68–83` 仍要求all-P helper在frozen closure，却在:78调用 `allp_module.validate(report, terminal)`。已冻结新API为：

```python
validate_complete(selected_inputs, lower_run, upper_run, read_bytes,
                  source_manifest=Ref(...), enabled=True)
```

`SelectedInputs` 要带原isolated/native两份完整旧RunAuthority及旧source-manifest；lower/upper需要原report/child/terminal、准确peer/opid/host Docker argv/cwd、container/proof/controller、same-process loaded/source、28个native-before checkpoints和逐row journal。不得把image Python替换真实host `/usr/bin/docker`，不得把唯一 `--` 两侧的packet flags混成重复参数。

当前assembly12仅source/software准备；需MAIN审阅NEW窄config/bridge/closure与producer-shaped行为回归，真实all-P原回执验证后才能引用。operator Agent只读准备该薄桥，本文不修改它。就算桥接完成，standalone eager PCP1、all-fresh/all-continuing、prebuilt_meta=None仍不证明真实mixed/prebuilt或48×4缓存。

### C. full新采集权威：不能只换hash

`tools/post_reference_plan_v1/post_reference_contract.py:14–18,107–138` 硬绑定原failed的resume AUDIT/CAPTURE/LOCK路径，`finalized` 要求无FAILURE/STOP_FAILURE及成功独立parent RESULT。`calibration/damp_calibrate/evidence.py:31–72` 要求full/smoke真实validation、重跑frozen full validator并完全相等。

因此新fixed-admission诊断/新full采集若成功，**仍需NEW、源绑定、受审阅的实际root/terminal/finalize适配**；不能回填旧失败RESULT、把短C1报告放到旧full锁里，或仅替换SHA冒充原MA0455成功。`final_plan_gate_v1/run.py:57–60` 也要求相同原parent路径，后继必须coherent适配完整依赖而非偷偷改常量。

当前NEW `tools/fixed_admission_capture_v1/` 由calibration Agent准备14文件；截至本审计未MAIN全文审阅/同镜像预检/NPU。仅C1/1024/33 OFF-A/OFF-B/ON、共同observer、45min诊断设计。OFF native shapes未知；ON实际1→4/1→2→4；最早token11早于anchor256，不能只怪anchor写盘。先OFF/OFF确认可重复，再ON比较相同输入/before/after，不能无证据原样重复36×4096。

### D. standalone float调度尚有真terminal bug

底层float compiled9/runtime15/fixed4及真实SO/build不等于dispatcher admission。实际 `tools/prefill_float_dispatch_v1/dispatch.py:196–210` 仍要求completed record.error为None，:359/:640直接调用它。真实MA0455为completed非零、error=`exit code`，该旧execute必拒绝。NEWselected97fd和independent allT已作正确窄修，**没有自动修复旧float**。

若MAIN认为独立float全matrix是下一相关缺证据，先NEW窄适配复用已经审阅的真实terminal/stopped guard，再source closure/behavior/CLI/同镜像检查；否则只执行已审selected后继，不重复跑已知拒绝的旧float命令。不能改原terminal、删异常检查或把READY文字当实际代码合同。

### E. all-T旧consumer结构兼容，不等于NEW执行授权

实际 `integration/service_all_batch_v2/damp_service_all_batch/identity.py:77–115` 调用旧 `tests/all_batch_gate_v1/contract.py:186–230` 的 `validate_shards(reports)`。NEW independent runner保留该old schema/status、compiled9/runtime20/SO与完整限制，所以**未来四片全量真实PASS报告在结构上可复用**；不需要重跑同一矩阵来满足这个old schema。

但旧consumer没有核NEW `execution_packet`、每片六个 `native_row_reference` anchors、NEWpacket、source-before/after或MAIN原始outer terminal。实际 `tools/independent_allT_dispatch_v1/independent_contract.py:146–167` 的 `validate_shards(reports, packet_sha)` 才核新增24anchor/source后再调用旧validator。进入assembly前应由NEW受审source-bound薄桥核该API、原child/outer执行authority，再把原四报告原样交旧parser；不能仅结构兼容或thin status签ready。本审计未执行该consumer，当前MA06a0未终态，generalSR/final192/模型缓存仍不在scope。


## 4. MAIN待办：原入口可复用，ready/pending逐项明确

所有命令的cwd均为 `/opt/host/vnf/austinov/model-tuning-lab`。以下源/默认OFF检查不授予Docker/NPU执行；真实execute只由MAIN在操作终态、exact-owned停止保留、fresh proof和新的非覆盖输出后进行。

1. **正在执行，不另启动：**完成MA06a0及四片原report/child/terminal、全部64case、6anchors/片、source-before/after、保护0–3和owned release。失败按最小真实原因修后继，不混入校准成功条件。保留目前进度与尾部等待原因。
2. **冻结解除后纠错准备（pending后继source）：**完成A的统一来源闭包和实际镜像预检。原source-only入口可审：
   `/usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_source_preflight_v1/preflight.py`；
   `/usr/bin/python3 -B projects/damp-ascend/tools/selected_prefill_dispatch_v1/test_dispatch.py`。
   具体后继选项/packet SHA由实际冻结给出，不能使用旧execute原样重跑失败。
3. **两stage完整通过后，准备真实P补证（已有源/CLI，数值未就绪）：**
   `/usr/bin/python3 -B projects/damp-ascend/tools/native_prefill_intermediate_v1/runner.py --check-sources`；
   `/usr/bin/python3 -B projects/damp-ascend/tools/native_prefill_intermediate_v1/test_runner.py`。
   原 `runner.py --execute --shard P2-8|P9-15` 的真实build/reference/device/packet参数见该目录READY；需要来源修正后的coherent pin和MAIN producer、原operation authority，不靠未来文件名。
   四case/P×160保持完整；两片5400s/8100s+180cleanup，1CPU/8GiB各，aggregate24GiB普通RAM。启动前必须实际剩余时间足够，不降矩阵。
4. **固定admission短诊断（NEW准备，NOT launchable）：**MAIN全文审阅14文件、实际镜像callback/fixture/CLI/sourceproof后，才考虑TP4独占45min OFF/OFF/ON。若失败保留首次分歧；若成功明确仅短scope，然后决定是否存在可信、已准备且剩余预算足够的full来源路线。无ready full-controller时不把卡耗在盲full重跑。
5. **仅合法full finalize后：**复用CPU selector、CPU admission、四片final192。源中的可审入口：
   `/usr/bin/python3 -B projects/damp-ascend/tools/cpu_selector_dispatch_v1/plan.py`；
   `/usr/bin/python3 -B projects/damp-ascend/tools/post_reference_plan_v1/run.py`；
   `/usr/bin/python3 -B projects/damp-ascend/tools/final_plan_gate_v1/run.py`。
   当前它们输出planning而非PASS。selector实际执行需要合法lock/result SHA、no-device image、2CPU/4GiB+8GiB普通reserve；前3个plan完成时长和cgroup peak给真实剩余估计，8h只是timeout。完整192 CPU admission需要实际same-dense common/FA/page/transient预算，不能用示例整数。
6. **最终192实际门禁（pending锁/index/admission/新root适配）：**四rank各48plans，原CLI `--mode all --rank r --physical-device 4+r`，实际index/admission/lock/parent/native/reference/source/device SHA一项不缺；每片独立6×160reference anchors，B1/B16×eager/graph×160 own-feedback。共122880个plan feedback steps，不是“192次调用”。四片实际PASS后使用 `aggregate.py --execute --shard path sha` ×4，`final_contract.validate_complete(report, read_case)` 验完整case/hash；只返回最终计划数值scope，不是serve_ready。
7. **服务源准备与真实gate（pending）：**完成B桥、真实immutable192 plans冷安装、ND/真实byte spans/common budget；真实native conv全row、chunk suffix、继续prefill selected unpack、真实prebuilt/mixed身份、FA/GDN共享arena、paused/ABA/回收/零状态/异常全worker退休、实际48层×4rank完整提交。
   原 `integration/service_assembly_v1/serve.py` 默认OFF、`--check-only`、`--execute` API存在，但没有可用成功config；不得造它。其checked observer/status D2H明确不能正式性能。formal-safe路径尚需实际设计/证据，不是删除检查后直接测。
8. **相关数值/lifecycle满足后立即配对服务screen，不继续无收益prep：**相同C16/TP4/固定1024输出、共同优化/内存预算、profile OFF；TTFT/TPOT/throughput分别，三次配对，至少10%端到端收益。最终thinkOFF/temperature0/seed0/max2048/normalEOS LongBench-v2与GSM8K，报告相对和百分点损失及原无损目标。1%任务允许值绝不能替代1e-5/.00303 tensor门禁。正式比较不能与fit/build/数值分片重叠。

源例子只确认现有API，不是将缺失hash补成占位PASS。新的full-root adapter、generalSR trueT参考锚点、formal-safe service path、完整benchmark/config尚缺，必须明示pending；不新增大型通用controller来回避这些关键缺口。

## 5. 剩余窗口与卡利用：可完成范围与不承诺范围

- **近期有界目标：**收尾当前allT真实矩阵；解除freeze后完成两处selected source/fixture修复与实际预检，跑完整组件门禁；完成C1短诊断的实际source/no-device admission。组件数值成功不能作为用户要求的最终落地，但确实直接清除算法迁移阻塞。
- **条件性执行：**只有selected/native全部真实过、corrected来源/producer闭包和时间足够时才发两片trueP；若独立两个dispatch的资源monitor不互认同owner/disjoint cgroup，不得假“并行ready”。只经MAIN审阅新symmetric admission后并行。
- **没有可证完成预算的尾段：**旧完整OFF约2.6h，真实MA0455 ON恢复2.983h；新固定调度fullpair不同不能把旧时间当保证，也不能未经同源证明复用旧OFF。再加8h selector timeout已大于18:54时剩余窗口，且还未计实际final192、trueP、48×4 lifecycle、formal-safe service、三次性能及任务。8h不是预测，所以不能据此证明论文无效，但**不能承诺在本24h窗口完成所有尾段**。CPUfit/final192真实峰值/每plan耗时尚缺；用前3plans实测而非凭少量软件测试推完成时间。
- trueP历史源记录的真实stdlib冷10k SR除法≈1.014s、热≈.0031s；93,585,408次Fraction decisions外推纯标量约2.64CPUh，两片约.78/1.86h，另有76,160个B1 reference calls、Torch/复制/同步/hash/压力量，均未计。这个外推不是NPU性能，也不保证5400/8100s。历史MB03ac记录本次operation_get已返回not_found；这里只沿用已冻结READY中明确历史值，未声称fresh重测。
- 当前连续T分组oracle成本 `sumT=10/26/42/58`，MAIN已观测其进度不均。**不修改、不重启live矩阵**。未来同样16T/64case矩阵可在NEW受审分组使用 `{1,8,9,16}/{2,7,10,15}/{3,6,11,14}/{4,5,12,13}`，各sumT34；还应实测CPU/graph开销再定，不把估计当吞吐。现CLI/authority绑定连续shards，必须后继coherent更新，不能暗改当前参数。
- 若某片提前完成，先真实stop-retain/release，尾部等待说明是预注册oracle成本，不填dummy。当前controller独占整组、原owner兼容协议未必允许中途另launch；只有MAIN确认disjoint admission和冻结依赖不受影响才放另一个**已就绪且相关**组件。否则利用CPUagent准备即可。
- 截止前无完整尾链则DAMP当前实现按 **inconclusive / 缺最终192、服务、配对性能与任务证据** 结案，保留safe defaultOFF及成功/失败原件；不是paper-wide no-go，不延DAMP计时。按既定DAMP→KVBuffer队列转下一distinct FP32 parallel-fold候选，其准备不是已开始正式24h，也不是旧serial负screen的原样重复。portfolio最后一天仍保留正式重复性能/最终任务预算。

## 6. 来源与审核边界

读取：canonical AGENTS、maintainer host/orientation/loop/paper/benchmark skills、branch最新HANDOFF/SCHEDULING/THREE_DAY_CLOSEOUT、calibration evidence/selector、post-reference、CPU admission、final192 runner/validator、general-SR/reference、selected/allP/float ready contracts、assembly/PlanStore/continuous-core和capture parity source audit。来源为本机实际文件，不是猜历史上下文。

MB03ef source-only read/hash，peer_direct→`lgw_53d59c2f73ef4b81ba3cc0e00c2f8d35`，completed0；没有model/设备/容器/Git操作。MB03f3把可变治理skill也误归冻结来源，原exit1保留：MAIN新增成本均衡条款使loop skill7180→7647B，不是算法漂移。已全文重读新skill；MB03f4的新源检查completed0、15项project来源全未变化，只记录该正常治理修订。核心源码SHA（本次真实读取；loop列为后一次MB03f4的现值）：

| path relative to canonical repository | SHA256 |
| --- | --- |
| .agents/skills/ascend-inference-tuning-loop/SKILL.md | 9f3d52f995085fe49358e51215b2e32dd5db4aa9fdc3dc8ef50b21e84a80af21 |
| .agents/skills/ascend-inference-tuning-loop/references/damp-migration-gates.md | 7b74c039f7176516939784407c3d01fe7da4567f793442877c50c7d3ed5e7219 |
| .agents/skills/paper-to-ascend/SKILL.md | d91abda6c131da0bee2583cd1ad63f6b9303be1223b83cda5675114b0bac47e6 |
| .agents/skills/ascend-benchmark-evidence/SKILL.md | 8985d1584bba855f76d8a57bbd04e0c6fdd52731e9d0eaa3e2325d6565de8223 |
| calibration/damp_calibrate/evidence.py (under projects/damp-ascend) | 3141314904cd5d3abbbedc15aed7c0f97a2370b9a435824cd7505073df16f5fa |
| calibration/damp_calibrate/pipeline.py (same project) | 641052ababa29c46440ab86fdc20fd6894737c8bf9afa9b240f4b687d1e35a55 |
| tools/post_reference_plan_v1/post_reference_contract.py (same project) | 643f0ce23c7e6a45471f2e8d37439634ab74e27a92c90ed47ea9767312ce4e78 |
| tools/final_plan_gate_v1/run.py (same project) | 95435fc1d2deca643251782e58eac695115eb8d8a42096bc69233735051c89da |
| tools/final_plan_gate_v1/final_contract.py (same project) | b10670ddb9b83a85fa4c6a13cd2f7c7ce6fc8105a8579692fc697cfef316acc5 |
| tools/calibrated_plan_admission_v2/admission.py (same project) | 53f4abc937505a970352d40ebe062293949a299c9ad291799c90e82cd9d2b4e5 |
| integration/service_assembly_v1/damp_checked_assembly/authority.py (same project) | 6564e09ba21f07189167b427c1614a080fde61d1119397391eff638f84228977 |
| integration/service_all_batch_v2/damp_service_all_batch/plan.py (same project) | cf8d17b4b1fe9e943b325e069557f25afdd4afa8406fa42055dc8aa1359032d6 |
| integration/service_all_batch_v2/damp_service_all_batch/identity.py (same project) | 7036cdccb6c7257918bae9d88dfa9cf028a9d4e829d742339c284df4f14ba5b7 |
| tests/all_batch_gate_v1/contract.py (same project) | f42a42ce36dc18cb65381f00ac3a4737cb8b50dbf50b22bf90a719dd800d87fd |
| tools/independent_allT_dispatch_v1/independent_contract.py (same project) | cd37e68500ba73d4a2bc7f1ab0b3c1392648f2592b93f373a402ab78eebdb272 |
| tools/independent_allT_dispatch_v1/runner.py (same project) | cedaa1f8aea6de829af1f203a0a014859a99525d1c22b4530c8082d99d18293d |
| tools/prefill_float_dispatch_v1/dispatch.py (same project) | 094defb90bfc6d748d13069a48bd24297d01caaab1720ef5b8a3bc32ecf87c9e |

Live documentation/source checkpoint may change after this read; onlyMAIN更新实际终态，不从本文件推定未来设备空闲或PASS。本文没有改skill、签lock、创建RunAuthority、隐藏FP32sidecar、解除数值门禁，或声称正式性能/精度。MAIN需全文审阅后决定后继最小工程动作及scoped checkpoint。
