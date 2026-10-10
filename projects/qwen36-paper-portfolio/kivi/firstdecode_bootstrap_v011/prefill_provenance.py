"""Diagnostic-only original dense-prefill tile provenance. No math or controller."""
import hashlib
from pathlib import Path

FORMAL_SHA = "d9e8dd2fa2656c79616e3576a2e58b3ce82a113f6c5fd55e4b41e504ae246841"
PRODUCER_SHA = "f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5"
CALLBACK_SHA = "291eb417eaecf97b4199072ae62012180c18af44b5a5d2c5c92c1060e3d38f5e"
LIFECYCLE_SHA = "20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533"
WRITER_SHA = "051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b"


def need(value, message):
    if not value:
        raise ValueError(message)


def capture_tiles(iterator, *, torch, producer, callback, root, sequence,
                  context, publish, completed):
    """Yield each original tuple unchanged; publish complete provenance on exhaustion.

    The caller already source-pins formal, producer and callback. RawSink streams
    the existing gathered tensors to host files. This function retains references
    and metadata only, never a dense tensor copy. Failure retains partial files
    and cannot publish a completed provenance receipt.
    """
    need(type(completed) is dict and not completed, "fresh completion destination")
    need(context["prompt_length"] == 32768 and context["original_attention_calls"] == 1,
         "real full completed native prefill only")
    need(context["allocation_replaced"] is False and context["graph_checked"] is False,
         "unchanged eager allocation scope")
    need(callable(publish) and torch.npu.is_current_stream_capturing() is False,
         "diagnostic publication on actual eager stream")
    sink = producer.RawSink(root, torch, callback, sequence)
    tiles = []
    cursor = 0
    dtype = None
    for item in iterator:
        need(type(item) is tuple and len(item) == 4, "original gather tuple")
        start, stop, key, value = item
        need(type(start) is int and type(stop) is int and start == cursor
             and stop == start + 128 and stop <= 32768, "complete ordered128 tiles")
        need(tuple(key.shape) == tuple(value.shape) == (128, 256)
             and key.dtype == value.dtype and key.device == value.device
             and key.dtype in (torch.float16, torch.bfloat16), "original A16 KV1/D256")
        actual_dtype = str(key.dtype).split(".")[-1]
        need(dtype is None or actual_dtype == dtype, "stable original prefill dtype")
        dtype = actual_dtype
        # RawSink checks contiguous extent and transfers at most64KiB per tensor.
        key_ref = sink.tensor("ORIGINAL-K-%05d" % start, key)
        value_ref = sink.tensor("ORIGINAL-V-%05d" % start, value)
        need(key_ref["bytes"] == value_ref["bytes"] == 65536, "whole original tile extent")
        tiles.append(dict(start=start, stop=stop, key_ref=key_ref, value_ref=value_ref))
        cursor = stop
        yield item
    need(cursor == 32768 and len(tiles) == 256, "no partial prefill promotion")
    body = dict(context)
    body.update(schema="kivi.actual-original-prefill/v1", status="ORIGINAL_PREFILL_CAPTURED",
                dtype=dtype, tiles=tiles, original_bytes=32768 * 256 * 2 * 2,
                capture_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                formal_source_sha256=FORMAL_SHA, packed_producer_source_sha256=PRODUCER_SHA,
                callback_source_sha256=CALLBACK_SHA, lifecycle_source_sha256=LIFECYCLE_SHA,
                writer_source_sha256=WRITER_SHA, model_ready=False, performance_ready=False,
                run_authority=False, writer_arithmetic_checked=False)
    completed["ref"] = publish("ORIGINAL-PREFILL", body)
