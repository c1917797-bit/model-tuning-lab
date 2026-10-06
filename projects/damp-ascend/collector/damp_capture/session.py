"""Request identity and exclusive state-slot ownership; no runtime dependency."""
from __future__ import annotations
import re
from .contract import LAYERS, require, token_digest
from .timeline import Timeline


class Session:
    def __init__(self, manifest, writer):
        self.manifest, self.writer = manifest, writer
        self.rows = {r["input_ids_sha256"]: r for r in manifest["rows"]}
        self.runtime_rows, self.logical_owners = {}, {}
        self.slots, self.timelines, self.seen, self.turn_ids = {}, {}, set(), ()

    def begin(self, ids, prompt_ids, active_ids, positions):
        require(not self.turn_ids, "nested model-forward capture")
        require(ids and len(ids) == len(set(ids)), "nonunique runtime request IDs")
        active = set(active_ids)
        # Batch omission is NOT completion; only runner.requests owns lifecycle.
        retired = set(self.runtime_rows) - active
        for rid in retired:
            require(all(self.timelines.get((rid, layer)) is not None and
                        self.timelines[(rid, layer)].complete for layer in LAYERS),
                    "request retired before complete all-layer capture")
            for key, owner in tuple(self.slots.items()):
                if owner == rid:
                    del self.slots[key]
        for rid in ids:
            require(rid in active, "scheduled request absent from runner.requests")
            fingerprint = token_digest(prompt_ids[rid])
            require(fingerprint in self.rows, "prompt not in immutable manifest")
            row = self.rows[fingerprint]
            if rid in self.runtime_rows:
                require(self.runtime_rows[rid]["id"] == row["id"], "runtime ID changed prompt")
            else:
                require(row["id"] not in self.logical_owners, "logical prompt replay or duplicate")
                self.runtime_rows[rid] = row
                self.logical_owners[row["id"]] = rid
                self.writer.event("request_bound", runtime_id=rid, logical_id=row["id"],
                                  prompt_token_sha256=fingerprint)
        self.turn_ids, self.positions, self.seen = tuple(ids), tuple(positions), set()

    def plan(self, layer, decode_slots, prefill_slots, prefill_lengths, prefill_initial):
        require(layer in LAYERS and layer not in self.seen, "unknown/repeated GDN layer")
        self.seen.add(layer)
        nd, np = len(decode_slots), len(prefill_slots)
        require(nd + np == len(self.turn_ids), "request/metadata count mismatch")
        require(len(prefill_lengths) == np and len(prefill_initial) == np,
                "prefill metadata cardinality mismatch")
        slots = tuple(decode_slots) + tuple(prefill_slots)
        require(len(set(slots)) == len(slots) and all(type(s) is int and s >= 0 for s in slots),
                "invalid/aliased state slots")
        expected_positions, decode = [], []
        for i, (rid, slot) in enumerate(zip(self.turn_ids, slots)):
            key = (layer, slot)
            require(self.slots.get(key, rid) == rid, "slot still owned by another request")
            old_slots = [k[1] for k, owner in self.slots.items() if k[0] == layer and owner == rid]
            require(not old_slots or old_slots == [slot], "request state slot moved")
            self.slots[key] = rid
            timeline_key = (rid, layer)
            if i < nd:
                require(timeline_key in self.timelines, "decode without fresh prefill")
                t = self.timelines[timeline_key]
                expected_positions.append(len(self.runtime_rows[rid]["input_ids"]) + t.step)
                decode.append((rid, slot, t))
            else:
                j = i - nd
                require(not prefill_initial[j] and timeline_key not in self.timelines,
                        "prefix restore/continuation/repeated prefill unsupported")
                require(prefill_lengths[j] == len(self.runtime_rows[rid]["input_ids"]),
                        "chunked/truncated prefill forbidden")
                expected_positions.extend(range(prefill_lengths[j]))
                self.timelines[timeline_key] = Timeline(
                    self.manifest["anchors"], self.manifest["horizon"], 12)
        require(tuple(expected_positions) == self.positions, "position/request ordering mismatch")
        return tuple(decode)

    def finish(self):
        require(self.seen == set(LAYERS), "not all 48 GDN layers executed exactly once")
        self.writer.event("turn_complete", runtime_ids=list(self.turn_ids), layers=sorted(self.seen))
        self.turn_ids = ()

    def logical_row(self, rid):
        return self.runtime_rows[rid]


def layer_index(prefix):
    match = re.search(r"(?:^|\.)layers\.(\d+)\.", prefix)
    require(match is not None, "unrecognized GDN prefix: " + str(prefix))
    value = int(match.group(1))
    require(value in LAYERS, "non-GDN model layer in capture")
    return value
