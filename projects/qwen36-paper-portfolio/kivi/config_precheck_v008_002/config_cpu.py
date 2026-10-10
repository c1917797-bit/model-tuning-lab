"""Actual same-image ModelConfig/SchedulerConfig precheck; no engine or weights.

This is deliberately NOT a full EngineArgs.create_engine_config proof. The
source-pinned Ascend platform's complete config path queries device type.
MAIN executes this inside the existing bounded Devices[] CPU8 owner.
"""
import argparse
import hashlib
import importlib
import importlib.util
import inspect
import json
import sys
from pathlib import Path

UPSTREAM_SHA = "e20059758ee2408951066a265050d66653484174232bc118d69eca5c802f2581"
UPSTREAM_ROOT = "/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-007"
PINS = {
    "vllm.engine.arg_utils": "3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d",
    "vllm.config.scheduler": "36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86",
    "vllm.config.model": "cf5aeb9e16d6cac82426cf7e8d140741b35c503ae8b9e1fc9ba3dde53c585a62",
    "vllm.config.vllm": "ba062ec38d075937b73d953059cf1d0e1b96f1474990bc6d45ed45e20ba6a336",
    "vllm.entrypoints.openai.api_server": "6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f",
    "vllm_ascend.platform": "30c75952f784c4d047d7202dd7f68c8fc7c22bb975853a5048fb51ffcbe1f2a8",
}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def actual_sources():
    refs = {}
    for name, expected in PINS.items():
        module = importlib.import_module(name)
        path = Path(inspect.getfile(module)).resolve()
        need(path.is_file() and not path.is_symlink(), "ordinary installed config source: " + name)
        wire = path.read_bytes()
        need(hashlib.sha256(wire).hexdigest() == expected, "installed config SHA: " + name)
        refs[name] = dict(path=str(path), bytes=len(wire), sha256=expected)
    return refs


def corrected_argv(original):
    need(type(original) is list and original.count("--no-enable-chunked-prefill") == 1
         and "--enable-chunked-prefill" not in original, "one original chunked OFF action")
    out = list(original)
    out[out.index("--no-enable-chunked-prefill")] = "--enable-chunked-prefill"
    need([(i, a, b) for i, (a, b) in enumerate(zip(original, out))]
         and sum(a != b for a, b in zip(original, out)) == 1,
         "only the boolean action changes; no batch/length/cache/worker change")
    return out


def parse(api, argv):
    parser = api.make_arg_parser(api.FlexibleArgumentParser(description=__doc__))
    args = parser.parse_args(argv)
    api.validate_parsed_serve_args(args)
    return args


def scheduler_config(engine, model, scheduler_cls):
    """Use the installed class and the same actual kwargs as EngineArgs L2033.

    No rewritten validator, synthetic ModelConfig, platform override or device
    architecture. Explicit values avoid hardware-dependent batch defaults.
    """
    engine._check_feature_supported()
    engine._set_default_chunked_prefill_and_prefix_caching_args(model)
    return scheduler_cls(
        runner_type=model.runner_type,
        max_num_batched_tokens=engine.max_num_batched_tokens,
        max_num_seqs=engine.max_num_seqs,
        max_model_len=model.max_model_len,
        enable_chunked_prefill=engine.enable_chunked_prefill,
        disable_chunked_mm_input=engine.disable_chunked_mm_input,
        is_multimodal_model=model.is_multimodal_model,
        is_encoder_decoder=model.is_encoder_decoder,
        policy=engine.scheduling_policy,
        scheduler_cls=engine.scheduler_cls,
        max_num_partial_prefills=engine.max_num_partial_prefills,
        max_long_partial_prefills=engine.max_long_partial_prefills,
        long_prefill_token_threshold=engine.long_prefill_token_threshold,
        scheduler_reserve_full_isl=engine.scheduler_reserve_full_isl,
        disable_hybrid_kv_cache_manager=engine.disable_hybrid_kv_cache_manager,
        async_scheduling=engine.async_scheduling,
        stream_interval=engine.stream_interval,
    )


def require_firstdecode_policy(model, scheduler, cache_bytes):
    need(model.architecture == "Qwen3_5ForConditionalGeneration"
         and model.hf_config.model_type == "qwen3_5"
         and model.runner_type == "generate" and model.is_encoder_decoder is False
         and model.is_chunked_prefill_supported is True,
         "actual checkpoint architecture/generative supported chunked-prefill")
    need(model.max_model_len == 33792 and model.enforce_eager is True,
         "unchanged model length/eager")
    need(type(scheduler.max_num_batched_tokens) is int and scheduler.max_num_batched_tokens == 32768
         and scheduler.max_num_seqs == 1 and scheduler.enable_chunked_prefill is True
         and scheduler.async_scheduling is False,
         "unchanged batch32768/one sequence/noasync; explicit chunked support")
    need(scheduler.long_prefill_token_threshold == 0
         and scheduler.max_num_partial_prefills == scheduler.max_long_partial_prefills == 1
         and scheduler.max_num_scheduled_tokens in (None, 32768)
         and scheduler.scheduler_reserve_full_isl is True,
         "no configured subchunk or alternate schedule budget; full-input reserve")
    need(type(cache_bytes) is int and 0 < cache_bytes <= 10 * 1024**3,
         "unchanged common cache bound")
    return dict(architecture=model.architecture, model_type=model.hf_config.model_type,
                runner_type=model.runner_type, max_model_len=model.max_model_len,
                enforce_eager=model.enforce_eager,
                max_num_batched_tokens=scheduler.max_num_batched_tokens,
                max_num_seqs=scheduler.max_num_seqs,
                enable_chunked_prefill=scheduler.enable_chunked_prefill,
                async_scheduling=scheduler.async_scheduling,
                long_prefill_token_threshold=scheduler.long_prefill_token_threshold,
                max_num_partial_prefills=scheduler.max_num_partial_prefills,
                max_long_partial_prefills=scheduler.max_long_partial_prefills,
                max_num_scheduled_tokens=scheduler.max_num_scheduled_tokens,
                scheduler_reserve_full_isl=scheduler.scheduler_reserve_full_isl,
                cache_bytes=cache_bytes)


def run(upstream_root, upstream_sha, output, port, cache_bytes):
    need(upstream_sha == UPSTREAM_SHA and str(upstream_root) == UPSTREAM_ROOT,
         "exact failed v007 source; not model permission")
    spec = importlib.util.spec_from_file_location("_kivi_config_cpu_v007_loader", upstream_root / "loader.py")
    need(spec.name not in sys.modules, "fresh source loader namespace")
    loader = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loader
    spec.loader.exec_module(loader)
    manifest, source, mods, adapter, new, own = loader.load(upstream_sha, memory_limit=8 * 1024**3)
    torch = importlib.import_module("torch")
    importlib.import_module("torch_npu")  # Required when backend autoload is explicitly OFF.
    need(torch.npu.is_initialized() is False, "Devices[] before actual config")
    installed = actual_sources()
    api = importlib.import_module("vllm.entrypoints.openai.api_server")
    native = loader.module("_kivi_config_original_server", loader.own(manifest, "server_entry.py"))
    old_argv = native.native_argv(port, cache_bytes)
    new_argv = corrected_argv(old_argv)
    old_args, new_args = parse(api, old_argv), parse(api, new_argv)
    engine_cls = importlib.import_module("vllm.engine.arg_utils").AsyncEngineArgs
    scheduler_cls = importlib.import_module("vllm.config.scheduler").SchedulerConfig
    old_engine = engine_cls.from_cli_args(old_args)
    new_engine = engine_cls.from_cli_args(new_args)
    model = new_engine.create_model_config()  # Actual checkpoint config/class inspection only; no model instance/weights.
    need(old_engine.model == new_engine.model == "/models/Qwen3.6-27B",
         "same actual checkpoint")
    try:
        scheduler_config(old_engine, model, scheduler_cls)
    except ValueError as error:
        old_error = str(error)
        need("max_num_batched_tokens (32768)" in old_error
             and "smaller than max_model_len (33792)" in old_error,
             "actual original invariant, not an unrelated exception")
    else:
        raise ValueError("original illegal scheduler config unexpectedly accepted")
    scheduler = scheduler_config(new_engine, model, scheduler_cls)
    policy = require_firstdecode_policy(model, scheduler, cache_bytes)
    need(new_engine.enable_prefix_caching is False and new_engine.mamba_cache_mode == "none",
         "common original prefix OFF / Mamba none")
    need(torch.npu.is_initialized() is False, "actual config precheck did not initialize NPU")
    memory = own["memory"].memory(expected_limit=8 * 1024**3)
    own["memory"].consume_memory(memory, expected_limit=8 * 1024**3)
    return loader.publish(output, dict(
        schema="kivi.actual-firstdecode-config-precheck/v1", status="ACTUAL_MODEL_SCHEDULER_CONFIG_CHECKED",
        probe_source=loader.ref(__file__), producer_source=source,
        actual_installed_sources=installed, actual_identity=mods["layout"][1].identity(), memory=memory,
        original_argv=old_argv, corrected_argv=new_argv, original_rejected=True,
        original_exception=dict(type="ValueError", message=old_error), actual_policy=policy,
        actual_model_config_constructed=True, actual_scheduler_config_constructed=True,
        full_engine_config_verified=False, full_engine_config_required_at_N1=True,
        actual_scheduler_frame_observed=False, NPU_initialized=False,
        model_ready=False, performance_ready=False, run_authority=False,
        scope="actual installed config validation only; no engine/worker/weights/requests"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--probe-source-sha256")
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--upstream-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--port", type=int, default=8250)
    parser.add_argument("--cache-bytes", type=int, default=10 * 1024**3)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(default_enabled=False, NPU=False, model_ready=False)))
        return 0
    need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == args.probe_source_sha256,
         "exact explicit independent probe source")
    need(args.output is not None and args.upstream_root is not None, "explicit actual inputs/output")
    run(args.upstream_root, args.upstream_sha256, args.output, args.port, args.cache_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
