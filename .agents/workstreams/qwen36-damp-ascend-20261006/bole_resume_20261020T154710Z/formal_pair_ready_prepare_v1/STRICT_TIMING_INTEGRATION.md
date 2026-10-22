# Strict token-receive timing integration (current: source proposal v2)

Actual reviewed-source artifacts are in strict-source-proposal-v2/{prepared-source-native_ar,prepared-source-bole}/ with402 files per arm; PREPARED_PAIR.json is source-only, never SOURCE_BOUND. Proposal_v1 is preserved, not to be dispatched (its changed-client alias was stale; v2 rebinds exact own Ref aliases/dependencies). No frozen/live source, authority, numerical gate or admission was changed.

## Implemented path, not another timing plan

render_strict_timing.py reuses actual paired_prepare.render_pair(), then applies a six-file reversible timing-only delta to each arm:
- performance_service_client.request count1024 calls strict_token_timing.request for real warmup and measured requests.
- The adapter captures monotonic ns immediately before the actual owner-provided POST, then the existing fixed1024 observer records actual read1 chunks/raw bytes and timestamps before parsing/writes.
- The unchanged independent parser/math reopens whole raw/chunk Ref3, validates actual delta1024 IDs, prompt/header/model/usage/DONE, and recomputes first/last token receipt. The only pure protocol change in copied observer/reader is explicit seed0 to match the old donor; echoFalse is made explicit identically for both arms.
- Legacy RequestResult ttft_ms and duration_s now derive from strict integer TTFT/T_total, not nonempty decoded text or EOF. Original donor summary formulas therefore use actual first/last token endpoints. Raw integer metrics remain available for exact comparison.
- performance_client_consumer retains its complete original HTTP/native retirement/commit checks FIRST, then independently replays raw SSE for warmup and measured outputs and rejects metric/token drift. Unmeasured one-token retirement barrier stays the original path.
- New observer/reader/evidence/helper have source-bound whole Refs. Changed streaming-client alias/dependency is rebound, and all source bytes inverse exactly to the existing two-arm preparation.
- Native arm truly removes MTP and BOLE policy; candidate uses MTP8. Both receive identical strict timing files/common optimization. Neither becomes numerical_qualified or performance_ready. Original formal public qualification remains fail-closed/unbound.

output_sha256 on the new legacy RequestResult is explicitly scoped ordered-token-IDs, not decoded-text equality; record.output_sha256_scope states this. Actual raw/token/scorer identities are the independent evidence. Do not relabel that hash as a text hash.

## Actual v0.23 protocol capability, not inferred from fake wire

Actual fixed-image stopped-copy completion_serving27822B SHA c67bff55...357–375 forwards delta_token_ids even when delta_text is empty; it skips only when BOTH are empty.401–414 returns output.token_ids when return_token_ids is true. Actual protocol21247B SHA93c72054...145–150 defines streaming IDs as delta;337–339 selects DELTA output. Output processor31616B SHA464c3cda...272–318 preserves the first token under interval batching;376–410 forwards text and token_ids separately. Thus role-only/usage chunks are not tokens, but empty-text chunks with actual IDs ARE token evidence. Unicode buffering never triggers fabricated/interpolated times. All IDs coalesced into one actual read share that real receipt timestamp; TPOT span can legitimately be0.

Source capability is established. Actual running worker protocol/source identity and real1024 SSE have NOT been requalified by these source-only controls.

## Actual source-function controls

Actual09c9:6 groups PASS. Tests call the newly rendered client.request, the real new adapter, original observer and independent reader using synthetic in-memory transport, plus the newly rendered public native consumer (legacy metadata gate is an explicitly labeled stub only for this seam test). Cases cover role-only chunk, first token with empty text, large usage/DONE/EOF delay, all1024 IDs, missing/extra/repeated delta chunks, forged metrics/IDs, identical timing delta for both arms, true native MTP0 versus BOLE MTP8, and exact changed-client alias closure. Fake-wire timings are NEVER an NPU performance result. Original complete owner/native/FAST checks remain future requirements, not replaced by stubs.

Reproducible software-only control:
python3 -I -B test_strict_timing.py -q

Source-only regeneration to a NEW own direct-child leaf:
python3 -I -B render_strict_timing.py --prepare --output <NEW_SOURCE_PROPOSAL>
No source freezing, authority issuance, owner creation, HTTP or NPU occurs here.

## Workload and remaining admission

131 input tokens are only the current inherited prototype definition, not accepted2k/16k workloads or generic serving benefit. The inspected frozen user protocol USER_72H_PROTOCOL_20261009.json1379B SHAb605d2a0... fixes output1024,10% and TTFT/TPOT, but contains no input131 approval. PROSPECTIVE_POLICY/current input template does not supply such approval either. Accordingly both manifests explicitly set workload_acceptance_pending=true and workload_acceptance_ref=null. Do not promote a131-token prototype gain to overall>=10%. Input2k/16k requires independent frozen input/source/numerical coverage, not changing the old131 matrix in place.

Pending before any real run: current exact FAST numerical/state qualification; independent review and real owning-source validator/Ref closure transplant (still pending_runtime_validator=true); same-image imports and worker-loaded source/precision/HCCL/native AR proof; permitted finite current authority/resource/clock/cleanup fit; actual source-bound1024 input Ref and workload acceptance; then one matched screening followed by3 formal pairs if promising. No missing proof is filled with boolean metadata, and no old deadline is extended.
