# Projects

`projects/` 是 Model Tuning Lab 的可扩展子项目目录。

每个项目使用 `projects/<project-id>/`，至少包含：

- `PROJECT.md`：身份、来源、状态、入口和外部制品边界；
- `AGENTS.md`：只记录该项目独有的算法、资源和验收约束；
- 项目自己的源码、测试和构建元数据。

维护者工作流只在根 `.agents/skills/` 定义，并由
`.agents/skills.registry.yaml` 统一发现。项目不得复制一套 Maintainer
Skill Tree；项目内 `skills/` 只可用于确有必要的产品、运行时或实验技能，
且不得覆盖根维护者规则。

新增项目时更新 `projects/registry.yaml`，记录来源提交和历史保留策略。
大模型权重、数据集、原始 profiler trace、构建缓存和大型实验输出继续放在
Git 外部，并在项目证据中记录路径与哈希。
