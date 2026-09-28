"""Read-only dense native-oracle request matching the failed 3584-token prompt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

from transformers import AutoTokenizer


MODEL_PATH = "/models/Qwen3.6-27B"
RESULT = Path("/results/dense-red-request-summary.json")
PROMPT_TOKENS = 3584


def main() -> None:
    if RESULT.exists():
        raise FileExistsError(f"immutable result exists: {RESULT}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    seed = tokenizer.encode("The red book records seventy three.\n", add_special_tokens=False)
    if not seed:
        raise RuntimeError("empty tokenizer seed")
    prompt_ids = (seed * (PROMPT_TOKENS // len(seed) + 1))[:PROMPT_TOKENS]
    body = {"model": "qwen36-adakv-live-v1", "prompt": prompt_ids, "max_tokens": 4,
            "temperature": 0, "seed": 0, "ignore_eos": True}
    wire = json.dumps(body, separators=(",", ":")).encode("utf-8")
    start = time.perf_counter()
    with urlopen(Request("http://127.0.0.1:8235/v1/completions", data=wire,
                         headers={"Content-Type": "application/json"},
                         method="POST"), timeout=600) as response:
        raw = response.read()
        status = response.status
    payload = json.loads(raw)
    summary = {"schema": "adakv-dense-red-oracle/v1", "http_status": status,
               "usage": payload.get("usage", {}), "elapsed_seconds": time.perf_counter() - start,
               "prompt_ids_sha256": hashlib.sha256(
                   json.dumps(prompt_ids, separators=(",", ":")).encode("utf-8")).hexdigest(),
               "response_sha256": hashlib.sha256(raw).hexdigest()}
    RESULT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
