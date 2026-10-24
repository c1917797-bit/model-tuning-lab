# BOLE V9 actual client input preflight (prepared only)

V8's first HTTP request never started: its historical generator path was absent in the guest. The current source-owned generator is exactly49810 bytes/SHA256 cba2b1b463a1e436c818722d92147d93f8396b8d64f8da6582d7e67d2cb45822. Only its Ref path is rebased, not generator/dataset/tokenizer or math.

Original preflight114.run now executes input_preflight.run after the actual text-only parser. It loads the exact client checkpoint /models/Qwen3.6-27B with trust_remote_code=True/local_files_only=True, actually invokes I.dataset and its full validation (42-case pool), records all tokenID hashes and lengths, shared-prefix hash, and actual warmup0/measured2/barrier1 selections. No HTTP or NPU; no numerical qualification. This actual tokenizer stage is NOT executed by source-only checks and remains a required MAIN same-image CPU result. Original CPU time/memory budgets remain unchanged; timeout is failure, not automatically expanded.

The same preflight also constructs all three real client requests (warmup8/measured8/barrier1) through the original donor/client functions and stops at a dedicated BaseException transport sentinel. It records request-body hashes and checks exact IDs/EOS/stream fields; no response is fabricated and HTTP remains false. Original parser child120-second cap is not expanded. Real tokenizer/request execution remains pending, not covered by host source controls.

Source-only: python3 -I -B runtime_lossless_imports.py --check
After MAIN exact new review/authority only: runtime_lossless_imports.py --prepare --authority-ref '<actual Ref3>', then original source-owned qualification_source_producer.py --bind / generated COMMANDS. Do not reuse V8 authority/PASS; new root/output are exclusive. Old V8 failure retained.

Lazy chain checked: client I.dataset -> generator checked Ref -> source-owned benchmark_shared_prefix -> original _build_prompts/_tokens_at_least with local _tokenize replacement; checkpoint tokenizer remains the original read-only /models mount. No broad repository mount or HTTP fallback added. Runtime tokenizer custom-code/file dependencies still require actual same-image execution; no claim that host source controls establish that result.

48GiB model/8GiB CPU/512MiB host and all original reserve/phase/cutoff/64-128/math gates unchanged. Short8 precedes related RAWON/OFF160 and fixed1024; no old numerical PASS inherited.
