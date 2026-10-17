"""One warmup and one real 129-token request; no synthetic GDN matrices.

MAIN invokes only after the private native API reports ready. Does not poll or
start a server. Same admitted container/loopback. Performance and accuracy false.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture_overlay as own


def payload(config, count):
    return dict(model="qwen36", prompt=own.prompt_ids(config, count), n=1, stream=True,
                temperature=0, seed=0, max_tokens=2, min_tokens=2, ignore_eos=True,
                echo=True, return_token_ids=True, stream_options={"include_usage": True})


def request_once(url, body, output, request_id):
    own.write_new(output.with_suffix(".request.json"), dict(request_id=request_id, url=url, payload=body))
    request = urllib.request.Request(url, json.dumps(body).encode(),
        {"Content-Type": "application/json", "X-Request-Id": request_id})
    limit = 4 * 1024**2
    with urllib.request.urlopen(request, timeout=120) as response:
        own.need(response.status == 200, "native HTTP success")
        # Preserve the exact original wire even if SSE or count validation fails.
        with output.with_suffix(".response.bin").open("xb") as handle:
            wire = response.read(limit + 1)
            handle.write(wire)
    own.need(len(wire) <= limit, "bounded diagnostic response")
    items, done = [], False
    for line in wire.decode("utf-8").splitlines():
        if not line.startswith("data: "):
            continue
        value = line[6:]
        if value == "[DONE]":
            done = True
        else:
            items.append(json.loads(value))
    usages = [item["usage"] for item in items if item.get("usage")]
    own.need(done and usages and usages[-1]["prompt_tokens"] == len(body["prompt"])
             and usages[-1]["completion_tokens"] == 2, "actual input and output count/SSE completion")
    return dict(request_id=request_id, response_sha=own.sha(output.with_suffix(".response.bin")), usage=usages[-1])


def main(argv=None):
    p = argparse.ArgumentParser(allow_abbrev=False)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--model-config", type=Path)
    p.add_argument("--server-output", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--run-id")
    p.add_argument("--port", type=int, default=8252)
    args = p.parse_args(argv)
    if not args.execute:
        print(json.dumps(dict(default_enabled=False, sends_requests=False)))
        return 0
    own.need(args.model_config is not None and args.server_output is not None and args.output is not None,
             "explicit actual model/server/output")
    own.need(own.START <= time.time() and time.time() + 330 <= own.CUTOFF, "request and cleanup fit R118")
    own.need(1024 <= args.port <= 65535 and own.sha(args.model_config) == own.MODEL_CONFIG_SHA, "native port/model")
    launch = json.loads((args.server_output / "LAUNCH.json").read_text("utf-8"))
    own.need(launch["run_id"] == args.run_id and launch["capture_manifest_sha"] == own.CAPTURE_MANIFEST_SHA
             and launch["native_worker"] == own.NATIVE_WORKER and launch["mode"] in ("capture", "shadow")
             and launch["candidate_enabled"] is (launch["mode"] == "shadow"),
             "same genuine native capture launch identity")
    own.need(launch["argv"][launch["argv"].index("--port") + 1] == str(args.port), "same native private port")
    capture = args.server_output / "capture"
    own.need(capture.is_dir() and not (capture / "ARM.json").exists(), "initially unarmed capture")
    own.need(args.output.is_absolute() and not args.output.exists(), "exclusive new client output")
    args.output.mkdir(parents=False)
    config = json.loads(args.model_config.read_text("utf-8"))
    url = "http://127.0.0.1:%d/v1/completions" % args.port
    warmup = request_once(url, payload(config, 16), args.output / "warmup", args.run_id + "-warmup")
    own.write_new(capture / "ARM.json", dict(schema="mxr.capture.arm/v1", run_id=args.run_id))
    actual = request_once(url, payload(config, 129), args.output / "capture", args.run_id + "-capture")
    own.write_new(args.output / "RESULT.json", dict(schema="mxr.actual-request-capture/v1", run_id=args.run_id,
        warmup=warmup, capture_request=actual, mode=launch["mode"], actual_A_tensors="worker artifacts still require independent consumer",
        NPU_numerical_pass=False, performance_ready=False, task_accuracy=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
