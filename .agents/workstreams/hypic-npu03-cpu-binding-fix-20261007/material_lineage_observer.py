"""Bounded material-generation sidecar; disabled by default, no device launcher.

Tracks actual committed storage, not ready reports. Samples are not full tensors.
Producer snapshots are store inputs/outputs, not independently recomputed material.
"""
from __future__ import annotations
import functools
import hashlib
import json
import os
import re
from pathlib import Path
import weakref

SWITCH = "HYPIC_MATERIAL_LINEAGE_ENABLE"
SOURCE_SHA = "cd677063af4e296be00d12ae9f148fc384cdf4f29b376170f89cd56eb5cf6f68"


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def sample(kind, tensors):
    """Canonical fixed coordinates shared by producer and consumer."""
    import torch
    result = []
    for tensor in tensors:
        shape = tuple(int(n) for n in tensor.shape)
        if kind == "kv":
            if len(shape) != 3 or min(shape) <= 0:
                raise ValueError("expected KV [rows,heads,width]")
            rows = sorted({0, shape[0]//2, shape[0]-1})
            selected = tensor[rows, 0, :]
            coordinates = dict(rows=rows, head=0, width=shape[2])
        else:
            index = len(result)
            if index in (0, 2):
                if len(shape) != 3 or min(shape) <= 0:
                    raise ValueError("expected GDN [heads,rows,columns]")
                selected = tensor[0]
                coordinates = dict(head=0, rows=shape[1], columns=shape[2])
            else:
                if len(shape) != 2 or min(shape) <= 0:
                    raise ValueError("expected conv [channels,history] or transpose")
                selected = tensor
                coordinates = dict(all_coordinates=True)
        if selected.numel() > 131072:
            raise ValueError("component sample budget exceeded")
        copied = selected.detach().to(device="cpu").clone()
        if not bool(torch.isfinite(copied).all()):
            raise ValueError("nonfinite material snapshot")
        result.append(dict(shape=list(shape), dtype=str(tensor.dtype),
            coordinates=coordinates, sampled_shape=list(copied.shape),
            values=copied.reshape(-1).tolist()))
    return result


def components(obj, kind, layer):
    if obj is None:
        return None
    if kind == "kv":
        return obj.full_kv_by_layer.get(layer)
    mappings = (obj.gdn_state_by_layer, obj.conv_tail_by_layer,
                obj.transition_by_layer)
    if not all(layer in mapping for mapping in mappings):
        return None
    return tuple(mapping[layer] for mapping in mappings)


class Tracker:
    def __init__(self, *, segment_hash, layers, emit, rank, context, request_id,
                 max_generations=4, max_events=24):
        if (not isinstance(segment_hash, bytes) or not segment_hash
                or set(layers) != {"kv", "gdn"}
                or not all(isinstance(x, str) and x for x in layers.values())
                or type(rank) is not int or rank not in range(4)
                or not callable(emit) or not callable(context)
                or not isinstance(request_id, str) or not request_id
                or not 1 <= max_generations <= 4 or not 1 <= max_events <= 24):
            raise ValueError("explicit bounded lineage identity required")
        self.segment_hash, self.layers = segment_hash, dict(layers)
        self.emit, self.context, self.rank = emit, context, rank
        self.request_id, self.bound_request, self.bound_step = request_id, None, None
        self.max_generations, self.max_events = max_generations, max_events
        self.generations, self.records, self.event_count = [], {}, 0
        self.active, self.failed = True, False

    def identity(self):
        identity = self.context()
        if (not isinstance(identity, dict)
                or type(identity.get("step")) is not int or identity["step"] < 0
                or not identity.get("producer_request_ids")
                or not all(isinstance(x, str) and x
                           for x in identity["producer_request_ids"])):
            raise ValueError("producer context missing")
        return json.loads(encode(identity))

    def event(self, data):
        if self.failed:
            raise RuntimeError("lineage tracker failed")
        if self.event_count >= self.max_events:
            self.failed = True
            raise RuntimeError("lineage event budget exceeded")
        event = dict(schema="hypic-material-lineage/v1", rank=self.rank,
                     pid=os.getpid(), segment_hash=self.segment_hash.hex(),
                     request_id=self.request_id,
                     sequence=self.event_count, **data)
        # Emit a detached JSON record, never caller-owned mutable objects.
        try:
            self.emit(json.loads(encode(event)))
        except Exception:
            self.failed = True
            raise
        self.event_count += 1
        return event

    def generation(self, obj, *, new=False):
        for index, reference in enumerate(self.generations, 1):
            if reference() is obj:
                return index
        if not new:
            raise ValueError("unobserved material generation")
        if len(self.generations) >= self.max_generations:
            raise RuntimeError("lineage generation budget exceeded")
        self.generations.append(weakref.ref(obj))
        return len(self.generations)

    def committed(self, before_obj, before_parts, after_obj, kind, layer,
                  input_parts, producer_identity):
        if after_obj is None:
            raise ValueError("successful write has no material")
        stored = components(after_obj, kind, layer)
        if stored is None:
            raise ValueError("successful write has no complete layer")
        retained = (before_obj is after_obj and before_parts is not None
                    and all(a is b for a, b in zip(before_parts, stored)))
        generation = self.generation(after_obj, new=not retained)
        key = (generation, kind, layer)
        if retained:
            if key not in self.records:
                raise ValueError("preexisting layer lacks producer receipt")
            return self.event(dict(event="retained", generation=generation,
                kind=kind, layer=layer, producer=producer_identity))
        if key in self.records:
            raise ValueError("in-place component replacement needs new observation design")
        inputs, saved = sample(kind, input_parts), sample(kind, stored)
        self.records[key] = dict(producer=producer_identity, snapshot=saved)
        return self.event(dict(event="committed", generation=generation,
            kind=kind, layer=layer, producer=producer_identity,
            input_sample=inputs, stored_sample=saved,
            sampled_clone_equal=(inputs == saved),
            independently_regenerated=False))

    def consume(self, obj, *, kind, layer, request_id, step):
        if not self.active:
            return None
        if (kind not in self.layers or self.layers[kind] != layer
                or not isinstance(request_id, str) or not request_id
                or type(step) is not int or step < 0):
            raise ValueError("invalid consumer identity")
        if not (request_id == self.request_id or re.fullmatch(
                re.escape(self.request_id) + r"-[0-9a-f]{8}", request_id)):
            raise ValueError("wrong consumer request")
        if self.bound_request is not None and (
                request_id != self.bound_request or step != self.bound_step):
            raise ValueError("consumer request/step rebound")
        self.bound_request, self.bound_step = request_id, step
        generation = self.generation(obj)
        key = (generation, kind, layer)
        if key not in self.records:
            raise ValueError("consumer lacks producer component")
        parts = components(obj, kind, layer)
        if parts is None:
            raise ValueError("consumer missing component")
        current = sample(kind, parts)
        original = self.records[key]
        return self.event(dict(event="consumed", generation=generation,
            kind=kind, layer=layer, consumer_request_id=request_id, step=step,
            producer=original["producer"], stored_sample=current,
            sampled_storage_equal=(current == original["snapshot"]),
            hot_receipt_join_required=True, physical_device_proven=False))

    def clear(self):
        self.active = False
        self.records.clear()
        self.generations.clear()
        self.context = self.emit = None


class Handle:
    def __init__(self, store=None, tracker=None, changes=()):
        self.store, self.tracker, self.changes = store, tracker, list(changes)

    def uninstall(self):
        if not self.changes:
            return
        if any(getattr(self.store, name) is not replacement
               for name, original, replacement in self.changes):
            raise RuntimeError("lineage wrapper ownership changed")
        # Saved wrappers only call the original once this flag is disabled.
        self.tracker.clear()
        for name, original, replacement in reversed(self.changes):
            delattr(self.store, name)
        self.changes.clear()


def install(store, *, segment_hash, layers, emit, rank, context, request_id):
    if os.environ.get(SWITCH) != "1":
        return Handle()
    cls = type(store)
    source = Path(cls.put_full_kv.__code__.co_filename)
    if (hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA
            or cls.__name__ != "MaterializedSegmentStore"):
        raise ValueError("material store source mismatch")
    names = ("put_full_kv", "put_gdn_state")
    if any(name in vars(store) for name in names):
        raise ValueError("existing instance write patch")
    if store._segments.get(segment_hash) is not None:
        raise ValueError("install before target materialization")
    tracker = Tracker(segment_hash=segment_hash, layers=layers, emit=emit,
                      rank=rank, context=context, request_id=request_id)
    changes = []
    for name, kind in zip(names, ("kv", "gdn")):
        original = getattr(store, name)
        if (original.__func__ is not getattr(cls, name)
                or original.__func__.__code__.co_filename != str(source)):
            raise ValueError("material method identity mismatch")
        def wrap(original, kind):
            @functools.wraps(original)
            def put(seg_hash, layer_name, *args, **kwargs):
                selected = (tracker.active and seg_hash == tracker.segment_hash
                            and layer_name == tracker.layers[kind])
                if not selected:
                    return original(seg_hash, layer_name, *args, **kwargs)
                # Read without get(): instrumentation must not change LRU timestamps.
                before = store._segments.get(seg_hash)
                before_parts = components(before, kind, layer_name)
                identity = tracker.identity()
                result = original(seg_hash, layer_name, *args, **kwargs)
                if result:
                    # Bind keyword or positional arguments using the real signature.
                    import inspect
                    bound = inspect.signature(original).bind(seg_hash, layer_name, *args, **kwargs)
                    bound.apply_defaults()
                    fields = ("key", "value") if kind == "kv" else ("state", "conv_tail", "transition")
                    inputs = tuple(bound.arguments[field] for field in fields)
                    if any(value is None for value in inputs):
                        raise ValueError("lineage requires complete material")
                    tracker.committed(before, before_parts, store._segments.get(seg_hash),
                                      kind, layer_name, inputs, identity)
                return result
            return put
        replacement = wrap(original, kind)
        changes.append((name, original, replacement))
    for name, original, replacement in changes:
        setattr(store, name, replacement)
    return Handle(store, tracker, changes)
