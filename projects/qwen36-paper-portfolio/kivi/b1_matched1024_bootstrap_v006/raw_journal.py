"""Actual first-decode Ref index around the unchanged scalar journal.
No controller, tensor copy, native call, numeric oracle, or admission authority.
"""
import hashlib
import json
from pathlib import Path

JOURNAL_SHA = "cd5b012684607465b2a5c489303a30bb55970c93786c455d675037d6723bb851"

def need(value, message):
    if not value:
        raise ValueError(message)

def raw(ref, cap=8*1024**2):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"},
         "original exact3 Ref")
    path = Path(ref["path"])
    need(type(ref["bytes"]) is int and 0 < ref["bytes"] <= cap
         and path.is_absolute() and path.resolve() == path and path.is_file()
         and not path.is_symlink(), "bounded original regular Ref")
    before = path.stat()
    blob = path.read_bytes()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
         and len(blob) == ref["bytes"]
         and hashlib.sha256(blob).hexdigest() == ref["sha256"],
         "whole unchanged original bytes/SHA")
    return json.loads(blob)

class FirstDecodeJournal:
    def __init__(self, original, publish, identity, rank, owner_ref, event_ref):
        import inspect
        source = Path(inspect.getfile(original.JournalPublisher)).resolve()
        need(source.is_file() and not source.is_symlink()
             and hashlib.sha256(source.read_bytes()).hexdigest() == JOURNAL_SHA,
             "exact unchanged original scalar journal")
        self.original = original.JournalPublisher(publish, identity, rank, owner_ref, event_ref)
        self.publish = publish
        self.identity = identity
        self.ident = dict(identity())
        self.rank = rank
        self.owner_ref = owner_ref
        self.event_ref = event_ref
        self.frames = {}
        self.closed = False

    def bind_packed(self, batches, actual_type, original_publish):
        """Bind the fresh real producers before installer/model invocation."""
        event = raw(self.event_ref)
        fa = {name for name, row in event["layers"].items() if row["kind"] == "FA"}
        need(not self.closed and self.identity() == self.ident and not self.frames
             and type(batches) is dict and set(batches) == fa and len(fa) == 16
             and len(event["layers"]) == 64 and original_publish is self.publish
             and len({id(batch) for batch in batches.values()}) == 16,
             "one whole16 fresh same-collector producer binding")
        for batch in batches.values():
            need(type(batch) is actual_type and batch.publish is original_publish
                 and batch.model is batch.metadata is batch.arena is None,
                 "actual fresh producer before first tensor/kernel publication")
        replacement = self.publish_packed
        for batch in batches.values():
            batch.publish = replacement

    def __call__(self, label, value):
        need(not self.closed and self.identity() == self.ident,
             "same live owner before original scalar publication")
        need(value.get("schema") != "kivi.actual-packed-qkav-frame/v1",
             "packed frames require actual dedicated publication, not scalar re-publication")
        return self.original(label, value)

    def publish_packed(self, label, value):
        """Publish original producer value once, then index that exact wire Ref.

        Original tensor math/writer and scalar journal are unchanged. JSON array
        semantics are compared after canonical serialization of the original
        value, so producer tuples are neither rejected nor rewritten in place.
        """
        need(not self.closed and self.identity() == self.ident,
             "same live owner before actual packed publication")
        ref = self.publish(label, value)
        if value.get("schema") != "kivi.actual-packed-qkav-frame/v1":
            return ref
        wire = raw(ref)
        expected = json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                        allow_nan=False))
        need(wire == expected and wire["snapshot_is_live_alias"] is False,
             "actual complete published JSON frame, no reconstructed or changed raw")
        rows = wire["rows"]
        need(type(rows) is list and len(rows) == 1,
             "this first-token smoke covers one real32768 request")
        row = rows[0]
        owner = raw(row["identity_refs"]["slot_owner"])
        need(owner["schema"] == "kivi.actual-qwen-slot-owner/v1"
             and owner["rank"] == self.rank and owner["identity"] == self.ident
             and owner["request_id"] == row["request_id"]
             and owner["slot"] == row["slot"] and owner["epoch"] == row["epoch"]
             and owner["computed"] == row["computed"] == 32768
             and row["controls"][0] == 32769
             and "original_prefill_ref" in owner,
             "actual same owner and true first decode after whole32768 prefill")
        event = raw(self.event_ref)
        layer = owner["layer"]
        need(layer in event["layers"] and event["layers"][layer]["kind"] == "FA"
             and layer not in self.frames, "one original first-decode frame per actual FA")
        self.frames[layer] = ref
        return ref

    def finish(self, final_ref):
        need(not self.closed and self.identity() == self.ident,
             "one actual source-qualified final")
        event = raw(self.event_ref)
        fa = {name for name, row in event["layers"].items() if row["kind"] == "FA"}
        need(len(event["layers"]) == 64 and len(fa) == 16
             and set(self.frames) == fa, "all16 actual first-decode frames; no sampling")
        journal_ref = self.original.finish(final_ref)
        value = dict(schema="kivi.actual-firstdecode-rank-bundle/v1",
                     rank=self.rank, identity=self.ident, journal_ref=journal_ref,
                     owner_ref=self.owner_ref, event_ref=self.event_ref,
                     frame_refs={name: self.frames[name] for name in sorted(fa)},
                     prompt_tokens=32768, first_decode_length=32769,
                     request_batch=1, graph_checked=False, model_ready=False,
                     performance_ready=False, run_authority=False)
        ref = self.publish("PACKED-QWEN-r%d-FIRSTDECODE-FINAL" % self.rank, value)
        need(raw(ref) == value, "original complete immutable first-decode bundle")
        self.closed = True
        return ref

