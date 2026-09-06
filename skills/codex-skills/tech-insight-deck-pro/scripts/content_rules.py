"""技术洞察页面文案的组合、计量与版面容量规则。"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable


BACKGROUND_MAX_UNITS = 118
# 技术细节拆成两个独立字段：
# - tech_detail_summary：「核心思想」，人类可读的一句完整表述，允许比分点略长；
# - tech_detail_points：「关键技术」分点，2–3 项，每项「名称：简述」，名称加粗。
#
# 以下数字不是拍脑袋定的版面感觉，而是按模板实际盒子尺寸换算的物理容量：
# 11pt 字号、1.2 倍行距下，一行约能容纳 36–37 个“版面单位”；每个分点都是
# 独立段落，无论多短都会独占一行，所以“单项上限”按能在一行内排完来定
# （避免换行吃掉额外一整行的高度），“总项上限”再按“标题 + 最多 3 个分点”
# 的行数总和来定。总结句允许换行，但上限按最多 2 行估算。
TECH_DETAIL_SUMMARY_MIN_CJK = 20
TECH_DETAIL_SUMMARY_MAX_UNITS = 70
TECH_DETAIL_POINTS_MAX_UNITS = 115
TECH_DETAIL_POINTS_ITEM_MAX_UNITS = 34
EXPERIMENT_METHOD_MAX_UNITS = 150
EXPERIMENT_METHOD_ITEM_MAX_UNITS = 56
# 实验结果同样拆成两个独立字段，格式与技术细节的「核心思想 + 关键技术」一致，
# 版面单位上限按同样的物理容量方法换算：
# - experiment_result_summary：「实验总结」，人类可读的一句完整表述；
# - experiment_result_points：「关键指标」分点，2–3 项，每项「指标名称：结果表现」，指标名称加粗。
EXPERIMENT_RESULT_SUMMARY_MIN_CJK = 20
EXPERIMENT_RESULT_SUMMARY_MAX_UNITS = 70
EXPERIMENT_RESULT_MAX_UNITS = 115
EXPERIMENT_RESULT_ITEM_MAX_UNITS = 34
# 实验结果不再支持/渲染 experiment_result_header：该分区在模板里已经有固定的
# 「实验结果」标签，spec 内部不需要也不应该再重复这几个字；「关键指标」标题
# 由 build_deck.py 固定加上，不需要 spec 提供。
# 洞察启示改为聚焦「先进性 / 成熟度 / 借鉴意义」三点的精简段落，
# 不再要求复述机制与实验细节，长度上下限相应收紧。
TAKEAWAY_MIN_CJK = 70
TAKEAWAY_MAX_UNITS = 110

BACKGROUND_PREFIX_RE = re.compile(
    r"^\s*(?:现状|当前现状|痛点|问题|待解问题|课题|课题问题)\s*[：:]\s*"
)
SENTENCE_ENDINGS = "。！？；.!?;"


def text(value: Any) -> str:
    return str(value or "").strip()


def strip_background_prefix(value: Any) -> str:
    """去掉结构化字段里误写的显式标签，避免标签进入观众可见页面。"""
    return BACKGROUND_PREFIX_RE.sub("", text(value), count=1)


def as_sentence(value: Any) -> str:
    value = strip_background_prefix(value)
    if not value:
        return ""
    return value if value[-1] in SENTENCE_ENDINGS else value + "。"


def compose_background_text(background: Any) -> str:
    """把内部结构字段组合为自然段，不显示“现状/痛点/问题”等字段名。"""
    if not isinstance(background, dict):
        return text(background)
    return "".join(
        as_sentence(background.get(key))
        for key in ("current_state", "pain_point", "research_question")
        if text(background.get(key))
    )


def display_units(value: Any) -> float:
    """估算模板字号下的横向占用；中文按 1，半角字符按较小权重计。"""
    total = 0.0
    for char in text(value):
        if char == "\n":
            total += 4.0
        elif char.isspace():
            total += 0.25
        elif "\u4e00" <= char <= "\u9fff":
            total += 1.0
        elif unicodedata.east_asian_width(char) in {"W", "F"}:
            total += 1.0
        elif char.isalnum():
            total += 0.55
        else:
            total += 0.45
    return round(total, 1)


def points_units(items: Iterable[Any]) -> float:
    values = [text(item) for item in items if text(item)]
    return round(
        sum(display_units(item) for item in values)
        + max(0, len(values) - 1) * 2.0,
        1,
    )


def cjk_count(value: Any) -> int:
    return sum(1 for char in text(value) if "\u4e00" <= char <= "\u9fff")


def clause_count(value: Any) -> int:
    return len(
        [
            part
            for part in re.split(r"[。！？；.!?;]+", text(value))
            if part.strip()
        ]
    )
