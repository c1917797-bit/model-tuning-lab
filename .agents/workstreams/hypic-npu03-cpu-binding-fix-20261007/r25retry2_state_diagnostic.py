#!/usr/bin/env python3
"""One-sample HYPIC observer integration; never a paired quality/performance verdict."""
from __future__ import annotations
import re
import time
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import signal
import time
from urllib.request import Request, urlopen
from r16_original_source_full_adapter import configure as base_configure

HERE = Path(__file__).resolve().parent
SOURCE = "/cache/cch/hypic_vllm_ascend-hotproof-20261008"
COMMIT = "4429e35177979c874bf053ab29789e4773f39b22"
ARM = "hypic-only"
KV = "language_model.model.layers.3.self_attn.attn"
GDN = "language_model.model.layers.0.linear_attn"
BODY_ID = "hypic-state-r25retry2-s059"
PROMPT_SHA = "7f8fe37b6b928123cf82ba839bd8c49a0677c5bf4a32446d990afb674c9e66ba"
CONTRACT = HERE / "r25retry2_state_preregistration.json"

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def configure(mode):
    c = base_configure(ARM)
    q = c.quality
    os.environ["HYPIC_QUALITY_PLUGIN_REPO"] = SOURCE
    os.environ["HYPIC_QUALITY_PLUGIN_COMMIT"] = COMMIT
    attempt = "hotpath-cache10r25retry2-state-" + mode
    q.ATTEMPT_ROOTS[attempt] = "quality-context-41984-" + attempt
    q.RESERVE_ATTEMPTS |= {attempt}
    q.ATTEMPT, q.QROOT = attempt, q.ROOT / q.ATTEMPT_ROOTS[attempt]
    q.EXPERIMENT = "hypic-r25retry2-bounded-state-" + mode
    original_spec = q.spec
    def spec(arm):
        source, binds, env, command = original_spec(arm)
        if command.count("exec vllm serve ") != 1:
            raise RuntimeError("serving launch seam drift")
        # Installation remains untouched; arm only the serving interpreter.
        launch = ("exec env PYTHONDONTWRITEBYTECODE=1 "
                  "HYPIC_STATE_OBSERVER_ENABLE=" + ("1" if mode == "enabled" else "0") +
                  " HYPIC_STATE_CAPTURE_CONFIG=/results/" + q.QROOT.name +
                  "/capture-config.json bash /diagnostic/state-observer-package-v3/run_with_patch.sh vllm serve ")
        command = command.replace("exec vllm serve ", launch)
        return source, [*binds, str(HERE)+":/diagnostic:ro"], env, command
    q.spec = spec
    original_guard = q.ForeignProcessGuard
    class RegistrationGuard(original_guard):
        last_registration_probe = 0
        def assert_clean(self):
            super().assert_clean()
            now = time.monotonic()
            if now - self.last_registration_probe < 20:
                return
            self.last_registration_probe = now
            output = q.run("docker", "logs", q.name_for(ARM), check=False)
            logs = output.stdout + output.stderr
            if ("Failed to load plugin hypic_vllm_ascend" in logs
                    or "HYPIC target not available" in logs):
                raise RuntimeError("HYPIC plugin load failed; abort before requests")
    q.ForeignProcessGuard = RegistrationGuard
    return c, q

def check(mode):
    frozen = json.loads(CONTRACT.read_text())
    for name, expected in frozen["files"].items():
        if digest(HERE/name) != expected:
            raise RuntimeError("preregistered code drift: "+name)
    c, q = configure(mode)
    if q.QROOT.exists():
        raise RuntimeError("immutable diagnostic root exists; inspect, never restart")
    disabled = q.ROOT/"r23-state-disabled-independent-audit.json"
    if digest(disabled) != "38f25f63e7d0e114c23bc9c8229f189e047d8a440097c4292a07e04403d46bab":
        raise RuntimeError("retained disabled diagnostic control identity drift")
    for name in ("sitecustomize.py", "run_with_patch.sh"):
        if digest(HERE/"state-observer-package"/name) != digest(HERE/"state-observer-package-v3"/name):
            raise RuntimeError("disabled wrapper no longer identical")
    fp = q.preflight()
    items, _ = c.cases()
    item = next(x for x in items if x["index"] == 59)
    if (item["prompt_sha256"] != PROMPT_SHA or item["prompt_tokens"] != 20414
            or item["boundary"] != 16384):
        raise RuntimeError("r20 sample identity drift")
    # Validate constructed owned-container specification without creating it.
    _source, binds, env, command = q.spec(ARM)
    if any("/dev/davinci"+str(i) in command for i in range(4, 8)):
        raise RuntimeError("forbidden device command")
    return c, q, item, fp, frozen

def request(q, item, identifier, maximum):
    payload = dict(model=q.MODEL_NAME, messages=[dict(role="user", content=item["prompt"])],
        request_id=identifier, n=1, max_tokens=maximum, temperature=0, seed=0,
        ignore_eos=False, stream=False, chat_template_kwargs=dict(enable_thinking=False),
        vllm_xargs=dict(hypic_segment_ends=[item["boundary"], item["prompt_tokens"]]))
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    req = Request(q.BASE_URL+"/v1/chat/completions", data=raw,
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=900) as response:
        data = json.load(response)
    if (data.get("id") != "chatcmpl-"+identifier or len(data.get("choices", [])) != 1
            or data.get("usage", {}).get("prompt_tokens") != item["prompt_tokens"]
            or not 1 <= data.get("usage", {}).get("completion_tokens", 0) <= maximum):
        raise RuntimeError("diagnostic response identity/accounting drift")
    return dict(request_id=data["id"], request_sha256=hashlib.sha256(raw).hexdigest(),
                max_tokens=maximum, response=data)

def guarded_request(q, item, guard, container_id, identifier, maximum):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(request, q, item, identifier, maximum)
        try:
            while True:
                try:
                    result = future.result(timeout=10)
                    guard.assert_clean()
                    return result
                except concurrent.futures.TimeoutError:
                    guard.assert_clean()
        except BaseException:
            q.stop_owned_for_abort(ARM, container_id)
            raise

def registered_workers(q, mode):
    output = q.run("docker", "logs", q.name_for(ARM))
    logs = output.stdout + output.stderr
    if "Failed to load plugin hypic_vllm_ascend" in logs:
        raise RuntimeError("HYPIC plugin load failed")
    namespace = json.loads((q.QROOT/ARM/"worker-namespace-map.json").read_text())
    expected = set(namespace["physical_npu_to_namespace_pid"].values())
    manifest_sha = digest(HERE/"state-observer-package-v3"/"MANIFEST.json")
    records = []
    for line in logs.splitlines():
        if '"schema": "hypic-state-observer-installed/v3"' not in line:
            continue
        record = json.loads(line[line.index("{"):line.rindex("}")+1])
        if record["pid"] not in expected:
            continue
        if (record["manifest_sha256"] != manifest_sha
                or record["request_id"] != "chatcmpl-"+BODY_ID
                or record["kv_layer"] != KV or record["gdn_layer"] != GDN
                or record["plugin_sha256"] != "84cfc3a61ac52aec9c40f6272fbab3768d728b7e0f94225c50b40ff3857f4fd8"):
            raise RuntimeError("observer worker identity drift")
        records.append(record)
    if mode == "enabled" and {x["pid"] for x in records} != expected:
        raise RuntimeError("four worker observer registration not proven")
    if mode == "disabled" and records:
        raise RuntimeError("disabled observer registered")
    q.write_json(q.QROOT/"worker-observer-registration.json",
                 dict(records=records, expected_pids=sorted(expected),
                      log_sha256=hashlib.sha256(logs.encode()).hexdigest()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["disabled", "enabled"], required=True)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    c, q, item, fp, frozen = check(args.mode)
    if not args.run:
        print(json.dumps(dict(root=str(q.QROOT), sample=59, source=COMMIT,
                              mode=args.mode, frozen_sha256=digest(CONTRACT))))
        return 0
    q.assert_lane_available()
    if q.inspect(q.name_for(ARM)) is not None:
        raise RuntimeError("owned container already exists")
    signal.signal(signal.SIGTERM, q.interrupt)
    signal.signal(signal.SIGINT, q.interrupt)
    q.QROOT.mkdir()  # Exclusive ownership: no partial-root reuse.
    (q.QROOT/"capture").mkdir()
    q.write_json(q.QROOT/"capture-config.json", dict(raw_root="/results/"+q.QROOT.name+"/capture",
        request_id="chatcmpl-"+BODY_ID, kv_layer=KV, gdn_layer=GDN))
    q.write_json(q.QROOT/"contract.json", dict(frozen=frozen, mode=args.mode,
        fingerprint=fp, preregistration_sha256=digest(CONTRACT),
        git_commit=q.run("git", "-C", str(HERE), "rev-parse", "HEAD").stdout.strip(),
        sample={k:v for k,v in item.items() if k != "prompt"}))
    container_id, guard, error = "", None, None
    try:
        container_id = q.create(ARM)
        q.write_json(q.QROOT/"container-inspect.json", q.inspect(q.name_for(ARM)))
        guard = q.ForeignProcessGuard(ARM, {}, owned_container_id=container_id)
        guard.start()
        q.start(ARM, container_id, fp, guard)
        start = json.loads((q.QROOT/ARM/"service-start.json").read_text())
        guard.set_expected_workers(start["worker_pid_by_physical_npu"])
        registered_workers(q, args.mode)
        for name, maximum in [("warm1",1), ("warm2",1), ("target",2048), ("after",1)]:
            identifier = BODY_ID if name == "target" else BODY_ID+"-"+name
            value = guarded_request(q, item, guard, container_id, identifier, maximum)
            q.write_json(q.QROOT/(name+".json"), value)
            q.status(ARM, "diagnostic-"+name+"-complete")
        if args.mode == "enabled":
            seals = list((q.QROOT/"capture").glob("rank-*/SEAL.json"))
            if len(seals) != 4:
                raise RuntimeError("selected hot capture missing four worker seals")
        elif list((q.QROOT/"capture").iterdir()):
            raise RuntimeError("disabled observer wrote capture")
        guard.assert_clean()
    except Exception as exc:
        error = type(exc).__name__+": "+str(exc)
    finally:
        try:
            if guard is not None:
                guard.close()
        except Exception as exc:
            error = (error or "")+"; guard close: "+str(exc)
        try:
            if container_id:
                q.cleanup(ARM, container_id)
        except Exception as exc:
            error = (error or "")+"; cleanup: "+str(exc)
        q.write_json(q.QROOT/"terminal.json", dict(completed=error is None,
            error=error, mode=args.mode, container_id=container_id,
            quality_or_performance_claim=False, independent_audit_required=True))
    return 1 if error else 0

if __name__ == "__main__":
    raise SystemExit(main())
