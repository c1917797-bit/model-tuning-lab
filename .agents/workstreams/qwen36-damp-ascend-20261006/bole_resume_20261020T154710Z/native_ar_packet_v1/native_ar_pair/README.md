# Actual native AR / BOLE reference smoke — advisory packet

This is source-only preparation in a new isolated directory. It changes no G1/G2/live source, original reference, mathematical threshold, native checkout, image, device, or remote process. No actual AR pair or same-image Torch/NPU execution is claimed.

The first executable scope is two sequential C1 requests, each with the **same frozen actual 131 input token IDs and exactly two returned output token IDs**, followed by a one-token native retirement barrier. `ignore_eos=True` is deliberate for this bounded smoke. It does not qualify normal EOS, long output, task accuracy, performance or model readiness.

The declared algorithm difference is explicit: native AR has no speculative config/drafter and no BOLE intervention; BOLE uses its already qualified G1 path with native MTP8. Removing that one speculative argv option changes the actual native attention route. The packet never assumes identical kernels on the two sides.

## Concrete files

- `prepare_native_ar_pair.py` creates a new unique source leaf, copies only exact source-bound donor helpers, and derives AR argv from the actual ON server command by removing exactly the declared MTP8 option. It does not modify its donor or start any process.
- `native_ar_server.py` is a default-OFF guest entry for MAIN's existing owner/controller. It writes actual argv, installs the original frontend identity journal and starts the original API module. The private plugin metadata directory is a read-only source overlay, not an image installation.
- `native_ar_bootstrap.py` installs after original NPUWorker.load_model, writes actual worker load/HF32 snapshots, retains the original worker identity journal, and installs the native AR observer.
- `native_ar_observer.py` observes original native model inputs/positions/last hidden, real head operands/logits, original neutral greedy sampling, actual ModelRunnerOutput bookkeeping and actual removal of both strong request objects. Every original method is called normally; no sample, cache or hidden result is substituted.
- `native_ar_capture.py` writes exclusive primitive/tensor captures under the declared owned output. Tensor charge plus the original metadata reserve is at most 1 GiB/rank; raw plus full future worker-journal/receipt allowance is bounded. A first fault propagates and poisons the observer; it is never converted into fallback success.
- `pair_entry.py` collects one already owned loopback variant. It reuses the original actual G1 tokenizer `INPUTS.json` Ref; there is no decoding/re-tokenization roundtrip. It writes actual wire responses and returned `choices[0].token_ids`, with counts 2/2/1. BOLE headers and HTTP schema remain compatible with the unchanged full G1 consumer.
- `launch_profile.py` records actual framework environment from an explicitly PID/start/cgroup-bound frontend. It filters credentials and records algorithm/observer keys by name only. It does **not** classify the effects of different plugins.
- `assemble_pair_inputs.py` binds existing actual owned variant ledgers. It cannot manufacture ownership or worker evidence.
- `consume_pair.py` is a Devices[] CPU consumer. It re-runs the source-bound full G1 consumer in a separate CPU process, independently reconstructs native AR full TP4 vocabulary argmax for every actual emitted token, joins both frontend assignments and all-four worker retirements, compares actual returned IDs, and independently checks every captured original native FA frame in FP32 and FP64 using the unchanged `.001 + .01*abs(reference)` pointwise bound. First mismatch ordinals and metrics are retained.

## Actual PA/FIA seam

The narrow per-instance seam is **`AscendAttentionBackendImpl.forward_impl` after original `reshape_and_cache`**. It covers both real branches. Native `DecodeOnly` may use `_npu_paged_attention`; other native configurations use `npu_fused_infer_attention_score`. A `DecodeOnly` or FIA-only hook is insufficient to establish coverage of the other configured stack.

A target-only ContextVar and module-local delegating proxies observe the actual lower PA/FIA calls. The actual `torch_npu` module is never mutated. Calls outside that target context delegate unchanged. Prefill and any draft model are excluded; native AR itself requires no drafter. All sixteen target FA layers must produce one actual decode frame per request.

Each frame joins the current actual request object, physical1536 allocation, full physical-to-kernel128 CPU/GPU/metadata expansion, actual current slot, original BF16 Q/K/V, actual owned-prefix native cache bytes, explicit lower kwargs and native output. It captures only owned-prefix KV bytes, not the whole cache arena. PA operands retain exact arena identity. FIA's actual `_get_fia_params` page-flattening view and `.contiguous()` may make a genuine native copy; the observer joins the **actual lower operand's selected bytes** to the original cache rather than inventing a pointer alias.

Actual kernel schema strings are retained when exposed by the installed dispatcher. Omitted kernel defaults remain explicitly unresolved. This is an observation of unchanged actual calls and output agreement for the captured C1/131/q1 frames, not a new global kernel or precision qualification.

| Evidence | What it can establish |
|---|---|
| Existing private dense FP16 AR saved-input matrix | Its qualified dense/BNSD/unmasked/ip0 private path only |
| Existing G1 component consumer | Its actual BOLE selected path and original component bounds |
| New actual native PA/FIA frame, after real execution | The original production native route and observed BF16 operands/output for that exact frame |
| This source packet alone | No numerical, token identity, kernel or model success |

`private_dense_FP16_proof_is_production_native_proof=False` and `global_FA_precision_alignment_qualified=False` remain explicit.

## Required MAIN integration and gates

MAIN must create and own all processes/containers with the existing controller/identity authority. This packet deliberately does not introduce a second controller. Its AR host bundle uses the same genuine snapshots/host bindings/journals as the existing ownership gate, populated from the new exact AR capture filenames; see `EVIDENCE_SCHEMA.md`.

Before any NPU admission, freeze a complete actual source closure, current authority, read-only mounts, model/tokenizer file manifest, image ID and output leaves. Check the actual private plugin metadata resolution and every native instance/class/torch inference-wrapper guard in the same image. The local executor has no Torch, so those checks have not run here. Default-OFF, `--help` and AST checks do not replace them.

The paired consumer verifies actual image ID, installed runtime Ref equality, actual common argv after the declared algorithm delta, actual model/tokenizer Ref equality and captured common framework environment equality. **Plugin effects still require independent source review.** The AR plugin profile omits the ON BOLE/MTP/dense-observer plugins; this packet does not assert that every omitted plugin is observational or that all common optimization effects are already matched.

Consequently a successful native reference smoke may set `native_AR_reference_smoke_pass=True`, but this source intentionally keeps `bounded_pair_pass=False` and `matched_common_plugin_effects_gate_pending=True`. MAIN must review exact plugin effects and freeze a subsequent explicit gate before claiming fully matched common optimizations. CLI exit zero alone is not that gate.

The pair consumer charges actual retained AR+BOLE rank raw/calibration/journal/HTTP/snapshot evidence together under the original 1 GiB plus 1 MiB header allowance. It rejects an oversized pair instead of increasing the cap. Normal EOS and output1024 require later scopes.

G2 smoke output4 / future streamed output1024 have **no full independent reader supplied by this packet**. The frozen G1 reader hardcodes length131/version0/remaining1. A G2 reader must separately preserve complete step coverage, old-after→next-before state joins, actual worker/history/generation ownership and independently owned streaming CPU acknowledgement/retention semantics. Runtime's builder must continue to require its exact independent-consumer Ref.

## Local verification

```sh
python -m unittest discover -s bole_service_proposals/native_ar_pair -p 'test*.py' -v
```

Thirteen synthetic pure software tests pass. They cover exact algorithm argv deltas, complete returned ID comparison, mismatch retention, bounded primitive evidence, default-OFF/help under `python -I -B`, endpoint limits, actual wire collection failure controls, module-local delegation outside a target context, environment redaction and exact Ref/symlink controls. All Python ASTs parse. These tests contain no actual model data and do not test NPU operator behavior.

Every model/task/performance/formal-ready flag remains false. Current formal task authority is GSM8K, HumanEval and MMLU; the older LongBench-v2 template is replaced. This packet performs none of those tasks.
