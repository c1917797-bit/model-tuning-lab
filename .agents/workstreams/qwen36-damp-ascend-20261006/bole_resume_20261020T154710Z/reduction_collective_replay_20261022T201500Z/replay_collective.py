"""Default-OFF saved-input TP4 HCCL replay. Diagnostic only; MAIN owns admission."""
import argparse
from array import array
import datetime
import hashlib
import inspect
import json
import marshal
import os
from pathlib import Path
import re
import sys
import traceback

SCHEMA = "bole.collective-replay-input/v1"
SHAPE = [131, 5120]
TENSOR_BYTES = 131 * 5120 * 2
ITERATIONS = 8
FLAGS = ("HCCL_DETERMINISTIC", "HCCL_ALGO", "ASCEND_LAUNCH_BLOCKING")
FALSES = dict(diagnostic_only=True, numerical_qualified=False,
              candidate_qualification=False, formal_performance=False, task_accuracy=False)


def need(value, reason):
    if not value:
        raise ValueError(reason)


def ordinary(path):
    path = Path(path)
    need(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)),
         "ordinary absolute path without symlink")
    return path


def signature(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def file_ref(path, cap=128 * 2**20):
    path = ordinary(path)
    before = path.stat()
    need(path.is_file() and 0 <= before.st_size <= cap, "bounded ordinary file")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        need(signature(os.fstat(stream.fileno())) == signature(before), "same opened input")
        while True:
            part = stream.read(1024 * 1024)
            if not part:
                break
            digest.update(part)
        need(signature(os.fstat(stream.fileno())) == signature(before), "stable opened input")
    need(signature(path.stat()) == signature(before), "stable whole-file identity")
    return dict(path=str(path), bytes=before.st_size, sha256=digest.hexdigest())


def checked(ref, cap):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"}
         and type(ref["path"]) is str and type(ref["bytes"]) is int
         and type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]),
         "complete typed Ref3")
    need(0 <= ref["bytes"] <= cap and file_ref(ref["path"], cap) == ref, "exact immutable Ref3")
    return ordinary(ref["path"])


def read_ref(ref, cap):
    path = checked(ref, cap)
    raw = path.read_bytes()
    need(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"]
         and file_ref(path, cap) == ref, "stable bounded read")
    return raw


def obj(ref, cap):
    return json.loads(read_ref(ref, cap))


def execution_environment(environ):
    def integer(name):
        value = environ.get(name)
        need(type(value) is str and re.fullmatch("0|[1-9][0-9]*", value), "canonical " + name)
        return int(value)
    rank, local, world, local_world = [integer(k) for k in
                                     ("RANK", "LOCAL_RANK", "WORLD_SIZE", "LOCAL_WORLD_SIZE")]
    need(world == local_world == 4 and rank == local and rank in range(4), "one-node four-rank launch")
    need(environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
         "controller-qualified four logical devices required")
    need(environ.get("MASTER_ADDR") in ("127.0.0.1", "localhost"),
         "single-node loopback rendezvous")
    port = integer("MASTER_PORT")
    need(1024 <= port <= 65535, "bounded controller-owned rendezvous port")
    return rank, local


def validate_manifest(reference, rank):
    need(sys.byteorder == "little", "actual BF16 host byte order is little endian")
    m = obj(reference, 128 * 1024)
    required = {"schema", "worker_ref", "variant", "generation", "iterations", "shape",
                "dtype", "physical_to_logical", "mapping_evidence", "source_ref",
                "projection_records", "inputs"}
    need(type(m) is dict and set(m) == required and m["schema"] == SCHEMA, "closed replay manifest")
    need(m["worker_ref"] == file_ref(__file__, 128 * 1024), "actual immutable replay worker")
    need(m["variant"] in ("default", "deterministic_true") and type(m["generation"]) is int
         and m["generation"] == 1 and type(m["iterations"]) is int and m["iterations"] == ITERATIONS
         and m["shape"] == SHAPE and m["dtype"] == "torch.bfloat16", "fixed diagnostic workload")
    need(m["physical_to_logical"] == [[4, 0], [5, 1], [6, 2], [7, 3]],
         "physical4-7 only; controller evidence required")
    checked(m["mapping_evidence"], 2 * 2**20)
    checked(m["source_ref"], 2 * 2**20)
    need(type(m["inputs"]) is dict and set(m["inputs"]) == {"0", "1", "2", "3"}
         and type(m["projection_records"]) is list and len(m["projection_records"]) == 4,
         "all four actual rank inputs and records")
    seen, refs = set(), [reference, m["worker_ref"], m["mapping_evidence"], m["source_ref"]]
    for record_ref in m["projection_records"]:
        record = obj(record_ref, 128 * 1024)
        r = record.get("rank")
        need(type(r) is int and r in range(4) and r not in seen, "unique original rank")
        seen.add(r)
        need(record.get("schema") == "bole.native-prefill-boundary-repeatability/v1"
             and record.get("event") == "PROJECTION-INTERNAL"
             and type(record.get("generation")) is int and record["generation"] == 1
             and record.get("source_sha256") == m["source_ref"]["sha256"], "same actual producer generation/source")
        rec = record["record"]
        need(rec.get("generation") == 1 and rec.get("diagnostic_only") is True, "actual projection scope")
        meta = rec["stages"]["pre_reduce"]
        raw_ref = m["inputs"][str(r)]
        need(meta.get("observed") is True and meta.get("full_actual_tensor") is True
             and meta.get("dtype") == m["dtype"] and meta.get("shape") == SHAPE
             and meta.get("bytes") == TENSOR_BYTES and meta.get("finite") is True
             and meta.get("raw") == raw_ref and raw_ref["bytes"] == TENSOR_BYTES
             and raw_ref["sha256"] == meta.get("sha256"), "actual complete immutable pre-reduce operand")
        raw = read_ref(raw_ref, TENSOR_BYTES)
        words = array("H")
        words.frombytes(raw)
        if sys.byteorder != "little":
            words.byteswap()
        need(all((word & 0x7F80) != 0x7F80 for word in words), "finite original BF16 words")
        refs += [record_ref, raw_ref]
    need(seen == set(range(4)), "complete original rank coverage")
    return m, read_ref(m["inputs"][str(rank)], TENSOR_BYTES), refs


def runtime_flags(torch, variant):
    env = {key: os.environ.get(key) for key in FLAGS}
    need(all(v is None or type(v) is str and len(v) <= 128 for v in env.values()),
         "bounded whitelist execution flags")
    need(env["HCCL_DETERMINISTIC"] is None if variant == "default"
         else env["HCCL_DETERMINISTIC"] == "true", "exact fresh-process variant")
    deterministic = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    need(type(deterministic) is bool and type(warn) is bool, "actual standard torch flags")
    return dict(environment=env, torch_deterministic_enabled=deterministic,
                torch_deterministic_warn_only=warn)


def callable_source(function):
    path = inspect.getsourcefile(function)
    need(path is not None, "actual all_reduce Python source available")
    chain, seen = [], set()
    current = function
    while current is not None:
        need(inspect.isfunction(current) and id(current) not in seen and len(chain) < 8,
             "bounded actual Python collective wrapper chain")
        seen.add(id(current))
        current_path = inspect.getsourcefile(current)
        need(current_path is not None, "actual wrapper source available")
        chain.append(dict(module=current.__module__, qualname=current.__qualname__,
            source=file_ref(Path(current_path).resolve(), 4 * 2**20),
            code_sha256=hashlib.sha256(marshal.dumps(current.__code__)).hexdigest()))
        current = current.__dict__.get("__wrapped__")
    return dict(module=function.__module__, qualname=function.__qualname__,
                source=file_ref(Path(path).resolve(), 4 * 2**20),
                python_wrapper_chain=chain,
                callable_identity_runtime_only=id(function),
                transport_kernel_observed=False)


def loaded_collective_libraries():
    rows = {}
    for line in Path("/proc/self/maps").read_text().splitlines():
        fields = line.split(None, 5)
        if len(fields) != 6 or not fields[5].startswith("/"):
            continue
        path = fields[5]
        if not any(name in Path(path).name for name in ("libhccl", "libtorch_npu")):
            continue
        key = (path, fields[3], fields[4])
        rows[key] = dict(path=path, maps_device=fields[3], maps_inode=fields[4],
                         mapped_identity_proven=False)
    out = []
    for row in rows.values():
        try:
            row["file_ref"] = file_ref(Path(row["path"]).resolve(), 2**30)
        except (OSError, ValueError) as error:
            row["file_ref"] = None
            row["observation_error"] = type(error).__name__
        out.append(row)
    return dict(libraries=sorted(out, key=lambda x: x["path"]),
                libhccl_observed=any("libhccl" in Path(x["path"]).name for x in out),
                libtorch_npu_observed=any("libtorch_npu" in Path(x["path"]).name for x in out),
                transport_kernel_identity_proven=False)


def write_file(path, raw):
    need(type(raw) is bytes, "raw bytes")
    fd = os.open(ordinary(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        need(stream.write(raw) == len(raw), "complete exclusive write")
        stream.flush()
        os.fsync(stream.fileno())
    return file_ref(path, max(len(raw), 128 * 1024))


def write_json(path, value):
    return write_file(path, (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode())


def cpu_bytes(tensor, torch):
    cpu = tensor.detach().cpu().contiguous()
    return cpu.view(torch.uint8).numpy().tobytes()


def run(reference, output):
    rank, local = execution_environment(os.environ)
    root = ordinary(output)
    need(root.is_dir(), "MAIN must create fresh outer replay output directory")
    owned = root / ("rank-%d" % rank)
    owned.mkdir(mode=0o700)  # Exclusivity prevents an accidental same-rank retry.
    report = dict(schema="bole.collective-replay-rank/v1", **FALSES, rank=rank,
                  local_rank=local, input_manifest_ref=reference, iterations=[],
                  primary=None, cleanup_error=None, input_recheck_error=None,
                  input_refs_rechecked=False, collective_calls_completed=0,
                  completed=False, NPU_executed=False)
    dist = None
    original_refs = []
    try:
        m, raw, original_refs = validate_manifest(reference, rank)
        report["variant"] = m["variant"]
        report["physical_device_scope"] = m["physical_to_logical"]
        report["mapping_evidence"] = m["mapping_evidence"]
        report["worker_source"] = m["worker_ref"]
        # No device-capable import or operation exists before explicit execution.
        import torch
        import torch_npu
        import torch.distributed as distributed
        dist = distributed
        report["execution_flags"] = runtime_flags(torch, m["variant"])
        report["versions"] = dict(torch=str(torch.__version__),
                                  torch_npu=str(getattr(torch_npu, "__version__", "unavailable")),
                                  python=sys.version.split()[0])
        torch.npu.set_device(local)
        report["NPU_executed"] = True
        dist.init_process_group(backend="hccl", init_method="env://",
                                rank=rank, world_size=4, timeout=datetime.timedelta(seconds=180))
        need(dist.get_world_size() == 4 and dist.get_rank() == rank
             and str(dist.get_backend()) == "hccl", "actual four-rank HCCL group")
        operation = dist.all_reduce
        operation_ref = callable_source(operation)
        report["all_reduce"] = operation_ref
        original = torch.frombuffer(bytearray(raw), dtype=torch.bfloat16).reshape(SHAPE).clone()
        need(cpu_bytes(original, torch) == raw, "original CPU BF16 bit-preserving conversion")
        tensor = torch.empty(SHAPE, dtype=torch.bfloat16, device="npu:%d" % local)
        pointer = tensor.data_ptr()
        report["fixed_tensor"] = dict(shape=SHAPE, dtype="torch.bfloat16",
                                     device=str(tensor.device), data_ptr=pointer)
        for iteration in range(ITERATIONS):
            row = dict(iteration=iteration, input_reset=False, pre_sha256=None, post_raw=None)
            report["iterations"].append(row)
            tensor.copy_(original, non_blocking=False)
            torch.npu.synchronize()
            need(tensor.data_ptr() == pointer, "one fixed device allocation")
            before = cpu_bytes(tensor, torch)
            need(before == raw, "actual NPU pre-input equals immutable full original bytes")
            row.update(input_reset=True, pre_sha256=hashlib.sha256(before).hexdigest(),
                       pre_bytes=len(before))
            need(dist.all_reduce is operation and callable_source(operation) == operation_ref,
                 "unchanged actual standard collective callable")
            operation(tensor, op=dist.ReduceOp.SUM, async_op=False)
            torch.npu.synchronize()
            report["collective_calls_completed"] += 1
            after = cpu_bytes(tensor, torch)
            need(len(after) == TENSOR_BYTES and tensor.data_ptr() == pointer,
                 "complete post-output and fixed actual storage")
            row["post_raw"] = write_file(owned / ("post-%02d.bin" % iteration), after)
            row["post_sha256"] = row["post_raw"]["sha256"]
            row["pre_matches_original"] = True
            write_json(owned / ("iteration-%02d.json" % iteration), dict(**FALSES, rank=rank, **row))
        report["loaded_libraries"] = loaded_collective_libraries()
        report["execution_flags_after"] = runtime_flags(torch, m["variant"])
        need(report["execution_flags_after"] == report["execution_flags"], "unchanged execution flags")
        need(cpu_bytes(original, torch) == raw, "original CPU input unchanged")
        report["completed"] = True
    except BaseException as error:
        report["primary"] = dict(type=type(error).__name__, message=str(error),
                                 traceback=traceback.format_exc(limit=16))
    finally:
        if dist is not None and dist.is_initialized():
            try:
                dist.destroy_process_group()
            except BaseException as error:
                report["cleanup_error"] = dict(type=type(error).__name__, message=str(error))
        if original_refs:
            try:
                for original_ref in original_refs:
                    checked(original_ref, 2 * 2**20)
                report["input_refs_rechecked"] = True
            except BaseException as error:
                report["input_recheck_error"] = dict(type=type(error).__name__, message=str(error))
        if report["NPU_executed"] and "loaded_libraries" not in report:
            try:
                report["loaded_libraries"] = loaded_collective_libraries()
            except BaseException as error:
                report["library_observation_error"] = type(error).__name__
        if report["cleanup_error"] is not None or report["input_recheck_error"] is not None:
            report["completed"] = False
        write_json(owned / "RESULT.json", report)
    return 0 if report["completed"] and report["primary"] is None else 1


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--manifest-ref")
    parser.add_argument("--output")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(enabled=False, NPU=False, **FALSES), sort_keys=True))
        return 0
    need(args.manifest_ref and args.output, "explicit manifest Ref and fresh controller output required")
    return run(json.loads(args.manifest_ref), args.output)


if __name__ == "__main__":
    raise SystemExit(main())
