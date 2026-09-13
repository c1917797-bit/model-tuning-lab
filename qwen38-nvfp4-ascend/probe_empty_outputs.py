#!/usr/bin/env python3
"""Bounded empty-output diagnosis; not a quality or performance benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from chat_benchmark import load_dataset, post_json


def variants():
    return [
        ("nonstream", {"stream": False}),
        ("special_tokens_visible", {"stream": False, "skip_special_tokens": False,
                                     "return_token_ids": True}),
        ("ignore_eos_diagnostic_only", {"stream": False, "skip_special_tokens": False,
                                       "ignore_eos": True, "max_tokens": 16,
                                       "return_token_ids": True}),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--source-rows", type=Path, required=True)
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = [json.loads(x) for x in args.source_rows.open() if x.strip()]
    empty = [r["request_index"] for r in rows if not r["output_nonempty"]][:3]
    good = [r["request_index"] for r in rows if r["output_nonempty"]][:1]
    assert empty and good, "Need observed empty and nonempty controls"
    items = dict(load_dataset(args.dataset, 0))
    summaries = []
    args.output.mkdir(parents=True, exist_ok=False)
    for idx in empty + good:
        for name, changes in variants():
            payload = dict(model=args.model, messages=items[idx], temperature=0,
                           seed=1024, max_tokens=64,
                           chat_template_kwargs={"enable_thinking": False},
                           cache_salt=f"{args.output.name}:{idx}:{name}")
            payload.update(changes)
            record = {"index":idx, "variant":name, "request":payload}
            started = time.monotonic()
            try:
                with post_json(args.base_url.rstrip("/")+"/v1/chat/completions",
                               payload, 300) as response:
                    result = json.load(response)
                record["response"] = result
                choice = result["choices"][0]
                message = choice.get("message", {})
                summaries.append({
                    "index":idx, "variant":name,
                    "content_chars":len(message.get("content") or ""),
                    "reasoning_chars":len(message.get("reasoning_content") or message.get("reasoning") or ""),
                    "finish_reason":choice.get("finish_reason"),
                    "completion_tokens":result.get("usage", {}).get("completion_tokens"),
                    "token_ids":choice.get("token_ids"),
                })
            except Exception as exc:
                record["error"] = repr(exc)
                summaries.append({"index":idx, "variant":name, "error_type":type(exc).__name__})
            record["wall_seconds"] = time.monotonic()-started
            path = args.output/f"{idx}-{name}.json"
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n")
            path.with_suffix(".sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest()+"  "+path.name+"\n")
    doc = {"scope":"diagnostic only; ignore_eos results must never be scored",
           "source_rows_sha256":hashlib.sha256(args.source_rows.read_bytes()).hexdigest(),
           "cases":summaries}
    (args.output/"summary.json").write_text(json.dumps(doc, indent=2)+"\n")
    print(json.dumps(doc))
    return int(any("error_type" in row for row in summaries))


if __name__ == "__main__":
    raise SystemExit(main())

