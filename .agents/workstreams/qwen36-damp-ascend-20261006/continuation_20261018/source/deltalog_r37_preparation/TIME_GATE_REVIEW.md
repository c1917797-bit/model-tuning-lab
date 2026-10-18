# R37 继承时间门的独立只读审阅

审阅日期：2026-10-18 UTC。本文只记录源码组合的约束，没有运行模型、CPU 消费者、存储 lease 或远程命令，也没有修改任何时间门。R37 最终模板尚须自行冻结；以下结论适用于完整继承所列 H017/008 与 R21 时间注册的实现。

## 结论

**原有效入口确实要求启动时完整剩余 3600 秒。模型 owner 与独立 CPU consumer 都必须在 2026-10-18 07:43:20 UTC 之前完成其前置准备，并到达生成的 `h.main` 时间断言。实际调用应留余量，不能按整数秒临界点操作。**

原截止为 `1792313000`，即 08:43:20 UTC；`PHASE` 经现有窗口适配后为 3600。最晚入口由 `cutoff − PHASE` 得到。不能把内部动态剩余预算计算解释为允许在 07:43:20 后启动。

这是入口准入条件，不是要求任务必须运行满一小时。若模型较快完成全部验证和释放，CPU consumer 可以在剩余准入窗口内启动。

## 硬门的完整来源

精确原008源码本地只读副本为：

`/workspace/scratch/6646d57c37ee/model_tuning_lab_review/resume_packets/deltalog_dependencies/host008.py`

该副本完整 25508 字节，SHA-256 为 `c1a26afb164af8fcf4b88fef24a524c2c890be772f56f136b5edc5006b1ff066`，本轮独立重新核对一致，没有附加换行。

其 `main` 第 415、416 行：

```python
start = time.monotonic()
need(START <= time.time() and time.time() + PHASE <= CUTOFF,
     "current R118 whole45min incl cleanup")
```

提示字符串中的旧 “45min” 不决定有效期限；实际判断使用适配后的 `PHASE` 常量。

完整组合如下：

1. 原 H017 的 `adapt` 校验完整008源码身份，执行有逐项唯一性和整体逆变换校验的适配。其替换列表没有修改上述 `time.time() + PHASE <= CUTOFF` 条件。
2. `window_overlay.py` 的 `install` 第 14 行设置 `H.PHASE = B.WHOLE`。`transform` 第 16 行仅把 `PHASE, CLEANUP_TOTAL = 2700, 270` 改为 `3600, 270`，同时切换已授权的 START、CUTOFF、authority 与 facade cutoff。它保留上述入口判断。
3. R36 `host_ticket.py` 的新部署、输出与 external-output 适配不修改该判断。它最终调用生成的 `h.main(['--execute', ...])`。拟继承这些源字节的 R37 同样受该判断约束。
4. 已冻结的严格 R36 `host_consumer.py` 也最终调用同一个生成的 `h.main`，其六项独立源适配没有时间断言替换。它增加的 `min(whole-elapsed, cutoff-wall) > 1260` 前检查是额外检查，不能替代较严格的原入口硬门。该 R36 consumer 不能承接 R37 Ref。

## 通过入口之后的动态预算

`phase_budget_r21.py` 的注册固定为：

| 项目 | 秒 |
|---|---:|
| whole | 3600 |
| cleanup | 270 |
| postverify | 900 |
| margin | 90 |
| 最大工作预算 | 2340 |

同文件 `work_remaining` 第 18 行起的实际计算是：

```python
value = min(3600 - (now - started), cutoff - wall) - 270 - 900 - 90
need(value > 0, ...)
```

`postwork_verify.protect` 在原 `Owned.remaining` 返回值上继续取与此工作预算的较小值。原008 `Owned.remaining` 第 125 行起也保留 whole end、UTC cutoff 与共享 cleanup 预算；cleanup 的单容器 deadline 是 `min(now + 90, state['end'], now + CUTOFF - time.time())`，没有跨 whole 或跨截止重置。

`post_remaining` 第 24 行起计算：

```python
min(900, 3600 - elapsed - 90, cutoff - wall - 90)
```

并要求严格大于零。`postwork_verify.run` 对该预算设置实际定时器，并在释放后执行 `lease.close`、完整 source-after、fresh own inspect 和 final metadata。它不会把后验时间延长至原 whole/cutoff 之外。

因此这些 `min(...)` 都是已合法启动后的进一步裁剪，没有“剩余不足3600也可新启动”的含义。按 `cutoff − 1260` 算出的 08:22:20 只描述内部工作预算最迟归零的边界，**不是新模型或 CPU consumer 的准入时刻**。

## 模型结束后的 CPU consumer

现有独立 CPU consumer 使用同样的 `PHASE=3600` 和原008 `h.main`，必须重新通过完整剩余3600秒的入口门。

原 `postconsume_recipe.cap` 第 5 行起使用 `min(900, work_remaining(...))`；新 R36 recipe 保持同一算法。create 前和实际 child 前都重新计算，child 的实际超时随剩余预算下降。**900 是 child 上限；CPU owner 的 whole 注册仍为3600，不能在启动时自行裁短。**

消费依赖原模型的真实失败 owner、已验证释放、原 P journal、ALL4-LOADED、四份实际报告和完整 INPUT。新 geometry sidecar 还必须固定相应真实证据。原模型完成 cleanup、postverify、RESULT 落盘并释放存储锁之后，才能进入独立 consumer 的现有完整准入链。不能把任务还在运行时预启动的消费者当作已经合法承接稍后才产生的 INPUT。

以 ROOT 给出的 07:31:00 规划时间为例，至 CPU consumer 最晚入口只剩 12 分20秒。这段时间必须容纳模型尚未完成的全部工作、cleanup、postverify、结果采集、消费者 source/INPUT/sidecar 准备与入门前校验。若来不及，现有门允许分别记录已完成的实际模型采集及其诊断/释放证据，但不能宣称完成独立消费，也不能为赶窗口更改 PHASE 或绕过 `h.main`。

`--source-audit` 的成功只代表其实际检查覆盖的源代码与引用验证，不代表模型或消费者取得运行准入。

## 关键冻结源 Ref3

以下 R36 helper Ref 是原模型 `SOURCE_TEMPLATE.json` 声明的真实远程引用，不能用附带换行的本地读取副本替代。R37 如继承这些字节，只能在其新路径中重新形成自己的 Ref 与模板闭包；本文不声称存在已冻结 R37 模板。

```json
[
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py",
    "bytes": 25508,
    "sha256": "c1a26afb164af8fcf4b88fef24a524c2c890be772f56f136b5edc5006b1ff066"
  },
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-service-empirical-owned-v1-017/host_ticket.py",
    "bytes": 14117,
    "sha256": "f29d8d5717baf61ca6ebf4728123afa1483f3bbd9888f4c93b10c09d75f3d3fc"
  },
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001/window_overlay.py",
    "bytes": 1566,
    "sha256": "19d5f557b8df41d9b222e6a0fa928a609ada823dcda05cfe2e7a6639bdb48966"
  },
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001/phase_budget_r21.py",
    "bytes": 1257,
    "sha256": "b67c9275f8fade6f70f0e5e680b6e52f707c698c09a1a724863e41a0e77e1b7a"
  },
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001/postwork_verify.py",
    "bytes": 2570,
    "sha256": "f3f128d476ee3381d6d47e6c76525f5dbbe1c851048566cb7452ae2055e89efe"
  },
  {
    "path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair36-all4-publication-20261018-001/postconsume_recipe.py",
    "bytes": 5852,
    "sha256": "2775c783e08e0afd0171c738ff76bf81c9a22d5478162f3339ba2cb6c5238d72"
  }
]
```

本地辅助定位：`resume_packets/deltalog_dependencies/host017.py` 中的 `adapt`、`bind`；`resume_packets/deltalog36/host_ticket.py` 中的 `adapted` 与最后 `h.main` 调用；`proposed/deltalog_consumer/host_consumer.py` 中的 `adapted` 和末尾两个门。审阅未修改上述任何文件。
