# 依赖说明

## 从哪里运行

本文命令从 `<workspace-root>/skills/hw-ppt-gen-html` 运行：

```powershell
Set-Location '<workspace-root>\skills\hw-ppt-gen-html'
```

## 必需依赖

| 依赖 | 用途 | 如何确认或修复 |
| --- | --- | --- |
| Python 3 | 运行依赖自检和两个导出脚本 | `python --version`；具体可用性仍应以自检和实际导出为准 |
| Playwright Python 包 | 驱动 Chromium 打开本地 HTML | `python -m pip install playwright` |
| Playwright Chromium | Deck 逐页截图与 Report 全页截图 | `python -m playwright install chromium` |
| `humanize-ppt/` 子仓内容 | AST 大纲、逐页/章节意图与生产交接物 | 确认子仓已检出且能读取其 `SKILL.md` |
| `html-ppt-skill/` 子仓内容 | Deck 模板、主题、布局和运行时 | 确认子仓已检出且能读取其 `SKILL.md` |
| `.codex/agents/html_ppt_visual_qa_checker.toml` | 声明独立视觉 checker | `verify_dependencies.py` 会检查文件与内部 `name`；平台还必须允许实际委派该 agent |

Report 与 Deck 共用 Python、Playwright 和 Chromium，不需要第二套浏览器依赖。

## 可选或按任务引入的依赖

- HTML 使用 CDN 字体、在线图片或视频时，渲染环境需要能访问对应地址；优先把关键证据素材落为本地文件，避免离线渲染缺失。
- 图片生成、Remotion 视频、网页抓取或 PDF 解析属于输入材料生产能力，只在任务确实使用时安装或授权，不是两个 wrapper 导出脚本的基础依赖。
- `ffmpeg`、Node.js 和第三方发布平台不是 `verify_dependencies.py` 的检查对象，也不是纯静态 HTML + Playwright 导出的统一必需项。

## `verify_dependencies.py` 实际检查范围

运行：

```powershell
python verify_dependencies.py
```

脚本当前只做三件事：

1. 输出当前 Python 的 `major.minor.micro` 版本；它没有设置或验证最低版本。
2. 检查 `.codex/agents/html_ppt_visual_qa_checker.toml` 是否存在。
3. 检查该文件文本是否包含 `name = "html_ppt_visual_qa_checker"`。

全部满足时输出“通过 依赖检查完成”并返回 0。它不会修改环境，也不会安装任何依赖。

## 它明确不会检查什么

`verify_dependencies.py` 不检查以下项目，因此不能把一次返回 0 描述为“环境已可完整制作和导出”：

- Playwright Python 包能否导入、Chromium 是否安装或能否启动。
- `humanize-ppt/`、`html-ppt-skill/` 子仓是否完整、版本是否匹配或其自身依赖是否满足。
- 两个导出脚本是否存在、HTML 是否符合 Deck/Report 结构、素材链接是否有效。
- custom agent 是否已被当前 Codex 平台注册、是否有委派权限、是否真的保持独立。
- 网络、CDN 字体、在线图片、文件读写权限、磁盘空间或发布权限。
- Node.js、`ffmpeg`、图片/视频生成器、网页抓取器、PDF 解析器和任何敏感凭据。

## 脚本自测的范围

```powershell
python scripts\render_html_ppt.py --self-test
python scripts\render_html_report.py --self-test
```

- Deck 自测检查默认 viewport、hash URL、`section.slide` 解析和输出目录/旧 PNG 清理逻辑。
- Report 自测检查 file URL 与若干 inspection 规则。
- 两个 `--self-test` 都不会启动 Playwright 或 Chromium，也不会渲染真实 HTML。因此自测通过后仍需对本次最终 HTML 运行实际导出命令。

## 故障修复方向

- `No module named playwright`：运行 `python -m pip install playwright`。
- 找不到浏览器可执行文件：运行 `python -m playwright install chromium`。
- checker 配置不存在或 `name` 不匹配：先确认仓库检出状态；不要在普通任务中临时伪造 checker 配置。
- 实际导出出现 `[ERROR]`：按错误修复 HTML、素材或模式结构，然后重跑同一个模式的导出入口；不要改用另一个入口规避门禁。
- `verify_dependencies.py` 通过但委派失败：这是平台注册或授权问题，需要在当前运行环境中确认 custom agent 可用性。

依赖文档不得记录 API key、账号密码、访问令牌或其他敏感值。
