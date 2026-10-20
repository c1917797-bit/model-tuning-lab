# Exact source findings before diagnostics

The seven entries in TOKENIZER_SOURCE_EXPECTED.json are actual whole files copied read-only from stopped G1 CID0731d3f91b532c38d56aa30acde830ff0f6304d93db9baa66d25d59ea3d4c2dc, immutable image660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1. Both actual copy receipt Refs are required and retained. No installed file is edited.

| Actual source | Relevant behavior |
| --- | --- |
| utils/import_utils.py, 114161B/c05e606... | is_torch_available directly checks torch package/version>=2.4; USE_TORCH/TF/FLAX are absent from this file. USE_TORCH_XLA is honored. is_torch_npu_available imports torch and torch_npu when installed, then queries NPU availability. |
| models/auto/tokenization_auto.py, 45679B/bbfe4c... | AutoTokenizer.from_pretrained discards use_fast, sets _from_auto, and with no explicit config calls AutoConfig.from_pretrained before resolving the tokenizer config class/backend. |
| tokenization_utils_base.py, 174898B/6c60e060... | Public inherited from_pretrained resolves local tokenizer assets and delegates _from_pretrained. _from_auto is popped for user-agent metadata; no AutoConfig call exists in this file. _from_pretrained loads tokenizer config and independent chat template, converts serialized added tokens/native format, then calls actual cls. |
| tokenization_utils_tokenizers.py, 65550B/b76df598... | Real TokenizersBackend inherits that base. When tokenizer.json exists and cls is this backend, convert_to_native_format uses TokenizerFast.from_file; constructor copies that genuine Rust tokenizer. Module dependencies include gguf/conversion helpers, so their actual imports still need the probe. |
| models/auto/configuration_auto.py, 63381B/6342126... | Actual AutoConfig source is retained for joining the lazy diagnostic call stack. |
| configuration_utils.py, 63302B/10e7339... | Actual original config source; the diagnostic never replaces a model config with a guessed stub. |
| utils/generic.py, 35163B/dbc2e532... | Computes a Torch-availability boolean from is_torch_available; importing this file does not make USE_TORCH=0 a supported disable switch. |

The retained actual v5 failure establishes when the existing CPU guard failed, not the full caller chain. The source above explains why an earlier deprecated env setting cannot be assumed sufficient and gives a public candidate path. Only the actual bounded audit trace can identify the precise first forbidden caller in this image. The public factory's semantic equivalence still requires a separate full actual decoder/provenance qualification, and every original frozen task/scorer threshold remains unchanged.
