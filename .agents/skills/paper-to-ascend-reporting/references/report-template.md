# Paper-to-Ascend 穿刺报告模板

Use this template for information architecture, not as a source of experiment
facts. Remove instructional comments from the delivered report.

# <算法/论文> 算法特性穿刺 · 完整实例（含命令）

> 对应论文：<title, version or DOI/arXiv>
> 算法/实现：<name, version, commit>
> 当前模型：<exact model/checkpoint identity>
> 当前硬件：<Ascend type and physical card count>
> 报告状态：final | progress | rejected | failed | inconclusive
> 实验 ID：<ledger ID>

State whether this is direction, magnitude, or absolute-value reproduction. A
colleague report is historical reference, not current evidence.

---

## Step 0. 环境准备

Record host and time, image ID/digest, repository branch/commit/dirty boundary,
model hashes, dataset/prompt/evaluator/scorer hashes, framework/CANN/driver
versions, physical-to-container NPU map, TP/PP/DP, CPU/NUMA set, ports,
container names, artifact root, protected resources, and isolation proof.

### 1. 获取镜像、代码和算法包

Show exact successful commands and pinned hashes. Remove credentials,
verification values, and private material; label every redaction.

### 2. 资源隔离预检

Show read-only commands plus summarized output proving device, port, container,
CPU, and competing-process ownership. State the fail-closed rule.

---

## Step 1–3. 拉起各组配置服务 → 跑测试

### 1. 实验契约与分组

| 组 | 名称 | 唯一开关/差异 | 回答的问题 |
|---|---|---|---|
| G1 | baseline | none | baseline question |
| G2 | treatment | one declared switch | paper mechanism question |

Add G3/G4 only when they actually ran. Do not attribute an interaction arm to
one component.

### 2. Treatment 核心拉起命令

~~~bash
<exact successful command or checked-in script invocation>
~~~

List the activation gate and evidence proving both control-plane and
worker/operator hot-path activation.

### 3. 数据集与评测配置

For each dataset include path/hash, row count, prompt/template, tokenizer, seed,
temperature, thinking setting, EOS policy, scorer, and repetitions. If a
reference dataset is unavailable, say "not available" and explain the impact;
do not substitute another dataset under the same name.

### 4. 性能测试

Record input/output length, requests, concurrency, warmups, repetitions, cache
state, ignore_eos, capacity budgets, timeout, and exact command.

### 5. 精度测试

Record deterministic, EOS-respecting settings and exact evaluator command. Do
not reuse the fixed-output performance service for quality unless the frozen
contract explicitly permits it.

---

## 基线组部署（G1，对比用）

~~~bash
<exact baseline launch command>
~~~

### 基线性能测试

~~~bash
<exact benchmark command>
~~~

### 基线精度测试

~~~bash
<exact evaluator command>
~~~

State how the baseline was stopped and why the quality restart is
configuration-identical.

---

## Treatment 组部署（G2）

~~~bash
<exact treatment launch command>
~~~

Repeat performance, quality, profile, and stop commands. Show the
machine-readable A/B diff or every differing field.

---

## 逐组测试流程

~~~text
For each frozen arm:
1. preflight resource ownership
2. start service and verify health
3. verify a real request and mechanism activation
4. warm up
5. run repeated fixed-output performance
6. stop service
7. restart the identical arm for deterministic EOS-respecting quality
8. run quality repetitions
9. stop service
10. run bounded profile when required
11. audit artifacts and prove resource release
~~~

Describe actual deviations; do not silently rewrite history.

---

## 实测结果

### 性能

List raw repetition values before the aggregate.

| 指标 | Baseline mean ± dispersion | Treatment mean ± dispersion | 变化 | 样本/重复 |
|---|---:|---:|---:|---:|
| TTFT (ms) | <measured> | <measured> | <relative %> | <n> |
| TPOT (ms/token) | <measured> | <measured> | <relative %> | <n> |
| Output throughput (tok/s) | <measured> | <measured> | <relative %> | <n> |
| Batch duration (s) | <measured> | <measured> | <relative %> | <n> |

Use:

~~~text
relative change (%) = (treatment - baseline) / baseline * 100
~~~

For lower-is-better metrics negative is improvement; for higher-is-better
positive is improvement. Do not flip signs to make every benefit positive.

### 精度/质量

| 数据集/指标 | Baseline | Treatment | Delta | 重复与波动 | 判定边界 | 状态 |
|---|---:|---:|---:|---:|---:|---|
| <task> | <measured> | <measured> | <percentage points or units> | <n, dispersion> | <boundary> | <decision> |

Report attempted, accepted, failed, retried, and unique sample counts. Use
percentage points for accuracy differences.

### 机制激活与 Profiling

| 证据 | Baseline | Treatment | 解释 | 范围限制 |
|---|---|---|---|---|
| activation event | <artifact> | <artifact> | <what it proves> | <what it does not> |
| target kernel/operator | <measured> | <measured> | <attribution> | <scope> |
| HBM/state/cache | <measured> | <measured> | <attribution> | <scope> |

If profiling was required but is missing, the report is not final.

---

## 与论文/同事历史实测结果对比

| 指标 | 论文报告 | 同事历史实测 | 当前主机实测 | 可直接比较 | 差异原因 |
|---|---:|---:|---:|---|---|
| <metric> | <source or N/A> | <historical or N/A> | <current> | yes/no | <model/hardware/ruler/etc.> |

Never copy a historical value into the current column.

---

## Decision 与结论

| Gate | 状态 | 证据 | 允许的结论 |
|---|---|---|---|
| feasibility | pass/reject/inconclusive/invalid | <artifact> | <scope> |
| mechanism activation | ... | ... | ... |
| performance benefit | ... | ... | ... |
| quality safety | ... | ... | ... |
| profile attribution | ... | ... | ... |
| adoption | ... | ... | ... |
| generalization | ... | ... | ... |

Then list:

- **允许声称：** claims directly supported by this experiment;
- **禁止声称：** broader or unsupported claims;
- **仍未证明：** pending questions and the next bounded experiment.

Avoid “可部署发布” unless every deployment gate was defined and passed.

---

## 报错与失败尝试总结

For each real incident:

### 问题 <N>：<short description>

- 阶段与时间：
- 可观察症状：
- 根因证据：
- 影响范围：
- 处置/恢复：
- 分类：environment | tooling | implementation | algorithm | evidence
- 是否进入正式 A/B：yes/no
- 证据路径与 SHA256：

If none occurred, write “本轮未观察到需记录的失败尝试”. Never leave a
placeholder in a final report.

---

## 证据索引

| 证据 ID | 类型 | 路径 | SHA256 | 生成命令 | 支撑/不支撑的结论 |
|---|---|---|---|---|---|
| <id> | raw/summary/profile/log/manifest | <path> | <hash> | <command> | <scope> |

Keep datasets, weights, checkpoints, and raw profiler traces out of Git; store
only manifests, hashes, compact summaries, and recovery pointers.

---

## 精确复现、审计与 Recovery/Resume Commands

Provide:

~~~bash
<read-only integrity audit>
<idempotent resume command and preconditions>
<owned-resource status check>
<safe stop command scoped to exact container/PID>
<post-stop resource-release verification>
~~~

End with artifact root, exact next action, preconditions, and stop criteria. A
future maintainer must be able to resume without chat history.
