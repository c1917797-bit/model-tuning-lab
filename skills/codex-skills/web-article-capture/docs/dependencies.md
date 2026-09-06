# 依赖说明

## 必需依赖

- **Python 3**：用于运行 `verify_dependencies.py` 和 `scripts/validate_capture_package.py`。脚本只使用 Python 标准库，不要求安装第三方 Python 包。
- **Codex in-app Browser**：真实网页抓取时必需，用于查看渲染页面、识别正文边界和读取原始媒体资源。开始 Browser 工作前，Agent应加载 `browser:control-in-app-browser` 的操作规范。
- **skill 自带文件**：`scripts/validate_capture_package.py` 以及 `forward-tests/` 的协议文件必须存在，依赖自检会检查这些文件的一部分。

## 按任务需要的依赖

- **目标网页和图片资源的网络访问**：真实抓取时需要；只运行依赖自检或 validator 自测时不需要。
- **页面可执行的渲染环境和访问权限**：登录墙、地区限制、机器人防护或站点故障可能导致部分抓取或 fallback。这些不是依赖脚本可以预先验证的项目。

## 运行依赖自检

从工作区根目录 `Mozhi-s-AgentWorkspace/` 执行：

```powershell
python skills/web-article-capture/verify_dependencies.py
```

从 skill 根目录 `skills/web-article-capture/` 执行：

```powershell
python verify_dependencies.py
```

脚本输出 JSON，并实际执行以下检查：

1. 使用 `py_compile` 编译 `scripts/validate_capture_package.py`。
2. 运行 `scripts/validate_capture_package.py --self-test`，确认有效 package 可通过，同时额外根文件、缺失图片引用和疑似截图文件名会被拒绝。
3. 检查 forward-test protocol files：套件根目录的 `forward-tests/README.md`、`forward-tests/main-agent-prompt.md`，以及每个 case 的 `main-agent-prompt.md`、`candidate/prompt.md`、`candidate/input/` 和 `judge/rubric.md` 是否存在。

其中 case 的 `candidate/input/` 只检查路径存在，不检查其中 URL、文件内容或案例质量。

## 自检不会检查什么

`verify_dependencies.py` 不会：

- 启动或控制 Codex in-app Browser，也不会确认 Browser 工具当前可用；
- 访问目标网页、测试 DNS/代理/登录状态，或下载正文图片；
- 验证网页正文边界、图片语义归属、fallback 可靠性或 `review.html` 质量；
- 校验实际用户输出目录中的 source package；该项需另行运行 validator；
- 检查 forward-test 协议文件的正文是否正确，也不实际运行 forward tests；
- 安装 Python、Browser、网络组件或任何依赖。

## 故障与修复方向

- **validator 文件缺失或无法编译**：确认当前 checkout 完整，并恢复 `skills/web-article-capture/scripts/validate_capture_package.py`；不要用修改文档绕过失败。
- **validator self-test 失败**：单独从 skill 根目录运行 `python scripts/validate_capture_package.py --self-test` 查看错误，确认 Python 版本和脚本文件未损坏。
- **forward-test protocol files 缺失**：根据 JSON 的 `missing` 列表恢复对应 `forward-tests/` 路径；目录存在不代表内容已通过语义审查。
- **Browser 不可用**：确认运行环境提供 Codex in-app Browser，并加载其操作规范；若创建标签页、导航、load state、DOM snapshot 或图片加载失败，应记录具体受阻阶段。
- **网页或图片网络不可达**：检查目标 URL、网络/代理、登录或地区限制，在新标签页进行页面级重试；持续失败时只使用官方来源 fallback，并在 `source.md` 记录 fallback URL、抓取模式和版本风险。
