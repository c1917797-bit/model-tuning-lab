# Exact bounded pair evidence interface

All references are ordinary absolute `{path,bytes,sha256}` Ref3 values. No placeholder Ref is accepted. `prepare_native_ar_pair.py` creates the actual AR source from the frozen actual G1 ON source and actual ON server command. Its output `SOURCE_BOUND.json` is a new source closure, not a model result. It requires an explicitly supplied current authority and actual immutable image ID.

The actual model/tokenizer manifest has schema `bole.actual-model-tokenizer-file-manifest/v1`, `model_root='/models/Qwen3.6-27B'`, and a nonempty `files` list of exact actual model and tokenizer Refs. The independent consumer reopens those files; MAIN must include them in the Devices[] readset. Large immutable model files are inputs, not newly produced raw capture evidence.

The frozen actual input Ref is the existing G1 `INPUTS.json`: source equals the actual BOLE source, `input_tokens=131`, `tokenizer='/models/Qwen3.6-27B'`, `data_generated_by_actual_tokenizer=True`, and the exact `token_ids` list. Both collectors use that single Ref.

## Native AR host bundle

Schema `bole.actual-four-rank-native-ar-inputs/v1`:

- `source`: actual newly bound AR source Ref.
- `http`: actual `pair_entry.py` native AR `HTTP_RESULT.json` Ref, schema `bole.actual-native-ar-smoke-HTTP/v1`.
- `journal`: all actual original `IDENTITY-frontend-*` and `IDENTITY-rank0..3-*` journal Refs, complete contiguous per-process ordinals.
- `snapshots`: actual decoded `NATIVE-AR-SNAPSHOT-RANK-0..3.json` documents.
- `snapshot_refs`: those four exact original snapshot Refs in rank order.
- `host_bindings`: four independently owned host/NSpid bindings to those guest snapshot documents; `host.physical` is exactly the original actual owned set4/5/6/7. No new ownership flag substitutes for the existing controller proof.
- `frontend_binding`: the actual original assignment frontend guest identity and its independently consumed host/NSpid/CID binding.
- `ranks`: four rank-ordered `{raw,receipt}` pairs, exact `NATIVE-AR-RANK-n.pt/.json` filenames in the source-declared sole-owned receipt root.
- `docker_inspect_ref`: the actual unmodified single-container `docker inspect` JSON array Ref. Its `.Image` must equal the frozen actual immutable image ID.
- `server_command_ref`: the actual AR `SERVER_COMMAND.json` Ref.
- `model_manifest_ref`: the exact shared model/tokenizer manifest Ref.
- `launch_profile_ref`: actual owned frontend environment receipt from `launch_profile.py`, schema `bole.actual-pair-launch-profile/v1`.

The native exporter payload schema is `bole.actual-native-ar-smoke-rank/v1`, primitive export schema `bole.model-diagnostic-primitives/v1`. The observer's source defines every field. Two request items retain actual request/generation/object IDs, prompt IDs, two original native samples, all16 actual decode FA frames and exact native retirement. The raw source/installed readsets are rechecked unchanged at freeze. Native speculative config is null and all intervention/ready flags are false.

## BOLE bundle

Use the existing complete qualified G1 bundle schema `bole.actual-four-rank-two-request-inputs/v1`, with its original exact `source,http,journal,snapshots,host_bindings,ranks,frontend_binding`. Add only the non-mutating extra actual refs `docker_inspect_ref`, `server_command_ref`, `model_manifest_ref`, and `launch_profile_ref` in a **new** bundle file. The original frozen G1 bundle and sources remain unchanged.

The BOLE collector uses original G1 headers `bole-g1-131-tree-1`, `...tree-2`, `...retirement-barrier`; AR uses `bole-native-ar-131-` with the same labels and budgets. The extra collector metadata does not alter the original G1 mathematical consumer. `consume_pair.py` re-runs that source-bound complete gate in a fresh independent CPU child and consumes its newly generated attribution.

## Outer ledger and invocation

`assemble_pair_inputs.py` writes schema `bole.actual-native-ar-bole-pair-inputs/v1` with `source`, exact `scope` from `pair_contract.SCOPE`, native `native_AR` bundle Ref, existing `BOLE` bundle Ref and `inputs_ref`.

Actual execution arguments are explicit JSON Refs:

```text
pair_entry.py --execute --source-ref <actual AR source Ref3 JSON> --variant native_AR|BOLE
  --variant-source-ref <actual variant source Ref3 JSON>
  --inputs-ref <same actual G1 INPUTS Ref3 JSON> --output <owned precreated variant leaf>
  --base-url http://127.0.0.1:8230

consume_pair.py --execute --source-ref <actual AR source Ref3 JSON>
  --inputs-ref <actual outer ledger Ref3 JSON> --output <source-bound precreated CPU output leaf>
```

The consumer must run with Devices[], no `/dev/davinci*`, `ASCEND_RT_VISIBLE_DEVICES=''`, `TORCH_DEVICE_BACKEND_AUTOLOAD=0`. These instructions do not create or authorize that runtime.

`launch_profile.py --execute` requires the pair source, variant, exact actual owned frontend PID/start/cgroup Ref and output path. It can run in the matching namespace or on the owned host; the consumer joins the resulting identity to the independently consumed frontend binding. It does not authenticate a new host or read an arbitrary unbound PID.

## Deliberate remaining admission gaps

No actual same-image source/metadata/instance guard test, native operator execution, actual paired evidence or plugin-effect review is included. Actual PA/FIA schema families are retained when available; omitted defaults are not synthesized. `native_AR_reference_smoke_pass` is only the observed bounded identity/native-frame gate. `bounded_pair_pass` remains false pending separate exact source review of the different ON/OFF plugin effects. This packet does not contain or certify a G2 streaming reader.
