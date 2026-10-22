# Projection 诊断读取器：待最终源哈希绑定的本地审查稿

这份扩展只读一个完整 ON 两请求诊断，保留原 boundary reader V2 的主机、单臂状态、清理、原始数值和预算谓词。它不调用 `R.compare`，不替换先前 ON/OFF 配对失败，不授予数值、性能或任务精度门禁。当前主入口明确失败封闭，等待 MAIN 对新五个 helper 与独立 auditor v3 的最终 Ref 绑定；这些字段不得用推测值填充。

## 新增的独立验证

- 完整文件集为每 rank 150 文件、其中 132 JSON 与原有 18 raw；`COMPLETE.references` 恰有 149 项，不含自身。新增两代 `PROJECTION-INTERNAL` 整个 envelope 各不超过 8192 B，所有输入仍按完整 SHA、长度、普通文件、无符号链接及前后身份不变验证。
- 每代顺序要求 `NATIVE-L00 < RAW-gated_norm < PROJECTION-INTERNAL < 原 out_projection.bin < NATIVE-L01`。原其他 native、phase、raw 和退休顺序全部保留。新 `COMPLETE` 还必须见证 projection observer 已恢复及两条完整记录。
- 五个已固定 guest runtime Ref 与新 source 的 `evidence/*` host 副本逐个匹配；只打开 host 副本。逐个重新读取完整源文件，独立解析 AST，校验实际 role、receiver、方法位置、支持的 reduction callsite、destination 和 fusion 类型。没有读取 guest 路径或导入模型代码。
- 方法 code SHA 是生产者 Python runtime 的 `marshal.dumps(code)` 见证。生产者已对完整模块编译结果与真实方法做相等检查；host reader 不跨 Python 版本重编译并冒称 bytecode 证明。五个调用方源文件的 pin 不扩大为 collective alias、通信实现、HCCL 或设备 kernel pin。
- 五个阶段固定存在，每个要么是完整实际逻辑 tensor 的有限 hash/geometry 见证，要么明确给出生产者支持的不可观测原因。融合必须由真实固定源 callsite 见证，不能由缺少 `quant_return` 推断。reduce-scatter 的中间形状可以与最终输出不同。
- 每个 observed stage 独立计费，ordinal 单调唯一；单次不超过 2 MiB，每代不超过 8 MiB，两代不超过 16 MiB。新增读量加到原退休和 COMPLETE 的累计读量校验，原 512 MiB、metadata 512 KiB、raw 836352 B、OTHER 3 MiB 与 64 KiB 余量约束保持。

## 输出解释

读取器同时报告跨代五阶段、同代四 rank、以及 norm→input、quant→pre、post→return、return→原 outer hook 的 join。SHA 相等、逻辑元数据相等和 geometry 差异分开报告；任何 join 的值相等均不是新增准入要求。缺少观测时相等字段为 `null`，不会默认成 `false` 或 `true`。每个阶段保留完整生产者 record，首个不同位置仅称为“首次观察到的 hash 差异”，不归因为具体 kernel。

`no_reduce_callsite_executed` 只表示未记录受支持 reduction callsite，后续 `all_gather` 等通信仍可能执行。权重只有版本和 geometry 元数据，没有内容 hash，也没有后台私有 format 证明。跨 TP rank 的 tensor 可能是不同 shard，因此跨 rank 相等只是观察值。

## 本地检查范围

新增 15 个 focused controls 使用明确标注的 synthetic record/AST，涵盖非融合、融合、inline return、scatter、无受支持 reduction、错误 stage/Ref 映射/callsite/receiver/计费/finite/geometry、闭包及未知值处理。本地首次执行全部通过；没有执行模型、NPU、容器或远端进程，也没有重复旧 13 项 controls。

独立 AST 比较确认旧 reader 的 `whole_file`、`Readset`、`original_readers`、`validate_host`、`validate_original_arm`、`geometry`、`slot_record`、`inventory`、`terminal_budget`、`bf16_compare`、`compare_rank`、`compare_http` 等 27 个函数/类完全不变。原函数中仅源身份入口、文件集合/顺序、加入 projection 计费的单 rank 验证、main 输出扩展发生修改，没有删除原函数。

额外用本地实际 SHA 匹配的 ascend linear、linear_op、upstream linear 全文解析九个真实方法，恢复了实际 generic、fused、Flashcomm2 和 Sequence callsite；与已审查源码行号一致。这是 source-only 解析核验。

## 执行包装

`run_projection_reader_once_v1.py` 派生自原已审查 v2 包装器。actual 与 controls 使用两个固定且不同的新输出目录，输出只能排他创建。512 MiB、CPU 180 s、wall 240 s、单文件 64 MiB、仅清理自有 child group、stdout/stderr、原样 traceback、输入前后 Ref 记录保持。controls 只运行新增 15 项，不读取实际模型 RESULT；actual 必须给齐三个真实 Ref，结果文件名为 `PROJECTION_DIAGNOSTIC.json`。两种模式都不启动 NPU，exit0 仅分别表示局部 controls 或完整只读证据有效。

当前读器与包装器均未冻结，最终部署必须以 MAIN 审查后的完整源码 SHA 为准。现有 boundary V1 结果、原 reader V2、所有旧失败证据均未修改。

## 已保存的本地复核

`LOCAL_CONTROL_EXECUTION.json` 保存了 15 项最终局部执行的原始 stdout/stderr Ref、实际本地 Python 版本、五份输入源码前后 SHA、Python 3.9 grammar 检查和旧 reader AST 比较。状态仅为 `PASS_LOCAL_SOURCE_CONTROLS`，`main_entry_executed`、`reader_frozen`、`wrapper_frozen`、`NPU` 及全部资格字段均为 false。

state_causal_review 与 lowobs_readiness_review 分别对 reader 93803 B / `17e3072fd7f7ecad89d0f1d6aacc731458a9065cb87674853a8c08b62e01b33e` 完成独立静态审查，未发现确定的生产者不兼容或解释阻断。他们没有重跑旧控件、运行 reader 主入口或修改原证据。`LOCAL_PIN_CANDIDATES.json` 仅记录当前本地候选源码字节，明确不是 MAIN 审查后的 pin。
