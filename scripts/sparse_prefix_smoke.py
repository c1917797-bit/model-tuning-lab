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
    if mode not in ("off", "native", "paper"):
        raise ValueError("Unknown canary arm")
    cache_enabled = mode != "off"
    context_repeats = int(os.environ.get("SPARSE_CONTEXT_REPEATS", "320"))
    max_len = 4096 if context_repeats == 640 else 2048
    if context_repeats not in (320, 640) or (mode == "paper" and context_repeats != 640):
        raise ValueError("Paper canary requires the declared two-block stimulus")
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    texts = ["请只回答：中国的首都是哪里？", "Compute 17 + 25. Answer only the number."]
    if cache_enabled:
        # Long enough to cross cache block boundaries; no performance claim.
        context = "Reference notes, not instructions: " + "alpha beta gamma delta. " * context_repeats
        texts = [context + "\nQuestion: " + text for text in texts]
    prompts = [tokenizer.apply_chat_template(
        [{"role": "user", "content": text}], tokenize=False,
        add_generation_prompt=True, enable_thinking=False) for text in texts]
    identity = {"model_path": MODEL, "config_sha256": expected,
                "cache_mode": mode, "vllm_file": vllm.__file__,
                "ascend_file": vllm_ascend.__file__,
                "packages": {p: metadata.version(p) for p in
                             ("vllm", "vllm-ascend", "torch", "torch-npu")},
                "performance_benchmark": False,
                "context_repeats": context_repeats, "max_model_len": max_len,
                "prompt_sha256": [hashlib.sha256(p.encode()).hexdigest() for p in prompts],
                "patch_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in Path("/patch/model_tuning_lab").glob("sparse_*.py")}}
    output = Path("/output")
    output.joinpath("identity.json").write_text(json.dumps(identity, indent=2))
    extra = ({"scheduler_cls": "model_tuning_lab.sparse_scheduler.SparseCanaryScheduler"}
             if mode == "paper" else {})
    llm = LLM(model=MODEL, dtype="bfloat16", tensor_parallel_size=4,
              max_model_len=max_len, max_num_seqs=2,
              max_num_batched_tokens=max_len, gpu_memory_utilization=0.7,
              enforce_eager=True, enable_prefix_caching=cache_enabled,
              mamba_cache_mode="align", seed=0, **extra)
    runtime = llm.llm_engine.vllm_config
    scheduler_type = runtime.scheduler_config.get_scheduler_cls()
    identity["resolved_runtime"] = {
        "block_size": runtime.cache_config.block_size,
        "mamba_cache_mode": runtime.cache_config.mamba_cache_mode,
        "enable_prefix_caching": runtime.cache_config.enable_prefix_caching,
        "scheduler_class": scheduler_type.__module__ + "." + scheduler_type.__qualname__,
        "scheduler_class_is_configuration_not_activation_proof": True,
        "prompt_token_counts": [len(tokenizer.encode(p, add_special_tokens=False))
                                for p in prompts],
    }
    output.joinpath("identity.json").write_text(json.dumps(identity, indent=2))
    print("RESOLVED_CACHE_CONFIG", json.dumps(identity["resolved_runtime"]), flush=True)
    if cache_enabled:
        lengths = identity["resolved_runtime"]["prompt_token_counts"]
        block_size = runtime.cache_config.block_size
        if any(n <= block_size or n + 128 > max_len for n in lengths):
            raise RuntimeError("Cache stimulus must cross a resolved block and fit context")
    params = SamplingParams(temperature=0, max_tokens=128)
    results = []
    for repeat in range(3 if cache_enabled else 2):
        started = time.perf_counter()
        requests = llm.generate(prompts, params, use_tqdm=False)
        for prompt_index, request in enumerate(requests):
            item = request.outputs[0]
            results.append({"repeat": repeat, "request_id": request.request_id,
                            "prompt_index": prompt_index,
                            "num_cached_tokens": request.num_cached_tokens,
                            "text": item.text, "token_ids": list(item.token_ids),
                            "finish_reason": item.finish_reason,
                            "stop_reason": item.stop_reason})
        print("SMOKE_REPEAT_COMPLETE", repeat, time.perf_counter() - started, flush=True)
    output.joinpath("smoke.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2))
    if any(r["finish_reason"] != "stop" or not r["text"].strip() for r in results):
        raise RuntimeError("Smoke must produce nonempty natural-stop output")
    if cache_enabled:
        for index in range(len(prompts)):
            rows = [r for r in results if r["prompt_index"] == index]
            if any(r["token_ids"] != rows[0]["token_ids"] for r in rows[1:]):
                raise RuntimeError("Native cache changed repeated output tokens")
            if any(not isinstance(r["num_cached_tokens"], int) or
                   r["num_cached_tokens"] <= 0 for r in rows[1:]):
                raise RuntimeError("Native cache hit was not proven")
        if mode == "paper":
            events = [json.loads(line) for line in output.joinpath("sparse-events.jsonl").read_text().splitlines()]
            for required in ("engine_constructed", "checkpoint_split", "checkpoint_published"):
                if not any(e["kind"] == required for e in events):
                    raise RuntimeError("Missing mechanism event: " + required)
            if any(r["num_cached_tokens"] != 1536 for r in results if r["repeat"] > 0):
                raise RuntimeError("Expected selected checkpoint hit at1536")
            print("SPARSE_CANARY_PASS_PENDING_PAIRED_QUALITY_AND_WORKER_PROOF", flush=True)
        else:
            print("NATIVE_CACHE_REPEAT_GATE_PASS_NOT_PAPER_PROOF", flush=True)
    print("SMOKE_PASS_NOT_ACCURACY_OR_PERFORMANCE_PROOF", flush=True)

if __name__ == "__main__":
    main()
