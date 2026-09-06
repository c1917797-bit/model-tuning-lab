"""从同一份 spec.json 生成 Markdown 与 HTML 内容确认稿。"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

from content_rules import compose_background_text
from validate_spec import split_bold_label, validate_spec_data


COLORS = {
    "red": "#CC0000",
    "blue": "#1B3A6B",
    "cyan": "#00C9C8",
    "orange": "#FF6B35",
    "text": "#333333",
    "muted": "#666666",
    "light": "#F0F0F0",
    "white": "#FFFFFF",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _background_text(tech: dict) -> str:
    return compose_background_text(tech.get("background"))


def _items(value: Any) -> list:
    return value if isinstance(value, list) else []


def _escape_md(value: Any) -> str:
    return _text(value).replace("|", "\\|").replace("\n", "<br>")


def _html_text(value: Any) -> str:
    return html.escape(_text(value)).replace("\n", "<br>")


def _bold_label_md(item: Any) -> str:
    """把「标签：正文」渲染成加粗标签，和最终 PPT 的加粗规则保持一致。"""
    label, rest = split_bold_label(item)
    if label is None:
        return _text(item)
    return f"**{label}：**{rest}"


def _bold_label_html(item: Any) -> str:
    label, rest = split_bold_label(item)
    if label is None:
        return _html_text(item)
    return f"<b>{html.escape(label)}：</b>{html.escape(rest)}"


def _image_paths(tech: dict, kind: str) -> list[str]:
    keys = (
        ("tech_detail_figures", "tech_detail_figure", "tech_detail_figure2")
        if kind == "detail"
        else ("experiment_figures", "experiment_figure")
    )
    result: list[str] = []
    for key in keys:
        value = tech.get(key)
        if isinstance(value, list):
            result.extend(_text(item) for item in value if _text(item))
        elif _text(value):
            result.append(_text(value))
    return list(dict.fromkeys(result))


def _resolve_asset(raw_path: str, spec_dir: Path) -> Path:
    path = Path(raw_path)
    return (path if path.is_absolute() else spec_dir / path).resolve()


def _md_image(raw_path: str, label: str, spec_dir: Path) -> str:
    path = _resolve_asset(raw_path, spec_dir).as_posix()
    return f"![{label}](<{path}>)"


def _html_image(raw_path: str, label: str, spec_dir: Path) -> str:
    path = _resolve_asset(raw_path, spec_dir)
    try:
        uri = path.as_uri()
    except ValueError:
        uri = path.as_posix()
    return (
        f'<figure><img src="{html.escape(uri)}" alt="{html.escape(label)}">'
        f"<figcaption>{html.escape(label)}</figcaption></figure>"
    )


def _flatten_technologies(spec: dict):
    for direction in _items(spec.get("directions")):
        if not isinstance(direction, dict):
            continue
        for tech in _items(direction.get("technologies")):
            if isinstance(tech, dict):
                yield direction, tech


def render_markdown(spec: dict, spec_dir: Path) -> str:
    review = spec.get("review", {})
    trend = spec.get("trend_insight", {})
    directions = _items(spec.get("directions"))
    tech_pairs = list(_flatten_technologies(spec))
    academic = spec.get("academic_resources", {})
    viewpoint = spec.get("overall_viewpoint", {})

    lines = [
        f"# {_text(spec.get('title'))}｜内容确认稿",
        "",
        (
            f"> 审阅状态：`{_text(review.get('status'))}` ｜ "
            f"版本：`v{_text(review.get('version'))}` ｜ "
            f"说明：{_text(review.get('review_note')) or '无'}"
        ),
        "",
        "## 页面顺序",
        "",
        "1. 封面",
        "2. 技术趋势洞察",
        "3. 洞察摘要",
        "4. 技术清单",
    ]
    page = 5
    for direction, tech in tech_pairs:
        lines.append(
            f"{page}. {_text(direction.get('direction_id'))} / "
            f"{_text(tech.get('technology_id'))}：{_text(tech.get('title'))}"
        )
        page += 1
    lines.extend(
        [
            f"{page}. 学术资源洞察",
            f"{page + 1}. 技术洞察观点",
            f"{page + 2}. 致谢",
            "",
            "---",
            "",
            "## 页面 1｜封面",
            "",
            f"- 标题：{_text(spec.get('title'))}",
            f"- 部门：{_text(spec.get('department'))}",
            f"- 作者：{_text(spec.get('author'))}",
            f"- 日期：{_text(spec.get('date'))}",
            "",
            "## 页面 2｜技术趋势洞察",
            "",
            f"**时间窗口：** {_text(trend.get('time_horizon'))}",
            "",
            "```mermaid",
            "flowchart LR",
        ]
    )
    stages = _items(trend.get("stages"))
    for index, stage in enumerate(stages, start=1):
        stage_id = _text(stage.get("stage_id"))
        label = f"{stage_id}｜{_text(stage.get('period'))}\\n{_text(stage.get('label'))}"
        lines.append(f'  {stage_id}["{label.replace(chr(34), chr(39))}"]')
        example = (
            stage.get("example")
            if isinstance(stage.get("example"), dict)
            else {}
        )
        example_label = _text(example.get("title")).replace(chr(34), chr(39))
        lines.append(f'  X{index}["{example_label}"]')
        lines.append(f"  {stage_id} --> X{index}")
    for left, right in zip(stages, stages[1:]):
        lines.append(
            f"  {_text(left.get('stage_id'))} --> {_text(right.get('stage_id'))}"
        )
    lines.extend(
        [
            "```",
            "",
        ]
    )
    for stage in stages:
        example = (
            stage.get("example")
            if isinstance(stage.get("example"), dict)
            else {}
        )
        lines.extend(
            [
                (
                    f"### {_text(stage.get('stage_id'))}｜"
                    f"{_text(stage.get('label'))}｜{_text(stage.get('period'))}"
                ),
                "",
                _text(stage.get("technical_change")),
                "",
                (
                    f"**{_text(example.get('title'))}**｜"
                    f"{_text(example.get('organization'))}｜{_text(example.get('date'))}"
                ),
                "",
                _text(example.get("fact")),
                "",
                f"[{_text(example.get('source'))}]({_text(example.get('source_url'))})",
                "",
                _md_image(
                    _text(example.get("figure")),
                    _text(example.get("figure_caption")),
                    spec_dir,
                ),
                "",
            ]
        )
    lines.extend(
        [
            f"**洞察观点：** {_text(trend.get('viewpoint'))}",
            "",
            "## 页面 3｜洞察摘要",
            "",
            f"核心问题：{_text(spec.get('topic'))}",
            "",
        ]
    )
    for direction in directions:
        link = direction.get("trend_link", {})
        lines.extend(
            [
                (
                    f"- **{_text(direction.get('direction_id'))} "
                    f"{_text(direction.get('name'))}** → "
                    f"`{_text(link.get('stage_id'))}`：{_text(link.get('claim'))}"
                ),
                f"  - 方向说明：{_text(direction.get('summary'))}",
            ]
        )
    lines.extend(
        [
            "",
            f"**总体摘要：** {_text(spec.get('overall_summary'))}",
            "",
            "## 页面 4｜技术清单",
            "",
            "| 趋势阶段 | 方向 | 技术 | 价值简述 |",
            "|---|---|---|---|",
        ]
    )
    for direction, tech in tech_pairs:
        link = tech.get("trend_link", {})
        lines.append(
            "| {stage} | {direction} | {tech} | {brief} |".format(
                stage=_escape_md(link.get("stage_id")),
                direction=_escape_md(direction.get("name")),
                tech=_escape_md(tech.get("name")),
                brief=_escape_md(tech.get("brief")),
            )
        )

    page = 5
    for direction, tech in tech_pairs:
        link = tech.get("trend_link", {})
        lines.extend(
            [
                "",
                f"## 页面 {page}｜{_text(tech.get('title'))}",
                "",
                (
                    f"> `{_text(link.get('stage_id'))}`｜"
                    f"{_text(link.get('claim'))}"
                ),
                "",
                f"**参考：** [{_text(tech.get('reference'))}]({_text(tech.get('reference_url'))})",
                "",
                f"### 技术背景",
                "",
                _background_text(tech),
                "",
                "### 技术细节",
                "",
            ]
        )
        core_idea = _text(tech.get("tech_detail_summary"))
        if core_idea:
            lines.append(f"**核心思想：**{core_idea}")
            lines.append("")
        lines.append("**关键技术：**")
        lines.append("")
        for item in _items(tech.get("tech_detail_points")):
            lines.append(f"- {_bold_label_md(item)}")
        lines.append("")
        for index, image_path in enumerate(_image_paths(tech, "detail"), start=1):
            lines.append(_md_image(image_path, f"技术图 {index}", spec_dir))
        lines.extend(["", "### 实验结果", ""])
        if _text(tech.get("experiment_method_header")):
            lines.append(f"**{_text(tech.get('experiment_method_header'))}**")
        for item in _items(tech.get("experiment_method_points")):
            lines.append(f"- {_bold_label_md(item)}")
        lines.append("")
        for index, image_path in enumerate(_image_paths(tech, "result"), start=1):
            lines.append(_md_image(image_path, f"实验图 {index}", spec_dir))
        lines.append("")
        result_summary = _text(tech.get("experiment_result_summary"))
        if result_summary:
            lines.append(f"**实验总结：**{result_summary}")
            lines.append("")
        lines.append("**关键指标：**")
        lines.append("")
        for item in _items(tech.get("experiment_result_points")):
            lines.append(f"- {_bold_label_md(item)}")
        lines.extend(
            [
                "",
                f"**结果说明：** {_text(link.get('evidence'))}",
                "",
                f"**对技术路线的影响：** {_text(link.get('decision'))}",
                "",
                f"**洞察启示：** {_text(tech.get('takeaway'))}",
                "",
                "<details>",
                "<summary>交叉核验来源</summary>",
                "",
            ]
        )
        for source in _items(tech.get("supporting_sources")):
            lines.append(f"- [{_text(source.get('name'))}]({_text(source.get('url'))})")
        lines.extend(["", "</details>"])
        page += 1

    lines.extend(
        [
            "",
            f"## 页面 {page}｜{_text(academic.get('title')) or '学术资源洞察'}",
            "",
            "### 高校",
            "",
        ]
    )
    for university in _items(academic.get("universities")):
        lines.extend(
            [
                f"- **[{_text(university.get('name'))}]({_text(university.get('url'))})**",
                f"  - {_text(university.get('school_lab'))}",
                f"  - {_text(university.get('focus'))}",
                f"  - {_text(university.get('strength'))}",
            ]
        )
    lines.extend(
        [
            "",
            "### 教师与课题",
            "",
            "| 教师 | 高校 / 团队 | 研究方向 | 代表课题 | 时间 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in _items(academic.get("faculty_projects")):
        lines.append(
            "| [{faculty}]({profile_url}) | {university} | {focus} | [{project}]({project_url}) | {period} |".format(
                faculty=_escape_md(
                    f"{_text(item.get('faculty'))} {_text(item.get('title'))}"
                ),
                profile_url=_text(item.get("profile_url")),
                university=_escape_md(item.get("university")),
                focus=_escape_md(item.get("research_focus")),
                project=_escape_md(item.get("project")),
                project_url=_text(item.get("project_url")),
                period=_escape_md(item.get("period")),
            )
        )
    lines.extend(
        [
            "",
            f"**学术观点：** {_text(academic.get('viewpoint'))}",
            "",
            f"## 页面 {page + 1}｜{_text(viewpoint.get('title')) or '技术洞察观点'}",
            "",
            _text(viewpoint.get("viewpoint")),
            "",
        ]
    )
    for section in _items(viewpoint.get("sections")):
        lines.extend(["", f"### {_text(section.get('title'))}", ""])
        for point in _items(section.get("points")):
            lines.append(f"- {_text(point)}")
    lines.extend(["", "**待解问题：**", ""])
    for item in _items(viewpoint.get("unresolved")):
        lines.append(f"- {_text(item)}")
    lines.extend(
        [
            "",
            f"**建议：** {_text(viewpoint.get('suggestion'))}",
            "",
            f"## 页面 {page + 2}｜致谢",
            "",
            "Thank you",
            "",
        ]
    )
    return "\n".join(lines)


def _bullet_html(items: list) -> str:
    return (
        "<ul>"
        + "".join(f"<li>{_bold_label_html(item)}</li>" for item in items)
        + "</ul>"
    )


def _slide(title: str, body: str, eyebrow: str = "") -> str:
    eyebrow_html = f'<div class="eyebrow">{html.escape(eyebrow)}</div>' if eyebrow else ""
    return (
        '<section class="slide">'
        f"{eyebrow_html}<h2>{html.escape(title)}</h2>"
        f'<div class="rule"></div><div class="content">{body}</div>'
        "</section>"
    )


def render_html(spec: dict, spec_dir: Path) -> str:
    review = spec.get("review", {})
    trend = spec.get("trend_insight", {})
    directions = _items(spec.get("directions"))
    tech_pairs = list(_flatten_technologies(spec))
    academic = spec.get("academic_resources", {})
    viewpoint = spec.get("overall_viewpoint", {})

    slides: list[str] = []
    cover = f"""
      <div class="cover-main">
        <h1>{_html_text(spec.get("title"))}</h1>
        <p class="topic">{_html_text(spec.get("topic"))}</p>
      </div>
      <div class="meta">
        <span>部门：{_html_text(spec.get("department"))}</span>
        <span>作者：{_html_text(spec.get("author"))}</span>
        <span>日期：{_html_text(spec.get("date"))}</span>
      </div>
    """
    slides.append(
        f'<section class="slide cover">{cover}<div class="review-badge">'
        f'{_html_text(review.get("status"))} · v{_html_text(review.get("version"))}'
        "</div></section>"
    )

    trend_rows = []
    for stage in _items(trend.get("stages")):
        example = (
            stage.get("example")
            if isinstance(stage.get("example"), dict)
            else {}
        )
        trend_rows.append(
            f"""
            <div class="trend-row">
              <article class="stage-card">
                <div class="stage-id">{_html_text(stage.get("stage_id"))}</div>
                <div class="stage-period">{_html_text(stage.get("period"))}</div>
                <h3>{_html_text(stage.get("label"))}</h3>
                <p>{_html_text(stage.get("technical_change"))}</p>
              </article>
              <span class="trend-arrow">→</span>
              <article class="progress-card">
                {_html_image(
                    _text(example.get("figure")),
                    _text(example.get("figure_caption")),
                    spec_dir,
                )}
                <div>
                  <h3>{_html_text(example.get("title"))}</h3>
                  <small>{_html_text(example.get("organization"))} · {_html_text(example.get("date"))}</small>
                  <p>{_html_text(example.get("fact"))}</p>
                  <a href="{html.escape(_text(example.get("source_url")))}">
                    来源：{_html_text(example.get("source"))}
                  </a>
                </div>
              </article>
            </div>
            """
        )
    trend_body = f"""
      <div class="trend-sequence">{''.join(trend_rows)}</div>
      <div class="insight-bar"><b>洞察观点</b>{_html_text(trend.get("viewpoint"))}</div>
    """
    slides.append(_slide(_text(trend.get("title")) or "技术趋势洞察", trend_body, "02 · TREND"))

    direction_cards = []
    for direction in directions:
        link = direction.get("trend_link", {})
        direction_cards.append(
            f"""
            <article class="direction-card">
              <div class="link-pill">{_html_text(link.get("stage_id"))}</div>
              <h3>{_html_text(direction.get("direction_id"))} · {_html_text(direction.get("name"))}</h3>
              <p>{_html_text(direction.get("summary"))}</p>
              <small>{_html_text(link.get("claim"))}</small>
            </article>
            """
        )
    slides.append(
        _slide(
            "洞察摘要",
            f'<div class="topic-line"><b>核心问题</b>{_html_text(spec.get("topic"))}</div>'
            f'<div class="direction-grid">{"".join(direction_cards)}</div>'
            f'<div class="decision"><b>结论</b>{_html_text(spec.get("overall_summary"))}</div>',
            "03 · SUMMARY",
        )
    )

    rows = []
    for direction, tech in tech_pairs:
        link = tech.get("trend_link", {})
        rows.append(
            "<tr>"
            f'<td><span class="link-pill">{_html_text(link.get("stage_id"))}</span></td>'
            f"<td>{_html_text(direction.get('name'))}</td>"
            f"<td><b>{_html_text(tech.get('name'))}</b></td>"
            f"<td>{_html_text(tech.get('brief'))}</td>"
            "</tr>"
        )
    slides.append(
        _slide(
            "技术清单",
            '<table class="resource-table"><thead><tr><th>趋势</th><th>方向</th>'
            f"<th>技术</th><th>价值简述</th></tr></thead><tbody>{''.join(rows)}</tbody></table>",
            "04 · MAP",
        )
    )

    page = 5
    for direction, tech in tech_pairs:
        link = tech.get("trend_link", {})
        detail_paths = _image_paths(tech, "detail")
        detail_images = "".join(
            _html_image(path, f"技术图 {index}", spec_dir)
            for index, path in enumerate(detail_paths, start=1)
        )
        result_images = "".join(
            _html_image(path, f"实验图 {index}", spec_dir)
            for index, path in enumerate(_image_paths(tech, "result"), start=1)
        )
        sources = "".join(
            f'<a href="{html.escape(_text(item.get("url")))}">{_html_text(item.get("name"))}</a>'
            for item in _items(tech.get("supporting_sources"))
        )
        body = f"""
          <div class="tech-link"><b>{_html_text(link.get("stage_id"))}</b>{_html_text(link.get("claim"))}</div>
          <p class="reference">参考：<a href="{html.escape(_text(tech.get("reference_url")))}">{_html_text(tech.get("reference"))}</a></p>
          <div class="background"><b>技术背景</b>{_html_text(_background_text(tech))}</div>
          <div class="two-col">
            <div class="panel">
              <h3>技术细节</h3>
              <div class="figures detail count-{len(detail_paths)}">{detail_images}</div>
              {f'<p><b>核心思想：</b>{_html_text(tech.get("tech_detail_summary"))}</p>' if _text(tech.get("tech_detail_summary")) else ""}
              <p><b>关键技术：</b></p>
              {_bullet_html(_items(tech.get("tech_detail_points")))}
            </div>
            <div class="panel">
              <h3>实验结果</h3>
              {_bullet_html(_items(tech.get("experiment_method_points")))}
              <div class="figures">{result_images}</div>
              {f'<p><b>实验总结：</b>{_html_text(tech.get("experiment_result_summary"))}</p>' if _text(tech.get("experiment_result_summary")) else ""}
              <p><b>关键指标：</b></p>
              {_bullet_html(_items(tech.get("experiment_result_points")))}
            </div>
          </div>
          <div class="evidence-grid">
            <p><b>结果说明</b>{_html_text(link.get("evidence"))}</p>
            <p><b>对技术路线的影响</b>{_html_text(link.get("decision"))}</p>
          </div>
          <div class="decision"><b>洞察启示</b>{_html_text(tech.get("takeaway"))}</div>
          <div class="source-links">{sources}</div>
        """
        slides.append(_slide(_text(tech.get("title")), body, f"{page:02d} · INSIGHT"))
        page += 1

    university_cards = []
    for university in _items(academic.get("universities")):
        university_cards.append(
            f"""
            <article class="university-card">
              <h3><a href="{html.escape(_text(university.get("url")))}">{_html_text(university.get("name"))}</a></h3>
              <b>{_html_text(university.get("school_lab"))}</b>
              <p>{_html_text(university.get("focus"))}</p>
              <small>{_html_text(university.get("strength"))}</small>
            </article>
            """
        )
    faculty_rows = []
    for item in _items(academic.get("faculty_projects"))[:5]:
        faculty_rows.append(
            "<tr>"
            f'<td><a href="{html.escape(_text(item.get("profile_url")))}">{_html_text(item.get("faculty"))}</a>'
            f"<small>{_html_text(item.get('title'))}</small></td>"
            f"<td>{_html_text(item.get('university'))}</td>"
            f"<td>{_html_text(item.get('research_focus'))}</td>"
            f'<td><a href="{html.escape(_text(item.get("project_url")))}">{_html_text(item.get("project"))}</a>'
            f"<small>{_html_text(item.get('period'))}</small></td>"
            "</tr>"
        )
    academic_body = f"""
      <div class="academic-grid">
        <div>
          <h3>高校</h3>
          <div class="university-list">{''.join(university_cards)}</div>
        </div>
        <div>
          <h3>教师与课题</h3>
          <table class="resource-table faculty-table">
            <thead><tr><th>教师</th><th>高校 / 团队</th><th>研究方向</th><th>代表课题</th></tr></thead>
            <tbody>{''.join(faculty_rows)}</tbody>
          </table>
        </div>
      </div>
      <div class="insight-bar"><b>学术观点</b>{_html_text(academic.get("viewpoint"))}</div>
    """
    slides.append(_slide(_text(academic.get("title")) or "学术资源洞察", academic_body, f"{page:02d} · ACADEMIC"))

    horizon_cards = []
    for section in _items(viewpoint.get("sections")):
        horizon_cards.append(
            f'<article class="horizon"><h3>{_html_text(section.get("title"))}</h3>'
            f'{_bullet_html(_items(section.get("points")))}</article>'
        )
    viewpoint_body = f"""
      <div class="overall-summary">{_html_text(viewpoint.get("viewpoint"))}</div>
      <div class="horizon-row">{'<span class="arrow">→</span>'.join(horizon_cards)}</div>
      <div class="bottom-grid">
        <div class="risk-box"><b>待解问题</b>{_bullet_html(_items(viewpoint.get("unresolved")))}</div>
        <div class="recommendation"><b>建议</b>{_html_text(viewpoint.get("suggestion"))}</div>
      </div>
    """
    slides.append(_slide(_text(viewpoint.get("title")) or "技术洞察观点", viewpoint_body, f"{page + 1:02d} · VIEWPOINT"))
    slides.append('<section class="slide thanks"><h1>Thank you</h1></section>')

    css = f"""
      :root {{
        --red: {COLORS["red"]}; --blue: {COLORS["blue"]}; --cyan: {COLORS["cyan"]};
        --orange: {COLORS["orange"]}; --text: {COLORS["text"]};
        --muted: {COLORS["muted"]}; --light: {COLORS["light"]}; --white: {COLORS["white"]};
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: #E9EDF3; color: var(--text);
        font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif; }}
      .preview-header {{ position: sticky; top: 0; z-index: 5; padding: 12px 24px;
        color: white; background: var(--blue); box-shadow: 0 4px 12px #0002; }}
      .preview-header b {{ color: var(--cyan); }}
      .deck {{ padding: 24px; display: grid; gap: 24px; justify-content: center; }}
      .slide {{ position: relative; width: min(1120px, calc(100vw - 48px)); min-height: 630px;
        padding: 34px 48px 30px; overflow: hidden; background: var(--white);
        box-shadow: 0 8px 28px #20304a2b; }}
      .slide h2 {{ margin: 0; color: var(--red); font-size: 32px; line-height: 1.2; }}
      .slide h3 {{ color: var(--blue); margin: 0 0 8px; }}
      .rule {{ width: 100%; height: 1px; margin: 12px 0 18px;
        background: #E5E7EB; }}
      .eyebrow {{ position: absolute; right: 48px; top: 39px; color: var(--muted);
        font-size: 12px; letter-spacing: 1.3px; }}
      .cover {{ display: flex; flex-direction: column; justify-content: center; }}
      .cover::before {{ content: ""; position: absolute; left: 0; top: 0; width: 18px;
        height: 100%; background: var(--cyan); }}
      .cover h1 {{ color: var(--red); font-size: 56px; margin: 0 0 24px; }}
      .topic {{ max-width: 78%; color: var(--blue); font-size: 24px; }}
      .meta {{ position: absolute; left: 48px; bottom: 42px; display: grid; gap: 6px; }}
      .review-badge {{ position: absolute; right: 42px; top: 42px; padding: 7px 14px;
        color: white; background: var(--orange); border-radius: 999px; }}
      .thesis, .topic-line, .background {{ padding: 14px 18px; border-left: 6px solid var(--cyan);
        background: #F4F7FB; }}
      .thesis b, .topic-line b, .background b, .decision b, .evidence-grid b,
      .reading b, .gap-box b, .risk-box b, .recommendation b {{
        display: block; color: var(--blue); margin-bottom: 5px; }}
      .trend-sequence {{ display: grid; gap: 10px; }}
      .trend-row {{ display: grid; grid-template-columns: .78fr 28px 1.22fr;
        align-items: stretch; gap: 8px; }}
      .trend-arrow {{ align-self: center; color: var(--cyan); font-size: 23px;
        font-weight: bold; text-align: center; }}
      .stage-card {{ padding: 12px; border: 1px solid #D8DEE8;
        border-left: 5px solid var(--blue); background: white; border-radius: 8px; }}
      .stage-card p {{ margin: 8px 0; font-size: 13px; line-height: 1.5; }}
      .stage-card small {{ color: var(--muted); }}
      .stage-id {{ float: right; color: white; background: var(--blue);
        border-radius: 12px; padding: 2px 8px; font-weight: bold; }}
      .stage-period {{ color: var(--muted); font-size: 12px; }}
      .trend-row:nth-child(2) .stage-card {{ border-left-color: var(--cyan); background: #F7FCFC; }}
      .trend-row:nth-child(3) .stage-card, .trend-row:nth-child(4) .stage-card {{
        border-left-color: var(--orange); }}
      .progress-card {{ display: grid; grid-template-columns: .72fr 1.28fr; gap: 10px;
        border: 1px solid #D8DEE8; border-radius: 8px; padding: 10px; background: white; }}
      .progress-card figure {{ margin: 0; }}
      .progress-card figure img {{ height: 108px; max-height: 108px; }}
      .progress-card h3 {{ font-size: 14px; }}
      .progress-card p {{ margin: 6px 0; font-size: 12px; line-height: 1.45; }}
      .progress-card a, .progress-card small {{ font-size: 11px; }}
      .insight-bar {{ margin-top: 13px; padding: 12px 16px; background: #D9D9D9;
        border-left: 5px solid var(--red); }}
      .insight-bar b {{ color: var(--red); margin-right: 12px; }}
      .horizon-row {{ display: flex; align-items: stretch; margin: 18px 0; }}
      .arrow {{ align-self: center; padding: 0 8px; color: var(--cyan);
        font-size: 24px; font-weight: bold; }}
      .driver-row {{ display: flex; gap: 9px; flex-wrap: wrap; margin-bottom: 14px; }}
      .driver-row span {{ padding: 7px 12px; border-radius: 16px;
        color: var(--blue); background: #E8FAFA; }}
      .decision {{ padding: 13px 17px; border-left: 6px solid var(--orange);
        background: #FFF3ED; font-weight: 500; }}
      .source-note, .reference {{ color: var(--muted); font-size: 12px; }}
      .direction-grid {{ display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 14px; margin: 18px 0; }}
      .direction-card {{ position: relative; padding: 18px; border: 1px solid #D8DEE8;
        border-radius: 10px; }}
      .direction-card p {{ line-height: 1.55; }}
      .direction-card small {{ display: block; color: var(--muted); border-top: 1px solid #E5E7EB;
        padding-top: 8px; }}
      .link-pill {{ display: inline-block; padding: 3px 8px; color: white;
        background: var(--blue); border-radius: 12px; font-size: 11px; }}
      .tech-link {{ float: right; max-width: 46%; margin-top: -46px; padding: 6px 10px;
        color: var(--blue); border-bottom: 2px solid var(--cyan); font-size: 12px; }}
      .tech-link b {{ margin-right: 8px; color: var(--orange); }}
      .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin: 14px 0; }}
      .panel {{ padding: 14px; background: #F8FAFC; border-radius: 8px; }}
      .panel ul {{ margin: 8px 0; padding-left: 20px; font-size: 13px; line-height: 1.55; }}
      .figures {{ display: flex; gap: 8px; align-items: flex-start; }}
      .figures figure {{ flex: 1 1 0; min-width: 0; margin: 8px 0; }}
      .figures.detail.count-1 figure {{ flex-basis: 100%; }}
      .figures.detail figure img {{ height: auto; max-height: 180px; }}
      figure {{ margin: 8px 0; }}
      figure img {{ width: 100%; max-height: 155px; object-fit: contain;
        background: white; border: 1px solid #E5E7EB; }}
      figcaption {{ color: var(--muted); font-size: 10px; text-align: center; }}
      .evidence-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
      .evidence-grid p {{ margin: 0 0 12px; padding: 10px; background: #EEF3F9; font-size: 12px; }}
      .source-links {{ margin-top: 10px; display: flex; gap: 12px; flex-wrap: wrap; }}
      .source-links a, a {{ color: var(--blue); }}
      .academic-grid {{ display: grid; grid-template-columns: 0.86fr 1.64fr; gap: 20px; }}
      .university-list {{ display: grid; gap: 9px; }}
      .university-card {{ position: relative; padding: 11px 13px; border-left: 5px solid var(--cyan);
        background: #F4F7FB; }}
      .university-card b, .university-card p, .university-card small {{
        display: block; margin: 3px 0; font-size: 12px; }}
      .university-card small {{ color: var(--muted); }}
      .resource-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
      .resource-table th {{ color: var(--blue); background: #EAF0F7; text-align: left; }}
      .resource-table th, .resource-table td {{ padding: 10px; border: 1px solid #D7DCE3; }}
      .resource-table tbody tr:nth-child(even) {{ background: #F5F7FA; }}
      .resource-table.compact {{ font-size: 11px; }}
      .resource-table.compact th, .resource-table.compact td {{ padding: 6px; }}
      .faculty-table {{ font-size: 11px; }}
      .faculty-table th, .faculty-table td {{ padding: 7px; vertical-align: top; }}
      .faculty-table small {{ display: block; margin-top: 4px; color: var(--muted); }}
      .gap-box, .reading, .risk-box {{ margin-top: 11px; padding: 11px; background: #F4F7FB; }}
      .gap-box ul, .risk-box ul {{ margin: 5px 0; padding-left: 18px; }}
      .overall-summary {{ padding: 14px 18px; border-left: 5px solid var(--red);
        background: #F2F2F2; }}
      .overall-summary b {{ display: block; color: var(--blue); margin-bottom: 5px; }}
      .horizon {{ flex: 1; min-height: 220px; padding: 18px; color: var(--text);
        background: white; border: 1px solid var(--blue); }}
      .horizon:nth-of-type(2) {{ background: #F7FCFC; border-color: var(--cyan); }}
      .horizon:nth-of-type(3) {{ background: #FFF9F5; border-color: var(--orange); }}
      .horizon h3 {{ color: var(--blue); font-size: 26px; }}
      .horizon ul {{ padding-left: 18px; line-height: 1.7; }}
      .bottom-grid {{ display: grid; grid-template-columns: 1fr 1.35fr; gap: 16px; }}
      .recommendation {{ padding: 18px; color: var(--text); background: #FFF3ED;
        border: 1px solid var(--orange); }}
      .recommendation b, .recommendation small {{ color: var(--blue); }}
      .recommendation small {{ display: block; margin-top: 14px; opacity: .85; }}
      .thanks {{ display: grid; place-items: center; background: var(--blue); }}
      .thanks h1 {{ color: white; font-size: 64px; }}
      @media (max-width: 850px) {{
        .slide {{ min-height: auto; padding: 28px; }}
        .horizon-row {{ flex-direction: column; }}
        .arrow {{ transform: rotate(90deg); text-align: center; }}
        .two-col, .academic-grid, .bottom-grid, .direction-grid, .trend-row,
        .progress-card {{ grid-template-columns: 1fr; }}
        .trend-arrow {{ transform: rotate(90deg); }}
        .tech-link {{ float: none; max-width: none; margin: 8px 0; }}
      }}
      @media print {{
        body {{ background: white; }}
        .preview-header {{ display: none; }}
        .deck {{ display: block; padding: 0; }}
        .slide {{ width: 13.333in; height: 7.5in; min-height: 0; box-shadow: none;
          page-break-after: always; }}
      }}
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(_text(spec.get("title")))}｜内容确认稿</title>
  <style>{css}</style>
</head>
<body>
  <div class="preview-header">
    <b>内容确认稿</b> · 状态 {_html_text(review.get("status"))}
    · v{_html_text(review.get("version"))} · {_html_text(review.get("review_note"))}
  </div>
  <main class="deck">{''.join(slides)}</main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="UTF-8 spec.json 路径")
    parser.add_argument("--out-dir", required=True, help="预览输出目录")
    parser.add_argument("--format", choices=("md", "html", "both"), default="both")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] 无法读取 spec：{exc}", file=sys.stderr)
        return 2

    report = validate_spec_data(spec, base_dir=spec_path.parent, phase="preview")
    if not report.ok:
        print("[FAIL] spec 未通过 preview 校验：", file=sys.stderr)
        for item in report.errors:
            print(f"  - {item}", file=sys.stderr)
        return 1
    for warning in report.warnings:
        print(f"[WARN] {warning}")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{spec_path.stem}_preview"
    written: list[Path] = []

    if args.format in ("md", "both"):
        path = out_dir / f"{stem}.md"
        path.write_text(render_markdown(spec, spec_path.parent), encoding="utf-8", newline="\n")
        written.append(path)
    if args.format in ("html", "both"):
        path = out_dir / f"{stem}.html"
        path.write_text(render_html(spec, spec_path.parent), encoding="utf-8", newline="\n")
        written.append(path)

    for path in written:
        print(f"[OK] 已生成 {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
