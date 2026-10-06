# Remaining equation-probe QA (not yet completed)

- v2 matched seeded packing and320 native-oracle steps. This does not certify
  all quantizer boundary values. Add whole quantizer ties,±1ULP around half
  integers, zero groups,±127 and a non-power-of-two scale before fused parity.
- Freeze x/scale arithmetic as well as max*reciprocal; standalone round alone
  cannot establish complete CPU/NPU quantizer identity.
- Add independent CPU unpack loop and nonidentity-layout reconstruction tests.
- rel() currently can emit nonfinite float before allow_nan=False serialization.
  Fix null+nonfinite diagnostics and case failure/current-step bookkeeping;
  preserve original exception if hashing/final save also fails.
- Preserve v2 whole-state preregistered gates, but add selected-slot per-head
  errors, norms, indices and max_abs to avoid dilution from untouched slots.
- Validate positive finite c, bijective permutations, group/khi and risk weights.
- Identify actual recurrent dispatch binary/vendor paths, not only wrapper SHA.
- Inverse permutations must be frozen offline, not Int64 ArgSort per token in
  a performance candidate (current reference legitimately ran on AiCPU).
