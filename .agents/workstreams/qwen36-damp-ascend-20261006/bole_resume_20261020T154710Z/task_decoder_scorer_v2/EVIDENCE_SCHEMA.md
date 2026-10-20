# Evidence routing

All Refs are exact `{path, bytes, sha256}` objects with absolute ordinary file paths and whole stable bytes. Ref JSON goes directly to the corresponding CLI argument. No caller-supplied pass/owner callback substitutes for raw evidence. No existing source, data, cutoff or score is overwritten.

## Preparation and actual CPU software smoke

1. `prepare_packet.py --prepare --authority-ref <new Ref> --rendered-inputs-ref <actual011 Ref> --image-id sha256:... --output <new SOURCE.json>` creates the immutable unbound new source. A new authority JSON needs numeric `start_epoch` / `cutoff_epoch`; both old authority hashes are explicitly rejected. MAIN supplies and records the new admission authority; this packet does not manufacture one. All executable files, frozen function copies, actual first-row fixtures and PROTOCOL.json are source-bound.
2. `restore_GSM_inputs.py --execute --source-ref <unbound Ref> --output <new absent directory>` checks every old row and restores existing original GSM IDs. No tokenizer is called. It emits `EFFECTIVE_INPUTS.json`; all original and011 inputs remain unchanged. This step can fail if any of the other1318 rows differs from the proposed constant insertion: that is a real failure, not permission to alter the parser or baseline.
3. `prepare_packet.py --bind-inputs --source-ref <unbound Ref> --effective-inputs-ref <actual new Ref> --output <new SOURCE_INPUTS_BOUND.json>` replays the complete derivation. The new bound source contains `input_preparation_source_ref`; the original preparation source is immutable and must equal the bound source with only its two input-binding fields reset to null.
4. In MAIN's owned **same immutable image / Devices[] CPU** runtime, `decoder.py --software-smoke --source-ref <bound Ref> --output <new decoder.json>` imports the real original tokenizer, verifies all7 assets plus recorded library files and versions, decodes the actual12-token instruction, replays all official source/gold/templates over1319/164/14042 rows, and executes synthetic decoding/parser controls. It does not encode/re-render any benchmark prompt. CPU Torch utility imports may occur; accelerator/inference backends and device FDs remain forbidden. Full CPU-owner/image evidence is a separate MAIN integration: the report keeps `same_image_owner_verified=false` until joined externally.
5. `stage_he.py --prepare --source-ref <bound Ref> --kind controls --container-name bole-he-... --output <new absent public stage>` copies only public exact official package bytes and source/inputs, sets readable modes explicitly despite umask, and prints exact `docker create` argv. It does not create/start/stop a container. MAIN must launch with its real owner, capture create argv/CID/wait/inspect/stdout and retain lifecycle evidence. `--preflight` is also available on the dedicated worker; the generated controls use `--controls`.
6. `consume_results.py --execute --source-ref <bound Ref> --decoder-smoke-ref <actual decoder Ref> --he-stage-ref <stage Ref> --he-owner-ref <actual owner Ref> --output <new result>` independently repeats actual tokenizer/provenance checks and consumes all actual sandbox evidence. Controls cannot produce task scores.

## Future actual model output records

`request_plan.py --prepare --source-ref <bound Ref> --phase smoke|full --arm OFF|ON --model <same served name> --output <new absent directory>` writes prompt-only JSONL plans and metadata. It sends no requests. Smoke is exactly2 fixed cases per task, in fixed task/order; full is1319/164/14042. Concurrency is1. Minimum context is5199. A task-aware native/BOLE model client and actual worker activation/EOS/retirement capture must be integrated by MAIN before these plans are executed; none is silently borrowed from the bounded131-token service.

Actual task client output must create a manifest:

```json
{
  "schema":"bole.actual-three-task-HTTP-completions/v1",
  "source_ref":{"path":"/.../SOURCE_INPUTS_BOUND.json","bytes":0,"sha256":"..."},
  "effective_inputs_ref":{"path":"/.../EFFECTIVE_INPUTS.json","bytes":0,"sha256":"..."},
  "phase":"smoke",
  "arm":"OFF",
  "model":"actual-served-name",
  "records":[{"task":"GSM8K","id":"gsm8k-test-0000","request_ref":{"path":"/.../request.json","bytes":0,"sha256":"..."},"response_ref":{"path":"/.../response.json","bytes":0,"sha256":"..."}}]
}
```

The illustrated sizes/hashes/partial records are schema placeholders, not evidence. The real record list must cover every selected case exactly once, ordered GSM8K / HumanEval / MMLU.

- Request file: `{"request_id":"actual-client-id","body":{...}}`. Body must exactly equal `score_tokens.request_body(row, model)` including JSON types: exact full frozen integer prompt IDs; max_tokens2048; ignore_eos false; temperature0; top_p1; seed0; n1; stream false; return_token_ids true. No gold, tests, forced/minimum tokens, extra stop policy or prompt repair.
- Response file: `{"status":200,"request_id":"same-actual-client-id","body":{...actual unmodified JSON body...}}`. The actual body needs a nonempty `id`, exact model, one index0 choice with actual `token_ids`, text and finish_reason, and usage. Preserve the raw wire/headers/HTTP client owner evidence as well: this compact envelope alone does not prove native-worker identity. The reader records frontend completion ID and explicitly leaves its worker join false.
- Returned IDs are never inferred by encoding text. Usage must equal whole IDs/prompt counts; independent real decode must equal server text. EOS248046, when returned, must be last and use stop reason. Length requires actual2048 IDs. An early stop may legitimately omit EOS from returned IDs: the native EOS cause remains unproved until joined. Length/capped cases are retained and explicitly counted; no case is dropped or relabelled as a naturally completed sequence.

`score_tokens.py --execute --source-ref <bound Ref> --raw-ref <actual manifest Ref> --output <new grades>` decodes and computes GSM/MMLU component grades; it retains every raw text, hash, complete row/source/raw Ref, finish type and HE transformation. It does not execute code. Stage HE using `stage_he.py --prepare ... --kind tasks --grades-ref <actual grades Ref>`; the stage independently recomputes grades before copying exact transformed completions and unchanged official tests. Launch the printed argv with MAIN's actual sandbox owner. `consume_results.py` adds `--grades-ref <actual grades Ref>` and independently recomputes grades again before consuming the official HE result rows. The full reader emits component scores only; all model/formal/lifecycle flags remain false.

## Actual sandbox owner record

```json
{
  "schema":"bole.actual-HE-sandbox-owner-evidence/v1",
  "stage_ref":{"path":"/.../STAGE.json","bytes":0,"sha256":"..."},
  "name":"bole-he-unique-name",
  "container_id":"actual-64-hex-ID",
  "create_argv_ref":{"path":"/.../argv.json","bytes":0,"sha256":"..."},
  "created_id_ref":{"path":"/.../docker-create.stdout","bytes":0,"sha256":"..."},
  "inspect_ref":{"path":"/.../docker-inspect.json","bytes":0,"sha256":"..."},
  "wait_ref":{"path":"/.../docker-wait.stdout","bytes":0,"sha256":"..."},
  "stdout_ref":{"path":"/.../actual-combined-log.txt","bytes":0,"sha256":"..."}
}
```

The argv file is the exact JSON string array passed to Docker; created_id/wait are actual plain stdout. Inspect is the final raw one-element Docker inspect array after completion and before owner cleanup. Owner should retain its actual command results, timing, PID/lease/stop-retain trail too; this reader does not invent the host ownership lease. Worker stdout has one `BOLE_HE_OFFICIAL_V1 ` marker. Reader checks exact actual ID, immutable image, name, env-i command, runc, uid, no network/devices/privileges, private IPC/PID, memory/CPU/PID/FD/file limits, tmpfs, only3 exact read-only public mounts, final exit0/non-OOM, source/package/input closure, exact completion strings and complete rows. A marker without those raw owner records fails.

## Full paired numerical comparison

`compare_components.py --execute --source-ref <same bound Ref> --off-ref <actual full independent OFF result Ref> --on-ref <actual full independent ON result Ref> --output <new comparison>` reopens both complete component results and their evidence. All three tasks must satisfy both <=1 percentage-point drop and <=1% relative drop. Exact integer count comparisons avoid rounding. OFF_correct=0 gives an undefined relative comparison and no pass. This deliberately remains `formal_task_accuracy_accepted=false`: actual same model/stack/input/concurrency/common effects, every-request BOLE activation, native reference, worker EOS/retirement, CPU-image owner join and any other current authority gates remain necessary outside this numerical component.


V2 constructor source delta: SOURCE schema is bole.three-task-decoder-scorer/source/v2, with decoder_constructor_protocol=transformers-public-TokenizersBackend.from_pretrained/v2. files includes DECODER_CONSTRUCTOR.json, frozen/decoder_v1.py and the exact frozen/original_packet_manifest.json. All other input/scorer/sandbox/reader Python hashes must match the preserved original manifest. Actual decoder identity adds constructor_protocol, constructor_source_ref, original_input_and_scorer_semantics_changed=false. The new public factory source/class/code-object checks precede actual construction; all seven source Refs are reopened before and after it. All prior complete coverage, sandbox and independent-readback gates remain mandatory. Diagnostic-only CPU receipts do not satisfy full software qualification. V1 CPU/HTTP source schemas are not silently accepted. No v2 source has been actually qualified by this advisory packet.
