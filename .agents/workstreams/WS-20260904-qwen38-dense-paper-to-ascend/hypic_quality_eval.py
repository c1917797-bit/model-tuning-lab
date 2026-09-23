#!/usr/bin/env python3
"""Dependency-free replay of the supplied AIS Bench LongBench v2/GSM8K ruler."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


LONGBENCH_PROMPT = (
    "Please read the following text and answer the questions below.\n <text> \n "
    "{context} \n </text> \n \n What is the correct answer to this question: "
    "{question} \n \n Choices: \n (A) {choice_A} \n (B) {choice_B} \n "
    "(C) {choice_C} \n (D) {choice_D} \n Let’s think step by step. Based on "
    "the above, what is the single, most likely answer choice? Format your "
    "response as follows: \"The correct answer is (insert answer here)"
)
GSM8K_PROMPT = (
    "Answer the following question.The last line of the response should follow "
    "this format: \"answer:$ANSWER\" (without quotes), where ANSWER is a "
    "number. Let's think step by step.\n\nQuestion: {question}"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_non_reasoning(text: str) -> str:
    if "<think>" not in text and "</think>" in text:
        return text.split("</think>")[-1].strip()
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def first_option(text: str) -> str:
    """Dependency-free copy of supplied AIS Bench first_option_postprocess."""
    options = "ABCD"
    patterns = [
        rf"答案是?\s*([{options}])",
        rf"答案是?\s*：\s*([{options}])",
        rf"答案是?\s*:\s*([{options}])",
        rf"答案选项应?该?是\s*([{options}])",
        rf"答案选项应?该?为\s*([{options}])",
        rf"答案应该?是\s*([{options}])",
        rf"答案应该?选\s*([{options}])",
        rf"答案选项为?\s*：\s*([{options}])",
        rf"答案选项为?\s+\(?\*?\*?([{options}])\*?\*?\)?",
        rf"答案选项是?\s*:\s*([{options}])",
        rf"答案为\s*([{options}])",
        rf"答案选\s*([{options}])",
        rf"选择?\s*([{options}])",
        rf"故选?\s*([{options}])" rf"只有选?项?\s?([{options}])\s?是?对",
        rf"只有选?项?\s?([{options}])\s?是?错",
        rf"只有选?项?\s?([{options}])\s?不?正确",
        rf"只有选?项?\s?([{options}])\s?错误",
        rf"说法不?对选?项?的?是\s?([{options}])",
        rf"说法不?正确选?项?的?是\s?([{options}])",
        rf"说法错误选?项?的?是\s?([{options}])",
        rf"([{options}])\s?是正确的",
        rf"([{options}])\s?是正确答案",
        rf"选项\s?([{options}])\s?正确",
        rf"所以答\s?([{options}])",
        rf"所以\s?([{options}][.。$]?$)",
        rf"所有\s?([{options}][.。$]?$)",
        rf"[\s，：:,]([{options}])[。，,\.]?$",
        rf"[\s，,：:][故即]([{options}])[。\.]?$",
        rf"[\s，,：:]因此([{options}])[。\.]?$",
        rf"[是为。]\s?([{options}])[。\.]?$",
        rf"因此\s?([{options}])[。\.]?$",
        rf"显然\s?([{options}])[。\.]?$",
        r"答案是\s?(\S+)(?:。|$)",
        r"答案应该是\s?(\S+)(?:。|$)",
        r"答案为\s?(\S+)(?:。|$)",
        rf"(?i)ANSWER\s*:\s*([{options}])",
        rf"[Tt]he answer is:?\s+\(?([{options}])\)?",
        rf"[Tt]he answer is:?\s+\(?\*?\*?([{options}])\*?\*?\)?",
        rf"[Tt]he answer is option:?\s+\(?([{options}])\)?",
        rf"[Tt]he correct answer is:?\s+\(?([{options}])\)?",
        rf"[Tt]he correct answer is option:?\s+\(?([{options}])\)?",
        rf"[Tt]he correct answer is:?.*?boxed{{([{options}])}}",
        rf"[Tt]he correct option is:?.*?boxed{{([{options}])}}",
        rf"[Tt]he correct answer option is:?.*?boxed{{([{options}])}}",
        rf"[Tt]he answer to the question is:?\s+\(?([{options}])\)?",
        rf"^选项\s?([{options}])",
        rf"^([{options}])\s?选?项",
        rf"(\s|^)[{options}][\s。，,：:\.$]",
        r"1.\s?(.*?)$",
        rf"1.\s?([{options}])[.。$]?$",
        rf"([{options}]):",
        rf"([{options}])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.strip(), re.DOTALL)
        if not match:
            continue
        outputs = match.group(1) if match.group(1) else match.group(0)
        for option in options:
            if option in outputs:
                return option
    return ""


def gsm8k_prediction(text: str) -> str:
    text = text.split("Question:")[0]
    numbers = re.findall(r"-?\d+\.\d+|-?\d+", text)
    return numbers[-1] if numbers else "NULL"


def load_samples(dataset: str, path: Path) -> list[dict[str, Any]]:
    if dataset == "longbenchv2":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("LongBench v2 data must be a JSON list")
        return data
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def build_case(dataset: str, sample: dict[str, Any]) -> tuple[str, str]:
    if dataset == "longbenchv2":
        return LONGBENCH_PROMPT.format(**sample), str(sample["answer"]).strip()
    return GSM8K_PROMPT.format(**sample), str(sample["answer"]).split("#### ")[1].replace(",", "")


def score_case(dataset: str, text: str, reference: str) -> tuple[str, bool]:
    clean = extract_non_reasoning(text)
    if dataset == "longbenchv2":
        prediction = first_option(clean)
        return prediction, prediction == reference
    prediction = gsm8k_prediction(clean)
    try:
        correct = prediction == reference or abs(float(prediction) - int(reference)) < 1e-6
    except (TypeError, ValueError):
        correct = False
    return prediction, correct


def request_one(args: argparse.Namespace, index: int, sample: dict[str, Any]) -> dict[str, Any]:
    prompt, reference = build_case(args.dataset, sample)
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": args.max_out_len,
        "temperature": 0,
        "seed": args.seed,
        "ignore_eos": False,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if args.dataset == "gsm8k":
        payload["stop"] = ["Question"]
    error = None
    started = time.perf_counter()
    data: dict[str, Any] | None = None
    for attempt in range(args.retries + 1):
        try:
            request = Request(
                args.base_url.rstrip("/") + "/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=args.timeout) as response:
                data = json.load(response)
            break
        except Exception as exc:
            if isinstance(exc, HTTPError):
                try:
                    detail = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    detail = ""
                error = f"{exc!r}: {detail[:1000]}"
            else:
                error = repr(exc)
            if attempt < args.retries:
                time.sleep(min(2 ** attempt, 5))
    elapsed = time.perf_counter() - started
    if data is None:
        return {
            "index": index,
            "ok": False,
            "error": error,
            "duration_s": elapsed,
            "reference": reference,
        }
    text = str(data["choices"][0]["message"].get("content") or "")
    prediction, correct = score_case(args.dataset, text, reference)
    return {
        "index": index,
        "ok": True,
        "error": None,
        "correct": correct,
        "prediction": prediction,
        "reference": reference,
        "response_text": text,
        "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "duration_s": elapsed,
        "finish_reason": data["choices"][0].get("finish_reason"),
        "usage": data.get("usage"),
        "sample_id": sample.get("_id"),
        "difficulty": sample.get("difficulty"),
        "length": sample.get("length"),
    }


def atomic_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        for row in sorted(rows, key=lambda item: int(item["index"])):
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=("longbenchv2", "gsm8k"), required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8221")
    parser.add_argument("--model", default="qwen36-hypic-piercing")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--max-out-len", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=2400)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    details_path = args.output_dir / f"{args.dataset}.{args.run_id}.jsonl"
    summary_path = args.output_dir / f"{args.dataset}.{args.run_id}.summary.json"
    samples = load_samples(args.dataset, args.data)
    rows: list[dict[str, Any]] = []
    if details_path.exists():
        with details_path.open(encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
    # Re-score persisted response text on every resume. This makes a corrected
    # local scorer recoverable without regenerating expensive model outputs.
    for row in rows:
        if row.get("ok") and row.get("response_text") is not None:
            prediction, correct = score_case(
                args.dataset, str(row["response_text"]), str(row["reference"])
            )
            row["prediction"] = prediction
            row["correct"] = correct
    completed = {int(row["index"]) for row in rows if row.get("ok")}
    pending = [(index, sample) for index, sample in enumerate(samples) if index not in completed]
    print(
        f"dataset={args.dataset} total={len(samples)} resume_ok={len(completed)} "
        f"pending={len(pending)} concurrency={args.concurrency}",
        flush=True,
    )
    by_index = {int(row["index"]): row for row in rows}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {
            pool.submit(request_one, args, index, sample): index
            for index, sample in pending
        }
        for count, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result()
            by_index[int(row["index"])] = row
            if count % 20 == 0 or count == len(futures):
                atomic_write_jsonl(details_path, list(by_index.values()))
                ok = sum(bool(item.get("ok")) for item in by_index.values())
                correct = sum(bool(item.get("correct")) for item in by_index.values())
                print(f"progress={len(by_index)}/{len(samples)} ok={ok} correct={correct}", flush=True)
    rows = [by_index[index] for index in sorted(by_index)]
    atomic_write_jsonl(details_path, rows)
    successful = [row for row in rows if row.get("ok")]
    correct = sum(bool(row.get("correct")) for row in successful)
    finish_reasons = {
        reason: sum(row.get("finish_reason") == reason for row in successful)
        for reason in sorted({str(row.get("finish_reason")) for row in successful})
    }
    category_accuracy_pct: dict[str, dict[str, float]] = {}
    if args.dataset == "longbenchv2":
        for field in ("difficulty", "length"):
            category_accuracy_pct[field] = {}
            for value in sorted({str(row.get(field)) for row in successful}):
                subset = [row for row in successful if str(row.get(field)) == value]
                category_accuracy_pct[field][value] = (
                    100 * sum(bool(row.get("correct")) for row in subset) / len(subset)
                )
    summary = {
        "schema": "hypic-quality-eval/v1",
        "dataset": args.dataset,
        "run_id": args.run_id,
        "data_path": str(args.data),
        "data_sha256": sha256_file(args.data),
        "prompt_template_sha256": hashlib.sha256(
            (LONGBENCH_PROMPT if args.dataset == "longbenchv2" else GSM8K_PROMPT).encode("utf-8")
        ).hexdigest(),
        "model": args.model,
        "base_url": args.base_url,
        "concurrency": args.concurrency,
        "max_out_len": args.max_out_len,
        "temperature": 0,
        "seed": args.seed,
        "ignore_eos": False,
        "enable_thinking": False,
        "scorer": (
            "supplied_ais_bench_first_option_postprocess"
            if args.dataset == "longbenchv2"
            else "supplied_ais_bench_gsm8k_numeric_postprocess"
        ),
        "requests": len(samples),
        "successful": len(successful),
        "failed": len(samples) - len(successful),
        "correct": correct,
        "accuracy_pct": (100 * correct / len(successful)) if successful else None,
        "category_accuracy_pct": category_accuracy_pct,
        "finish_reasons": finish_reasons,
        "completion_tokens": sum(
            int((row.get("usage") or {}).get("completion_tokens") or 0)
            for row in successful
        ),
        "unique_response_sha256": len(
            {row.get("response_sha256") for row in successful}
        ),
        "evaluator_script_sha256": sha256_file(Path(__file__)),
        "details_path": str(details_path),
        "details_sha256": sha256_file(details_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0 if len(successful) == len(samples) else 1


if __name__ == "__main__":
    raise SystemExit(main())
