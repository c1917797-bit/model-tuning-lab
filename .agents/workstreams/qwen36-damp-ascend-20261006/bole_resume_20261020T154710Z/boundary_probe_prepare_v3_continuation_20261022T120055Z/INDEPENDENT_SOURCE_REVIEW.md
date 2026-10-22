# Continuation v3：独立源码复核（供 MAIN 最终 source review）

**结论：在已读取的22个核心文件与已声明变换范围内，未发现剩余的确定阻断。此结论仅限本地源码身份、静态依赖与内存中的逆变换检查，不是 SOURCE freeze、host controls、v4 audit、NPU或性能准入。** 原配对 FAIL 和全部最终验收缺口保持。

本次只写 `new_v3_independent_review/`，未改准备包源码。实际读取22核心文件及其旧版对照，完成全文 SHA、长度与 stat/lstat 前后稳定检查；其中13文件与 v2 字节完全相同。最后的准确文件集合以 `FINAL_CORE_REVIEW.json` 为准。[R1–R2]

## 1. 授权和时钟

| 项目 | 独立核对值 |
|---|---|
| 新内部起点 | 1792670455 = 2026-10-22 12:00:55 UTC |
| 新内部截止 | 1792692055 = 2026-10-22 18:00:55 UTC |
| 时差 | **21600秒，精确六小时** |
| 原硬报告截止 | 1792672721 = 2026-10-22 12:38:41 UTC，保持不变 |
| owner phase / cleanup | 3600 / 180秒，沿用原记账含义 |
| 完整 prepare 准入 | 3780秒，不缩短 |

新外部授权 schema 为 `bole.explicit-continuation-authorization/v1`；内部 SHORT_AUTHORITY 仍为 `bole.short-state-authority/v1`。实际对原886B票据执行纯内存转换并逐字段比较，变化恰为 `batch_id`、`scope`、`user_authorization_ref`、`historical_authority_ref`、`start_epoch`、`cutoff_epoch`、`cutoff_iso` 七项。原票据对象及本地文件未变；新历史链接指向原 ON-v2 票据。授权JSON与文档的完整Ref互相一致，`old_window_extended=False`，设备仍仅4–7并保护0–3。[R2]

parent始终固定为 `.../bole_performance_profile_prepare_20261021/successor_layer/bound-short-ON-v2/SOURCE_BOUND.json`，1503149B / SHA `a285ac43d953cf257255ec4848d8719b613010bf339491e2a39d20d2f3b73b8f`。本次对子任务收到的本地索引及代码固定Ref交叉核对；没有重新读取远端完整parent SOURCE。[R2]

## 2. Clock 与 current coordinator 的路径严格区分

builder和原validator都从相同的固定 `short_parent_source` / `P.PIN` 祖先取得六个 clock 文件，而不是把已经换过时钟的现 ON-v2 文件误当base。prepare的 `clock` 函数与旧v2 AST相同，原validator的 `clock`、`enumerate_tests`、`dependency_contract` AST也全部相同。[R2]

现 ON-v2 `performance_software_stages.py` 是独立的5440B输入，固定 SHA `b862faa3ac7763c34af4055e48fef2c3d1140eea023e10de71d73770d13f05cd`。它有三处当前截止字面值1792672721，不能靠仅识别旧base时钟的renderer自动换掉。本次调用纯renderer，确认新文本只有这三处改成1792692055；反向替换后逐字节等于5440B原文。builder与child validator均检查该完整文本，不跳过软件预算或当前20项控制。[R2]

**边界：没有在此子任务中逐个读取六个祖先clock正文并生成/比较新冻结文件。** 已确认的是来源选择、同一renderer与现六文件的固定身份。真正 freeze 后的原validator完整 expected-file比较和独立v4 audit仍是必过门禁，不能被这里的静态结论代替。

## 3. Validator 与两处软件 scope

`render_validator` 对完整6933B旧validator执行固定额外helper声明、单个BV lineage hook，以及恰好一行授权谓词的替换。已实际逐项逆变换，完整恢复原SHA `c45e114ab03fd35a47c85c8dd6f70bb71bbc406fa08be151222d082d8d57d824`。原D.runtime全文比较、数学/共同配置约束、source文件闭包、test枚举和命令契约均保留。[R2]

`performance_software_scope` 和 `service_software_scope` 均只能改变 `fixed_cutoff`。child validator使用整字典与 `dict(parent_scope, fixed_cutoff=I.CUTOFF_EPOCH)` 相等比较，原分配120/60/120秒、aggregate300秒、phase3600秒、cleanup180秒、current20不变。[R2]

## 4. 本次发现并复核的依赖修复

`test_boundary_integration.setUpClass` 实际打开四个旧文件：short delta、validator、current coordinator、SHORT_AUTHORITY。原runner只强制本prep输入，MAIN若只传22核心，旧四文件就不会自动进入输入前后检查。本次将此缺口立即交给准备包负责人；负责人仅修改runner及配套说明/索引。

最终runner现在硬编码四个原完整Ref，并在首个 `OUT.mkdir` **之前**要求它们逐项等于 `inputs.files` 中的Ref。它们因此进入既有 `unique → before → after` 全文读取。四个实际旧文本/JSON本次均重新读取并核对长度/SHA。完整runner反向删除新增四Ref门禁、授权输入和新身份后，逐字节等于旧v2 runner；原child生命周期、120秒whole/30秒child、资源与排他输出逻辑未改。[R1]

## 5. MAIN_REVIEW、控制与 auditor 闭包

builder要求新 `bole.boundary-probe-main-source-review/v2-continuation` review、明确新授权Ref、五helper完整Ref和control_refs；review本身、builder、旧完整文件/依赖/audit readset、新授权JSON/文档与control_refs进入source依赖。child validator保留原parent全部文件/依赖，逐项校验五helper、原runtime和命令readset。[R1–R2]

历史原auditor固定4631B / SHA `318abb...` 必须仍在原完整readset。prep中另有同名4631B / SHA `57dd...` 的保留副本，其身份不同且不作续批执行入口。新v4程序位于独立auditor目录，主入口要求自身完整外部Ref并前后校验，严格比较actual host readset与validator proof。新reader再独立读取v4程序和历史auditor；不得将三种身份混为一份文件。

**实际MAIN_REVIEW与新控制输出尚未由本次复核取得；control Ref 的成员关系或哈希本身不能证明其结果为PASS。** MAIN须检查实际新stdout/stderr、确切测试数量、退出码、无跳过和输入前后身份，再签核。当前报告不替MAIN创建或签署review，也不证明尚未运行的source/audit闭包已执行通过。

## 6. Owner扫描与same-image20的可报告范围

保存的扫描记录覆盖239个顶层Python文件，9个命中旧窗口字面值。本次重新打开9个命中的完整本地副本，按记录Ref核对并重新计算命中行；没有打开其余230个远端文件。9项为六clock、current coordinator、validator，以及历史 `prepare_bound_short.py`。附加窄字符串扫描只在旧builder自身清单发现其名字；结合实际新builder/命令闭包，它属于历史构造输入。窄扫描本身不是对任意动态导入的完整程序证明。[R3–R4]

已独立打开三份固定20-test源码并核对SHA，测试方法数量为 **10+6+4**，没有旧窗口epoch/日期字面值预期；本次不需要修改这些测试。fixtures和实际runtime导入闭包没有在此子任务重新执行，**fresh same-image20仍未通过本次真实运行验证**。[R5]

## 7. 数值、生命周期和reader限制

boundary observer、projection observer、delta、容量计算和五个runtime源码快照与旧v2字节相同，没有加入新GEMM/collective/写入、容差、设备读量或生命周期策略。独立reader包的历史27函数AST保留及新授权限定审查已有单独证据；这里不把“27”误称为准备包的函数数量。[R1、R6]

原150文件闭包、因果边界解释、严格Ref/hash/cleanup与数值门禁没有因本次clock适配降低。新的源冻结、真实projection请求、独立reader实际执行，以及低观察开销路径的真实资格都仍需后续证据。原pair FAIL、≥10%整模型收益、正式TTFT/TPOT、三任务精度未验收的结论保持。

## MAIN 下一步

先独立核对22个精确部署源码与授权Ref，按已修复的强制旧四Ref运行新的有界prep controls并复核原始结果；随后签署实际MAIN_REVIEW。只在完整3780秒仍可容纳时，创建新source一次并运行独立v4 auditor，要求原validator的全文runtime/clock比较与host readset完全相等。新冻结源必须完成fresh same-image20及严格资源/owner准入后，才能开展这次NPU4–7有界诊断。以上每步失败保留新身份输出，不降低门禁。

## 复核证据

- R1: `/workspace/scratch/e65c435145b1/new_v3_independent_review/FINAL_CORE_REVIEW.json` — 39199 B / SHA `815c5ab5ffa72bad06bc030bb29813843ed60d5649b9cb6423f1fceb52b1ff91`。
- R2: `/workspace/scratch/e65c435145b1/new_v3_independent_review/SOURCE_TRANSFORMATION_REVIEW.json` — 45660 B / SHA `1974742728b549d6fc2566c27d96ebf1a1622693f804ab3deebe4a53e815e4ed`。
- R3: `/workspace/scratch/e65c435145b1/continuation_clock_inputs/INDEX.json` — 91060 B / SHA `67bb26fda544b16a6d4cd64467f6c05f83c1553a78c37712f2106edd9a602c6f`。
- R4: `/workspace/scratch/e65c435145b1/continuation_clock_inputs/REACHABILITY_SCAN.json` — 3634 B / SHA `77b4464441f78ee69d56b6fe05fa19c304fbe8dcaca977f09e71ce0277978b7e`。
- R5: `/workspace/scratch/e65c435145b1/continuation_clock_inputs/TEST_REFS.json` — 1129 B / SHA `06974dd27fce80dfa844e6f7f3316afd176c656b0288ce2b991623201ef8a636`。
- R6: `/workspace/scratch/e65c435145b1/projection_reader_v2_continuation_draft/INDEPENDENT_AUTHORITY_STATIC_REVIEW.json` — 2693 B / SHA `2e770a50ceec1802b55c698657d9337d603bd7acba0b295e748a0b982a61e9b6`。

## 最终22核心身份

下表为本地实读字节；远端部署路径映射见 `FINAL_CORE_REVIEW.json`，不是本子任务完成远端读验的声明。

| 文件 | bytes | SHA-256 |
|---|---:|---|
| `AUTHORIZATION_CONTINUATION.json` | 1886 | `e0808a184326bfcf70e5ce158c7a00dac03b5f7aeab2aabc99b7c99618e40fac` |
| `AUTHORIZATION_CONTINUATION.md` | 3956 | `3bd808a5012bbe447b2a48bbc611116771f9f65a0b40f8c99e02c702000de0ba` |
| `CONTINUATION_README.md` | 8436 | `de56e59f565b1ab82473e443ccea2a7b4235bdf9013ea7bb03278a16049704af` |
| `PROJECTION_README.md` | 12599 | `a78cacf68fa83fc9c3c99f78ef3183e195ca8a4c108e64efec84e61908031574` |
| `audit_boundary_source.py` | 4631 | `57dd114a5810c064f7cdae9d3d0daebc112d9592dbd2309839a578c5ef1bf0d9` |
| `audit_boundary_source_v4.py` | 7159 | `274f85c96758523796704b3bf45e4457be35cde45b787e4089aca61e1ab6ee8a` |
| `boundary_delta.py` | 9827 | `56efb9a324ce9f15d468409e95dbed00694a681a780432349c96159e94c793be` |
| `boundary_integration.py` | 9879 | `6d86ce8b5b4114966cd8d6e1d16ace80ccbc5fc6fb2a55a73ddf15cf3f33501b` |
| `boundary_probe_v1.py` | 31338 | `14c69907adffb9ed5661f6ffd6023f85ab58730af69232b9a54a4ff6883e4bdf` |
| `boundary_validation.py` | 12004 | `c4846f9b49255143e005995ce609cfae3ecbdf1f6e5b28d9259cf2fb32351614` |
| `evidence/ascend_linear.py` | 21354 | `3f14a92019a6612158ba41a26c358c8f164cbda66b743c518a5e4019694b5dc3` |
| `evidence/ascend_linear_op.py` | 30813 | `0333d3229dbfed3010413510b76395a9ad89138dfd1d578caab057573b6cd0fb` |
| `evidence/ascend_utils.py` | 67646 | `575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02` |
| `evidence/custom_op.py` | 13924 | `4b4ba01623005d6a93698eaec007a934dd512bf9ec7241090927de819621de2e` |
| `evidence/vllm_linear.py` | 63273 | `a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab` |
| `metadata_envelope.py` | 8323 | `7ebae10ba2a320b371db4f21c4136ab049d0d990546cdc6da4c358e3df463faf` |
| `prepare_boundary.py` | 13210 | `2b94c6936c68c184c8542b720377c7e1b3b95bf85b482fd0edd9aeb27a23fa2d` |
| `projection_probe_v1.py` | 30248 | `4c442d86077efcb64e0d7f845d77accabe9b310e844c88a2a9731b2c3b450765` |
| `run_boundary_controls.py` | 8951 | `b672851d91267bf98f3aa0883e98531f99e97ce5074cd562ff3ced3abe22037c` |
| `test_boundary_integration.py` | 8248 | `f5b7969bdbac00f97f56bd1cc1720042dceb5b4877df3ba275da9bd12ee751eb` |
| `test_boundary_probe_v1.py` | 8959 | `4f345ee0968f845875726d847fc6d94cd95c88525493fad6db85c8780e470e7c` |
| `test_projection_probe_v1.py` | 21696 | `c042973efc22e4505dcd852d9dbefbbcec4837931c7b6292b6e1f9711ab2a010` |
