"""Default-OFF H8 HTTP client; never starts a model, Docker, or an NPU job."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import (PROTOCOL, StreamState, arm_contract, canonical, digest,
                      prompt_ids, require, sha, sources, summarize, write_new)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--arm-dir", type=Path)
    p.add_argument("--port", type=int)
    p.add_argument("--output-dir", type=Path)
    a = p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"status": "OFF", "starts_model": False, "NPU_executed": False,
                          "matched_e2e_verified": False, "task_accuracy_verified": False}))
        return 0
    require(a.arm_dir is not None and a.port is not None and a.output_dir is not None,
            "explicit arm, port, and new output root")
    arm_path = a.arm_dir / "ARM.json"
    require(arm_path.is_file() and not arm_path.is_symlink(), "ordinary actual arm manifest")
    arm = arm_contract(json.loads(arm_path.read_text()), a.port)
    root = a.output_dir.resolve()
    require(Path("/kvbuffer-results") in root.parents and not root.exists(), "new mounted external output only")
    root.mkdir(parents=True, exist_ok=False)
    write_new(root / "PROTOCOL.json", {
        "schema": "kvbp.h8-http-protocol/v1", "protocol": PROTOCOL,
        "arm_file_sha256": sha(arm_path), "client_sources": sources(),
        "prompts": [{"index": i, "sha256": digest(prompt_ids(i))} for i in range(40)],
        "quality_evaluation": False,
    })

    def request(index, outputs, tag, enqueued):
        prompt = prompt_ids(index)
        state = StreamState(prompt, outputs)
        payload = {
            "model": arm["served_model_name"], "prompt": prompt, "max_tokens": outputs,
            "min_tokens": outputs, "temperature": 0, "seed": 0, "ignore_eos": True,
            "stream": True, "return_token_ids": True, "echo": PROTOCOL["echo"], "n": 1,
            "request_id": "h8-" + root.name + "-" + tag + "-" + str(index),
            "stream_options": {"include_usage": True},
        }
        row = {"index": index, "enqueued": enqueued, "submitted": None,
               "prompt_ids_sha256": digest(prompt), "prompt_tokens": len(prompt),
               "completion_tokens": 0, "ok": False, "done": False, "error": None}
        try:
            req = Request("http://127.0.0.1:%d/v1/completions" % a.port,
                          data=canonical(payload), headers={"Content-Type": "application/json"}, method="POST")
            # The actual HTTP submission occurs in the worker, not when its future is enqueued.
            row["submitted"] = time.perf_counter()
            with (root / (tag + "-%02d.sse.jsonl" % index)).open("xb") as raw:
                with urlopen(req, timeout=7200) as response:
                    require(response.status == 200, "HTTP status")
                    for line in response:
                        now = time.perf_counter()
                        # Preserve bytes and receive time before parsing or checking any gate.
                        raw.write(canonical({"receipt": now, "line": line.decode("utf-8", errors="replace")}) + b"\n")
                        raw.flush()
                        if not line.startswith(b"data: "):
                            continue
                        state.feed(line[6:].strip(), now)
                        if state.done:
                            break
            state.finish_check()
            row.update(ok=True, done=state.done, first=state.first, last=state.last,
                       finish_reason=state.finish, completion_tokens=len(state.tokens),
                       output_ids_sha256=digest(state.tokens), usage=state.usage)
        except BaseException as error:
            row.update(error=repr(error), finish_reason=state.finish, done=state.done,
                       completion_tokens=len(state.tokens), first=state.first, last=state.last)
        row["response_end"] = time.perf_counter()
        write_new(root / (tag + "-%02d.result.json" % index), row)
        return row

    report = {
        "schema": "kvbp.h8-http-measurement/v1", "arm": arm["arm"], "status": "running",
        "protocol": PROTOCOL, "arm_sha256": sha(arm_path), "client_sources": sources(),
        "measurement_scope": arm["measurement_scope"], "quality_evaluated": False,
        "NPU_execution_authority_checked": False, "matched_e2e_verified": False,
        "task_accuracy_verified": False, "rounds": 1,
        "consumer_required": "whole-MAIN-terminal+TP4-worker+matched-arm+cache-budget-consumer",
    }
    try:
        warmups = [request(i, 1, "warmup", time.perf_counter()) for i in range(2)]
        write_new(root / "WARMUPS.json", warmups)
        require(all(r["ok"] for r in warmups), "warmup failed; measured requests not dispatched")
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(request, i, 1024, "request", time.perf_counter()) for i in range(40)]
            responses = sorted((f.result() for f in futures), key=lambda r: r["index"])
        report["responses"] = responses
        report["metrics"] = summarize(responses)
        report["status"] = "client_measurement_complete_not_acceptance"
    except BaseException as error:
        report.update(status="failed", error=repr(error))
        raise
    finally:
        write_new(root / "REPORT.json", report)
    print(json.dumps(report["metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
