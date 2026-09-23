"""Send one long-context diagnostic request to the owned local service."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

from transformers import AutoTokenizer


MODEL_PATH = "/models/Qwen3.6-27B"
MODEL_NAME = "qwen36-self-indexing-v2"
RESULT = Path("/results/request-summary.json")
BASE_URL = "http://127.0.0.1:8235"


def main() -> None:
    if RESULT.exists():
        raise FileExistsError(f"immutable request result exists: {RESULT}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    seed_ids = tokenizer.encode(
        "Attention can recall facts from a long document. The answer is forty two.\n",
        add_special_tokens=False,
    )
    if not seed_ids:
        raise RuntimeError("empty tokenizer seed")
    prompt_ids = (seed_ids * (20718 // len(seed_ids) + 1))[:20718]
    body = {"model": MODEL_NAME, "prompt": prompt_ids, "max_tokens": 4,
            "temperature": 0, "seed": 0, "ignore_eos": True}
    wire = json.dumps(body, separators=(",", ":")).encode("utf-8")
    start = time.perf_counter()
    with urlopen(Request(
        BASE_URL + "/v1/completions", data=wire,
        headers={"Content-Type": "application/json"}, method="POST",
    ), timeout=600) as response:
        raw = response.read()
        status = response.status
    result = json.loads(raw)
    summary = {
        "schema": "self-indexing-request/v2", "http_status": status,
        "model": result.get("model"), "prompt_tokens_requested": len(prompt_ids),
        "usage": result.get("usage", {}),
        "elapsed_seconds": time.perf_counter() - start,
        "prompt_ids_sha256": hashlib.sha256(
            json.dumps(prompt_ids, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "choices": len(result.get("choices", [])),
    }
    RESULT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
