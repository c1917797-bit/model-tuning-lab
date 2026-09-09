# Model Tuning Lab

用于模型微调、推理优化与评测实验的 Git 原生实验室。根目录维护共享
Maintainer Skill Tree，各研究或工程项目位于 `projects/`。

## 目录

- `configs/`：训练、推理和评测配置
- `scripts/`：可复用命令与任务入口
- `src/`：核心 Python 代码
- `tests/`：自动化测试
- `projects/`：具有独立源码、测试和项目边界的子项目
- `.agents/skills/`：所有子项目共享的维护者 skills

## 开始使用

先读根 `AGENTS.md` 和目标项目的 `AGENTS.md`。项目依赖、安装入口和
运行方法由各项目自己的 `README.md` 或 `PROJECT.md` 维护。

当前项目：

- `projects/drror_vllm_ascend/`：Qwen3.8-27B DRRQR 在 vLLM-Ascend
  上的算法、插件、正确性与性能研究。

## 维护者 Skill/插件清单

维护者可在此维护推荐插件与可安装能力清单：

- `configs/maintainer-plugins.md`
