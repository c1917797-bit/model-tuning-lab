#!/usr/bin/env bash
set -Eeuo pipefail

WORKTREE=/cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
OUTPUT_ROOT=/cache/cch/hypic-qwen36-piercing-20260904
BASELINE_CONTAINER=qwen36_hypic_pdc_baseline_npu0_3
TREATMENT_CONTAINER=qwen36_hypic_pdc_treatment_npu0_3
BASELINE_PROFILE_CONTAINER=qwen36_hypic_pdc_baseline_profile_npu0_3
TREATMENT_PROFILE_CONTAINER=qwen36_hypic_pdc_treatment_profile_npu0_3
MODEL_NAME=qwen36-hypic-piercing
PORT=8221
QUALITY_SCRIPT=.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py
CANARY_SCRIPT=.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_semantic_canary.py
PROFILE_SCRIPT=.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_native_profile.py
PROFILE_CLONE_SCRIPT=.agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_profile_clone.py
if [[ ${1:-} == "--self-test" ]]; then
  SELF_TEST=1
  WAIT_PID=
else
  SELF_TEST=0
  WAIT_PID=${1:-}
fi

cd "$WORKTREE"
mkdir -p "$OUTPUT_ROOT"
exec 9>"$OUTPUT_ROOT/resume-hypic-piercing.lock"
if ! flock -n 9; then
  echo "another Hypic continuation controller owns the lock" >&2
  exit 75
fi
exec > >(tee -a "$OUTPUT_ROOT/resume-hypic-piercing.log") 2>&1

on_exit() {
  continuation_rc=$?
  trap - EXIT
  printf '%s controller_exit=%s\n' "$(date -Is)" "$continuation_rc"
  exit "$continuation_rc"
}
trap on_exit EXIT

echo "$(date -Is) controller_start wait_pid=${WAIT_PID:-none}"

{
  printf '%s  %s\n' 9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0 "$QUALITY_SCRIPT"
  printf '%s  %s\n' 12f0b2807127b1b58f2108b7bbb03687b4ee3603d037dcf8288a06b470d2b9c0 "$CANARY_SCRIPT"
  printf '%s  %s\n' c317127243ab93a9e2245754538e4907f9f62c80cf2c58658b394a4cec147518 "$PROFILE_SCRIPT"
  printf '%s  %s\n' 4653c1ec3e1b109fc35cd87a96e3d688cd8255b4caba9d84538d4ca8714f730e "$PROFILE_CLONE_SCRIPT"
} | sha256sum -c -

inspect_container() {
  inspected_container=$1
  expected_state=$2
  expected_hypic=$3
  python3 - "$inspected_container" "$expected_state" "$expected_hypic" <<'PY'
import json
import re
import subprocess
import sys

name, expected_state, expected_hypic = sys.argv[1:]
item = json.loads(subprocess.run(
    ["docker", "inspect", name],
    check=True,
    text=True,
    capture_output=True,
).stdout)[0]
state = item["State"]["Status"]
if state != expected_state:
    raise SystemExit(f"{name}: state={state!r}, expected {expected_state!r}")
cpuset = item["HostConfig"]["CpusetCpus"]
if cpuset != "112-191":
    raise SystemExit(f"{name}: cpuset={cpuset!r}, expected '112-191'")
devices = [
    entry["PathOnHost"]
    for entry in item["HostConfig"]["Devices"]
    if re.fullmatch(r"/dev/davinci\d+", entry["PathOnHost"])
]
expected_devices = [f"/dev/davinci{index}" for index in range(4)]
if devices != expected_devices:
    raise SystemExit(f"{name}: accelerator devices={devices!r}, expected {expected_devices!r}")
environment = dict(
    entry.split("=", 1)
    for entry in item["Config"].get("Env", [])
    if "=" in entry
)
hypic_enabled = environment.get("VLLM_ASCEND_HYPIC_ENABLE") == "1"
if expected_hypic == "enabled" and not hypic_enabled:
    raise SystemExit(f"{name}: VLLM_ASCEND_HYPIC_ENABLE is not 1")
if expected_hypic == "disabled" and hypic_enabled:
    raise SystemExit(f"{name}: HYPIC unexpectedly enabled")
print(json.dumps({
    "container": name,
    "container_id": item["Id"],
    "image": item["Image"],
    "state": state,
    "cpuset": cpuset,
    "accelerator_devices": devices,
    "hypic_enabled": hypic_enabled,
}, sort_keys=True))
PY
}

assert_npu03_process_ownership() {
  allowed_container=${1:-}
  python3 - "$allowed_container" <<'PY'
import re
import subprocess
import sys

allowed = sys.argv[1]
output = subprocess.run(
    ["npu-smi", "info"],
    check=True,
    text=True,
    capture_output=True,
).stdout
marker = "| NPU     Chip              | Process id"
if marker not in output:
    raise SystemExit("npu-smi process table marker not found")
process_table = output.split(marker, 1)[1]
observed = {}
for line in process_table.splitlines():
    match = re.match(r"^\|\s*([0-7])\s+\d+\s+\|\s+(\d+)\s+\|", line)
    if match:
        device, pid = map(int, match.groups())
        if device <= 3:
            observed.setdefault(device, set()).add(pid)
observed_pids = set().union(*observed.values()) if observed else set()
if not allowed:
    if observed_pids:
        raise SystemExit(f"NPU0-3 unexpectedly occupied: {observed!r}")
    print("NPU0-3 process ownership check passed; no processes")
    raise SystemExit(0)
top = subprocess.run(
    ["docker", "top", allowed, "-eo", "pid"],
    check=True,
    text=True,
    capture_output=True,
).stdout.splitlines()
container_pids = {int(line.strip()) for line in top[1:] if line.strip().isdigit()}
foreign = observed_pids - container_pids
if foreign:
    raise SystemExit(
        f"NPU0-3 has process(es) outside {allowed}: foreign={sorted(foreign)!r}, observed={observed!r}"
    )
if set(observed) != {0, 1, 2, 3}:
    raise SystemExit(f"expected one occupied process set on every NPU0-3 device: {observed!r}")
print(f"NPU0-3 process ownership check passed; allowed={allowed!r}, observed={observed!r}")
PY
}

wait_for_health() {
  health_deadline=$((SECONDS + 2400))
  until curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null; do
    if (( SECONDS >= health_deadline )); then
      echo "health timeout on port $PORT" >&2
      return 1
    fi
    sleep 10
  done
}

run_quality_phase() {
  quality_phase=$1
  quality_output="$OUTPUT_ROOT/quality/$quality_phase"
  mkdir -p "$quality_output"
  for quality_run in run1 run2 run3; do
    python3 "$QUALITY_SCRIPT" --dataset longbenchv2 --data /cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json --base-url "http://127.0.0.1:$PORT" --model "$MODEL_NAME" --output-dir "$quality_output" --run-id "$quality_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2
  done
  for quality_run in run1 run2 run3; do
    python3 "$QUALITY_SCRIPT" --dataset gsm8k --data /cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl --base-url "http://127.0.0.1:$PORT" --model "$MODEL_NAME" --output-dir "$quality_output" --run-id "$quality_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2
  done
}

verify_quality_phase() {
  quality_phase=$1
  python3 - "$OUTPUT_ROOT/quality/$quality_phase" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
expected = {"longbenchv2": 127, "gsm8k": 1319}
verified = {}
for dataset, count in expected.items():
    verified[dataset] = []
    for run_id in ("run1", "run2", "run3"):
        path = root / f"{dataset}.{run_id}.summary.json"
        data = json.loads(path.read_text())
        if data["successful"] != count or data["failed"] != 0:
            raise SystemExit(f"invalid summary {path}: successful={data['successful']} failed={data['failed']}")
        if data["data_sha256"] not in {
            "cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a",
            "3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14",
        }:
            raise SystemExit(f"unexpected dataset hash in {path}")
        if data["evaluator_script_sha256"] != "9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0":
            raise SystemExit(f"unexpected evaluator hash in {path}")
        verified[dataset].append({
            "run_id": run_id,
            "correct": data["correct"],
            "accuracy_pct": data["accuracy_pct"],
            "details_sha256": data["details_sha256"],
        })
print(json.dumps(verified, indent=2, sort_keys=True))
PY
}

container_state() {
  if inspected_state=$(docker inspect -f '{{.State.Status}}' "$1" 2>/dev/null) \
      && [[ -n "$inspected_state" ]]; then
    printf '%s\n' "$inspected_state"
  else
    printf 'absent\n'
  fi
}

verify_profile_phase() {
  profile_phase=$1
  profile_container=$2
  python3 - "$OUTPUT_ROOT/profiles/$profile_phase/profile-manifest.json" "$profile_phase" "$profile_container" <<'PY'
import hashlib
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
phase = sys.argv[2]
container = sys.argv[3]
data = json.loads(path.read_text())
if data["phase"] != phase or data["container"] != container:
    raise SystemExit(f"profile identity mismatch in {path}")
if data["profiler_exit_code"] != 0:
    raise SystemExit(f"profiler failure recorded in {path}")
if data["workload_exit_code"] != 0:
    capture = data.get("profile_capture_stimulus")
    observed = capture.get("observed") if isinstance(capture, dict) else None
    capture_ok = (
        phase == "pdc-hypic"
        and data["workload_exit_code"] == 1
        and isinstance(capture, dict)
        and capture.get("verified") is True
        and capture.get("algorithm_acceptance_derived_from_this_gate") is False
        and isinstance(observed, dict)
        and observed.get("configured_requests") == 4
        and observed.get("summary_requests") == 4
        and observed.get("successful") == 4
        and observed.get("failed") == 0
        and observed.get("fixed_output_verified") is True
        and observed.get("result_count") == 4
        and observed.get("all_measured_results_ok") is True
    )
    if not capture_ok:
        raise SystemExit(f"profile capture stimulus failure recorded in {path}")
if data["host_accelerator_devices"] != [f"/dev/davinci{i}" for i in range(4)]:
    raise SystemExit(f"profile device isolation mismatch in {path}")
if not data["profile_files"]:
    raise SystemExit(f"profile has no files: {path}")
for item in data["profile_files"]:
    artifact = pathlib.Path(item["path"])
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if not artifact.is_file() or artifact.stat().st_size != item["size_bytes"]:
        raise SystemExit(f"profile artifact mismatch: {artifact}")
    if digest != item["sha256"]:
        raise SystemExit(f"profile hash mismatch: {artifact}")
print(f"{path}: OK")
PY
}

profile_phase_with_clone() {
  profile_source=$1
  profile_clone=$2
  expected_hypic=$3
  profile_phase=$4

  if verify_profile_phase "$profile_phase" "$profile_clone" 2>/dev/null; then
    echo "$(date -Is) verified existing profile phase=$profile_phase"
    for profile_cleanup in "$profile_source" "$profile_clone"; do
      if [[ $(container_state "$profile_cleanup") == running ]]; then
        inspect_container "$profile_cleanup" running "$expected_hypic"
        assert_npu03_process_ownership "$profile_cleanup"
        docker stop --time 60 "$profile_cleanup"
      fi
    done
    assert_npu03_process_ownership ""
    return
  fi

  profile_phase_root="$OUTPUT_ROOT/profiles/$profile_phase"
  if [[ -e "$profile_phase_root" || -L "$profile_phase_root" ]]; then
    profile_parent=$(realpath "$OUTPUT_ROOT/profiles")
    if [[ $(realpath "$(dirname "$profile_phase_root")") != "$profile_parent" ]]; then
      echo "refusing to archive profile path outside output root" >&2
      return 1
    fi
    profile_archive="${profile_phase_root}-failed-$(date -u +%Y%m%dT%H%M%SZ)"
    if [[ -e "$profile_archive" || -L "$profile_archive" ]]; then
      echo "profile archive already exists: $profile_archive" >&2
      return 1
    fi
    mv -- "$profile_phase_root" "$profile_archive"
    echo "$(date -Is) archived invalid profile phase=$profile_phase path=$profile_archive"
  fi

  source_state=$(container_state "$profile_source")
  if [[ "$source_state" == running ]]; then
    inspect_container "$profile_source" running "$expected_hypic"
    assert_npu03_process_ownership "$profile_source"
    docker stop --time 60 "$profile_source"
    inspect_container "$profile_source" exited "$expected_hypic"
    assert_npu03_process_ownership ""
  elif [[ "$source_state" != exited ]]; then
    echo "unexpected source state for $profile_source: $source_state" >&2
    return 1
  fi

  clone_state=$(container_state "$profile_clone")
  if [[ "$clone_state" == running ]]; then
    inspect_container "$profile_clone" running "$expected_hypic"
    assert_npu03_process_ownership "$profile_clone"
    docker stop --time 60 "$profile_clone"
    assert_npu03_process_ownership ""
  elif [[ "$clone_state" != absent && "$clone_state" != created && "$clone_state" != exited ]]; then
    echo "unexpected profile clone state for $profile_clone: $clone_state" >&2
    return 1
  fi

  python3 "$PROFILE_CLONE_SCRIPT" \
    --source "$profile_source" \
    --clone "$profile_clone" \
    --expected-hypic "$expected_hypic"
  assert_npu03_process_ownership ""
  docker start "$profile_clone"
  wait_for_health
  inspect_container "$profile_clone" running "$expected_hypic"
  assert_npu03_process_ownership "$profile_clone"
  python3 "$PROFILE_SCRIPT" \
    --container "$profile_clone" \
    --phase "$profile_phase" \
    --output-root "$OUTPUT_ROOT/profiles" \
    --duration 300
  verify_profile_phase "$profile_phase" "$profile_clone"
  inspect_container "$profile_clone" running "$expected_hypic"
  assert_npu03_process_ownership "$profile_clone"
  docker stop --time 60 "$profile_clone"
  inspect_container "$profile_clone" exited "$expected_hypic"
  assert_npu03_process_ownership ""
}

verify_treatment_canary() {
  python3 - "$OUTPUT_ROOT/pdc-hypic/active_semantic_canary_reproducible.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
if not data["answer_contains_key"]:
    raise SystemExit("treatment active semantic canary answer failed")
if data["prompt_token_sha256"] != "2f755435529f63b255cdfe3248b625c0aacf76986919debe43715138ea1dc844":
    raise SystemExit("treatment canary prompt ruler mismatch")
if data["public_segment_token_sha256"] != "91c13332ac4a7f80ea082d8a84aeb4222a11a7407883fbee67931659b71c39e4":
    raise SystemExit("treatment canary public segment ruler mismatch")
print("treatment active semantic canary verified")
PY
}

if (( SELF_TEST )); then
  inspect_container "$TREATMENT_CONTAINER" exited enabled
  if [[ $(container_state "$BASELINE_CONTAINER") == running ]]; then
    inspect_container "$BASELINE_CONTAINER" running disabled
    assert_npu03_process_ownership "$BASELINE_CONTAINER"
    wait_for_health
  else
    inspect_container "$BASELINE_CONTAINER" exited disabled
    assert_npu03_process_ownership ""
  fi
  printf '%s  %s\n' 9193e45cf414bcb380676bdc872b0e59063166e90e6fcff52a73d478c59e3cbc "$OUTPUT_ROOT/pdc-baseline/active_semantic_canary_reproducible.json" | sha256sum -c -
  echo "controller self-test passed; no workload or container state changed"
  exit 0
fi

if [[ -n "$WAIT_PID" ]] && kill -0 "$WAIT_PID" 2>/dev/null; then
  echo "$(date -Is) waiting for existing baseline chain pid=$WAIT_PID"
  while kill -0 "$WAIT_PID" 2>/dev/null; do
    sleep 30
  done
fi
while pgrep -af '[h]ypic_quality_eval.py' >/dev/null; do
  echo "$(date -Is) waiting for existing quality evaluator"
  sleep 30
done

inspect_container "$TREATMENT_CONTAINER" exited enabled

echo "$(date -Is) resume/verify baseline quality"
if ! verify_quality_phase pdc-baseline; then
  inspect_container "$BASELINE_CONTAINER" running disabled
  assert_npu03_process_ownership "$BASELINE_CONTAINER"
  wait_for_health
  run_quality_phase pdc-baseline
  verify_quality_phase pdc-baseline
fi

printf '%s  %s\n' 9193e45cf414bcb380676bdc872b0e59063166e90e6fcff52a73d478c59e3cbc "$OUTPUT_ROOT/pdc-baseline/active_semantic_canary_reproducible.json" | sha256sum -c -

echo "$(date -Is) baseline profile-only clone"
profile_phase_with_clone \
  "$BASELINE_CONTAINER" \
  "$BASELINE_PROFILE_CONTAINER" \
  disabled \
  pdc-baseline

if verify_treatment_canary >/dev/null 2>&1 \
    && verify_quality_phase pdc-hypic >/dev/null 2>&1 \
    && verify_profile_phase pdc-hypic "$TREATMENT_PROFILE_CONTAINER" >/dev/null 2>&1; then
  inspect_container "$TREATMENT_CONTAINER" exited enabled
  inspect_container "$TREATMENT_PROFILE_CONTAINER" exited enabled
  assert_npu03_process_ownership ""
  echo "$(date -Is) controller_complete_existing_evidence"
  exit 0
fi

inspect_container "$TREATMENT_CONTAINER" exited enabled
docker start "$TREATMENT_CONTAINER"
wait_for_health
inspect_container "$TREATMENT_CONTAINER" running enabled
assert_npu03_process_ownership "$TREATMENT_CONTAINER"

echo "$(date -Is) treatment active semantic canary"
if ! verify_treatment_canary 2>/dev/null; then
  python3 "$CANARY_SCRIPT" --base-url "http://127.0.0.1:$PORT" --model "$MODEL_NAME" --phase pdc-hypic --output "$OUTPUT_ROOT/pdc-hypic/active_semantic_canary_reproducible.json" --timeout 2400
  verify_treatment_canary
fi

echo "$(date -Is) treatment quality"
if ! verify_quality_phase pdc-hypic; then
  run_quality_phase pdc-hypic
fi
verify_quality_phase pdc-hypic

inspect_container "$TREATMENT_CONTAINER" running enabled
assert_npu03_process_ownership "$TREATMENT_CONTAINER"
docker stop --time 60 "$TREATMENT_CONTAINER"
inspect_container "$TREATMENT_CONTAINER" exited enabled
assert_npu03_process_ownership ""
echo "$(date -Is) treatment profile-only clone"
profile_phase_with_clone \
  "$TREATMENT_CONTAINER" \
  "$TREATMENT_PROFILE_CONTAINER" \
  enabled \
  pdc-hypic
echo "$(date -Is) controller_complete"
