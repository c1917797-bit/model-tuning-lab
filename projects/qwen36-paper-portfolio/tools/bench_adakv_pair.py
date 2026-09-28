"""Small immutable matched dense/Ada-KV serving screen, not final acceptance.

Run against exactly one already healthy service at a time with the same image,
model, runtime flags, prompt IDs, concurrency and 1024-token output cap.
The response stream supplies TTFT/TPOT; a non-streaming total duration cannot.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
from pathlib import Path
from threading import Barrier
import time
from urllib.request import Request, urlopen

from transformers import AutoTokenizer


SEEDS = ("The blue book records forty two.\n",
         "The red book records seventy three.\n")
LENGTHS = (4096, 3584)
MODEL_PATH = "/models/Qwen3.6-27B"
BASE_URL = "http://127.0.0.1:8235"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", choices=("dense", "candidate"), required=True)
    parser.add_argument("--max-tokens", type=int, default=1024)
    args = parser.parse_args()
    result = Path(args.output)
    if result.exists():
        raise FileExistsError(f"immutable benchmark result exists: {result}")
    if result.parent != Path("/results") or args.max_tokens != 1024:
        raise ValueError("screen requires /results/<new-file> and fixed 1024 outputs")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    seeds = tuple(tokenizer.encode(seed, add_special_tokens=False) for seed in SEEDS)
    prompts = tuple((seed * (length // len(seed) + 1))[:length]
                    for seed, length in zip(seeds, LENGTHS))
    barrier = Barrier(len(prompts))

    def request(index: int) -> dict:
        body = {"model": "qwen36-adakv-live-v1", "prompt": prompts[index],
                "max_tokens": args.max_tokens, "temperature": 0, "seed": 0,
                "ignore_eos": True, "stream": True,
                "stream_options": {"include_usage": True}}
        wire = json.dumps(body, separators=(",", ":")).encode("utf-8")
        barrier.wait(timeout=30)
        start = time.perf_counter()
        req = Request(BASE_URL + "/v1/completions", data=wire,
                      headers={"Content-Type": "application/json"}, method="POST")
        first = last = None
        usage = None
        chunks = 0
        with urlopen(req, timeout=2400) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            for raw_line in response:
                if not raw_line.startswith(b"data: "):
                    continue
                now = time.perf_counter()
                data = raw_line[6:].strip()
                if data == b"[DONE]":
                    break
                payload = json.loads(data)
                if payload.get("usage"):
                    usage = payload["usage"]
                for choice in payload.get("choices", ()):
                    if choice.get("text"):
                        chunks += 1
                        first = now if first is None else first
                        last = now
        end = time.perf_counter()
        if usage is None or usage.get("completion_tokens") != args.max_tokens:
            raise RuntimeError(f"missing or short output usage: {usage}")
        if first is None or last is None or chunks < 2:
            raise RuntimeError("stream did not contain enough token chunks")
        tokens = int(usage["completion_tokens"])
        return {"index": index, "prompt_tokens": len(prompts[index]),
                "prompt_ids_sha256": hashlib.sha256(json.dumps(
                    prompts[index], separators=(",", ":")).encode()).hexdigest(),
                "completion_tokens": tokens, "chunks": chunks,
                "ttft_seconds": first - start,
                "tpot_seconds": (last - first) / (tokens - 1),
                "end_to_end_seconds": end - start,
                "start_seconds": start, "last_token_seconds": last}

    with ThreadPoolExecutor(max_workers=len(prompts)) as pool:
        futures = [pool.submit(request, index) for index in range(len(prompts))]
        responses = sorted((future.result() for future in futures),
                           key=lambda item: item["index"])
    total = sum(item["completion_tokens"] for item in responses)
    wall = max(item["last_token_seconds"] for item in responses) - min(
        item["start_seconds"] for item in responses)
    summary = {"schema": "adakv-matched-serving-screen/v1", "label": args.label,
               "max_tokens": args.max_tokens, "concurrency": len(prompts),
               "total_output_tokens": total, "output_tokens_per_second": total / wall,
               "wall_seconds": wall,
               "mean_ttft_seconds": sum(x["ttft_seconds"] for x in responses) / len(responses),
               "mean_tpot_seconds": sum(x["tpot_seconds"] for x in responses) / len(responses),
               "responses": responses}
    result.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
