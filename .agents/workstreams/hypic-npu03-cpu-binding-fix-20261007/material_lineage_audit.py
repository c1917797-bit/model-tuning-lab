"""Independent replay of material-lineage records; no runtime hook imports."""
from __future__ import annotations
import math
import re


def require(value, message):
    if not value:
        raise ValueError(message)


def check_samples(samples, kind):
    require(isinstance(samples, list) and len(samples) == (2 if kind == "kv" else 3),
            "wrong component inventory")
    for index, item in enumerate(samples):
        shape = item.get("shape")
        require(isinstance(shape, list) and shape
                and all(type(x) is int and x > 0 for x in shape), "invalid shape")
        if kind == "kv":
            require(len(shape) == 3, "KV dimensions")
            rows = sorted({0, shape[0]//2, shape[0]-1})
            coordinates = dict(rows=rows, head=0, width=shape[2])
            selected = [len(rows), shape[2]]
        elif index in (0, 2):
            require(len(shape) == 3, "GDN state dimensions")
            coordinates = dict(head=0, rows=shape[1], columns=shape[2])
            selected = shape[1:]
        else:
            require(len(shape) == 2, "conv dimensions")
            coordinates = dict(all_coordinates=True)
            selected = shape
        require(item.get("coordinates") == coordinates
                and item.get("sampled_shape") == selected, "sampling coordinate drift")
        values = item.get("values")
        require(isinstance(item.get("dtype"), str)
                and item["dtype"].startswith("torch.")
                and isinstance(values, list)
                and len(values) == math.prod(selected) <= 131072
                and all(type(x) in (int, float) and math.isfinite(x) for x in values),
                "invalid sample values")


def audit(events, *, request_id, rank, pid, segment_hash, layers):
    require(0 < len(events) <= 24, "event bounds")
    require(type(rank) is int and rank in range(4)
            and type(pid) is int and pid > 0
            and set(layers) == {"kv", "gdn"}, "audit identity")
    records, results = {}, []
    latest = 0
    consumer_identity = None
    for seq, event in enumerate(events):
        require(event.get("schema") == "hypic-material-lineage/v1"
                and event.get("sequence") == seq
                and event.get("request_id") == request_id
                and event.get("rank") == rank and event.get("pid") == pid
                and event.get("segment_hash") == segment_hash,
                "event identity/sequence mismatch")
        kind, layer = event.get("kind"), event.get("layer")
        require(kind in layers and layer == layers[kind], "layer identity mismatch")
        generation = event.get("generation")
        require(type(generation) is int and 1 <= generation <= 4, "generation invalid")
        key = (generation, kind, layer)
        producer = event.get("producer", {})
        require(type(producer.get("step")) is int and producer["step"] >= 0
                and isinstance(producer.get("producer_request_ids"), list)
                and producer["producer_request_ids"]
                and all(isinstance(x, str) and x for x in producer["producer_request_ids"]),
                "producer identity missing")
        action = event.get("event")
        if action == "committed":
            require(key not in records and generation in (latest, latest+1),
                    "producer generation/component sequence invalid")
            latest = max(latest, generation)
            check_samples(event["input_sample"], kind)
            check_samples(event["stored_sample"], kind)
            records[key] = event
        elif action == "retained":
            require(key in records, "retained material lacks producer")
            require(producer["step"] >= records[key]["producer"]["step"],
                    "retained step precedes producer")
        elif action == "consumed":
            require(key in records, "consumer lacks producer")
            origin = records[key]
            actual = event.get("consumer_request_id")
            step = event.get("step")
            require(isinstance(actual, str) and (
                actual == request_id or re.fullmatch(
                    re.escape(request_id)+r"-[0-9a-f]{8}", actual)), "wrong consumer")
            require(type(step) is int and step >= producer["step"]
                    and producer == origin["producer"], "consumer producer/step mismatch")
            if consumer_identity is None:
                consumer_identity = (actual, step)
            require(consumer_identity == (actual, step), "consumer step/request changed")
            check_samples(event["stored_sample"], kind)
            # Recompute from raw samples; never trust producer-supplied pass flags.
            results.append(dict(generation=generation, kind=kind, layer=layer,
                request_id=actual, step=step,
                sampled_clone_equal=origin["input_sample"] == origin["stored_sample"],
                sampled_storage_equal=origin["stored_sample"] == event["stored_sample"],
                latest_observed_generation=latest,
                consumes_latest_observed_generation=(generation == latest)))
        else:
            raise ValueError("unknown lineage event")
    require({x["kind"] for x in results} == {"kv", "gdn"},
            "both selected KV and GDN consumption required")
    return dict(schema="hypic-material-lineage-audit/v1", rank=rank, pid=pid,
                request_id=consumer_identity[0], step=consumer_identity[1],
                observations=results, independent_material_regeneration=False,
                physical_device_proven=False, hot_receipts_join_required=True,
                quality_cause_proven=False)
