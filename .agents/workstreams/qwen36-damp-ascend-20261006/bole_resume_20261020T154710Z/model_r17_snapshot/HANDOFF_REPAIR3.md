# BOLE131 repair3: source-only, not model qualification

R1 is the complete remote copy donor. R2 has only 79 remote unchanged copies;
its changed payload was never deployed/bound/launched. R2 remains frozen local
prepared evidence, not an actual numerical failure.

## Proven input ABI corrections

1. The actual multimodal Qwen3_5ForConditionalGeneration config has no top-level
vocab_size forwarding. Resolve the unique real CausalLM head owning the actual
inner model; bind its class/method source, shared text-config object, target
embedding vocabulary and actual independent MTP text-config vocabulary.
2. The actual native base runner embeds pure text for the multimodal architecture
and can pass input_ids=None. Before the unchanged native call, recover only the
actual runner input_ids.gpu[:131] and require exact equality to the strong request
prompt and actual CPU batch row. Reject MM features, soft prompts, wrong rows,
wrong length and encoder-decoder route. For embeddings, execute the source-bound
real token embedding and require actual BF16 embedding bytes equal before forward.
This is an input identity check, not an independent model numerical oracle.
3. The actual installed runner buffer is int32. Preserve its dtype and values in
raw and independent consumer checks. Hand-created three-node tree IDs remain
int64. This corrects an ABI predicate; it changes no numerical limit.

The wrapper preserves all original native argument objects and result. Observation
only supplies recovered IDs to the diagnostic callback. After the one tree trial,
the original native retirement-barrier request runs without another 131-token
observation; real worker identity/retirement evidence remains required.

## Evidence and verification

Full source-pinned base runner/HF evidence is in evidence/. Existing patch identity
and strict one-layer contextmanager identity checks from R2 remain intact. Actual
installed method ASTs exercise the input embedding/prepare route in CPU fixtures.
Six new tests cover real CPU BF16/int32 tensors, corrupt embeddings, CPU/request
identity, MM and dtype rejection, unique LM owner/config/MTP mismatches, actual HF
non-forwarding, and wrapper argument/result preservation. These are not NPU proof.

One final cold -I entry --software aggregate: 48/48 PASS, 3.193 seconds. No actual
backend or device launched. Source/UTF8/LF/AST/AddFile round-trip audit is separate.
The model entry still has no whole-model numerical qualification or scheduler
commit. Original GDN/conv/FA mathematics, raw numerical consumers' limits, three
nodes, 131 input, 10 output, 3600/180 budgets and resource limits are unchanged.

## Deployment and execution

Use bole131repair3-deployment-final/COPY_MAP.json and CHANGED_ADD_FILES.patch;
all copy sources are the complete actual R1 remote root, never partial R2.
COMMANDS.json has cold, bind, sourceaudit, CPU and model typed argv. Actual
component Ref3 objects and actual bound source Ref3 must be supplied by MAIN.
Default OFF is preserved. No model/NPU result exists for R3.
