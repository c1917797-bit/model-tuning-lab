# KIVI packed3: masked signed-cast Ascend repair

Default OFF. This is an algorithm-specific candidate, not a released model/performance plugin.

The previous real Ascend run (0185) failed before any numerical frame: the backend could not lower `uint32_t_to_float_rintmode`. QK and AV now cast only the already-masked 2/4-bit code to int32 before float32. The 0..3/0..15 values are represented exactly. Packed words remain uint32 for shifts, and both A16 rounding points and all forward operations are unchanged. The earlier JIT module-global language binding is retained.

Actual physical NPU4 run 018c completed all20 eager frames/24 output rows/60 calls for2/4bit × FP16/BF16, batch1/2, lengths128/129/130/256/257, including fork and slot reuse. Independent original-evidence consumer0193 exited0, checking all outputs and all8 cache fields plus writer/lifecycle invariants. Maximum numerical error to the registered Ascend-boundary reference was0 for these inputs; the separate official Python split-boundary relative RMS maximum was0.003284108772782965. This is not CUDA parity, full-model equivalence, task accuracy or speedup evidence.

The source-frozen matrix and raw results remain outside Git. Authoritative paths/hashes and exact scope are in `.agents/workstreams/qwen36-damp-ascend-20261006/KIVI_PACKED3_SIGNED_PASS_20261010.json`. 33792 is metadata capacity, NOT tested context length. Model bootstrap, real32768 input, graph, formal1024-token paired timing and final task accuracy are still incomplete.

Software regression:

```sh
python3 -I -B projects/qwen36-paper-portfolio/kivi/packed3_signed_cast_v3/test_signed.py --baseline-root projects/qwen36-paper-portfolio/kivi/packed3_tl_binding_v2 --original projects/qwen36-paper-portfolio/kivi/packed3_tl_binding_v2/failed_kernel_v1.py
```

20 software checks passed on the host. The original baseline source and both failed runs remain preserved; do not relabel them as passes.
