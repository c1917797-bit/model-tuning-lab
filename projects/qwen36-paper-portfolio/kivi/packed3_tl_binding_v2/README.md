# KIVI packed QK/softmax/AV: qualified Triton language binding repair

This is a default-OFF Ascend adaptation component, not a deployed or accepted performance technique.

## Actual failure and causal repair

MAIN operation exec-000000000000017c completed with exit1 after a successful physical NPU4 (guest0) arithmetic canary. At the first QK JIT compilation, the compiler raised NameError('tl is not defined') at the tl.constexpr annotation. No candidate frame or output completed. The original source (SHA72771419067bc420c6cb812e67d97a9a13e84b30f6bff16045319836455b1137) is retained as failed_kernel_v1.py and at its immutable experiment location.

The factory-local tl object was absent from the module globals used by Triton's AST compiler. kernel.py binds the source-qualified actual language object before the JIT decorators, only after the existing opt-in and qualification gates. Same-object reuse is allowed; different-object rebinding rejects. The three kernel ASTs and ModelNew.forward are unchanged. No tensor threshold, gate, case, resource reserve or deadline changed.

## Verified scope

- MAIN0182: all12 stdlib regressions passed on chicaihong01 Python3.9.9. The old source fails the compiler-name-lookup surrogate; all3 repaired definitions resolve the actual language. No Torch/Triton/NPU execution in this test.
- MAIN0183: all8 actual numeric-entry source/CLI/guard tests passed with the new source manifest.
- MAIN0184: all12 actual host-entry, mount, predecessor and source tests passed.
- MAIN0185: terminal exit1 at JIT lowering (`uint32_t_to_float_rintmode` unsupported), with zero completed frames. Preserve this failed source; it is not an algorithm-numerical or paper-level result. The separately named `../packed3_signed_cast_v3/` repair passed MAIN018c's controlled 20-frame NPU matrix and MAIN0193's independent original/raw consumption; that does not promote this v2 source or establish model/performance readiness.
- No model, FULL graph, CUDA parity, E2E throughput, LongBench-v2 or GSM8K acceptance.

## Reproduce and audit

Canonical repository: /opt/host/vnf/austinov/model-tuning-lab
Current branch: work/qwen36-damp-ascend-20261006

Regression:
`/usr/bin/python3 -I -B /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/kivi/packed3_tl_binding_v2/test_kernel.py --original /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/kivi/packed3_tl_binding_v2/failed_kernel_v1.py`

Numerical source manifest:
/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-packed-three-kernel-numeric-v2-tl-20261010-001/SOURCE_MANIFEST.json
SHA256 24ea0765fa04fdba321128b313839410ada1a63d6cc643a97988470127cbe5c8

Owned host manifest:
/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-packed-three-kernel-singlecard-host-v2-tl-20261010-001/SOURCE_MANIFEST.json
SHA256 fda4d51fc1805341f50a320f85fc8e9c82e7f8d2f137204f923bf651a50345d8

New actual output: /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-packed3-owned-main-tl-v2-20261010-001
Original failed output: /cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-packed3-owned-main-user72h-20261010-001
Original RESULT SHA256 3465eb342beb62603538d5a72fae8518093528b923ae262251b098078cd87943

The complete entry CLI, actual operation originals and outputs stay in the experiment evidence directory. Preserve originals and use a new output for any new revision. Re-run the affected complete20-frame/24-row/60-call independent numerical gate before any model diagnostic. Then confirm actual TP4 candidate decode activation, paired fixed1024 performance and final no-thinking max2048 normal-EOS tasks. This failure does not establish a paper-level no-go.
