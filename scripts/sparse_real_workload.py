"""Bounded offline c1 real-request screen; not an HTTP baseline replacement."""
import hashlib
import json
import math
import os
from pathlib import Path
from vllm import LLM, SamplingParams

dataset = Path("/data/query_rewrite.jsonl")
assert hashlib.sha256(dataset.read_bytes()).hexdigest() == "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
assert hashlib.sha256(Path("/model/Qwen3.8-27B/config.json").read_bytes()).hexdigest() == "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
questions = [json.loads(line)["question"] for line in dataset.read_text().splitlines() if line.strip()]
assert len(questions) == 357
arm = os.environ["SPARSE_SMOKE_CACHE"]
assert arm in ("native", "paper")
phase = os.environ["SPARSE_REAL_PHASE"]
assert phase in ("performance", "quality")
if arm == "paper" and not os.environ.get("SPARSE_TRAINING_REPORT"):
    raise RuntimeError("Real workload requires frozen past-only training report")
output = Path("/output")
identity = dict(model="Qwen3.8-27B", arm=arm, phase=phase, tp=4,
                scope="offline c1 first16 heldout requests; not production HTTP benchmark",
                train_indices=[0,71], test_indices=[71,87], max_model_len=6144,
                dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                patch_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in Path("/patch/model_tuning_lab").glob("sparse_*.py")})
output.joinpath("identity.json").write_text(json.dumps(identity, indent=2))
extra = {"scheduler_cls":"model_tuning_lab.sparse_scheduler.SparseCanaryScheduler"} if arm == "paper" else {}
llm = LLM(model="/model/Qwen3.8-27B", dtype="bfloat16", tensor_parallel_size=4,
          max_model_len=6144, max_num_seqs=1, max_num_batched_tokens=4096,
          gpu_memory_utilization=0.7, enforce_eager=True, enable_prefix_caching=True,
          mamba_cache_mode="align", disable_log_stats=False, seed=0, **extra)
params = SamplingParams(temperature=0, seed=0, max_tokens=64 if phase=="performance" else 512,
                        ignore_eos=phase=="performance")
# Use training requests only for warmup; no heldout outputs influence the plan.
llm.generate(questions[:1], params, use_tqdm=False)
with output.joinpath("requests.jsonl").open("w") as stream:
    for repeat in range(3 if phase=="performance" else 1):
        for index in range(71,87):
            request = llm.generate([questions[index]], params, use_tqdm=False)[0]
            result = request.outputs[0]
            stats = request.metrics
            if stats is None or stats.is_corrupted:
                raise RuntimeError("Missing metrics or corrupted result")
            count = len(result.token_ids)
            ttft = stats.first_token_latency * 1000
            tpot = (stats.last_token_ts - stats.first_token_ts) * 1000 / (count-1) if count>1 else None
            if not math.isfinite(ttft) or ttft<=0 or (tpot is not None and (not math.isfinite(tpot) or tpot<0)):
                raise RuntimeError("Invalid same-clock latency metrics")
            row = dict(index=index, repeat=repeat, token_ids=list(result.token_ids),
                       text=result.text, finish_reason=result.finish_reason,
                       num_cached_tokens=request.num_cached_tokens,
                       ttft_ms=ttft, tpot_ms=tpot, output_tokens=count)
            stream.write(json.dumps(row, ensure_ascii=False)+"\n")
            stream.flush()
            if phase=="performance" and count!=64:
                raise RuntimeError("Fixed-output performance contract failed")
            if phase=="quality" and (result.finish_reason!="stop" or not result.text.strip()):
                raise RuntimeError("Quality requires nonempty natural EOS")
print("REAL_SCREEN_COMPLETE_PENDING_PAIRED_AUDIT", flush=True)
