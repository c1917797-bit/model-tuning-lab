# Historical first core-only design note (superseded)

Read HANDOFF131.md for the current actual HTTP/owned/independent-consumer
entry. The text below records the earlier core-only preparation boundary,
not the final131 deployment contract or evidence of an actual execution.

This is necessary algorithm integration code, not an installed worker,
qualification, controller or scheduler. No NPU/model run occurred. It is not
an HTTP BOLE server. OFF does not import Torch or mutate any object.

The exact actual30278B Qwen3Next source is included in evidence. Its complete
Attention.forward is preserved: projection, split, q/k RMSNorm, native RoPE,
attention, optional sigmoid gate, output projection. Only each real Attention
instance's inner `self.attn.forward` is temporarily overridden. That is after
RoPE and before the backend's unconditional flattened-KV writes.

For GDN, only the actual instance's `_forward_core` is overridden. Actual
outer projection, z/norm/gate/out_proj remain unchanged. The wrapper accepts
the real core_attn_out keyword ABI. It gathers true raw-conv ancestor tails,
executes the actual calibrated native12arg convolution on isolated node slots,
uses actual rearrange_mixed_qkv, DeviceOperator.fused_gdn_gating and l2norm_fwd,
then invokes frozen112 parallel GDN. Q scaling happens once; GQA4->12 and native
[Dv,Dk] transpose are explicit. Original committed GDN/conv arenas are not
written. Actual projected/RoPE operands come from the real target forward,
never hand-made random joint components.

`Bridge` registers exactly the64 actual inner_model.layers objects and48/16
configured kinds. It requires exact original callable source identities,
real layer-owned GDN arenas and registered ND page128 FA caches/table. Binding
an actual FA cache to its runner metadata is still the caller's responsibility;
shape equality is not provenance. `Bridge.forward` requires the real owner,
root+two distinct draft input IDs, positions[L,L+1,L+1], exactly-once ordered64
traversal and unchanged scheduler generation/version. Missing/duplicate layers
or unknown cache layouts fail. No global class is patched, no background job
is created; per-instance methods restore on explicit `restore` outside forward.

`sequential_native_paths` runs the SAME real learned model twice: root->left
and root->right, one actual model token at a time. It preserves original outer
model projection/norm/RoPE/residual/MLP, but redirects cache-boundary calls to
source-derived original native12arg convolution and native recurrent GDN.
It never invokes112's closedform, candidate factors or ancestor mask. Native
FA controls independently walk actual physical prefix pages and use ordinary
contiguous BNSD on the true root-to-child path. This is a source-derived native
operator AR comparator, not a claim that original `_forward_core` runs intact.
Every step requires all64 layers; all persistent selected slots/pages must stay
bitwise unchanged. Its new one-token operator compositions still require real
execution. An original full native-runner AR control remains an additional
useful cross-check, not software evidence invented here.

## Concrete still-required code (cannot be called completed)

1. `worker_entry.install_after_load` now provides the real after-load hook:
   exact native NPUWorker.load_model completes first, then actual
   model_runner.get_model/named_modules selects the unique source-proved
   Qwen3_5Model and all64 actual layer objects/prefixes. It stores strong
   references on that worker and emits a nonqualification registry receipt.
   `actual_logits_head` joins the real CausalLM head by owning-inner identity
   and actual qwen3_5 source. It never selects objects by matching dimensions.
   The actual request/forward hook after target/drafter loading must obtain
   real inner model, real per-layer FA cache/table from runner and request
   generation/exclusive commit window. GDN caches are directly identity-joined
   to actual layer.kv_cache; FA runner binding is not yet implemented here.
2. `mtp_entry.install` now wraps the actual source-proved proposer._propose
   and actual Qwen3_5MTP.compute_logits. The original first pass supplies root
   next_token_ids and first vocabulary logits; the observer stores top2 from
   those genuine logits, not linear draft IDs relabelled as siblings. It
   preserves the original proposal result object and captures logits before
   sampler cleaning. It is diagnostic and performs D2H finite checks; it is
   neither a production accelerator nor a cache-owner proof. Real MTP loading
   and NPU execution are still unobserved in this packet.
   Target must use the calibrated no-spec SD conv arena width3. Native114
   MTP8 config allocates extra speculation-state width; it cannot be passed to
   this bridge as-is. A separate actual MTP drafter must supply real root/top2
   with source/load/logit-row proof, without configuring the target's ordinary
   linear speculative path. No fabricated tokens count as BOLE model input.
3. Wire `Bridge.forward` and `sequential_native_paths` inside an actual worker
   forward-context callback, after a real request's native prefill. Preserve
   raw model logits/hidden, all selected state/cache and original inputs. The
   callback must register actual native text position layout:1D or three-axis
   MRoPE, never infer it from a flattened token count. Initial prefix lengths
   are restricted to actual paged matrix0/127/128/131; not2K/16K extrapolation.
4. Compose staged GDN factors, conv tails and FA accepted path for all layers;
   prevalidate destinations, require TP4 unanimous path and invalidate request
   generation on partial write. Publish scheduler counts/bonus/MTP history
   only after all writes. Existing canonical joint.py does not implement paged
   runtime commit, so this packet performs NO publication. `greedy_proposal`
   uses the actual source-proved target LM head and existing neutral greedy
   acceptance to derive terminal/root path from real logits; it only stages
   all64 writes, never processes the bonus into cache. Current forward phase
   is FORWARD_COMPLETE_NOT_QUALIFIED; staged phase is STAGED_NOT_PUBLISHED.
5. Actual118tR1 has now passed all8 pagedD256 cases (4996b5d1... independent);
   `component_gate` reopens that exact source and released numeric/consumer
   chain, plus actual112full72 and identical math bytes. It does not borrow
   old contiguous attention or promote components into whole-model proof.
   Actual118c source/owners/raw joins and actual extension/opapi mappings are
   also checked.118c proves chronology, not new three-node native batching.

## Minimum actual next experiment and budget

Reuse114 existing safety/resource owner for one genuine prefetched B1 request and real
MTP top2, then tree pass plus two native root-child paths on isolated clones.
Capture actual64-layer source/row joins, logits, selected states and pages.
Do not add a random-component round in place of that model. First scope is
one request/eager/sync/prefixOFF/mamba-none, source/precision common to controls;
not C16, graph or paper depth8. Target model48GiB+host.5+reserve8 remains the
existing admission; real additional drafter/clone peak is unknown and must be
measured/hard-failed, not inferred from component RAM. Selected snapshot bytes
per rank are 48*12*128*128*4 +16*2*ceil((L+2)/128)*128*256*2, around68MiB at2K;
four ranks are about272MiB per one complete selected-state image, before
multiple tree/native clones, tensors and serialization. This2K arithmetic is
ONLY a budget example, not admitted2K scope; first scope is real prefix127.
The candidate FA adapter copies only logically valid prefix cells into bounded
private compact pages, zeroes unused private capacity and never clones the
whole engine KV pool. Before/after anchors cover the registered selected real
pages/slots including their arbitrary padding bits; they do not claim an
all-inactive-arena scan. Existing model owner
deadline/cleanup remain; no new stage is authorized by this source.

Eighteen local CPU controls include executing COMPLETE real QwenNextAttention
forward AST with explicit CPU projection/norm/RoPE/operator fixtures to test
call order and output wiring. These are source-layout software controls, not
real vLLM loading or numerical/model results. They also execute COMPLETE real
NPUWorker.load_model body in its explicit CPU no-sleep fixture, verify observer
ordering, all64 actual wrapper keyword routes/restoration, and future missing
receipt rejection before backend access. No main environment is stubbed.
