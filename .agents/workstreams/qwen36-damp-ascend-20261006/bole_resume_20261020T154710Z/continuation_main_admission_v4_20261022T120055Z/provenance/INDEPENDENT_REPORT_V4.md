# continuation launcher v4 独立限定静态复核

**结论：四个稳定源码在本次限定静态范围内通过复核；B1、I1、I2 均已在 v4 源码中解决，未发现剩余确定静态阻断。此结论不是 MAIN 派发批准，也不是资源或真机资格。**

v3 的失败发现和报告完整保留。MAIN 已取得的新 source freeze 与 source-only audit，与尚未运行的 launcher 真实六链/current integration 分别记录。

## 精确代码身份

| 文件 | bytes | SHA-256 |
|---|---:|---|
| `main_admission_v4.py` | 31959 | `fdb867c17f5b4ec9da34a3b9203482df437df8a20bfcee2dcd0cad3f01f126e6` |
| `historical_owner_context_v1.py` | 13079 | `63aecade69f568496412e4aff43de422151bca3d835389b678486e40ee162e75` |
| `complete_inspect_receipt_v1.py` | 3807 | `05d212afa6d84af8f0a665c4d1605c756e1e603b52c533e983bc866e13804e5a` |
| `restore_snapshot_mounts_v1.py` | 6438 | `8177437cda4df4d85db41392588fff18ce8422598d73bdc163ab950b26a32f9c` |

## 三项修复的独立核对

**B1，历史 owner 上下文。** 每个旧 CID 由其旧 source/output 建立独立验证器。历史 create、cleanup 前后 inspect 和最新 current inspect 均改用对应 context，不再调用新 OUT 绑定的验证器。私有 c/S 使用原 constants/require 及完整原函数 AST；原 MEM32 provider 只改私有 S；原 external 与 g2 derive 的完整 forward/inverse 保留。旧角色固定为 cpu-preflight/dense，原 g2 nonconsumer 首分支明确核对，原环境、标签、设备、资源和 mount 谓词保留。构造与每次调用前后检查活动 c/S/external 指纹，未切换活动 OUT。

已独立重算 MAIN 提供的七份 helper 全文 SHA，并核对新旧资源 profile 完全相同。observer 只改 Controller.observe；output-scan 只改 Controller.resources 与 scanner 句柄，不改 pure create/inspect 环境等依赖。旧/新源码的六 helper Ref 仍通过运行时 readset 全读；未执行历史 load/install。原 loader 的73GiB源常量检查之后，会经既有 provider 设为 MEM32/reserve8/host0.5，原初始门禁是40.5GiB。v4 没有新增73GiB准入要求，也没有新降低资源阈值。

**I1，加载前 opt-in。** `DENSE090_EXTERNAL_OUTPUT_ENABLE=1` 在 source load 前显式检查，原 install guard 未删除。README 和 LAUNCH_CONTRACT 将它列为 check-only 与 execute 两种外层 argv 的环境项。真实 dispatch 仍另需 `BOLE_CONTINUATION_MAIN_ENABLE=1`、冻结入口、精确 config 与 genuine MAIN review。后续 model argv 的 env 不再被误当作已经作用于先前 load。

**I2，完整 current inspect 保存。** 每份 current inspect 的完整 receipt 进入 live 记录，以 zlib+base64 保存 stdout 原 UTF8 字节/SHA、压缩字节/SHA、全部原 metadata 与完整 receipt canonical 字节/SHA。严格 base64、原8MiB单命令原始上限、受输出长度限制的解压、EOF及无 trailing/unused/unconsumed 数据、严格 UTF8 与完整 roundtrip 均核对。check-only 与 execute 的整个证据仍限16MiB；超限拒绝，不截断。

## 锁、时钟、预算与原始闭包

与 v3 相比，只有 historical_owners、source_inputs、current_live_checks、main 四个原顶层函数变动，并增加两个 helper pin。原完整 mount 次序恢复函数和 decoder 保持原字节。Decoder 校验完整 table、所有数组与 row/CID/pass 绑定、原顺序和重复次数、整段 canonical bytes/SHA；所有检查完成前不写回任何数组。

MAIN 锁仍采用 nofollow 打开、非阻塞排他 flock；在最终 live 检查前取得，exec 前再次核对 inode/device 并显式保留 FD。原 model argv 经 source-owned command_contract 验证后整体 exec。主机 CPU166、soft AS512MiB/hard无限、CPU/FSIZE soft/hard均无限的继承检查保持；180秒 predispatch alarm 在 exec 前取消。原 phase3600 含 shared cleanup180，初始 prepare3780不变。

新批次1792670455–1792692055恰为21600秒；旧报告截止1792672721未延长。快照在入口和派发前都必须不超过180秒。原 SMI/HBM/FD、RAM/swap、磁盘/Docker/CPU、protected boundary 门禁保留，消失 PID 留在证据中。原 source controller 在每次 create 前仍重新检查。既有 source/audit/build/authority/commands 完整引用及原 validators、最后 input reread 未删除；template 中五项实际 source/audit/build/commands/auditor Ref 与 MAIN 的 QUALIFIED_SOURCE_REFS 精确相同。

## 本地 controls 的实际证据及边界

已读取并校验作者保存的两份记录：既有纯数据/default-OFF controls **11项、exit0**，以及新 source-derived private-context/codec controls **5项、exit0**。两组分别记录，本文没有重新执行。新测试使用真实已保存 helper 正文，但 OWNED、inspect、active controller fixture 与本地 path/reference transport 是明确合成的；它们验证旧 OUT 根因、私有上下文及原资源/环境/设备拒绝行为，不能计为真实六条历史原始链或当前主机集成通过。

所有源码/controls/config/docs/输入的精确 Ref、已核对的原函数 AST 变化范围和原始 MAIN source-only 回执均列于 `REVIEW_V4.json`。该文件中所有资源、NPU、数值、paired gate 和性能资格仍为 false。

## MAIN 后续必须完成的实际步骤

当前仍是默认关闭草案：`REVIEWED_FROZEN=False`，三 helper pin为None，template=true；actual authorization 与新的 snapshot/program/execution pins 尚未填入。MAIN 需在独立保存的 frozen successor 中完成精确 helper/launcher 绑定、不可覆盖 config 与 genuine review。新单位的参数应读取原 terminal unit 后确定，并保持原主机/phase/cleanup与limit契约。

随后必须对实际六条 raw owner 链、新 source-owned controller、完整 current inspect 与新资源观察执行真正的检查。12:14旧快照不是新执行租约，source-only audit PASS 也不是资源批准。所有真实历史上下文和 host integration 目前仍 pending；本次复核没有远程操作、main/check-only、NPU或模型运行，不改变原完整 short pair FAIL，也不提供吞吐、TTFT/TPOT或任务精度结论。
