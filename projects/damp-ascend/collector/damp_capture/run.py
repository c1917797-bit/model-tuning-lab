"""Single opt-in offline vLLM generation run. Parent exclusively schedules NPU."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from .contract import RESULT_ROOT, canonical, digest, load_manifest, require, token_digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--capture", choices=["on", "off"], required=True)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--memory-utilization", type=float, default=0.80)
    args = parser.parse_args()
    m = load_manifest(args.manifest)
    require(1 <= args.batch_size <= 4, "bounded calibration concurrency 1..4")
    require(0 < args.memory_utilization <= 0.85, "unsafe memory-utilization")
    root = Path(args.output_dir).resolve()
    require(root.is_relative_to(Path(RESULT_ROOT)) and root != Path(RESULT_ROOT), "output path outside approved result root")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
            "require parent-inspected container physical4..7 -> logical0..3")
    # Exclusive creation before loading weights: an old run can never be overwritten.
    root.mkdir(parents=True, exist_ok=False)
    run = dict(schema="damp-live-run/v1", manifest_sha256=digest(m),
               capture_enabled=args.capture == "on", mode=m["mode"],
               evidence_scope="smoke-hook-not-calibration" if m["mode"] == "smoke" else "FP32-reference-calibration-only",
               generation=m["generation"], batch_size=args.batch_size,
               physical_devices=[4, 5, 6, 7], logical_devices=[0, 1, 2, 3],
               enforce_eager=True, prefix_cache=False, chunked_prefill=False)
    (root / "RUN.json").write_bytes(canonical(run) + b"\n")
    os.environ["DAMP_CAPTURE_ENABLE"] = "1" if args.capture == "on" else "0"
    os.environ["DAMP_CAPTURE_MANIFEST"] = str(Path(args.manifest).resolve())
    os.environ["DAMP_CAPTURE_OUTPUT"] = str(root)
    os.environ["VLLM_PLUGINS"] = "damp_capture"
    os.environ["VLLM_USE_V1"] = "1"
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    from vllm import LLM, SamplingParams
    # Native model, native FP32 state and native GDN path remain unchanged.
    llm = LLM(model=m["model_path"], tensor_parallel_size=4, dtype="bfloat16",
              enforce_eager=True, enable_prefix_caching=False, enable_chunked_prefill=False,
              max_model_len=8192, max_num_seqs=args.batch_size,
              max_num_batched_tokens=max(8192, args.batch_size * 1024),
              gpu_memory_utilization=args.memory_utilization, seed=0,
              trust_remote_code=False, disable_log_stats=True)
    generation = m["generation"]
    params = SamplingParams(temperature=0, seed=0, top_p=1,
                            min_tokens=generation["min_tokens"],
                            max_tokens=generation["max_tokens"], ignore_eos=True)
    with (root / "client.jsonl").open("x", encoding="utf-8") as audit:
        for start in range(0, len(m["rows"]), args.batch_size):
            batch = m["rows"][start:start + args.batch_size]
            results = llm.generate([{"prompt_token_ids": row["input_ids"]} for row in batch],
                                   params, use_tqdm=False)
            require(len(results) == len(batch), "client request count mismatch")
            for row, output in zip(batch, results):
                require(list(output.prompt_token_ids) == row["input_ids"],
                        "engine input token IDs changed")
                require(len(output.outputs) == 1, "multiple generation candidates unsupported")
                sample = output.outputs[0]
                ids = list(sample.token_ids)
                require(len(ids) == generation["max_tokens"] and output.finished,
                        "fixed-length generation incomplete")
                record = dict(logical_id=row["id"], runtime_id=output.request_id,
                              prompt_token_sha256=row["input_ids_sha256"],
                              output_tokens=len(ids), output_token_ids=ids,
                              output_token_sha256=token_digest(ids),
                              finish_reason=sample.finish_reason, stop_reason=sample.stop_reason)
                audit.write(canonical(record).decode() + "\n")
                audit.flush()
    (root / "CLIENT_COMPLETE.json").write_bytes(canonical(dict(
        rows=len(m["rows"]), mode=m["mode"], manifest_sha256=digest(m))) + b"\n")
    print(json.dumps(dict(output_dir=str(root), scope=run["evidence_scope"]), sort_keys=True))


if __name__ == "__main__":
    main()
