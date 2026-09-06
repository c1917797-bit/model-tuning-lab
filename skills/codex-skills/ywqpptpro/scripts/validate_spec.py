"""校验技术洞察 spec 的结构、阶段关联、资源与审批状态。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from content_rules import (
    BACKGROUND_MAX_UNITS,
    BACKGROUND_PREFIX_RE,
    EXPERIMENT_METHOD_ITEM_MAX_UNITS,
    EXPERIMENT_METHOD_MAX_UNITS,
    EXPERIMENT_RESULT_ITEM_MAX_UNITS,
    EXPERIMENT_RESULT_MAX_UNITS,
    EXPERIMENT_RESULT_SUMMARY_MAX_UNITS,
    EXPERIMENT_RESULT_SUMMARY_MIN_CJK,
    TAKEAWAY_MAX_UNITS,
    TAKEAWAY_MIN_CJK,
    TECH_DETAIL_POINTS_ITEM_MAX_UNITS,
    TECH_DETAIL_POINTS_MAX_UNITS,
    TECH_DETAIL_SUMMARY_MAX_UNITS,
    TECH_DETAIL_SUMMARY_MIN_CJK,
    cjk_count,
    clause_count,
    compose_background_text,
    display_units,
    points_units,
)

try:
    from PIL import Image, ImageStat
except ImportError:  # pragma: no cover - build runtime is expected to include Pillow.
    Image = None
    ImageStat = None


APPROVED = "approved"
VALID_REVIEW_STATES = {"draft", APPROVED}
PLACEHOLDERS = ("xxx", "待补充", "待确认", "tbd", "todo", "[图：")
MIN_IMAGE_LONG_EDGE = 1000
MIN_IMAGE_SHORT_EDGE = 350
MIN_IMAGE_PIXELS = 450_000
AI_TONE = (
    "近年来",
    "随着",
    "赋能",
    "全方位",
    "值得注意的是",
    "总的来说",
    "总体而言",
    "综合来看",
    "持续关注",
    "积极布局",
    "核心判断",
    "证据依据",
    "业界实践",
    "最新论文",
    "研究集群",
    "证据缺口",
    "阅读策略",
    "优先阅读",
)
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# 洞察启示（takeaway）改为聚焦三件事：先进性、成熟度、借鉴意义。
# 三组标记词用于粗粒度校验这三层是否都被提到，而不是要求复述机制或实验细节。
TAKEAWAY_ADVANCEMENT_MARKERS = (
    "先进",
    "领先",
    "突破",
    "首次",
    "相比",
    "优于",
    "超越",
    "更强",
    "更高",
    "更快",
    "更优",
)
TAKEAWAY_MATURITY_MARKERS = (
    "成熟度",
    "成熟",
    "原型",
    "验证阶段",
    "生产环境",
    "工程化",
    "尚处",
    "仍需",
    "落地难度",
    "规模化",
    "小规模",
)
TAKEAWAY_GUIDANCE_MARKERS = (
    "借鉴",
    "启示",
    "可用于",
    "建议",
    "参考",
    "指导",
    "值得",
    "适用",
    "可优先",
)

# 实验方法固定按「实验设计 → 平台与基线 → 数据与变量」从整体到细节展开，
# 体现层次感；每一层的标签必须来自对应的固定用语集合。
EXPERIMENT_METHOD_MACRO_LABELS = ("实验设计", "验证目标", "总体设计")
EXPERIMENT_METHOD_MESO_LABELS = ("平台与基线", "环境与基线", "实验环境")
EXPERIMENT_METHOD_MICRO_LABELS = ("数据与变量", "关键变量", "数据与负载", "负载与变量")

# 实验结果的标签必须是具体指标名称，不能是这类空泛占位词。
EXPERIMENT_RESULT_BANNED_LABELS = (
    "关键数据",
    "实验数据",
    "数据表现",
    "效果展示",
    "结果显示",
    "核心数据",
    "数据",
    "结果",
    "效果",
)
EXPERIMENT_RESULT_NUMBER_RE = re.compile(r"[0-9%×xX倍]")


@dataclass
class ValidationReport:
    """保存校验错误和非阻断警告。"""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def warn(self, condition: bool, message: str) -> None:
        if not condition:
            self.warnings.append(message)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _items(value: Any) -> list:
    return value if isinstance(value, list) else []


def split_bold_label(value: str) -> tuple[str | None, str]:
    """按 build_deck.py 的加粗规则拆出「标签：正文」中的标签部分。

    与 build_deck.write_bold_prefix_paragraphs 保持一致：优先匹配全角
    冒号（任意位置），否则匹配前 28 个字符内的半角冒号；都不存在时
    视为没有标签的纯文本句。
    """
    value = _text(value)
    if "：" in value:
        idx = value.index("：")
        return value[:idx].strip(), value[idx + 1 :].strip()
    if ":" in value and value.index(":") < 28:
        idx = value.index(":")
        return value[:idx].strip(), value[idx + 1 :].strip()
    return None, value


def _require_max_units(
    report: ValidationReport,
    label: str,
    value: Any,
    maximum: float,
) -> None:
    units = display_units(value)
    report.require(
        units <= maximum,
        f"{label} 预计占用 {units} 个版面单位，超过上限 {maximum}；"
        "请先压缩信息，不得依靠自动缩小字号。",
    )


def _require_points_budget(
    report: ValidationReport,
    label: str,
    items: list,
    *,
    total_maximum: float,
    item_maximum: float,
) -> None:
    values = [_text(item) for item in items if _text(item)]
    units = points_units(values)
    report.require(
        units <= total_maximum,
        f"{label} 合计预计占用 {units} 个版面单位，超过上限 "
        f"{total_maximum}；请删减或重写。",
    )
    for index, value in enumerate(values):
        _require_max_units(
            report,
            f"{label}[{index}]",
            value,
            item_maximum,
        )


def _image_paths(tech: dict, kind: str) -> list[str]:
    if kind == "detail":
        keys = ("tech_detail_figures", "tech_detail_figure", "tech_detail_figure2")
    else:
        keys = ("experiment_figures", "experiment_figure")
    paths: list[str] = []
    for key in keys:
        value = tech.get(key)
        if isinstance(value, list):
            paths.extend(_text(item) for item in value if _text(item))
        elif _text(value):
            paths.append(_text(value))
    return list(dict.fromkeys(paths))


def _resolved_path(raw_path: str, base_dir: Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else base_dir / path


def _path_key(raw_path: str) -> str:
    return Path(raw_path).as_posix().casefold()


def _validate_image_quality(
    report: ValidationReport,
    path: Path,
    label: str,
    *,
    required: bool,
) -> None:
    """检查可自动判断的清晰度与空白图问题。"""
    if not path.is_file():
        if required:
            report.errors.append(f"{label} 图片不存在：{path}")
        return
    if Image is None or ImageStat is None:
        if required:
            report.errors.append("图片质量校验需要 Pillow。")
        else:
            report.warnings.append("未安装 Pillow，跳过图片像素质量检查。")
        return
    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            long_edge = max(width, height)
            short_edge = min(width, height)
            pixels = width * height
            thumbnail = image.convert("L").resize((64, 64))
            contrast = ImageStat.Stat(thumbnail).stddev[0]
    except Exception as exc:
        report.errors.append(f"{label} 无法读取：{path}（{exc}）")
        return

    checker = report.require if required else report.warn
    checker(
        long_edge >= MIN_IMAGE_LONG_EDGE,
        f"{label} 长边只有 {long_edge}px，至少需要 {MIN_IMAGE_LONG_EDGE}px。",
    )
    checker(
        short_edge >= MIN_IMAGE_SHORT_EDGE,
        f"{label} 短边只有 {short_edge}px，至少需要 {MIN_IMAGE_SHORT_EDGE}px。",
    )
    checker(
        pixels >= MIN_IMAGE_PIXELS,
        f"{label} 总像素只有 {pixels}，至少需要 {MIN_IMAGE_PIXELS}。",
    )
    checker(
        contrast >= 2.0,
        f"{label} 接近空白或对比度过低，请重新截取：{path}",
    )


def _walk_strings(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def validate_spec_data(
    spec: dict,
    *,
    base_dir: Path | None = None,
    phase: str = "preview",
) -> ValidationReport:
    """校验已加载的 spec。

    preview 阶段允许 review.status=draft，也不强制本地图片已落盘；
    build 阶段要求显式批准且全部图片存在。
    """

    report = ValidationReport()
    root = Path(base_dir or ".").resolve()
    is_build = phase == "build"

    report.require(isinstance(spec, dict), "根节点必须是 JSON 对象。")
    if not isinstance(spec, dict):
        return report

    review = spec.get("review") if isinstance(spec.get("review"), dict) else {}
    status = _text(review.get("status")).lower()
    version = review.get("version")
    report.require(status in VALID_REVIEW_STATES, "review.status 必须为 draft 或 approved。")
    report.require(
        isinstance(version, int) and not isinstance(version, bool) and version >= 1,
        "review.version 必须是大于等于 1 的整数。",
    )
    if is_build:
        report.require(
            status == APPROVED,
            "PPT 构建被阻止：review.status 必须为 approved，且只能在用户明确确认后修改。",
        )

    for key, label in (
        ("title", "标题"),
        ("topic", "核心问题"),
        ("overall_summary", "总体摘要"),
    ):
        report.require(bool(_text(spec.get(key))), f"{label}（{key}）不能为空。")

    trend = spec.get("trend_insight") if isinstance(spec.get("trend_insight"), dict) else {}
    report.require(bool(trend), "缺少 trend_insight 技术趋势洞察。")
    report.require(
        bool(_text(trend.get("viewpoint"))),
        "trend_insight.viewpoint 不能为空。",
    )

    stages = _items(trend.get("stages"))
    report.require(3 <= len(stages) <= 4, "trend_insight.stages 必须包含 3–4 个趋势阶段。")
    stage_ids: list[str] = []
    for index, stage in enumerate(stages, start=1):
        prefix = f"trend_insight.stages[{index - 1}]"
        if not isinstance(stage, dict):
            report.errors.append(f"{prefix} 必须是对象。")
            continue
        stage_id = _text(stage.get("stage_id"))
        stage_ids.append(stage_id)
        for key in ("stage_id", "period", "label", "technical_change"):
            report.require(bool(_text(stage.get(key))), f"{prefix}.{key} 不能为空。")
        example = stage.get("example") if isinstance(stage.get("example"), dict) else {}
        report.require(bool(example), f"{prefix}.example 必须提供本阶段的代表性进展。")
        for key in (
            "kind",
            "title",
            "organization",
            "date",
            "fact",
            "source",
            "source_url",
            "figure",
            "figure_caption",
        ):
            report.require(bool(_text(example.get(key))), f"{prefix}.example.{key} 不能为空。")
        report.require(
            _text(example.get("kind")) in {"practice", "paper", "project", "standard"},
            f"{prefix}.example.kind 必须为 practice、paper、project 或 standard。",
        )
        report.require(
            bool(URL_RE.match(_text(example.get("source_url")))),
            f"{prefix}.example.source_url 必须是 http(s) URL。",
        )
        if _text(example.get("figure")):
            _validate_image_quality(
                report,
                _resolved_path(_text(example.get("figure")), root),
                f"{prefix}.example.figure",
                required=True,
            )
    report.require(
        len([item for item in stage_ids if item]) == len(set(item for item in stage_ids if item)),
        "趋势阶段 stage_id 必须唯一。",
    )
    valid_stage_ids = {item for item in stage_ids if item}

    directions = _items(spec.get("directions"))
    report.require(bool(directions), "directions 至少包含一个洞察方向。")
    direction_ids: list[str] = []
    technology_ids: list[str] = []
    for d_index, direction in enumerate(directions, start=1):
        prefix = f"directions[{d_index - 1}]"
        if not isinstance(direction, dict):
            report.errors.append(f"{prefix} 必须是对象。")
            continue
        direction_id = _text(direction.get("direction_id"))
        direction_ids.append(direction_id)
        for key in ("direction_id", "name", "summary"):
            report.require(bool(_text(direction.get(key))), f"{prefix}.{key} 不能为空。")
        d_link = direction.get("trend_link") if isinstance(direction.get("trend_link"), dict) else {}
        d_stage = _text(d_link.get("stage_id"))
        report.require(d_stage in valid_stage_ids, f"{prefix}.trend_link.stage_id 必须引用有效趋势阶段。")
        report.require(bool(_text(d_link.get("claim"))), f"{prefix}.trend_link.claim 不能为空。")

        technologies = _items(direction.get("technologies"))
        report.require(bool(technologies), f"{prefix}.technologies 至少包含一项技术。")
        for t_index, tech in enumerate(technologies, start=1):
            t_prefix = f"{prefix}.technologies[{t_index - 1}]"
            if not isinstance(tech, dict):
                report.errors.append(f"{t_prefix} 必须是对象。")
                continue
            technology_id = _text(tech.get("technology_id"))
            technology_ids.append(technology_id)
            for key in (
                "technology_id",
                "name",
                "brief",
                "title",
                "reference",
                "reference_url",
                "takeaway",
            ):
                report.require(bool(_text(tech.get(key))), f"{t_prefix}.{key} 不能为空。")
            report.require(
                bool(URL_RE.match(_text(tech.get("reference_url")))),
                f"{t_prefix}.reference_url 必须是 http(s) URL。",
            )

            t_link = tech.get("trend_link") if isinstance(tech.get("trend_link"), dict) else {}
            t_stage = _text(t_link.get("stage_id"))
            report.require(t_stage in valid_stage_ids, f"{t_prefix}.trend_link.stage_id 必须引用有效趋势阶段。")
            for key in ("claim", "evidence", "decision"):
                report.require(bool(_text(t_link.get(key))), f"{t_prefix}.trend_link.{key} 不能为空。")

            background = tech.get("background")
            report.require(
                isinstance(background, dict),
                f"{t_prefix}.background 必须包含 current_state、pain_point "
                "与 research_question。",
            )
            if isinstance(background, dict):
                for key in (
                    "current_state",
                    "pain_point",
                    "research_question",
                ):
                    value = _text(background.get(key))
                    report.require(
                        bool(value),
                        f"{t_prefix}.background.{key} 不能为空。",
                    )
                    if value:
                        report.require(
                            not bool(BACKGROUND_PREFIX_RE.match(value)),
                            f"{t_prefix}.background.{key} 不要以“现状：”"
                            "“痛点：”或“问题：”等标签开头；请直接写自然句。",
                        )
                        report.require(
                            "\n" not in value and "\r" not in value,
                            f"{t_prefix}.background.{key} 必须写成连续自然句，"
                            "不能手工换行。",
                        )
                        report.require(
                            display_units(value) >= 18,
                            f"{t_prefix}.background.{key} 过短，无法说明"
                            "具体对象、约束或待解问题。",
                        )
                research_question = _text(
                    background.get("research_question")
                )
                if research_question:
                    report.require(
                        any(
                            marker in research_question
                            for marker in (
                                "需要",
                                "如何",
                                "必须",
                                "应",
                                "目标",
                                "要解决",
                            )
                        ),
                        f"{t_prefix}.background.research_question 必须明确"
                        "课题要解决什么问题。",
                    )
                _require_max_units(
                    report,
                    f"{t_prefix}.background",
                    compose_background_text(background),
                    BACKGROUND_MAX_UNITS,
                )

            detail_paths = _image_paths(tech, "detail")
            result_paths = _image_paths(tech, "result")
            report.require(bool(detail_paths), f"{t_prefix} 缺少真实技术/架构图。")
            report.require(
                len(detail_paths) <= 2,
                f"{t_prefix}.tech_detail_figures 只允许 1–2 张图片。",
            )
            report.require(bool(result_paths), f"{t_prefix} 缺少真实实验结果图。")
            raw_detail_paths = [
                _text(item)
                for item in _items(tech.get("tech_detail_figures"))
                if _text(item)
            ]
            report.require(
                len({_path_key(item) for item in raw_detail_paths})
                == len(raw_detail_paths),
                f"{t_prefix}.tech_detail_figures 不得重复使用同一图片。",
            )
            for raw_path in detail_paths + result_paths:
                _validate_image_quality(
                    report,
                    _resolved_path(raw_path, root),
                    f"{t_prefix} 图片",
                    required=True,
                )

            expected_quality_paths = {
                _path_key(item) for item in detail_paths + result_paths
            }
            quality_checks = _items(tech.get("figure_quality_checks"))
            checked_paths: set[str] = set()
            for q_index, check in enumerate(quality_checks):
                q_prefix = f"{t_prefix}.figure_quality_checks[{q_index}]"
                if not isinstance(check, dict):
                    report.errors.append(f"{q_prefix} 必须是对象。")
                    continue
                check_path = _text(check.get("path"))
                report.require(bool(check_path), f"{q_prefix}.path 不能为空。")
                if check_path:
                    checked_paths.add(_path_key(check_path))
                report.require(
                    bool(_text(check.get("source_ref"))),
                    f"{q_prefix}.source_ref 不能为空。",
                )
                report.require(
                    check.get("complete") is True,
                    f"{q_prefix}.complete 必须为 true。",
                )
                report.require(
                    check.get("clean_crop") is True,
                    f"{q_prefix}.clean_crop 必须为 true。",
                )
                report.require(
                    check.get("legible") is True,
                    f"{q_prefix}.legible 必须为 true。",
                )
                report.require(
                    bool(_text(check.get("crop_note"))),
                    f"{q_prefix}.crop_note 必须说明保留与排除的内容。",
                )
            report.require(
                checked_paths == expected_quality_paths,
                f"{t_prefix}.figure_quality_checks 必须逐一覆盖全部技术图和实验图，且不得包含无关路径。",
            )

            detail_points = _items(tech.get("tech_detail_points"))
            method_points = _items(tech.get("experiment_method_points"))
            result_points = _items(tech.get("experiment_result_points"))

            # ── 技术细节：核心思想（人类可读的完整表述）+ 关键技术分点（名称加粗） ──
            summary_text = _text(tech.get("tech_detail_summary"))
            report.require(
                bool(summary_text),
                f"{t_prefix}.tech_detail_summary 不能为空，需要一句更完整、"
                "适合人读的核心思想描述。",
            )
            if summary_text:
                report.require(
                    "\n" not in summary_text and "\r" not in summary_text,
                    f"{t_prefix}.tech_detail_summary 必须写成连续自然句，"
                    "不能手工换行。",
                )
                summary_label, _ = split_bold_label(summary_text)
                report.require(
                    summary_label is None,
                    f"{t_prefix}.tech_detail_summary 本身不能包含冒号标签；"
                    "加粗的“核心思想：”前缀由 build_deck.py 自动添加。",
                )
                report.require(
                    cjk_count(summary_text) >= TECH_DETAIL_SUMMARY_MIN_CJK,
                    f"{t_prefix}.tech_detail_summary 至少需要 "
                    f"{TECH_DETAIL_SUMMARY_MIN_CJK} 个中文字符，写成完整、"
                    "适合人读的一句话，而不是电报式短语。",
                )
                _require_max_units(
                    report,
                    f"{t_prefix}.tech_detail_summary",
                    f"核心思想：{summary_text}",
                    TECH_DETAIL_SUMMARY_MAX_UNITS,
                )

            report.require(
                2 <= len(detail_points) <= 3,
                f"{t_prefix}.tech_detail_points 必须包含 2–3 个关键技术分点。",
            )
            for k_index, k_point in enumerate(detail_points):
                k_label, k_rest = split_bold_label(k_point)
                report.require(
                    bool(k_label) and bool(k_rest),
                    f"{t_prefix}.tech_detail_points[{k_index}] 必须写成"
                    "「关键技术名称：简述」，技术名称会自动加粗；"
                    "不能省略冒号或名称。",
                )
            _require_points_budget(
                report,
                f"{t_prefix}.tech_detail_points",
                # 固定的“关键技术：”标题也占用版面，一并计入总预算；单项上限
                # 单独在下面按原始索引校验，避免加上标题后序号错位。
                ["关键技术："] + [f"• {item}" for item in detail_points if _text(item)],
                total_maximum=TECH_DETAIL_POINTS_MAX_UNITS,
                item_maximum=TECH_DETAIL_POINTS_MAX_UNITS,
            )
            for k_index, k_point in enumerate(detail_points):
                _require_max_units(
                    report,
                    f"{t_prefix}.tech_detail_points[{k_index}]",
                    f"• {k_point}",
                    TECH_DETAIL_POINTS_ITEM_MAX_UNITS,
                )

            # ── 实验方法：实验设计 → 平台与基线 → 数据与变量，体现层次感 ──
            report.require(
                3 <= len(method_points) <= 4,
                f"{t_prefix}.experiment_method_points 必须包含 3–4 项，"
                "按「实验设计→平台与基线→数据与变量」从整体到细节分层组织。",
            )
            if method_points:
                macro_label, _ = split_bold_label(method_points[0])
                report.require(
                    macro_label in EXPERIMENT_METHOD_MACRO_LABELS,
                    f"{t_prefix}.experiment_method_points[0] 的标签必须是 "
                    f"{list(EXPERIMENT_METHOD_MACRO_LABELS)} 之一，先说明整体"
                    "实验设计与验证目标。",
                )
            if len(method_points) >= 2:
                meso_label, _ = split_bold_label(method_points[1])
                report.require(
                    meso_label in EXPERIMENT_METHOD_MESO_LABELS,
                    f"{t_prefix}.experiment_method_points[1] 的标签必须是 "
                    f"{list(EXPERIMENT_METHOD_MESO_LABELS)} 之一，说明运行平台"
                    "与对照基线。",
                )
            for extra_index in range(2, len(method_points)):
                micro_label, _ = split_bold_label(method_points[extra_index])
                report.require(
                    micro_label in EXPERIMENT_METHOD_MICRO_LABELS,
                    f"{t_prefix}.experiment_method_points[{extra_index}] 的标签"
                    f"必须是 {list(EXPERIMENT_METHOD_MICRO_LABELS)} 之一，说明"
                    "具体数据规模、负载或受控变量。",
                )
            method_content = (
                [_text(tech.get("experiment_method_header"))]
                + method_points
            )
            _require_points_budget(
                report,
                f"{t_prefix}.experiment_method",
                method_content,
                total_maximum=EXPERIMENT_METHOD_MAX_UNITS,
                item_maximum=EXPERIMENT_METHOD_ITEM_MAX_UNITS,
            )

            # ── 实验结果：实验总结（人类可读）+ 关键指标（指标名称加粗分点）──
            result_summary_text = _text(tech.get("experiment_result_summary"))
            report.require(
                bool(result_summary_text),
                f"{t_prefix}.experiment_result_summary 不能为空，需要一句更"
                "完整、适合人读的实验总结。",
            )
            if result_summary_text:
                report.require(
                    "\n" not in result_summary_text
                    and "\r" not in result_summary_text,
                    f"{t_prefix}.experiment_result_summary 必须写成连续自然句，"
                    "不能手工换行。",
                )
                result_summary_label, _ = split_bold_label(result_summary_text)
                report.require(
                    result_summary_label is None,
                    f"{t_prefix}.experiment_result_summary 本身不能包含冒号"
                    "标签；加粗的“实验总结：”前缀由 build_deck.py 自动添加。",
                )
                report.require(
                    cjk_count(result_summary_text) >= EXPERIMENT_RESULT_SUMMARY_MIN_CJK,
                    f"{t_prefix}.experiment_result_summary 至少需要 "
                    f"{EXPERIMENT_RESULT_SUMMARY_MIN_CJK} 个中文字符，写成完整、"
                    "适合人读的一句话，而不是电报式短语。",
                )
                _require_max_units(
                    report,
                    f"{t_prefix}.experiment_result_summary",
                    f"实验总结：{result_summary_text}",
                    EXPERIMENT_RESULT_SUMMARY_MAX_UNITS,
                )

            report.require(
                2 <= len(result_points) <= 3,
                f"{t_prefix}.experiment_result_points 必须包含 2–3 项。",
            )
            for r_index, r_point in enumerate(result_points):
                r_label, r_rest = split_bold_label(r_point)
                report.require(
                    bool(r_label) and bool(r_rest),
                    f"{t_prefix}.experiment_result_points[{r_index}] 必须写成"
                    "「指标名称：结果表现」，指标名称会自动加粗。",
                )
                if r_label:
                    report.require(
                        r_label not in EXPERIMENT_RESULT_BANNED_LABELS,
                        f"{t_prefix}.experiment_result_points[{r_index}] 不能用"
                        f"「{r_label}」这类空泛标签，请直接写具体指标名称"
                        "（如吞吐量、延迟、显存占用、准确率等）。",
                    )
                report.require(
                    bool(EXPERIMENT_RESULT_NUMBER_RE.search(r_rest)),
                    f"{t_prefix}.experiment_result_points[{r_index}] 的结果表现"
                    "必须包含具体数字、百分比或倍数，不能只写定性结论。",
                )
            report.require(
                not _text(tech.get("experiment_result_header")),
                f"{t_prefix} 不要设置 experiment_result_header：该分区在模板里"
                "已经有固定的“实验结果”标签，不需要在内容里重复这几个字，"
                "直接列出 experiment_result_points 即可。",
            )
            _require_points_budget(
                report,
                f"{t_prefix}.experiment_result_points",
                # 固定的“关键指标：”标题也占用版面，一并计入总预算；单项上限
                # 单独在下面按原始索引校验，避免加上标题后序号错位。
                ["关键指标："] + [f"• {item}" for item in result_points if _text(item)],
                total_maximum=EXPERIMENT_RESULT_MAX_UNITS,
                item_maximum=EXPERIMENT_RESULT_MAX_UNITS,
            )
            for r_index2, r_point2 in enumerate(result_points):
                _require_max_units(
                    report,
                    f"{t_prefix}.experiment_result_points[{r_index2}]",
                    f"• {r_point2}",
                    EXPERIMENT_RESULT_ITEM_MAX_UNITS,
                )

            # ── 洞察启示：聚焦先进性、成熟度、借鉴意义三点，不再要求复述机制 ──
            takeaway = _text(tech.get("takeaway"))
            report.require(
                "\n" not in takeaway and "\r" not in takeaway,
                f"{t_prefix}.takeaway 必须写成连续自然段，不能手工换行。",
            )
            report.require(
                cjk_count(takeaway) >= TAKEAWAY_MIN_CJK,
                f"{t_prefix}.takeaway 至少需要 {TAKEAWAY_MIN_CJK} "
                "个中文字符，简明说清先进性、成熟度和借鉴意义。",
            )
            _require_max_units(
                report,
                f"{t_prefix}.takeaway",
                takeaway,
                TAKEAWAY_MAX_UNITS,
            )
            report.require(
                clause_count(takeaway) >= 3,
                f"{t_prefix}.takeaway 至少写 3 个完整分句。",
            )
            report.require(
                any(
                    marker in takeaway
                    for marker in TAKEAWAY_ADVANCEMENT_MARKERS
                ),
                f"{t_prefix}.takeaway 缺少技术先进性的说明"
                "（与现有方案或基线相比的具体优势）。",
            )
            report.require(
                any(
                    marker in takeaway
                    for marker in TAKEAWAY_MATURITY_MARKERS
                ),
                f"{t_prefix}.takeaway 缺少技术成熟度的说明"
                "（研究原型、验证阶段还是可规模化落地）。",
            )
            report.require(
                any(
                    marker in takeaway
                    for marker in TAKEAWAY_GUIDANCE_MARKERS
                ),
                f"{t_prefix}.takeaway 缺少对当前系统的借鉴或指导意义。",
            )
            supporting = _items(tech.get("supporting_sources"))
            report.require(
                len(supporting) >= 3,
                f"{t_prefix}.supporting_sources 至少包含 3 个独立权威来源。",
            )
            for s_index, source in enumerate(supporting):
                s_prefix = f"{t_prefix}.supporting_sources[{s_index}]"
                if not isinstance(source, dict):
                    report.errors.append(f"{s_prefix} 必须是对象。")
                    continue
                report.require(bool(_text(source.get("name"))), f"{s_prefix}.name 不能为空。")
                report.require(
                    bool(URL_RE.match(_text(source.get("url")))),
                    f"{s_prefix}.url 必须是 http(s) URL。",
                )

    report.require(
        len([item for item in direction_ids if item]) == len(set(item for item in direction_ids if item)),
        "direction_id 必须唯一。",
    )
    report.require(
        len([item for item in technology_ids if item])
        == len(set(item for item in technology_ids if item)),
        "technology_id 必须唯一。",
    )

    academic = (
        spec.get("academic_resources")
        if isinstance(spec.get("academic_resources"), dict)
        else {}
    )
    report.require(bool(academic), "缺少 academic_resources 学术资源洞察。")
    universities = _items(academic.get("universities"))
    report.require(
        len(universities) >= 3,
        "academic_resources.universities 至少包含 3 所高校。",
    )
    for u_index, university in enumerate(universities):
        prefix = f"academic_resources.universities[{u_index}]"
        if not isinstance(university, dict):
            report.errors.append(f"{prefix} 必须是对象。")
            continue
        for key in ("name", "school_lab", "focus", "strength", "url"):
            report.require(bool(_text(university.get(key))), f"{prefix}.{key} 不能为空。")
        report.require(
            bool(URL_RE.match(_text(university.get("url")))),
            f"{prefix}.url 必须是 http(s) URL。",
        )

    faculty_projects = _items(academic.get("faculty_projects"))
    report.require(
        len(faculty_projects) >= 3,
        "academic_resources.faculty_projects 至少包含 3 位教师及其课题。",
    )
    for f_index, item in enumerate(faculty_projects):
        prefix = f"academic_resources.faculty_projects[{f_index}]"
        if not isinstance(item, dict):
            report.errors.append(f"{prefix} 必须是对象。")
            continue
        for key in (
            "faculty",
            "title",
            "university",
            "research_focus",
            "project",
            "period",
            "profile_url",
            "project_url",
        ):
            report.require(bool(_text(item.get(key))), f"{prefix}.{key} 不能为空。")
        for key in ("profile_url", "project_url"):
            report.require(
                bool(URL_RE.match(_text(item.get(key)))),
                f"{prefix}.{key} 必须是 http(s) URL。",
            )
    report.require(
        bool(_text(academic.get("viewpoint"))),
        "academic_resources.viewpoint 不能为空。",
    )

    viewpoint = (
        spec.get("overall_viewpoint")
        if isinstance(spec.get("overall_viewpoint"), dict)
        else {}
    )
    report.require(bool(viewpoint), "缺少 overall_viewpoint 技术洞察观点。")
    for key in ("viewpoint", "suggestion"):
        report.require(bool(_text(viewpoint.get(key))), f"overall_viewpoint.{key} 不能为空。")
    sections = _items(viewpoint.get("sections"))
    report.require(
        len(sections) == 3,
        "overall_viewpoint.sections 必须包含 3 个按主题命名的部分。",
    )
    for s_index, section in enumerate(sections):
        prefix = f"overall_viewpoint.sections[{s_index}]"
        if not isinstance(section, dict):
            report.errors.append(f"{prefix} 必须是对象。")
            continue
        report.require(bool(_text(section.get("title"))), f"{prefix}.title 不能为空。")
        report.require(bool(_items(section.get("points"))), f"{prefix}.points 至少包含 1 项。")
    report.require(
        bool(_items(viewpoint.get("unresolved"))),
        "overall_viewpoint.unresolved 至少包含 1 项。",
    )

    for path, value in _walk_strings(spec):
        lowered = value.lower()
        for placeholder in PLACEHOLDERS:
            if placeholder.lower() in lowered:
                message = f"{path} 包含占位内容“{placeholder}”。"
                if is_build:
                    report.errors.append(message)
                else:
                    report.warnings.append(message)
        for phrase in AI_TONE:
            if phrase in value:
                report.warnings.append(f"{path} 包含建议改写的套话“{phrase}”。")

    return report


def _print_report(report: ValidationReport, phase: str) -> None:
    if report.errors:
        print(f"[FAIL] {phase} 校验发现 {len(report.errors)} 个错误：")
        for item in report.errors:
            print(f"  - {item}")
    else:
        print(f"[OK] {phase} 校验通过。")
    if report.warnings:
        print(f"[WARN] {len(report.warnings)} 个非阻断提醒：")
        for item in report.warnings:
            print(f"  - {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, help="UTF-8 spec.json 路径")
    parser.add_argument("--phase", choices=("preview", "build"), default="preview")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] 无法读取 spec：{exc}", file=sys.stderr)
        return 2

    report = validate_spec_data(spec, base_dir=spec_path.parent, phase=args.phase)
    _print_report(report, args.phase)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
