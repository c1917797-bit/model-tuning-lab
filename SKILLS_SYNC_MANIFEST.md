# 维护者技能仓库（用户态同步）

本仓库包含以下两类技能：

- `skills/codex-skills/`：从 `C:\Users\Huawei\.codex\skills` 同步的用户技能（已排除 `.system`）
- `skills/agents-skills/`：从 `C:\Users\Huawei\.agents\skills` 同步的用户技能

## 新机器恢复步骤

1. 克隆仓库。
2. 将目录拷贝到目标机器对应位置：
   - `skills/codex-skills/*` -> `C:\Users\\<用户>\\.codex\\skills\\`
   - `skills/agents-skills/*` -> `C:\Users\\<用户>\\.agents\\skills\\`
3. 可选：对 `configs/maintainer-plugins.md` 再执行技能安装。

> 注意：`model-tuning-lab` 中默认不包含系统内置技能（如 `.system`）。

## 同步范围说明

本快照保留真实用户技能的 `SKILL.md`、`agents/`、`references/`、`scripts/`、模板和必要资源，目标是让新机器克隆本仓库后可以直接恢复用户态技能。

已排除 `skills/codex-skills/ppt-deep-search/docs/showcase/latest/`。该目录是本机生成的展示缓存，包含缺失的 Git LFS 展示资源，不影响 skill 的调用和维护。

## 一条命令恢复（Windows）

```powershell
git clone https://github.com/c1917797-bit/model-tuning-lab.git; powershell -ExecutionPolicy Bypass -File .\model-tuning-lab\scripts\restore-user-skills.ps1
```

该脚本会创建 `%USERPROFILE%\.codex\skills` 和 `%USERPROFILE%\.agents\skills`，然后覆盖同步仓库中的用户态 skill 快照。
