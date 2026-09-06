# 依赖说明

使用这个 skill 前，请先让 Agent 跑依赖检查。依赖状态以子仓根目录的 `verify_dependencies.py` 输出为准；文档只说明它会检查什么。

## 让 Agent 先做什么

你可以直接这样说：

```text
我要使用 ppt-deep-search，请先检查它的依赖；如果校验器或网页证据包工具缺失，请帮我处理到可用。
```

## 检查命令

在 workspace 根目录运行。在本仓库默认位置下，可完整复制：

```powershell
Set-Location "D:\Agent Repo\Mozhi-s-AgentWorkspace"
python skills/ppt-deep-search/verify_dependencies.py
```

`--skip-services` 仅为 workspace 协议兼容参数；该 skill 没有必需外部服务，传入此参数也不会跳过本地文件、校验器、Playwright 或 Chromium 检查。

## 必需依赖

| 类型 | 说明 |
| --- | --- |
| Python | Python 3.9+ |
| 浏览器渲染 | Python 包 `playwright` 与已安装、可启动的 Chromium，用于 Source Understanding HTML 截图导出 |
| 子仓运行资产 | `.codex/agents/*.toml`、必需 references、validators、forward-test 契约文件和 `agents/openai.yaml` |
| workspace helper skills | `skills/web-article-capture`、`skills/hw-ppt-gen-html`、`skills/grobid_pdf_skill`。依赖脚本检查其关键入口文件；网页抓取、HTML deck 生成和论文解析分别由它们提供 |

## 可选或按任务触发的依赖

| 类型 | 何时需要 | 说明 |
| --- | --- | --- |
| 网络访问 | 从 URL 抓取网页或下载论文时 | 本地 Markdown、已有 source package 或仓库文件不一定需要联网 |
| GROBID 服务与 PDF 解析工具 | 需要新解析论文/PDF 时 | 由 `grobid-docling-pdf` 的依赖契约负责；`ppt-deep-search/verify_dependencies.py` 不探测其服务健康度 |

## `verify_dependencies.py` 实际检查范围

它会：

- 确认 Python 3.9+。
- 确认本 skill 的必需 agent、reference、validator、forward-test 契约文件存在，并检查三个 custom agent 的 `name`。
- 确认 helper skills 的必需入口文件存在；对 `web-article-capture` 只检查 `SKILL.md`、`validate_capture_package.py` 和 `output-contract.md` 存在。
- 执行 `validate_markdown_size.py --self-test`，并对子仓执行 Markdown size 检查。
- 执行 `validate_source_understanding_html.py --self-test`。
- 实际 import Playwright，启动后关闭 Chromium。

它不会：

- 不会执行 `web-article-capture` 的 capture package self-test，也不会抓取真实网页。
- 不会完整验证三个 helper skill 的全部运行时依赖。
- 不会检查 GROBID 服务、外网连通性、来源 URL 可访问性，也不会证明某次任务的产物已齐全。

## 缺失时的修复方向

- Playwright import 或 Chromium 启动失败：运行 `python -m pip install playwright`，再运行 `python -m playwright install chromium`。
- helper skill 文件缺失：先运行 `git submodule update --init --recursive`；如果仍缺失，检查对应子模块的登记和 checkout 状态。
- 本 skill 的 agent、reference、validator 或 forward-test 契约文件缺失：从子仓的受控版本恢复，不要用空文件绕过检查。
- helper skill 自身运行失败：进入对应 helper skill 的依赖文档，按它自己的 `verify_dependencies.py` 或服务说明处理。

## 判断标准

看到所有 `[OK]` 后，只能说明上述本地 gate 已通过。若任务使用网页抓取或论文解析，还应分别按 helper skill 的契约检查它们的运行环境。
