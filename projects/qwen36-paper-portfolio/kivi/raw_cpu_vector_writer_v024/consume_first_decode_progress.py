"""All4/FA64 first-decode raw consumer; calls original independent oracles.
This is an eager32768->32769 smoke, not model performance/FULL/COW/task authority.
"""
import hashlib
import inspect
import json
import time
from pathlib import Path

JOURNAL_SHA = "cd5b012684607465b2a5c489303a30bb55970c93786c455d675037d6723bb851"
BOOK_SHA = "6488a5ca3fb6f606bbb82bf86e226fc30741e8dc7288ff03e3e5e8b71cec07c7"
BINDINGS_SHA = "71b5c3650eab308b86a26da62abcd249c77fc7528c4c8022bf779af56ef38f99"
ASSIGNMENT_ORACLE_SHA = "f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333"
RAW_OUTPUT_SHA = "4dda2abbabc3a474d4ee09f462bb1ea9acbd4847cd3c49fe4f360efe4eef3bfa"
OUTPUT_ORACLE_SHA = "f57c2703e19b59c3cd6c6b0df52a21fdfc1c0a43ab6fe86d236b6e750e24d39c"
FIELDS_SHA = "77b678af5eea524c59405d98a3681415810e2e77b7f8cf9cde9fd241b28d4157"
SPANS_SHA = "2eb0a604dead0181c51e4314a15efb6aca48d51436f7eeb254ef3f5ce4518831"

def need(value, message):
    if not value:
        raise ValueError(message)

def raw(ref, maximum=8*1024**2):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"},
         "whole exact3 original evidence")
    path = Path(ref["path"])
    need(path.is_absolute() and path.resolve() == path and path.is_file()
         and not path.is_symlink() and type(ref["bytes"]) is int
         and 0 < ref["bytes"] <= maximum, "bounded ordinary original")
    before = path.stat()
    wire = path.read_bytes()
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
         and len(wire) == ref["bytes"]
         and hashlib.sha256(wire).hexdigest() == ref["sha256"],
         "complete stable original bytes/SHA")
    return json.loads(wire)

def pin(value, expected):
    path = Path(inspect.getfile(inspect.unwrap(getattr(value, "__func__", value)))).resolve()
    need(path.is_file() and not path.is_symlink()
         and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
         "actual independent source callable")

def progress(phase, rank, layer, frame_ref, completed, started):
    """Diagnostic stdout only; no progress line is a numerical acceptance."""
    print(json.dumps(dict(schema="kivi.raw64-reference-progress/v1", phase=phase,
          rank=rank, layer=layer, frame_ref=frame_ref, completed_FA=completed,
          total_FA=64, wall_utc_ns=time.time_ns(),
          elapsed_seconds=time.monotonic()-started,
          numeric_acceptance=False), sort_keys=True, allow_nan=False), flush=True)


def require_one_prefill(frame,rank,identity,request_id,book):
    need(frame["schema"]=="kivi.actual-packed-qwen-frame/v1" and frame["kind"]=="prefill"
         and frame["rank"]==rank and frame["identity"]==identity
         and frame["req_ids"]==[request_id] and frame["req_id_to_index"]=={request_id:0}
         and frame["computed_tokens"]==[0] and frame["scheduled_counts"]==[32768]
         and frame["query_start_loc"]==[0,32768] and frame["total_tokens"]==32768,
         "actual one complete32768 native prefill, not a chunk ending at32768")
    book.frame_valid(frame)
    return True

def consume(rank_refs, *, journal, book, bindings, assignment_oracle,
            output_reader, writer_reader, codec_ref, fields, spans,
            installer_sha256, capture_sha256, kernel_sha256, writer_reader_ref):
    """The existing source-bound caller supplies exact loaded original modules.
    No imported candidate algorithm and no candidate score/feedback is reused.
    Each FA whole-pool oracle is consumed and released sequentially.
    """
    pin(journal.consume_four, JOURNAL_SHA)
    pin(book.Book, BOOK_SHA)
    pin(bindings.Verifier, BINDINGS_SHA)
    pin(assignment_oracle.validate_assignment, ASSIGNMENT_ORACLE_SHA)
    pin(output_reader.consume, RAW_OUTPUT_SHA)
    pin(output_reader.oracle.attention, OUTPUT_ORACLE_SHA)
    pin(fields.consume_geometry, FIELDS_SHA)
    pin(spans.consume_spans, SPANS_SHA)
    pin(writer_reader.consume, writer_reader_ref["sha256"])
    need(writer_reader.KERNEL_SHA == kernel_sha256,
         "writer source must be explicitly rebound; never change old module globals")
    need(type(rank_refs) is list and len(rank_refs) == 4,
         "four actual distinct rank bundles")
    bundles = [raw(ref) for ref in rank_refs]
    need([value["rank"] for value in bundles] == [0, 1, 2, 3]
         and all(value["schema"] == "kivi.actual-firstdecode-rank-bundle/v1"
                 and value["prompt_tokens"] == 32768
                 and value["first_decode_length"] == 32769
                 and value["request_batch"] == 1
                 and value["graph_checked"] is value["model_ready"]
                     is value["performance_ready"] is value["run_authority"] is False
                 for value in bundles), "ordered exact first-token scope, not original whole176")
    scalar_bundles = [raw(value["journal_ref"]) for value in bundles]
    scalar = journal.consume_four(scalar_bundles, book, installer_sha256,
                                 bindings.Verifier(assignment_oracle))
    all_results = []
    started = time.monotonic()
    ids = set()
    identities = set()
    cid = None
    for bundle, scalar_bundle in zip(bundles, scalar_bundles):
        rank = bundle["rank"]
        ident = bundle["identity"]
        identities.add((ident["pid"], ident["start_ticks"]))
        need(scalar_bundle["rank"] == rank and scalar_bundle["identity"] == ident
             and scalar_bundle["owner_ref"] == bundle["owner_ref"]
             and scalar_bundle["event_ref"] == bundle["event_ref"],
             "same actual independent scalar and raw origins")
        event = raw(bundle["event_ref"])
        owner = raw(bundle["owner_ref"])
        fa = {name for name, value in event["layers"].items() if value["kind"] == "FA"}
        need(len(event["layers"]) == 64 and len(fa) == 16
             and set(bundle["frame_refs"]) == fa
             and event["rank"] == rank and event["identity"] == ident
             and owner["rank_bindings"][str(rank)] == ident,
             "actual whole64 layout and complete16FA per rank")
        if cid is None:
            cid = owner["container_id"]
        need(owner["container_id"] == cid and cid in ident["cgroup"],
             "same actual owning container, not four arbitrary rank copies")
        # Reconsume exact initialized descriptors, including all native GDN,
        # complete full-stride FA and initialized/absent guarded zeroer footprints.
        geometry_refs = owner.get("field_geometry_refs")
        need(type(geometry_refs) is dict and set(geometry_refs) == fa,
             "all16 actual field geometry Refs in the model owner")
        geometries = {name: raw(ref) for name, ref in geometry_refs.items()}
        compact = {}
        for name, geometry in geometries.items():
            fields.consume_geometry(geometry, event)
            compact[name] = {field["name"]: field["descriptor"]
                             for field in geometry["fields"]}
        disjoint = fields.consume_rank(owner,event, compact, raw(owner["zeroer_writer_receipt_ref"]))
        need(raw(owner["layout_consumer_ref"]) == disjoint,
             "fresh independent exact full native/compact exclusions")
        for name in sorted(fa):
            frame_ref = bundle["frame_refs"][name]
            frame = raw(frame_ref)
            need(frame["schema"] == "kivi.actual-packed-qkav-frame/v1"
                 and frame["kernel_source_sha256"] == kernel_sha256
                 and frame["snapshot_is_live_alias"] is False
                 and len(frame["rows"]) == 1, "one original physical snapshot per FA")
            row = frame["rows"][0]
            actual_owner = raw(row["identity_refs"]["slot_owner"])
            need(actual_owner["rank"] == rank and actual_owner["identity"] == ident
                 and actual_owner["layer"] == name
                 and actual_owner["request_id"] == row["request_id"]
                 and actual_owner["computed"] == row["computed"] == 32768
                 and row["controls"][0] == 32769,
                 "same actual whole-prefix first decode, no reconstructed query")
            prefill=raw(actual_owner["original_prefill_ref"])
            need(prefill["rank"]==rank and prefill["identity"]==ident
                 and prefill["layer"]==name and prefill["request_id"]==row["request_id"],
                 "same actual original prefill owner")
            require_one_prefill(raw(prefill["frame_ref"]),rank,ident,row["request_id"],book)
            ids.add(row["request_id"])
            geometry = geometries[name]
            # Initialized native/kernel geometry, not scheduler1536 guessed as128.
            expected_pages = (event["num_blocks"] * event["layers"][name]["block_size"] + 127) // 128
            need(geometry["pages"] == expected_pages and frame["pool_geometry"]
                 == [expected_pages, expected_pages*128, 16],
                 "full actual physical capacity, never replace raw frame by fixed4224")
            progress("writer-start", rank, name, frame_ref, len(all_results), started)
            writer_started = time.monotonic()
            writer = writer_reader.consume(frame_ref, codec_ref,
                installer_sha256=installer_sha256, capture_sha256=capture_sha256)
            writer_seconds = time.monotonic() - writer_started
            progress("writer-complete-output-start", rank, name, frame_ref, len(all_results), started)
            output_started = time.monotonic()
            output = output_reader.consume(frame_ref, kernel_sha=kernel_sha256)
            output_seconds = time.monotonic() - output_started
            need(len(writer["rows"]) == len(output["rows"]) == 1,
                 "full writer and1536-value attention output for the same actual request")
            all_results.append(dict(rank=rank, layer=name, frame_ref=frame_ref,
                                    writer=writer, numerical=output,
                                    reference_seconds=dict(writer=writer_seconds, output=output_seconds)))
            progress("FA-complete", rank, name, frame_ref, len(all_results), started)
    need(len(identities) == 4 and len(ids) == 1 and len(all_results) == 64,
         "whole all4/FA64 same actual request, not64 repeated observations")
    return dict(schema="kivi.actual-firstdecode-independent/v1",
                status="FIRSTDECODE_RAW_COMPONENTS_CONSUMED",
                rank_bundle_refs=rank_refs, scalar=scalar, frames=all_results,
                actual_ranks=4, actual_FA_layers_per_rank=16,
                original_prefill_tokens=32768, actual_first_decode_length=32769,
                full1536_attention_outputs_per_FA_checked=True,
                source_bound_original_writer_checked=True,
                native_and_compact_disjoint_spans_checked=True,
                untouched_GDN_content_checked=False,
                model_ready=False, performance_ready=False, run_authority=False,
                graph_checked=False, allocation_replaced=False, whole_176=False,
                scope="single-request eager first-decode integration only; model whole-terminal/resource/owner consumption remains external")


