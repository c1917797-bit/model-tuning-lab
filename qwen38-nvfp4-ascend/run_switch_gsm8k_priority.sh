#!/usr/bin/env bash
# Run GSM8K first on the existing owned quality service; restore the paused client.
set -Eeuo pipefail
source_run="${1:?source run}"
out="${2:?fresh output directory}"
model_id="${3:?exact model container id}"
client_id="${4:?exact MMLU client container id}"
[[ "$source_run" == /cache/austinov/eval-runs/switch12h-* && "$out" == /cache/austinov/eval-runs/gsm8k-priority-* ]] || exit 64
[[ "$model_id" =~ ^[0-9a-f]{64}$ && "$client_id" =~ ^[0-9a-f]{64}$ ]] || exit 64
[[ -d "$out" && ! -e "$out/status.json" ]] || exit 65
[[ "$(cat "$source_run/container.id")" == "$model_id" ]] || exit 65
[[ "$(cat "$source_run/quality-full.container.id")" == "$client_id" ]] || exit 65
code="$(cd "$(dirname "$0")" && pwd)"
image=quay.io/ascend/vllm-ascend@sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a
paused=false
cleanup() {
 rc=$?; trap - EXIT INT TERM
 if [[ -f "$out/evaluator.id" ]]; then
  own="$(cat "$out/evaluator.id")"
  if [[ "$own" =~ ^[0-9a-f]{64}$ ]] && docker inspect "$own" >/dev/null 2>&1; then
   docker logs --timestamps "$own" > "$out/evaluator.final.log" 2>&1 || true
   docker stop --time 30 "$own" >> "$out/cleanup.log" 2>&1 || true
  fi
 fi
 if $paused && [[ "$(docker inspect -f '{{.State.Paused}}' "$client_id" 2>/dev/null)" == true ]]; then
  docker unpause "$client_id" >> "$out/cleanup.log" 2>&1 || rc=71
 fi
 printf '{"exit_code":%s,"finished_utc":"%s"}\n' "$rc" "$(date -u +%FT%TZ)" > "$out/status.json"
 exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT TERM
docker inspect "$model_id" > "$out/model.inspect.json"
docker inspect "$client_id" > "$out/client.before.inspect.json"
python3 - "$source_run" "$out" <<'PY'
import json,sys
from pathlib import Path
source,out=map(Path,sys.argv[1:])
model=json.loads((out/'model.inspect.json').read_text())[0]
client=json.loads((out/'client.before.inspect.json').read_text())[0]
initial=json.loads((source/'service.start.inspect.json').read_text())[0]
image=json.loads((source/'image.inspect.json').read_text())[0]
assert model['Image']==client['Image']==image['Id']
assert model['Config']==initial['Config']
assert {x['Destination']:x for x in model['Mounts']}=={x['Destination']:x for x in initial['Mounts']}
assert model['State']['Running'] and not model['State']['Paused']
assert client['State']['Running'] and not client['State']['Paused']
assert not client['HostConfig']['Privileged'] and not client['HostConfig']['Devices']
assert any(x['Destination']=='/output' and x['Source']==str(source) for x in client['Mounts'])
assert any(x['Destination']=='/model' and x['Source']=='/cache/austinov/Qwen3.8-27B' and not x['RW'] for x in model['Mounts'])
assert 'Qwen/Qwen3.8-27B' in client['Config']['Cmd']
assert json.loads((source/'server-profile.json').read_text())==dict(gpu_memory_utilization=.75,max_num_batched_tokens=2048,stage='quality-full')
PY
sha256sum -c "$source_run/inputs.sha256" > "$out/input-check.log"
sha256sum -c "$source_run/evaluator.sha256" > "$out/evaluator-check.log"
cp "$source_run/image.inspect.json" "$source_run/inputs.sha256" "$source_run/evaluator.sha256" "$source_run/server-profile.json" "$source_run/models.json" "$out/"
sha256sum "$code/run_switch_gsm8k_priority.sh" > "$out/controller.sha256"
docker pause "$client_id"
paused=true
# Drain only in-flight requests; no parallel scoring or performance measurement.
python3 - <<'PY'
import time,urllib.request
for attempt in range(60):
 with urllib.request.urlopen('http://127.0.0.1:10010/metrics',timeout=5) as r:
  lines=r.read().decode().splitlines()
 gauges=[float(x.rsplit(' ',1)[1]) for x in lines if x.startswith(('vllm:num_requests_running{','vllm:num_requests_waiting{'))]
 if len(gauges)==2 and sum(gauges)==0: break
 time.sleep(2)
else: raise RuntimeError('Existing requests failed to drain')
PY
printf '{"phase":"gsm8k","state":"running","started_utc":"%s"}\n' "$(date -u +%FT%TZ)" > "$out/status.json"
docker run --cidfile "$out/evaluator.id" --rm --network host --read-only --cap-drop ALL --security-opt no-new-privileges  --cpus 4 --memory 8g --tmpfs /tmp:rw,size=2g  -e PYTHONDONTWRITEBYTECODE=1 -e HF_HUB_OFFLINE=1 -e HF_DATASETS_OFFLINE=1 -e TORCH_DEVICE_BACKEND_AUTOLOAD=0  -e HF_HOME=/tmp/hf -e PYTHONPATH=/cache/austinov/eval-tools/lm-evaluation-harness-v0.4.13  -v /cache/austinov/eval-tools:/cache/austinov/eval-tools:ro  -v /cache/austinov/eval-data/general:/data:ro -v "$code:/code:ro"  -v /cache/austinov/Qwen3.8-27B:/tokenizer:ro -v "$out:/output"  --entrypoint /cache/austinov/eval-tools/lm-eval-v0.4.13-venv/bin/python "$image"  /code/run_standard_text_quality.py --harness /cache/austinov/eval-tools/lm-evaluation-harness-v0.4.13  --data-root /data --tokenizer /tokenizer --model Qwen/Qwen3.8-27B  --base-url http://127.0.0.1:10010/v1/completions --output /output/gsm8k  --tasks gsm8k --concurrency 8 > "$out/gsm8k.log" 2>&1 &
child=$!
while kill -0 "$child" 2>/dev/null; do
 [[ "$(docker inspect -f '{{.State.Running}}' "$model_id" 2>/dev/null)" == true ]] || exit 70
 [[ "$(docker inspect -f '{{.State.Paused}}' "$client_id" 2>/dev/null)" == true ]] || exit 70
 sleep 5
done
wait "$child"
