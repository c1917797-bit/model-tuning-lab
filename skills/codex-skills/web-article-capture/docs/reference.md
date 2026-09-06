# 能力展示

`web-article-capture` 把网页正文、正文图片和来源可靠性说明整理成下游 Agent 可复用的 source package。以下示例链接到仓库中已经存在的固定提交，不是示意目录或临时路径。

## 真实示例：NVIDIA DGX Spark 产品页

示例来源是 NVIDIA 官方产品页：[Personal AI Supercomputer Powered by Blackwell | NVIDIA DGX Spark](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)。现有交付记录显示其抓取模式为 Codex in-app Browser 渲染抓取，并包含正文边界、媒体取舍和 Browser DOM snapshot 失败后的恢复说明。

- [在线打开 `source.md`](https://github.com/MozhiJiawei/hw-ppt-gen-html/blob/a0578c54074669a3e8fdcf87e8e1e2a721794e97/forward-tests/rtx-spark-agent-pc-report/sources/web/nvidia-dgx-spark/source.md)
- [在线查看完整 `images/` 目录](https://github.com/MozhiJiawei/hw-ppt-gen-html/tree/a0578c54074669a3e8fdcf87e8e1e2a721794e97/forward-tests/rtx-spark-agent-pc-report/sources/web/nvidia-dgx-spark/images)
- [在线打开正文 hero 原图交付件](https://github.com/MozhiJiawei/hw-ppt-gen-html/blob/a0578c54074669a3e8fdcf87e8e1e2a721794e97/forward-tests/rtx-spark-agent-pc-report/sources/web/nvidia-dgx-spark/images/image-01-hero-dgx-spark.jpg)

该 source package 展示了：

- 在 `source.md` 开头保留原始页面 URL、发布者、抓取日期和 `rendered capture` 模式；
- 将 hero、功能卡片、工作负载和软件章节的原始网页图片放在对应正文附近；
- 为每张保留图片记录原始图片 URL，并在结尾说明保留与排除媒体；
- 明确正文从产品 H1 开始、在 Partners 后停止，排除 footer 导航；
- 记录 DOM snapshot API 失败后改用只读页面求值和滚动加载懒加载资源，便于下游判断证据可靠性。

这是另一子仓 forward-test 输入中实际留存的网页 source package，固定 commit 链接用于证明交付形态和内容；它不是本 skill 仓内的内置 demo，也不代表每个站点都能得到相同图片数量。

## 交付形态

每个抓取页面输出一个独立目录：

```text
<output-root>/<source-slug>/
  source.md
  images/
```

`source.md` 记录页面来源、抓取时间、正文内容、正文图片、原始图片 URL、图注、抓取模式和可靠性说明。`images/` 保存正文实际引用的原始图片资产。用户按需要求的 `review.html` 是汇总检查面，不放进单页 package 内。

## 覆盖能力

- 抓取文章、官方文档、博客、公告或媒体丰富页面的正文。
- 为 PPT、研究、资料整理或后续 Agent分析准备可追踪来源包。
- 保留正文图片、图表、图注和附近文本的对应关系。
- 记录 Browser 受阻阶段、部分抓取、官方来源 fallback 和媒体不确定性。
- 通过 validator 发现 package 结构、引用和疑似截图文件名问题。

## 能力边界

- 不把整页截图当作 source package，也不把截图放进 `images/` 冒充原始正文图片。
- 不保留导航、页脚、推荐、评论、联系卡片、社交组件或装饰图，除非正文明确讨论它们。
- 不绕过登录、访问控制或站点限制；页面持续受阻时应明确降级和风险。
- validator 只证明结构符合约定，不证明正文完整、图片语义正确或来源事实真实。
- 页面无正文图片时可以保留空 `images/`，但必须说明可见媒体是不存在还是因不属于正文而被排除。
