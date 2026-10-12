# HYPIC r19 · 2048-token 配对质量最终负结果报告

> 状态：**final negative quality report**。报告覆盖 r19 四个完整质量阶段，
> 不是整个三阶段目标完成，也不是 HYPIC 全论文、性能或生产采用验收。
> 实现：HYPIC v0.8.5 派生源码 `4429e35177979c874bf053ab29789e4773f39b22`。
> 设备实验发生于 2026-10-10；本次 2026-10-12 只读复核，不重新上卡。

结论：LongBench 显式分段全请求质量 227/381→219/381，冻结判定
`REJECT_OR_QUALIFY`；GSM8K 自然请求安全 3838/3957→3840/3957，
为 off-path PASS。两项数据都已完整收齐，不能把质量不通过说成
“精度测试尚未完成”。质量下降的技术因果根仍未证明。

## Step 0. 环境准备、源身份与证据范围

chicaihong01 EulerOS/aarch64、Ascend910B4，物理0–3一一映射到
容器0–3，单副本TP4，CPU112–191、CPU binding关闭，端口8223。
禁止使用物理4–7或修改外来任务。上下文41984、内存比例0.85、
material cache3584MiB/10段。模型目录 `/cache/efim/Qwen3.6-27B`；
模型索引SHA256
`a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`。
这不是对所有权重分片逐字节完整性的额外证明。独立 tokenizer 全文件摘要和
当时逐包驱动/CANN/vLLM版本清单未在本报告取得，不以当前安装版本补写历史。

镜像：
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`。
两组均挂载 `/cache/cch/hypic_vllm_ascend-hotproof-20261008:/source-hypic:ro`，
实际导入为 `/opt/hypic/hypic_vllm_ascend/__init__.py`。
四个阶段的实际启动命令、bind、镜像、源码树摘要分别保存在各根
`ARM/source-attestation.json`；本次复核逐项与冻结服务配置比较。
没有重新下载或重建镜像；不伪造一条历史拉取命令。

当前源码比仓库历史 `3ad0967` 多一个提交，含 pending-materialization
调度保护与逐请求热证明，不是相同源码，也不只是日志。
同事的Qwen3.5/TP2实践与2026-09-06仓库Qwen3.6/TP4案例是两份
历史参考，不能混成一个精确基线。员工环境与3ad0967逐字节一致性未证明。

预检必须新鲜解析 ma、证明直连、核验物理0–3和8223真实空闲。
当时每组都有持续物理进程守卫和自有资源精确释放收据；旧释放记录
不表示现在设备空闲。连接认证仅在连接器字段传递，不属于下面命令。

## Step 1. 分组与冻结评测协议

| 组 | 服务开关 | 其他差异 |
| --- | --- | --- |
| G1 no-cache | VLLM_ASCEND_HYPIC_ENABLE=0 | 独立输出根和证据文件路径 |
| G2 hypic-only | VLLM_ASCEND_HYPIC_ENABLE=1 | 独立输出根和证据文件路径 |

每个数据集内双方模型、镜像、源码、容量、请求和评分配置匹配。
质量为max2048、自然EOS、temperature0、seed0、thinking关闭、c32、三轮。
**2048是最大输出，不是要求固定生成2048。** 没有把性能服务的ignore_eos
参数混入精度测试。

- LongBench-v2：127题。路径
  `/cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json`；
  SHA256 `cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a`。
  每题两次1-token预热，三次计分；题内依次执行，最多32题并发。
  两组都传显式段边界，边界规则见冻结审计的 `payload_hash` /
  `frozen_cases`；一个串行热哨兵后，首32题并发波包含在全量计分中。
- GSM8K：1319题。路径
  `/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl`；
  SHA256 `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`。
  三次整套评测，自然chat请求，没有显式可复用段，故只证明off-path安全。
- 冻结评分器：
  `/cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py`；
  SHA256 `9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0`。
  提示词构造、答案提取和评分以此文件为准，独立审计重新构造并重评分，
  不从答案文本相似度推断正确性。

预登记文件：
`HYPIC_R19_REPAIRED_C32_2048_PREREGISTRATION_20261010.json`
（SHA256 `0a949a279dc75cffd20f2143320a56022bd4707c3a7018e626dc4b54e0d87722`）；
`HYPIC_R19_GSM8K_PHASE_PREREGISTRATION_20261010.json`
（SHA256 `1f470d1d37a99a4f5a6141c2bccb2a84460424b958b09c0c87281e236c3773af`）。

## Step 2. 基线与候选部署、评测及停止

以下为已执行方式的源码绑定入口，**不得重跑既有根**。
入口会核验预登记文件内全部支持代码哈希；所需镜像和源码已在主机，
完整实际容器命令在四份source-attestation中，不用简写替代收据。
运行目录为本报告所在工作流目录。

```sh
cd /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007
HYPIC_R19_ARM=no-cache python3 -B r19_repaired_c32_longbench_adapter.py --run
HYPIC_R19_ARM=hypic-only python3 -B r19_repaired_c32_longbench_adapter.py --run
HYPIC_R19_GSM8K_ARM=no-cache python3 -B r19_c32_gsm8k_adapter.py --run
HYPIC_R19_GSM8K_ARM=hypic-only python3 -B r19_c32_gsm8k_adapter.py --run
```

四个入口分别创建新服务、完成健康/源身份/worker核验、运行本组质量，
最后调用冻结 `binding_off_quality.cleanup(arm, container_id)` 精确清理。
各根`ARM/service-stop.json`与`ARM/lane-guard.json`是实际停止/隔离证据，
不是仅凭控制器退出码断定已释放。现在这四个容器已删除，
没有需要再次执行的旧停止命令或同根续跑命令。

## Step 3. 实际逐组流程与完整性

下表为2026-10-10 UTC的service-start到service-stop收据时间，
不含全部启动前准备时长，不作为推理性能指标：

| 阶段 | 开始 | 精确释放 | 有效计分 | 最终响应失败 |
| --- | --- | --- | --- | --- |
| LongBench G1 | 11:06:46 | 12:14:03 | 381/381 | 0 |
| LongBench G2 | 12:24:07 | 13:43:17 | 381/381 | 0 |
| GSM8K G1 | 14:13:40 | 15:37:27 | 3957/3957 | 0 |
| GSM8K G2 | 15:48:22 | 17:11:41 | 3957/3957 | 0 |

每组LongBench127个唯一题×3，每组GSM8K1319个唯一题×3；
合计8676条计分响应。预热和短Canary不进入分数分母。
没有因冷路径、达到输出上限或答案错误后验删样本。
GSM8K命令设重试预算2；原始行未保存每次HTTP尝试数，
因此只能确认最终零失败，不能声称底层零重试。

实际顺序是质量先完成，未运行该源码的采用性能测试。
这偏离模板中常见的性能先行顺序，是r19预登记质量优先规则，
不是补写历史。CANN profiler不是这两个质量计分任务的必要条件，
本报告不提出算子或通信根因归属。

## 实测结果：完整质量，不等于质量通过

| 数据集 | G1正确/总数 | G2正确/总数 | G1三轮正确数 | G2三轮正确数 | 差值pp | 冻结判定 |
| --- | --- | --- | --- | --- | --- | --- |
| longbench | 227/381 | 219/381 | 74/77/76 | 73/70/76 | -2.099738 | REJECT_OR_QUALIFY |
| gsm8k | 3838/3957 | 3840/3957 | 1280/1274/1284 | 1281/1279/1280 | +0.050543 | PASS |

三轮正确率均值 ± 样本标准差：
- LongBench G1 **59.580052 ± 1.202776**，G2 **57.480315 ± 2.362205**。
- GSM8K G1 **96.992671 ± 0.381594**，G2 **97.043215 ± 0.075815**。
均值单位为%，标准差单位为百分点；不是置信区间。
差值公式是 `(G2正确数-G1正确数)/每组总响应数*100`。

LongBench：15个改善、23个退化；输出达到上限49→67。
候选平均73题正确，低于基线单轮最低74；候选平均截断22.33，
高于基线最大17；easy/short分类亦触发冻结门槛。
GSM8K：12个改善、10个退化；截断28→27，冻结安全门槛通过。
不能让GSM8K通过覆盖LongBench拒绝，也不能混合两个数据集算一个“总体通过率”。

### 机制、性能与历史参考

LongBench有381/381显式边界记录。补充的逐ID核对将536个
`worker_hot_request_verified`事件唯一关联到134条计分响应，每条都
包含同一服务四个worker；物理PID到容器PID映射与收据一致。
其余247条**未证明热命中**，不等于已经证明是冷请求。
原始配对审计内“仅聚合证明”的措辞被这个后续证据补充，不修改旧文件。
这仍不构成381/381机制全覆盖，也不提供每个decode step证明。

**同源码性能未测。** r13的三轮weighted TPOT下降21.5243%、
TTFT P95节省40.8694s属于另一个源码c12060c及其固定输出性能尺；
这里只作历史参考，不拼接为4429e35的“性能与精度完整通过”。
论文数字不作为本次测量或门槛。历史1024输出案例不改写为2048证据。

## Decision 与结论

| 门槛 | 判定 | 允许解释 |
| --- | --- | --- |
| 数据/评分/源身份/隔离/释放 | 有效 | 四个完整质量阶段可以报告 |
| 显式分段全请求质量 | REJECT_OR_QUALIFY | 在冻结尺上观察到下降 |
| GSM8K自然请求安全 | PASS，off-path | 仅该任务开插件安全性 |
| 每条计分请求机制覆盖 | 未通过 | 134/381，不能声称全部走热路径 |
| 当前源码性能收益 | 未测 | 不从r13转借 |
| 数值/通信/缓存质量根因 | 未证明 | 不能把相关性当因果 |
| 生产采用/全论文/全Skill验收 | 未通过/未完成 | 不是本报告完成所能推导 |

**允许声称：** 两个数据集的当前源码质量测试已完成并独立审计，
LongBench负结果和GSM8K安全结果均有效。
**禁止声称：** 无损、HYPIC已整体成功、质量根因已定位、
当前源码同样快、main/远端已同步或29个Skill全部通过。
**仍未证明：** 当前源码性能；LongBench下降的单一技术原因；
完整HYPIC采用；剩余Skill功能验收。报告负结果不需要无限追加诊断。

## 报错、失败和排除边界

本报告四个正式arm中唯一终态控制器错误是LongBench G2在全部381条
保存后报`candidate scored boundary/hot coverage incomplete`（exit1）。
这属于机制覆盖门槛失败，不是请求丢失或清理失败；所有响应保留计分。
全请求质量门槛另行失败，不能把两者互相替代。

r18原始3ad0967/c32在33/127题终止，r22小样本诊断以及r23–r25观察器
故障/修复都不是这四个arm，不纳入其分母，也不要求为完成此报告重跑。
r19的完整四arm没有发现外来进程或守卫探测错误；对应守卫样本为
865/997/991/990。精确释放全部通过，外来任务与物理4–7未被本任务停止或修改。

## 证据索引与可重复审计

配对审计：
- LongBench：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r19-c32-2048-longbench-paired-audit.json`，
  SHA256 `40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`。
- GSM8K：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r19-c32-2048-gsm8k-paired-audit.json`，
  SHA256 `496f1dfacb3c3a8dd03f8ee07368fb142b432498c0ee5dbb5722e1d4f85fd187`。

四个原始根及其独立源身份证据：

- longbench/G1：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-baseline`
  - arm-result SHA256：`a37204901a95768121e116e72a3978ee64865ca085b09b4993265431133c200d`
  - contract SHA256：`2071d4d80e2496d9d3bc583e8c87d0f0d6d790c0efdd1f59195214ff0f5f4154`
  - source-attestation SHA256：`c67ceb8ed8388416e620f1c95b04dbde0d55699c339eece25091f1564e38bc22`
  - 精确容器 ID：`f976bcebe9953925133bc8adec19e2716058167f35c170e929afecba04c7f197`；干净守卫采样 865 次。

- longbench/G2：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-hypic`
  - arm-result SHA256：`c1b7283c8d46ffb330af3be35232703d9b935819813a68288eb02b0608abdb74`
  - contract SHA256：`68b518b42260ec5ca9843d91242768f212b7157b1deb9245bbc2c9ac72e8c2ab`
  - source-attestation SHA256：`6d60986406beef14be49b1375d805be635ef7709d94762652056c286503d4a35`
  - 精确容器 ID：`1e186957c93fbc94e5188c2fe1a8d6fd8c60ffbb11109c833283d347ea5eca68`；干净守卫采样 997 次。

- gsm8k/G1：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-baseline`
  - arm-result SHA256：`03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897`
  - contract SHA256：`8f76b216800c8f75b293ca91aeeec3422e881126bfe79391484d897aed48b20e`
  - source-attestation SHA256：`cb03725476b63a1759fce6a33d765d314f3a57f8b7cda319489ebfdbf1b9f09d`
  - 精确容器 ID：`748ff800682d5f085fea77d7cb2b403f7bff18dca9d98bc536b07da9ca48ae98`；干净守卫采样 991 次。

- gsm8k/G2：`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-hypic`
  - arm-result SHA256：`3814b62c948bdc275cc3ef221678191c1160b97dbe2f7907c545f89f108dfa9b`
  - contract SHA256：`334804779b3f9331574c2a29c5f2f4e0568481ffb152842c9c36125a4c0e7cf5`
  - source-attestation SHA256：`a7bf16215c534ef7de559a4eaca926fc819be948af895049914a530c5c31fb28`
  - 精确容器 ID：`886d5fb47f380095527904b66e3936d3393051dea5e627434270ac031a6bb4a2`；干净守卫采样 990 次。

原始审计生成入口是`r19_repaired_c32_longbench_audit.py`和
`r19_c32_gsm8k_audit.py`，因原始OUT已存在，它们的main禁止覆盖。
下面的新只读复核入口直接调用冻结审计函数、不调用其writer/main，
重评分8676条响应并核对实际服务命令、统计公式、哈希、隔离和释放。
不是只检查文件存在，也不是新一轮模型推理。

```sh
cd /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007
python3 -B verify_r19_final_quality_report.py --check-report
```

若出现哈希、身份或评分不一致，停止对应报告结论并保留原始根；
不得用重跑覆盖证据。当前不存在该四arm的恢复运行需求。
下一步是按收敛清单处理真正缺失的验收，不重复这四组测试。
未来设备动作仍须重新核验物理0–3/8223、持续隔离、新根和冻结协议。

本次复核记录：exec0066原始响应重评分、实际命令/bind、源身份、四worker
补充关联、隔离/释放与报告数据核对通过；exec0067四项主机报告回归测试
通过，其中包含九种文本反例。此结果增加报告Skill真实任务证据，
不自动将旧r13报告的历史命令/全失败清单缺口判为已修复；该Skill总体
验收仍为partial-evidence，main29项计数不变。
