"""Independent sequential original-input writer check; stdlib, no candidate import.

Only the first real decode frame after full32768 prefill is consumed here.
This closes original writer provenance, not output/lifecycle/whole-model gates.
"""
import argparse
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

KERNEL_SHA = "ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a"
CODEC_SHA = "45ccb0c2fff417e518cb591aaf5ba201645551a1aeafc9d8bdc3c97ce6a8fd49"
PINS = dict(formal_source_sha256="d9e8dd2fa2656c79616e3576a2e58b3ce82a113f6c5fd55e4b41e504ae246841",
            packed_producer_source_sha256="f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5",
            callback_source_sha256="291eb417eaecf97b4199072ae62012180c18af44b5a5d2c5c92c1060e3d38f5e",
            lifecycle_source_sha256="20e49b37b1fc62201dd749813e5aba56dd9211bbaf140c672dca5162e190a533",
            writer_source_sha256="051afead07ff88b65b494bacda0b50ed575fc9669509ed0dcefc53e74407e17b")
FIELDS = ("key_codes", "key_scales", "key_minima", "value_codes", "value_scales",
          "value_minima", "key_residual", "value_residual")


def need(value, message):
    if not value:
        raise ValueError(message)


class VerifiedFile:
    """One whole immutable Ref verification, bounded reads through the same FD."""
    def __init__(self, ref, maximum):
        need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"}
             and type(ref["bytes"]) is int and 0 < ref["bytes"] <= maximum
             and type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]),
             "exact bounded3Ref")
        self.path = Path(ref["path"])
        need(self.path.is_absolute() and self.path.resolve() == self.path
             and not self.path.is_symlink() and self.path.is_file(), "ordinary absolute Ref")
        self.handle = self.path.open("rb")
        self.size = ref["bytes"]
        self.before = self.path.stat()
        try:
            need(self.before.st_size == self.size, "whole Ref size")
            digest = hashlib.sha256()
            while True:
                blob = self.handle.read(65536)
                if not blob:
                    break
                digest.update(blob)
            need(digest.hexdigest() == ref["sha256"], "whole Ref SHA")
        except BaseException:
            self.handle.close()
            raise

    def read(self, offset, size):
        need(type(offset) is int and type(size) is int and 0 <= offset
             and 0 < size <= 8 * 1024**2 and offset + size <= self.size, "bounded file range")
        self.handle.seek(offset)
        blob = self.handle.read(size)
        need(len(blob) == size, "complete bounded file range")
        return blob

    def __enter__(self):
        return self

    def __exit__(self, kind, value, trace):
        try:
            after = self.path.stat()
            need((self.before.st_dev, self.before.st_ino, self.before.st_size, self.before.st_mtime_ns)
                 == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "Ref unchanged during consumption")
        finally:
            self.handle.close()


def raw(ref, maximum=8 * 1024**2):
    with VerifiedFile(ref, maximum) as source:
        return source.read(0, source.size)


def document(ref):
    return json.loads(raw(ref))


def codec_module(ref):
    need(ref["sha256"] == CODEC_SHA, "frozen independent codec source")
    code = raw(ref)
    name = "_kivi_original_prefill_independent_codec"
    spec = importlib.util.spec_from_file_location(name, ref["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(code, ref["path"], "exec"), module.__dict__)
    return module



def tensor_extent(descriptor, shape, dtype, *, nd=False, strided=False):
    """Independent scalar layout proof; never imports fields/allocator/arena."""
    widths = {"torch.int32": 4, "torch.float16": 2, "torch.bfloat16": 2,
              "torch.int8": 1, "torch.uint8": 1}
    need(type(descriptor) is dict and dtype in widths
         and type(shape) is list and all(type(x) is int and x > 0 for x in shape),
         "typed expected tensor geometry")
    stride, count = [], 1
    for dimension in reversed(shape):
        stride.insert(0, count)
        count *= dimension
    width = widths[dtype]
    need(descriptor["shape"] == shape
         and all(type(x) is int for x in descriptor["shape"])
         and type(descriptor["stride"]) is list and len(descriptor["stride"]) == len(shape)
         and all(type(x) is int for x in descriptor["stride"])
         and all(x >= 0 for x in descriptor["stride"])
         and (strided or descriptor["stride"] == stride)
         and descriptor["dtype"] == dtype and type(descriptor["contiguous"]) is bool
         and (strided or descriptor["contiguous"] is True)
         and type(descriptor["element_size"]) is int and descriptor["element_size"] == width,
         "exact full shape stride dtype width")
    for key in ("logical_bytes", "storage_base", "storage_bytes", "storage_offset_elements", "data_ptr"):
        need(type(descriptor[key]) is int, "exact integer physical descriptor " + key)
    base, total = descriptor["storage_base"], descriptor["storage_bytes"]
    start = descriptor["storage_offset_elements"] * width
    stop = start + (sum((n - 1) * step for n, step in zip(shape, descriptor["stride"])) + 1) * width
    need(base > 0 and total > 0 and 0 <= start < stop <= total
         and descriptor["data_ptr"] == base + start and descriptor["logical_bytes"] == count * width
         and type(descriptor["device"]) is str and re.fullmatch(r"npu:\d+", descriptor["device"]),
         "whole bounded physical tensor bytes")
    if nd:
        need(descriptor["layout"] == "ND_CONTIGUOUS"
             and type(descriptor["observed_format_code"]) is int
             and descriptor["observed_format_code"] == 2, "original observed ND2 field")
    return base, start, stop, total


def source_geometry(frame, provenance, owner):
    """Derive full physical capacity from immutable native event, not frame claims.

    The producer only transports actual descriptors. Shapes/strides/byte counts
    below use scalar integer arithmetic independently of candidate field_oracle,
    allocator.layout, CompactArena and writer functions. Quantization is still
    the separate pinned stdlib codec, with no candidate runtime imports.
    """
    need(type(frame["bits"]) is int and frame["bits"] in (2, 4)
         and frame["dtype"] in ("float16", "bfloat16"), "exact packed geometry precision")
    event = document(provenance["event_ref"])
    geometry_ref = provenance["geometry_ref"]
    geometry = document(geometry_ref)
    layer = owner["layer"]
    need(event["rank"] == owner["rank"] == provenance["rank"]
         and event["identity"] == owner["identity"] == provenance["identity"]
         and provenance["layer"] == layer and len(event["layers"]) == 64
         and event["layers"][layer]["kind"] == "FA", "same native geometry owner rank layer")
    native = event["layers"][layer]
    blocks, block_size = event["num_blocks"], native["block_size"]
    need(type(blocks) is int and blocks > 0 and type(block_size) is int and block_size > 0,
         "actual native blocks and block size")
    capacity = blocks * block_size
    pages = (capacity + 127) // 128
    records = pages * 128
    need(capacity >= 33792, "native capacity retains logical33792 owner horizon")
    shape = provenance["native_shape"]
    need(type(shape) is list and len(shape) == 4 and shape[2:] == [1, 256]
         and all(type(x) is int and x > 0 for x in shape)
         and shape[0] * shape[1] == capacity and block_size % shape[1] == 0
         and shape[0] == blocks * (block_size // shape[1]),
         "actual kernel split preserves whole native capacity")
    dtype, bits = "torch." + frame["dtype"], frame["bits"]
    need(provenance["native_shape"] == shape
         and provenance["native_views"] == native["views"]
         and type(native["views"]) is list and len(native["views"]) == 2,
         "exact original D256 KV1 native shape and views")
    native_spans = [tensor_extent(view, shape, dtype, strided=True) for view in native["views"]]
    need(all(type(view["observed_format_code"]) is int and view["observed_format_code"] == 2
             for view in native["views"]), "actual native ND2 format")
    need(type(frame["pool_geometry"]) is list and frame["pool_geometry"] == [pages, records, 16]
         and all(type(x) is int for x in frame["pool_geometry"]),
         "native-derived K128 pages V records fixed16 slots")
    need(geometry["schema"] == "kivi.actual-disjoint-field-geometry/v1"
         and geometry["rank"] == owner["rank"] and geometry["identity"] == owner["identity"]
         and geometry["layer"] == layer and type(geometry["pages"]) is int
         and geometry["pages"] == pages and type(geometry["slots"]) is int and geometry["slots"] == 16
         and type(geometry["bits"]) is int and geometry["bits"] == bits and geometry["dtype"] == dtype,
         "original geometry receipt exact native dimensions")
    need(type(geometry["newly_allocated_device_bytes"]) is int and geometry["newly_allocated_device_bytes"] == 0
         and geometry["original_dense_storage_still_live"] is True
         and all(geometry[key] is False for key in ("packing_checked", "reader_checked", "allocation_replaced",
                                                   "native_ready", "model_ready", "run_authority")),
         "geometry only no allocation or numerical promotion")
    pools = [pool for pool in event["pools"] if layer in pool["shared_by"]]
    need(len(pools) == 1, "one actual native parent membership")
    pool, region = pools[0], geometry["region"]
    need(region["pool"] == pool and type(pool["size"]) is int and pool["size"] > 0
         and geometry["original_parent_bytes"] == pool["size"], "whole original parent receipt")
    raw = pool["raw"]
    parent_base, raw_start, raw_stop, parent_bytes = tensor_extent(raw, [pool["size"]], raw["dtype"], nd=True)
    need(raw["dtype"] in ("torch.int8", "torch.uint8") and raw_start == 0
         and type(region["base"]) is int and region["base"] == parent_base
         and all(span[0] == parent_base and span[3] == parent_bytes for span in native_spans)
         and all(view["device"] == raw["device"] for view in native["views"]),
         "actual native and compact common parent")
    start, stop = region["start"], region["stop"]
    need(type(start) is int and type(stop) is int and 0 <= start < stop <= raw_stop and start % 4 == 0
         and region["all_original_native_writers_enabled"] is True
         and region["allocation_replaced"] is False and region["run_authority"] is False,
         "unchanged aligned compact region and native writers")
    lanes = 32 // bits
    expected = [
        ("key_codes", [pages, 128 // lanes, 256], "torch.int32"),
        ("key_scales", [pages, 4, 256], dtype), ("key_minima", [pages, 4, 256], dtype),
        ("value_codes", [records, 256 // lanes], "torch.int32"),
        ("value_scales", [records, 8], dtype), ("value_minima", [records, 8], dtype),
        ("key_residual", [16, 128, 256], dtype), ("value_residual", [16, 129, 256], dtype),
        ("shifts", [lanes], "torch.int32")]
    need(type(geometry["fields"]) is list and len(geometry["fields"]) == 9
         and set(frame["live_alias_descriptors_before_snapshot"]) == set(FIELDS)
         and set(frame["pool_fields"]) == set(FIELDS), "all9 geometry and all8 captured fields")
    sizes, cursor = {}, start
    for observed, (name, dimensions, field_dtype) in zip(geometry["fields"], expected):
        need(observed["name"] == name, "original exact field order")
        desc = observed["descriptor"]
        base, lo, hi, total = tensor_extent(desc, dimensions, field_dtype, nd=True)
        width = 4 if field_dtype == "torch.int32" else 2
        cursor = (cursor + width - 1) // width * width
        need(base == parent_base and total == parent_bytes and lo == cursor
             and desc["device"] == raw["device"], "exact field alias offset parent device")
        need(all(hi <= native_lo or native_hi <= lo for unused, native_lo, native_hi, total in native_spans),
             "compact fields exclude this native KV span; ALL64 zeroer separate")
        cursor = hi
        if name in FIELDS:
            live = frame["live_alias_descriptors_before_snapshot"][name]
            need(tensor_extent(live, dimensions, field_dtype) == (base, lo, hi, total)
                 and all(live[key] == desc[key] for key in live),
                 "same actual live field before immutable snapshot")
            sizes[name] = hi - lo
            need(type(frame["pool_fields"][name]["bytes"]) is int
                 and frame["pool_fields"][name]["bytes"] == sizes[name], "whole raw snapshot field size")
    need(cursor == stop and type(region["field_bytes"]) is int and region["field_bytes"] == stop - start,
         "exact nine-field reservation extent")
    # Match the unchanged producer capture envelope; no inherited budget waiver.
    need(sum(sizes.values()) <= 192 * 1024**2, "unchanged whole compact capture budget")
    return dict(pages=pages, records=records, slots=16, native_capacity=capacity,
                logical_capacity_per_owner=33792, sizes=sizes, captured_bytes=sum(sizes.values()),
                event_ref=provenance["event_ref"], geometry_ref=geometry_ref, layer=layer)

def consume(frame_ref, codec_ref, *, installer_sha256, capture_sha256):
    need("torch" not in sys.modules and "torch_npu" not in sys.modules, "independent no-Torch process")
    need(all(type(x) is str and re.fullmatch("[0-9a-f]{64}", x)
             for x in (installer_sha256, capture_sha256)), "new reviewed source identities")
    frame = document(frame_ref)
    need(frame["schema"] == "kivi.actual-packed-qkav-frame/v1"
         and frame["kernel_source_sha256"] == KERNEL_SHA and frame["snapshot_is_live_alias"] is False
         and frame["model_ready"] is False and frame["run_authority"] is False, "actual packed snapshot scope")
    bits, dtype = frame["bits"], frame["dtype"]
    need(type(bits) is int and bits in (2, 4) and dtype in ("float16", "bfloat16"), "frozen2/4 A16 cases")
    rows = frame["rows"]
    need(type(rows) is list and 1 <= len(rows) <= 16, "whole actual first-decode batch")
    need(set(frame["pool_fields"]) == set(FIELDS), "all8 original packed fields")
    first_owner = document(rows[0]["identity_refs"]["slot_owner"])
    first_provenance = document(first_owner["original_prefill_ref"])
    physical = source_geometry(frame, first_provenance, first_owner)
    sizes = physical["sizes"]
    codec = codec_module(codec_ref)
    results = []
    seen = {"slots": set(), "kp": set(), "vp": set(), "owners": set()}
    with ExitStack() as stack:
        fields = {name: stack.enter_context(VerifiedFile(frame["pool_fields"][name], 192 * 1024**2))
                  for name in FIELDS}
        for name, source in fields.items():
            need(source.size == sizes[name], "actual complete physical field extent " + name)
        inputs = frame["whole_prewrite_input_refs"]
        need(set(inputs) == {"query", "key", "value"}, "whole actual prewrite QKV")
        key_input, value_input = raw(inputs["key"], 8192), raw(inputs["value"], 8192)
        need(len(key_input) == len(value_input) == len(rows) * 512, "whole prewrite append inputs")
        need(len(raw(inputs["query"], 49152)) == len(rows) * 6 * 512, "whole prewrite query input")

        def equal(name, offset, expected):
            need(fields[name].read(offset, len(expected)) == expected,
                 "independent original-input writer bytes " + name)

        for index, row in enumerate(rows):
            length, kp_length, vp_length, slot = row["controls"]
            need(all(type(x) is int for x in row["controls"])
                 and (length, kp_length, vp_length) == (32769, 32768, 32640)
                 and row["computed"] == 32768 and type(row["computed"]) is int
                 and row["generation"] == 1 and type(row["generation"]) is int,
                 "only true first decode after complete32768 prefill")
            need(type(slot) is int and 0 <= slot < 16 and row["slot"] == slot
                 and type(row["epoch"]) is int and row["epoch"] > 0, "actual slot epoch")
            kp, vp = row["kp"], row["vp"]
            need(len(kp) == 256 and len(vp) == 32640
                 and len(set(kp)) == len(kp) and len(set(vp)) == len(vp)
                 and all(type(x) is int and 0 <= x < physical["pages"] for x in kp)
                 and all(type(x) is int and 0 <= x < physical["records"] for x in vp), "actual independent prefix maps")
            for key, values in (("slots", [slot]), ("kp", kp), ("vp", vp), ("owners", [row["request_id"]])):
                need(not seen[key].intersection(values), "disjoint first-prefill owners " + key)
                seen[key].update(values)
            owner = document(row["identity_refs"]["slot_owner"])
            provenance_ref = owner["original_prefill_ref"]
            provenance = document(provenance_ref)
            need(source_geometry(frame, provenance, owner) == physical,
                 "every owner same actual native allocation geometry")
            need(owner["schema"] == "kivi.actual-qwen-slot-owner/v1"
                 and owner["request_id"] == row["request_id"] and owner["slot"] == slot
                 and owner["epoch"] == row["epoch"] and owner["computed"] == 32768
                 and owner["generation"] == 1, "actual source-bound decode owner")
            need(provenance["schema"] == "kivi.actual-original-prefill/v1"
                 and provenance["status"] == "ORIGINAL_PREFILL_CAPTURED"
                 and provenance["rank"] == owner["rank"] and provenance["identity"] == owner["identity"]
                 and provenance["layer"] == owner["layer"]
                 and provenance["request_id"] == row["request_id"] and provenance["slot"] == slot
                 and provenance["slot_epoch"] == row["epoch"] and provenance["dtype"] == dtype
                 and provenance["bits"] == bits and type(provenance["bits"]) is int,
                 "original source and actual owner/layer continuity")
            need(provenance["installer_source_sha256"] == installer_sha256
                 and provenance["capture_source_sha256"] == capture_sha256
                 and all(provenance[key] == sha for key, sha in PINS.items()), "exact unchanged critical sources")
            need(provenance["prompt_length"] == 32768 and provenance["original_bytes"] == 33554432
                 and provenance["original_attention_calls"] == 1
                 and all(provenance[key] is False for key in ("allocation_replaced", "graph_checked",
                     "model_ready", "performance_ready", "run_authority", "writer_arithmetic_checked")),
                 "original dense prefill scope, no borrowed numerical authority")
            prefill_frame = document(provenance["frame_ref"])
            decode_frame = document(owner["frame_ref"])
            for actual, kind in ((prefill_frame, "prefill"), (decode_frame, "decode")):
                need(actual["schema"] == "kivi.actual-packed-qwen-frame/v1" and actual["kind"] == kind
                     and actual["rank"] == owner["rank"] and actual["identity"] == owner["identity"]
                     and row["request_id"] in actual["req_ids"], "actual native scheduler frame")
            need(prefill_frame["epoch"] < decode_frame["epoch"], "real prefill before decode")
            need(decode_frame["req_ids"] == [item["request_id"] for item in rows]
                 and decode_frame["computed_tokens"] == [32768] * len(rows)
                 and decode_frame["scheduled_counts"] == [1] * len(rows), "whole real decode row ordering")
            pidx = prefill_frame["req_ids"].index(row["request_id"])
            need(prefill_frame["computed_tokens"][pidx] + prefill_frame["scheduled_counts"][pidx] == 32768,
                 "native complete prefill boundary")
            event = document(provenance["event_ref"])
            need(event["rank"] == owner["rank"] and event["identity"] == owner["identity"]
                 and len(event["layers"]) == 64 and event["layers"][owner["layer"]]["kind"] == "FA"
                 and event["layers"][owner["layer"]]["views"] == provenance["native_views"],
                 "actual unchanged native cache origin; overlap authority separate")
            shape, block_row = provenance["native_shape"], provenance["native_block_row"]
            need(type(shape) is list and len(shape) == 4 and shape[2:] == [1, 256]
                 and all(type(x) is int and x > 0 for x in shape)
                 and type(block_row) is list and len(block_row) * shape[1] >= 32768
                 and all(type(x) is int and 0 <= x < shape[0] for x in block_row), "source-derived native page map")
            tiles = provenance["tiles"]
            need(type(tiles) is list and len(tiles) == 256, "whole original32768 coverage")
            paths = [tile[axis + "_ref"]["path"] for tile in tiles for axis in ("key", "value")]
            need(len(set(paths)) == 512, "each original gather tile has its own actual publication")
            for tile_index, tile in enumerate(tiles):
                start, stop = tile_index * 128, (tile_index + 1) * 128
                need(tile["start"] == start and tile["stop"] == stop, "ordered whole original tile coverage")
                originals = {axis: raw(tile[axis + "_ref"], 65536) for axis in ("key", "value")}
                need(all(len(blob) == 65536 for blob in originals.values()), "whole original A16 tile bytes")
                decoded = codec.scalars(originals["key"], dtype)
                expected = codec.pack((decoded[t * 256:(t + 1) * 256] for t in range(128)), "K", bits, dtype)
                page = kp[tile_index]
                equal("key_codes", page * 128 * 256 * bits // 8, expected.payload)
                equal("key_scales", page * 2048, expected.scales)
                equal("key_minima", page * 2048, expected.minima)
                if start < 32640:
                    decoded = codec.scalars(originals["value"], dtype)
                    expected = codec.pack((decoded[t * 256:(t + 1) * 256] for t in range(128)), "V", bits, dtype)
                    for offset, record in enumerate(vp[start:stop]):
                        width = 256 * bits // 8
                        equal("value_codes", record * width, expected.payload[offset * width:(offset + 1) * width])
                        equal("value_scales", record * 16, expected.scales[offset * 16:(offset + 1) * 16])
                        equal("value_minima", record * 16, expected.minima[offset * 16:(offset + 1) * 16])
                else:
                    equal("value_residual", slot * 129 * 512, originals["value"])
            equal("key_residual", slot * 128 * 512, key_input[index * 512:(index + 1) * 512])
            equal("value_residual", (slot * 129 + 128) * 512, value_input[index * 512:(index + 1) * 512])
            results.append(dict(request_id=row["request_id"], rank=owner["rank"], layer=owner["layer"],
                                slot=slot, epoch=row["epoch"], original_prefill_ref=provenance_ref,
                                original_tokens=32768, original_bytes=33554432,
                                exact_code_scale_minimum_and_residual_bytes=True))
    need("torch" not in sys.modules and "torch_npu" not in sys.modules, "independent process remains no-Torch")
    return dict(schema="kivi.original-prefill.independent/v1", status="ORIGINAL_PREFILL_WRITER_CONSUMED",
                frame_ref=frame_ref, codec_ref=codec_ref, installer_source_sha256=installer_sha256,
                capture_source_sha256=capture_sha256, rows=results, bits=bits, dtype=dtype,
                physical_geometry=physical, geometry_independently_checked=True,
                scope="original32768 prefill writer and first real decode append bytes only",
                output_arithmetic_checked=False, unused_writer_bytes_checked=False,
                all64_overlap_checked=False, full_model_coverage_checked=False, lifecycle_checked=False,
                native_ready=False, model_ready=False, performance_ready=False, run_authority=False,
                allocation_replaced=False, graph_checked=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--frame-ref-json", type=Path)
    parser.add_argument("--codec-ref-json", type=Path)
    parser.add_argument("--installer-sha256")
    parser.add_argument("--capture-sha256")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(status="DEFAULT_OFF", model_ready=False, run_authority=False)))
        return 0
    need(all((args.frame_ref_json, args.codec_ref_json, args.installer_sha256, args.capture_sha256)),
         "all actual input/source Refs required")
    result = consume(json.loads(args.frame_ref_json.read_bytes()), json.loads(args.codec_ref_json.read_bytes()),
                     installer_sha256=args.installer_sha256, capture_sha256=args.capture_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
