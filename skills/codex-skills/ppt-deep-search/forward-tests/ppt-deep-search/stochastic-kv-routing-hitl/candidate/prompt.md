# Candidate Prompt: PPT Deep Search Source Understanding Task

请在 workspace 根目录执行 PPT Deep Search，并使用以下 skill：

```text
skills/ppt-deep-search/SKILL.md
```

输入材料：

```text
skills/ppt-deep-search/forward-tests/ppt-deep-search/stochastic-kv-routing-hitl/candidate/input/source-request.md
```

允许按 skill 流程使用子 agent，包括论文获取/解析、Source Understanding HTML deck 生成和视觉 QA。

请将产物写入：

```text
.tmp/forward-tests/stochastic-kv-routing-hitl/<run-id>/
```

`<run-id>` 必须是清晰、全新且不存在的目录，例如 `candidate-YYYYMMDD-HHMMSS`。不要覆盖或复用历史运行目录。

