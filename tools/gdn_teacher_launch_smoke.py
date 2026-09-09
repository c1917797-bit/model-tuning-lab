"""One bounded TP4 HCCL smoke test of the exact teacher-launcher environment.

No model is loaded. This validates communication initialization/reduction only,
not DRRQR numerics, determinism, performance, or real-model capture.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, record):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")


def communication_worker(output):
    rank, local_rank, world = (int(os.environ[x]) for x in ("RANK", "LOCAL_RANK", "WORLD_SIZE"))
    if not (world == 4 and rank == local_rank and rank in range(4)):
        raise ValueError("TP4 local rank contract differs")
    if os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0,1,2,3":
        raise ValueError("audited device namespace differs")
    if any(x in os.environ for x in ("HCCL_DETERMINISTIC", "LCCL_DETERMINISTIC")):
        raise ValueError("native determinism overrides must be absent")
    report = {"schema": "gdn-teacher-communication-smoke/v1", "rank": rank,
              "local_rank": local_rank, "world_size": world, "status": "failed",
              "native_determinism_overrides": "absent"}
    initialized = False
    try:
        import torch
        import torch_npu  # noqa: F401; register actual Ascend backend.
        import torch.distributed as dist
        torch.npu.set_device(local_rank)
        dist.init_process_group("hccl", timeout=timedelta(seconds=45))
        initialized = True
        values = torch.full((16,), rank + 1, dtype=torch.float32, device=f"npu:{local_rank}")
        dist.all_reduce(values)
        torch.npu.synchronize()
        actual = values.cpu().tolist()
        if actual != [10.0] * 16:
            raise RuntimeError("TP4 all_reduce output mismatch")
        report.update(status="passed", reduction=actual, dtype=str(values.dtype),
                      device=str(values.device), torch_version=torch.__version__,
                      torch_npu_version=torch_npu.__version__,
                      torch_npu_source=str(Path(torch_npu.__file__).resolve()))
    except BaseException as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        if initialized:
            try:
                dist.destroy_process_group()
            except BaseException as error:
                report.update(status="failed", cleanup_error=repr(error))
        write_json(output / f"rank{rank}.json", report)
    if report["status"] != "passed":
        raise RuntimeError("communication worker cleanup failed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--service-output-dir", type=Path)
    parser.add_argument("--capture-manifest", type=Path)
    parser.add_argument("--capture-manifest-sha256")
    parser.add_argument("--launcher-sha256")
    args = parser.parse_args(argv)
    if args.worker:
        if not args.output_dir.is_absolute() or not args.output_dir.is_dir():
            raise ValueError("controller-owned output required")
        communication_worker(args.output_dir)
        return 0
    launcher_path = Path(__file__).with_name("run_gdn_teacher_capture.py")
    if digest(launcher_path) != args.launcher_sha256:
        raise ValueError("explicit launcher identity differs")
    import run_gdn_teacher_capture as launcher
    if args.capture_manifest is None or args.service_output_dir is None:
        parser.error("controller requires capture manifest and intended service output")
    launcher.shared.read_bound_json(args.capture_manifest, args.capture_manifest_sha256)
    output = args.output_dir
    if (not output.is_absolute() or output != output.resolve() or output.exists()
            or Path("/drrqr-results").resolve() not in output.parents):
        raise ValueError("fresh absolute smoke output below /drrqr-results required")
    if (not args.service_output_dir.is_absolute()
            or args.service_output_dir != args.service_output_dir.resolve()
            or Path("/drrqr-results").resolve() not in args.service_output_dir.parents
            or args.service_output_dir.exists() or args.service_output_dir == output):
        raise ValueError("fresh distinct intended service output required")
    env, disabled, observer, inherited = launcher.service_environment(args, args.service_output_dir)
    if any(name in env for name in launcher.UNSET_RUNTIME_FLAGS):
        raise ValueError("launcher failed to remove invalid native overrides")
    output.mkdir(exist_ok=False)
    command = [sys.executable, "-m", "torch.distributed.run", "--standalone",
               "--nnodes=1", "--nproc-per-node=4", str(Path(__file__).resolve()),
               "--worker", "--output-dir", str(output)]
    context = {"schema": "gdn-teacher-communication-smoke/v1", "script_sha256": digest(__file__),
               "launcher_sha256": args.launcher_sha256, "command": command,
               "capture_manifest_sha256": args.capture_manifest_sha256,
               "intended_service_output": str(args.service_output_dir),
               "disabled_flags": disabled, "observer_flags": observer,
               "unset_runtime_flags": list(launcher.UNSET_RUNTIME_FLAGS),
               "inherited_runtime_environment": inherited,
               "physical_mapping": "external fresh preflight required: physical4-7 -> logical0-3",
               "budget_seconds": 120, "claim": __doc__}
    write_json(output / "manifest.json", context)
    code = launcher.shared.run_service(command, env, output, 120, 10)
    report = {"schema": context["schema"], "status": "failed", "process_exit_code": code,
              "manifest_sha256": digest(output / "manifest.json"), "ranks": [],
              "claim": "HCCL startup and a 16-element FP32 all_reduce only; no model/numerical/performance result."}
    if code == 0:
        for rank in range(4):
            path = output / f"rank{rank}.json"
            row = json.loads(path.read_text())
            if (row.get("status") != "passed" or row.get("rank") != rank
                    or row.get("reduction") != [10.0] * 16):
                raise RuntimeError("rank report coverage/result mismatch")
            report["ranks"].append({"rank": rank, "path": str(path), "sha256": digest(path)})
        report["status"] = "passed"
    write_json(output / "report.json", report)
    print(json.dumps(report), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())

