"""Pure descriptive partition for the frozen r13 paired quality denominator."""

from __future__ import annotations


def cohort_summary(base_rows: list[dict], cand_rows: list[dict],
                   cold_keys: set[tuple[int, int]]) -> dict:
    base = {(row["index"], row["repetition"]): row for row in base_rows}
    cand = {(row["index"], row["repetition"]): row for row in cand_rows}
    if base.keys() != cand.keys() or len(base) != 381:
        raise RuntimeError("r13 cohort keys or cardinality drift")
    if not cold_keys <= base.keys():
        raise RuntimeError("cold request outside frozen pair")

    def summarize(keys: set[tuple[int, int]]) -> dict:
        left = sum(base[key]["correct"] for key in keys)
        right = sum(cand[key]["correct"] for key in keys)
        return {"requests": len(keys), "baseline_correct": left,
                "candidate_correct": right,
                "delta_pp": 100 * (right - left) / len(keys) if keys else None}

    return {"hot": summarize(base.keys() - cold_keys),
            "cold": summarize(cold_keys),
            "strata_are_descriptive_not_causal": True}
