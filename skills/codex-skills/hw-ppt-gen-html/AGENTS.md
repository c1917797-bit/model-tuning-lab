# 仓库协作说明

本仓库仅作为 `html-ppt-skill` 的 workspace 接入 wrapper。

## 开发约定

- 运行时能力、模板、主题、脚本和参考文档都以 `html-ppt-skill/` 子仓为准。
- 修改实际 PPT 生成能力时，优先在 `html-ppt-skill/` 子仓内完成。
- wrapper 层只保留接入所需的轻量入口文件。
- `forward-tests/` 是本 wrapper 保留的验证资产，不随运行时能力下沉到子仓。
