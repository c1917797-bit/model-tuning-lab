"""Bounded raw state collector for the opt-in observer; no acceptance decisions."""
from __future__ import annotations
import os


class Collector:
    def __init__(self, emit, *, rank, attention_module=None, max_scalars=1_000_000):
        if rank not in range(4):
            raise ValueError("only TP ranks 0..3 supported")
        self.emit = emit
        self.attention_module = attention_module
        self.rank = rank
        self.max_scalars = max_scalars
        self.scalars = 0

    def tensor(self, value, scope):
        count = int(value.numel())
        if count > self.max_scalars - self.scalars:
            raise RuntimeError("observer scalar budget exceeded")
        # Synchronous detached CPU ownership: never retain mutable device views.
        copied = value.detach().to(device="cpu").clone()
        self.scalars += count
        return dict(shape=list(copied.shape), dtype=str(copied.dtype),
                    source_device=str(value.device), scope=scope,
                    values=copied.reshape(-1).tolist())

    def __call__(self, stage, request_id, frame):
        ctx = frame["ctx"]
        index = ctx.req_ids.index(request_id)
        plan = ctx.plans[request_id]
        event = dict(schema="hypic-state-capture/v1", stage=stage,
                     request_id=request_id, rank=self.rank, pid=os.getpid(),
                     step=int(ctx.batch_plan.step_id),
                     layer=frame.get("layer_name"),
                     hot_receipt_join_required=True,
                     physical_device_proven=False)
        if stage == "positions_committed":
            start = sum(int(ctx.num_scheduled_tokens.get(r, 0))
                        for r in ctx.req_ids[:index])
            count = int(ctx.num_scheduled_tokens[request_id])
            runner = frame["runner"]
            event.update(expected_positions=list(plan.physical_positions),
                         actual_positions=self.tensor(
                             runner.positions[start:start+count], "request rows"))
        elif stage == "kv_committed":
            if frame["cache_layout"] != "normal":
                raise RuntimeError("observer only supports proven normal KV layout")
            key_cache, value_cache = frame["key_cache"], frame["value_cache"]
            block_size = int(frame["block_size"])
            table = frame["attn_metadata"].block_tables[index].detach().cpu().tolist()
            segments = []
            for segment, entry in zip(plan.segments, plan.entries):
                if entry is None:
                    continue
                seg_hash = bytes(entry.seg_hash)
                key, value = frame["materials"][seg_hash].full_kv_by_layer[frame["layer_name"]]
                seam = len(plan.hit_seam[(segment.start, segment.end)])
                count = int(key.shape[0])
                rows = sorted({0, count//2, count-1})
                if count <= 0:
                    raise RuntimeError("empty material")
                material = dict(segment_hash=seg_hash.hex(), anchor=int(segment.start),
                                seam=seam, full_material_shape=list(key.shape), samples=[])
                for row in rows:
                    position = int(segment.start) + seam + row
                    block = int(table[position//block_size])
                    offset = position % block_size
                    material["samples"].append(dict(
                        material_row=row, logical_position=position,
                        destination_slot=block*block_size+offset,
                        canonical_key=self.tensor(key[row, 0], "head0 full width"),
                        canonical_value=self.tensor(value[row, 0], "head0 full width"),
                        actual_key=self.tensor(key_cache[block, offset, 0], "head0 full width"),
                        actual_value=self.tensor(value_cache[block, offset, 0], "head0 full width")))
                segments.append(material)
            event["segments"] = segments
            geometry = getattr(self.attention_module, "_ROPE_GEOMETRY", None)
            if geometry is None or not geometry.is_neox_style:
                raise RuntimeError("observer requires registered NeoX RoPE geometry")
            event["rope"] = dict(rotary_dim=int(geometry.rotary_dim), neox=True,
                rows={str(item["anchor"]): self.tensor(
                    geometry.cache[item["anchor"]], "anchor cos/sin table row")
                    for item in segments})
        elif stage == "gdn_initial":
            structure = frame["structure"]
            stages = structure.stages_by_req[index]
            if len(stages) > 16:
                raise RuntimeError("observer GDN stage budget exceeded")
            event["incoming_state"] = self.tensor(frame["h_batch"][index, 0],
                                                  "GDN head0 complete matrix")
            event["conv_initial"] = self.tensor(
                frame["conv_request_states"][index], "request full initial conv state")
            event["conv_dim_first"] = bool(frame["dim_first"])
            event["state_len"] = int(frame["state_len"])
            event["conv_actions"] = []
            for kind, payload in structure.conv_actions_by_req[index]:
                if kind == "row":
                    value = frame["mixed_qkv"][payload.start:payload.end][-event["state_len"]:]
                    item = dict(kind="row", original_tokens=payload.end-payload.start)
                else:
                    value = frame["conv_material_by_hash"][bytes(payload)]
                    item = dict(kind="cache", segment_hash=bytes(payload).hex())
                item["value"] = self.tensor(value, "conv-tail reconstruction input")
                event["conv_actions"].append(item)
            event["stages"] = []
            for kind, payload in stages:
                if kind == "row":
                    transition = frame["transitions"][int(payload), 0]
                    state = frame["zero_finals"][int(payload), 0]
                    identity = dict(kind=kind, row=int(payload))
                else:
                    seg_hash = bytes(payload)
                    transition = frame["transition_material_by_hash"][seg_hash][0]
                    state = frame["state_material_by_hash"][seg_hash][0]
                    identity = dict(kind=kind, segment_hash=seg_hash.hex())
                identity.update(
                    transition=self.tensor(transition, "GDN head0 complete matrix"),
                    zero_state=self.tensor(state, "GDN head0 complete matrix"))
                event["stages"].append(identity)
        elif stage == "gdn_committed":
            slot = int(frame["ssm_state_indices"][index].item())
            conv_slot = int(frame["conv_state_indices"][index].item())
            event.update(
                state_slot=slot, conv_slot=conv_slot,
                actual_state=self.tensor(frame["ssm_cache"][slot, 0],
                                         "cache-layout GDN head0 complete matrix"),
                actual_conv=self.tensor(frame["conv_cache"][conv_slot],
                                        "request full convolution state"))
        else:
            raise ValueError("unknown capture stage")
        self.emit(event)
