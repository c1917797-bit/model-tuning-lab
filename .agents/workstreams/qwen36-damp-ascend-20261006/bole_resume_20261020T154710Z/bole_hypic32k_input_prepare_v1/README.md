# Current32k shared-input component, not a complete runtime packet

Keeps MAIN WORKLOAD.json/V2 untouched. Current input is32768 tokens with first
16384 shared, using the actual current benchmark_shared_prefix _build_prompts
and _tokens_at_least. Current generator SHA is
cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822.
Historical HYPIC prompt BYTE identity is not proven; the actual local checkpoint
tokenizer must produce a NEW immutable input Ref before any paired run. No HYPIC
plugin/routing is activated. Historical40requests/C16 is reference only.
Correctness8/160 and formal1024 use the same source pool; current C1 is preserved.

## Actual code

hypic32k_input.py wraps the ORIGINAL generator, supplying the checkpoint
tokenizer through its existing _tokenize adapter. It checks42 exact32768-token
cases,16384 shared IDs and distinct suffixes, typed IDs, bounded packet bytes.
The native request adapter explicitly uses PromptCase(ids,()) and rejects any
vllm_xargs/HYPIC transport. Fake-tokenizer controls are not actual prompt IDs.

render_input32k.py reads/hash-checks actual V3 files and performs typed AST edits
ONLY in named input/domain functions and input schema assignments. It preserves
EVENT_METADATA_CAP=2048 (bytes), original131 legacy FIA, all mathematical
references/transaction and resource caps. Native server max-model-len and
max-num-batched-tokens become40960, max-num-seqs stays1. Permanent accepted pages
at last before33790 require264; private3-row scratch requires265, not265 native
pages. Source-owned strong native geometry still requires actual native prefill
tables/slots/cache aliases; no allocation is fabricated.

The current request() usage assertion and receipt starting length become32768.
Warmup/measured/barrier select different cases from the SAME generator pool.
The old full source-owned validator remains closed: this component does not
claim an executable32k source or bind an authority. All changed files restore
the actual V3 bytes through the full inverse.

## Concrete remaining algorithm/evidence edges

1. Whole source profile/producer/validator, INPUTS role identity consumers and
   current source-bound decoder bridge must be rebound together; no old ticket.
2. Actual native32768 prefill: all16FA/48GDN, actual physical allocation/slotmap,
   RoPE/full IDs and cache identities; C1 only. Existing2k observations do not
   qualify32k. Minimum native BF16 geometry is not guessed from length alone.
3. Full-frame before_FA alone has a hard lower bound512MiB at minimum256 pages:
   16layers *2(K,V)*256pages*128*256*2bytes. It exceeds unchanged384MiB frame cap.
   Actual ratio12/22physical blocks would be264pages,528MiB, but is NOT observed.
   An after-prefix lossless delta codec alone cannot fix that logical before cap.
   Existing state_capture_codec only deduplicates GDN same-frame roles.
4. Smallest viable next design is bounded layerwise before export plus full
   actual post-page digests/accepted writes, independent reconstruction and
   untouched-page coverage; cross-frame immediate-ACK base reuse may avoid
   retaining two full prefix images. Neither is implemented/qualified here.
   No candidate-supplied equality/boolean can replace the independent oracle.
5. input_identity's full native+independent embeddings also grow to320MiB each;
   its evidence must be bounded/chunked without deleting input equality.
6. Formal1024 strict token reader/TTFT/TPOT and paired source gate still need the
   same32k scope; old131/2k guards are not promoted. No performance claim.

No Docker/NPU/authority/physical SOURCE_BOUND or output root is created. Use:
python3 -I -B render_input32k.py --check
python3 -I -B -m unittest test_input32k
The latter is PURE HOST SOFTWARE ABI/generator-fixture evidence, not Torch,
real tokenizer/HTTP, native geometry or numerical PASS. Prepare next source and
output roots uniquely under MAIN review; current total deadline stays
2026-10-24T07:35:53Z, physical4-7 only, original resource gates unchanged.
