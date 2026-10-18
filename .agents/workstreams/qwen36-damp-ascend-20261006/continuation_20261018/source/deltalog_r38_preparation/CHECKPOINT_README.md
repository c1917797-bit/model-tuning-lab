# DeltaLog 2026-10-18 continuation checkpoint

本目录保存 R38 准备程序、纯 CPU 控制及审阅记录；相邻的 `deltalog_r37_preparation/` 保存原四件 storage-admission patch 和派生工具，`deltalog_consumer/` 保存独立 geometry 消费者。所有冻结源码保留原字节。本 checkpoint 不是新的 authority、bound source、模型运行结果或验收证明。

## 必须保留的内容

| 目录 | 本轮冻结文件数 | 用途 |
| --- | ---: | --- |
| `deltalog_r38_preparation/` | 6 | 三个准备/传输/纯复制程序、两个控制文件、完整审阅 |
| `deltalog_r37_preparation/` | 16 | 四件 patch、原始及 repair1 派生程序、逆变换说明、控制和时间门审阅 |
| `deltalog_consumer/` | 10 | 七个实现/测试文件、差异说明、48 控制记录、R34 三 rank 元数据 fixture 记录 |

以上 32 件合计 321,495 B；不含本 README、checkpoint 清单、`__pycache__` 或 raw。逐文件实际字节数和 SHA256 见 `DELTALOG_SOURCE_INVENTORY.json`。副本所在仓库路径不是原 Ref 的替代身份；保留各文档和 JSON 内部的历史路径。

## 下一次派生所用原 PATCHES Ref

以下是 MAIN 提供的实际远端四件 patch 清单 Ref；`PATCHES_LOCAL.json` 只是本地准备记录，不能替代它。

```json
{
  "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-r37-preparation-MAIN-renew24h-20261018-001/PATCHES.json",
  "bytes": 1885,
  "sha256": "0bd70da9feea656e0146853d90078fcd3e7684c6ec42551129b3738edfc18b1f"
}
```

其 schema 为 `deltalog.r37-preparation-patches/v1`，四件文件是 `firstdecode_refs.py`、`bind_source.py`、`readonly_closed_admission.py`、`test_readonly_closed_admission.py`。再次使用时应读取并验证原清单及四件原 Ref，不修改该清单的旧路径，不把 R37 的包 ID 用于 R38。

## 已完成与尚未证明的边界

R38 针对 R37 实际 early child 的旧 `MODEL_ROOT` 失败，修复 recover、owner、early 模板、双 model 镜像及最终命令/模板的完整身份依赖；同时保留 R37 released failure、无 stage 的原证据。R38 本地准备控制 8 项、纯传输/复制控制 12 项已通过；storage-admission helper 的 12 项控制属于模型完整 255 项、early 253 项加 payload 26 项的来源。这些本地控制不替代实际同镜像 early、source binding 或模型门。

独立消费者只将控制字节等式改为 `prefill_control.bytes + authenticated_geometry.bytes`，保留原报告和数值/状态/inactive 门。其 48 项本地控制与 R34 的 rank 0/1/3 元数据 fixture 已通过；三 rank fixture 不包含 raw 数学验收，也不满足 all4。现有 host 仍固定 R36 root/template/P leaf；后续模型需要审阅并冻结新的消费者继任源，不能给当前 host 填入新的模型 Ref。

## 合法续做顺序

原 cutoff `1792313000` 对应 2026-10-18 08:43:20 UTC，原模型 whole 3600 秒门要求 07:43:20 UTC 前进入 owner；本 checkpoint 时该窗口已结束。后续实机必须取得有效新窗口，并创建带新 authority、root/label/output/P/journal 身份及完整 Ref 闭包的不可变继任包。不要修改这里的冻结 R38 源、旧 authority 或伪造 bound manifest。

在新条件满足后，先核验原 Ref 和继任包的完整身份审计，再完成实际 cheap-prebind、early 绑定与同镜像 253 + 26 门、closed/readset/component binder、bound-source 审计和原资源/cleanup 门。实际四 rank publication 与 CPU 后验消费仍需完整原始 REPORT/geometry/raw、精确 ALL4/owner/PID 因果关联及原阈值。保留数值、服务、性能和准确率资格为未证明，直至对应真实证据通过。
