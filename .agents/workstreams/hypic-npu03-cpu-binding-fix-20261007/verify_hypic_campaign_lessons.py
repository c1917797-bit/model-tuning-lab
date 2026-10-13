"""Read-only provenance/claim checks for the whole HYPIC campaign retrospective."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
NAME = "HYPIC_CAMPAIGN_LESSONS_20261013.json"
REPORT = "HYPIC_CAMPAIGN_RETROSPECTIVE_20261013.md"

def validate(data, base=BASE, report=None):
    def need(ok, message):
        if not ok:
            raise ValueError(message)
    need(data["scope"] == "whole-hypic-second-piercing-retrospective", "scope")
    need(3 <= len(data["facts"]) <= 7, "facts")
    o = data["outcomes"]
    need(o["runtime_source"] == "4429e35177979c874bf053ab29789e4773f39b22", "source mixing")
    need(o["performance"] == {
        "phases": 6, "scored_responses": 240, "candidate_hot_requests": 120,
        "tpot_median_reduction_pct": 22.0163,
        "ttft_p95_median_reduction_pct": 49.6429,
        "throughput_median_increase_pct": 31.7543}, "performance claims")
    need(o["quality"] == {
        "baseline": 227, "candidate": 219, "responses_per_arm": 381,
        "hot_proved": 134, "decision": "REJECT_OR_QUALIFY",
        "gsm8k_scope": "off-path"}, "quality claims")
    need(o["skills"] == {"total": 29, "bounded_verified": 13, "partial": 16}, "skill claims")
    for key in ("deployment_allowed", "new_device_work",
                "historical_verdicts_changed", "whole_branch_main_integration"):
        need(o[key] is False, key)
    evidence = data["evidence"]
    paths = [item["path"] for item in evidence]
    need(len(paths) == len(set(paths)) == 10, "source set")
    for item in evidence:
        path = base / item["path"]
        need(Path(item["path"]).name == item["path"] and not path.is_symlink(), "unsafe source")
        need(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], "source hash")
    lessons = data["lessons"]
    need({x["id"] for x in lessons} == {
        "identity", "effect", "reuse", "gates", "quality", "focus", "isolation",
        "profiling", "lifecycle", "handoff", "acceptance", "publication"
    } and len(lessons) == 12, "lesson coverage")
    for lesson in lessons:
        need(lesson["classification"] == 5, "classification")
        for key in ("trigger", "different_action", "destination", "verification"):
            need(isinstance(lesson.get(key), str) and lesson[key].strip(), "missing " + key)
        need(lesson["destination"] == NAME + "#" + lesson["id"], "destination")
        need(lesson["evidence"] and set(lesson["evidence"]) <= set(paths), "lesson evidence")
        skill = lesson["related_skill"]
        need("/" not in skill and (base.parents[1] / "skills" / skill / "SKILL.md").is_file(), "skill")
    report = (base / REPORT).read_text() if report is None else report
    for fragment in ("227/381→219/381", "22.0163%", "49.6429%", "31.7543%",
                     "13 bounded verified、16 partial", "134", "REJECT_OR_QUALIFY",
                     "不是始终同一个实现", "诊断偏离主线", "不等于已合入 main"):
        need(fragment in report, "report missing: " + fragment)
    return {"passed": True, "sources": len(paths), "lessons": len(lessons),
            "new_device_work": False, "acceptance_promoted": False,
            "scope": "retrospective integrity only; not new functional/NPU acceptance"}

if __name__ == "__main__":
    print(json.dumps(validate(json.loads((BASE / NAME).read_text())), ensure_ascii=False))
