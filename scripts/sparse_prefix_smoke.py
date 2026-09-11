"""Official-image Qwen3.8 BF16 smoke; not a performance benchmark."""
import hashlib
import json
import os
from pathlib import Path
import time

MODEL = "/model/Qwen3.8-27B"

def main():
    if os.environ.get("SPARSE_DEVICE_PREFLIGHT") == "1":
        import subprocess
        import torch_npu
        probe = subprocess.run(["npu-smi", "info"], capture_output=True, text=True)
        count = torch_npu.npu.device_count()
        print(probe.stdout, probe.stderr, flush=True)
        print("DEVICE_COUNT", count, flush=True)
        if count != 4:
            raise RuntimeError("Expected exactly four visible NPUs")
        return
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    import importlib.metadata as metadata
    import vllm
    import vllm_ascend
    config = Path(MODEL, "config.json").read_bytes()
    expected = "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
    if hashlib.sha256(config).hexdigest() != expected:
        raise RuntimeError("Unexpected model config; refuse model substitution")
    mode = os.environ.get("SPARSE_SMOKE_CACHE", "off")
    if mode not in ("off", "native"):
        raise ValueError("Only official baseline arms are supported")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    texts = ["请只回答：中国的首都是哪里？", "Compute 17 + 25. Answer only the number."]
    prompts = [tokenizer.apply_chat_template(
        [{"role": "user", "content": text}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False) for text in texts]
    identity = {"model_path": MODEL, "config_sha256": expected,
                "cache_mode": mode, "vllm_file": vllm.__file__,
                "ascend_file": vllm_ascend.__file__,
                "packages": {p: metadata.version(p) for p in
                             ("vllm", "vllm-ascend", "torch", "torch-npu")},
                "performance_benchmark": False}
    output = Path("/output")
    output.joinpath("identity.json").write_text(json.dumps(identity, indent=2))
    llm = LLM(model=MODEL, dtype="bfloat16", tensor_parallel_size=4,
              max_model_len=2048, max_num_seqs=2,
              max_num_batched_tokens=2048, gpu_memory_utilization=0.7,
              enforce_eager=True, enable_prefix_caching=(mode == "native"),
              mamba_cache_mode="align", seed=0)
    params = SamplingParams(temperature=0, max_tokens=128)
    results = []
    for repeat in range(2):
        started = time.perf_counter()
        requests = llm.generate(prompts, params, use_tqdm=False)
        for request in requests:
            item = request.outputs[0]
            results.append({"repeat": repeat, "request_id": request.request_id,
                            "text": item.text, "token_ids": list(item.token_ids),
                            "finish_reason": item.finish_reason,
                            "stop_reason": item.stop_reason})
        print("SMOKE_REPEAT_COMPLETE", repeat, time.perf_counter() - started, flush=True)
    output.joinpath("smoke.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2))
    if any(r["finish_reason"] != "stop" or not r["text"].strip() for r in results):
        raise RuntimeError("Smoke must produce nonempty natural-stop output")
    print("SMOKE_PASS_NOT_ACCURACY_OR_PERFORMANCE_PROOF", flush=True)

if __name__ == "__main__":
    main()
