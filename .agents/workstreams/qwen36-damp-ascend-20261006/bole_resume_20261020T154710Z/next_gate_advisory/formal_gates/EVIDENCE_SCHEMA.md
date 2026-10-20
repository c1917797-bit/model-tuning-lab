# Evidence contract, version 1 — advisory

Every Ref3 is `{path:absolute ordinary file,bytes:integer,sha256:64 lowercase hex}`.
The consumer reopens/hashes references. Content matching permits a different
mount path only when byte count and SHA256 match. JSON uses unique keys and no
NaN/Infinity. No example below is a measured result.

## Top-level manifest: bole.formal-evidence/v1

- `policy`: Ref3 of the fully populated prospective policy, prepared_only=false.
- `protocols`: map from both exact protocol filenames to their Ref3s.
- `workload`: Ref3 of `bole.formal-workload/v1`.
- `model_qualification`: proof entry for candidate_source.
- `composition_qualification`: proof entries for actual component source Refs
  when composition applies.
- `runs`: entries `{record:Ref3,proofs:{runtime,lineage,activation,resources}}`.
  The run record is `bole.formal-perf-run/v1`; exactly rounds 1,2,3 and the
  declared variants (OFF/ON, or D/A/B/A+B) must appear once each.
- `tasks`: entries `{record:Ref3,proofs:{runtime,lineage,activation,resources,
  prompt_render,task_score}}` for each task, baseline/final variant, smoke/full.

## Source freeze and common stack

Each run/task record has `source_packet`, `stack`, `feature_profile`,
`candidate_source`, `started_epoch_ns`, `finished_epoch_ns` and `clock` Refs/
times. `bole.formal-source/v1` contains the exact `policy`, `current_authority`,
`candidate_source`, `stack`, `feature_profile`, `purpose`, `variant`,
`created_epoch_ns` and, for performance, `workload`. The actual source-bound
owner runtime validator must prove this packet was frozen before launch and
was unchanged after cleanup. The lightweight reader checks those identities
and chronology; it never rewrites historical campaign deadlines.

`bole.formal-common-stack/v1` fixes image, model type/config hash, full weights
manifest (not config-only), tokenizer, native libraries/driver/precision,
server settings, actual TP4 physical mapping, CPU placement and all common
optimizations. Delivery is plugin/monkeypatch with base_image_changed=false,
training=false, distillation=false. Actual runtime proof must match this stack,
including current full checkpoint identity. Variant-specific feature profiles
are `bole.formal-feature-profile/v1` with `variant`,
`expect_bole_decode` (`all`, `none`, `component-only`) and
`required_components` (actual named components for a composition variant).

## Workload and streaming records

`bole.formal-workload/v1`: `concurrency` positive integer, `arrival_policy` =
closed_loop, `measured_requests` and nonempty `warmup_requests` arrays. Each
request has unique `request_key`, actual `prompt_token_ids`, `request_body`
Ref3 of the entire prospectively frozen HTTP body, and a declared
fixed-1024 generation profile (shared by every variant).

`bole.formal-perf-run/v1` adds `round_id`, `variant`, `workload`, `request_records`
(Ref3 array, exact workload dispatch order), `warmup_records` (Ref3 array), plus
the common source fields above. Every stream request is
`bole.formal-stream-request/v1`: `phase` (measured/warmup), `request_key`,
`engine_request_id`, `response_id`, `request_body` Ref3, `raw_stream` Ref3,
`clock` Ref3, `submit_ns`, `end_ns`, `http_status`, `error`, `done_received`,
`finish_reason`, `prompt_token_ids`, `final_output_token_ids`, `usage`, and
`events`. Events have contiguous ordinal, received_ns, response_id,
choice_index=0, token_ids delta list. Empty chunks are valid but do not start
TTFT. The lineage reader must independently parse the retained raw SSE bytes
and join actual response/frontend/engine/TP4 worker identities, not trust the
canonical events alone.

The actual performance request body has prompt token IDs, max_tokens=1024,
ignore_eos=true, stream=true, return_token_ids=true, n=1, temperature=0, top_p=1.
Exactly 1024 real delta token IDs and a complete stream are required. Actual
maximum in-flight measured requests must equal declared concurrency. Warmups
must complete before the first measured submit and are excluded from timing.

## Activation proof result payload

`rows` contains exactly every request (including warmups, or every task case),
with `request_key`, `phase`, `engine_request_id`, and `ranks` exactly 0..3.
Each rank has `required_decode_inputs`, `bole_processed_inputs`,
`native_processed_inputs`, `unattributed_decode_inputs`, `tree_steps`, and
`component_calls` map. Counts must account for every actual decode input.
For fixed1024 performance, required_decode_inputs=1023; final ON/A+B requires
all1023 through BOLE, native/unattributed=0, tree_steps>0. Baseline OFF/D has
BOLE=0 and native=1023. For tasks the independent activation reader derives
required counts from real native token/counter/retirement traces, including
EOS accounting; zero-decode requests are explicitly ineligible, not falsely
called inactive fallbacks. All declared required components must have actual
positive calls on eligible requests.

## Full and smoke tasks

`bole.formal-task-run/v1` adds `task`, `variant`, `stage` (smoke/full),
`dataset_manifest`, `prompt_policy`, `generation_profile`, `outputs` Ref3 array,
`score_items` Ref3, `smoke_record` Ref3 for full runs, `concurrency`, and the
common source fields. Only baseline OFF/D and final ON/A+B are required for
the full task union; intermediate A/B measurement alone does not invent
extra task-loss requirements.

The task launch source packet also pins dataset_manifest, prompt_policy,
generation_profile, scorer_source and, for full runs, the already consumed
smoke_record Ref3 before inference. The actual body of every case must equal
the complete frozen prompt-record request_body, not just match max_tokens.

`bole.formal-task-dataset/v1`: `task`, `official_source` and `source_revision`,
`split`, `complete_declared_split=true`, `cases`, `smoke_case_ids`,
`official_snapshot` Ref3, `scorer_source` Ref3 and `metric`. Each case has
`case_id`, `source_item` Ref3, `gold` Ref3, `prompt_record` Ref3 and
`metric_weight:{n,d}`. Each `bole.formal-prompt/v1` has task, case_id, actual
token_ids and a request_body Ref3 of the complete frozen HTTP body. Per-case
prompt files avoid enormous central long-context JSON documents.
The approved scorer/data validator proves the complete
official split and actual metric; the final reader enforces exact once-only
coverage and rational weighted arithmetic, including frozen subject weights.

`generation_profile`: `thinking=false`, `max_tokens=2048`, `normal_eos=true`,
`temperature=0`, `top_p=1`, `n=1`, `stop=[]`, `stop_token_ids=[]`,
`return_token_ids=true`. The prompt-render reader joins actual tokenizer/chat
template controls (thinking disabled) and final token IDs. It must not strip
thought text as a substitute for disabling thinking.

Each `bole.formal-task-output/v1`: `case_id`, `request_key`,
`engine_request_id`, `prompt_token_ids`, `output_token_ids`, `request_body`
Ref3, `raw_response` Ref3, `http_status`, `error`, `stream_complete`,
`finish_reason` (stop/length), `termination` (eos/max_tokens), `phase`
(smoke/full). Length stops contain exactly2048 token IDs and stay in scoring;
normal EOS outputs contain up to2048 tokens. The lineage/runtime validator
joins actual native EOS/counter traces, source and request IDs to these records.

`score_items`: `schema=bole.independent-task-items/v1`, same task/dataset/
scorer_source, and `items` exactly once per expected case. Each item has
`case_id`, `output` Ref3, and `value:{n,d}`. Official correctness metrics here
are binary item outcomes; the scorer's actual official parser/executor must
exist and be source-pinned. This final reader does not execute generated
HumanEval code or invent answer extraction. It independently recomputes the
weighted aggregate from those executed independent item outcomes.

## Proof entries and executed validator provenance

`{result:Ref3,owner:Ref3}` avoids circular self-references. Result schema is
`bole.formal-independent-proof/v1`: `kind`, `reader_source` (a predeclared
reader source-package Ref3), `subject` (run/task/candidate Ref3), `inputs`
(Ref3 array containing subject and mandatory raw inputs), `producer_identity`,
`source_before`, `source_after` equal that source package, `passed=true`, and
kind-specific result fields.

CPU owner schema is `bole.formal-CPU-owner/v1`: `reader_source`,
`source_before`, `source_after`, `inputs`, `outputs` (Ref3 array including the
proof result), `identity` equal producer_identity (positive pid/start_ticks,
nonempty cgroup/boot_id), `image_id`, `devices=[]`, `device_nodes=[]`,
`exit_code=0`, `primary=null`, `secondary=[]`, `started_epoch_ns`,
`finished_epoch_ns`. Actual owned host/container identity binding and cleanup
must be produced and checked by the predeclared independent owner source.
The source package includes every imported helper and is reopened recursively
when it contains Ref3s. Kind-specific runtime/resource booleans are accepted
only from this frozen executed reader package, never from the measured model.

Runtime proof requires profile_off, diagnostics_off, unchanged_image,
weights_full_identity_verified, explicit_optin, no_training, no_distillation,
source_packet_frozen_before_launch all true. Resource proof requires
observed_exclusive_target, protected_untouched, monitoring_complete,
owned_cleanup_complete all true, with actual physical4–7/protected0–3.
Model qualification requires model_ready=true, same candidate source and
scope: max_generated_tokens>=2048, max_total_tokens sufficient for all frozen
prompt+output caps, max_concurrency sufficient, all_request_reuse=true,
normal_eos=true. Current four-token service results cannot satisfy it.
