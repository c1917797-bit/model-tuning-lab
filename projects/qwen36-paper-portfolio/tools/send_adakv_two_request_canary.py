"""One immutable, asymmetric two-request Ada-KV NPU correctness canary."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from threading import Barrier
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from transformers import AutoTokenizer


MODEL_PATH = "/models/Qwen3.6-27B"
RESULT_BASENAME = os.environ.get("QWEN36_ADAKV_CANARY_RESULT_BASENAME", "two-request-summary.json")
if Path(RESULT_BASENAME).name != RESULT_BASENAME or not RESULT_BASENAME.endswith(".json"):
    raise ValueError("result basename must be a plain .json filename")
RESULT = Path("/results") / RESULT_BASENAME
BASE_URL = "http://127.0.0.1:8235"
LENGTHS = (4096, 3584)
MAX_TOKENS = int(os.environ.get("QWEN36_ADAKV_CANARY_MAX_TOKENS", "4"))


def main() -> None:
    if RESULT.exists():
        raise FileExistsError(f"immutable request result exists: {RESULT}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    seeds = (
        tokenizer.encode("The blue book records forty two.\n", add_special_tokens=False),
        tokenizer.encode("The red book records seventy three.\n", add_special_tokens=False),
    )
    if any(not seed for seed in seeds):
        raise RuntimeError("empty tokenizer seed")
    prompts = tuple((seed * (length // len(seed) + 1))[:length]
                    for seed, length in zip(seeds, LENGTHS))
    barrier = Barrier(2)

    def request(index: int) -> dict:
        body = {"model": "qwen36-adakv-live-v1", "prompt": prompts[index],
                "max_tokens": MAX_TOKENS, "temperature": 0, "seed": 0, "ignore_eos": True}
        wire = json.dumps(body, separators=(",", ":")).encode("utf-8")
        barrier.wait(timeout=30)
        start = time.perf_counter()
        request_obj = Request(BASE_URL + "/v1/completions", data=wire,
                              headers={"Content-Type": "application/json"},
                              method="POST")
        try:
            with urlopen(request_obj, timeout=2400) as response:
                raw = response.read()
                status = response.status
        except HTTPError as error:
            raw = error.read()
            status = error.code
        payload = json.loads(raw)
        return {"index": index, "http_status": status, "usage": payload.get("usage", {}),
                "elapsed_seconds": time.perf_counter() - start,
                "prompt_ids_sha256": hashlib.sha256(
                    json.dumps(prompts[index], separators=(",", ":")).encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(raw).hexdigest(),
                "choices": len(payload.get("choices", []))}

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request, index) for index in range(2)]
        responses = [future.result() for future in futures]
    summary = {"schema": "adakv-two-request-canary/v1", "requested_lengths": LENGTHS,
               "max_tokens": MAX_TOKENS,
               "responses": sorted(responses, key=lambda item: item["index"])}
    RESULT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    if any(response["http_status"] != 200 for response in responses):
        raise RuntimeError("Ada-KV two-request canary returned non-200 response")


if __name__ == "__main__":
    main()
