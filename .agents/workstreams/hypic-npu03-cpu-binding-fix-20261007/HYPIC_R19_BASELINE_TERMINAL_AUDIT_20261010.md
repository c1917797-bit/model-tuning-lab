# R19 repaired-source LongBench no-cache baseline — terminal audit

This is one control arm of the frozen HYPIC explicit-segment 2048-token,
concurrency-32, three-repeat LongBench-v2 pair on physical NPU0–3. It does
not establish a paired quality or HYPIC adoption verdict.

- Frozen protocol: `HYPIC_R19_REPAIRED_C32_2048_PREREGISTRATION_20261010.json`;
  source `4429e35177979c874bf053ab29789e4773f39b22`, same repaired-source
  mount in both arms, one treatment switch `VLLM_ASCEND_HYPIC_ENABLE=0/1`.
- Immutable raw root:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-baseline`.
  Controller `exec-000000000000032c` exited 0 at 2026-10-10 12:14 UTC;
  independent read-only audit `exec-0000000000000387` exited 0.
- Completeness and score replay: 127/127 samples, 381/381 scored responses,
  227 correct, with repetition counts 74/77/76. There were 49
  length-limited scored outputs. Sample IDs, prompt hashes, explicit
  boundaries, five unique request IDs per sample, payload hashes,
  response hashes, scorer replay, and absence of extra sample artifacts
  passed the frozen independent `audit_arm` checks.
- Deterministic 128-token short canary passed three identical baseline
  outputs. The integrated 32-sample capacity wave passed, with 295 guard
  samples by that checkpoint. The full arm had 865 clean physical-device
  isolation samples and no foreign process or probe error.
- Source attestation, four distinct worker PIDs on physical NPU0–3, pinned
  service fingerprint, one-switch pair seam, exact owned-container removal,
  worker release, and port release passed the independent audit. The
  baseline container ID was
  `f976bcebe9953925133bc8adec19e2716058167f35c170e929afecba04c7f197`.
- SHA256: contract
  `2071d4d80e2496d9d3bc583e8c87d0f0d6d790c0efdd1f59195214ff0f5f4154`;
  arm result
  `a37204901a95768121e116e72a3978ee64865ca085b09b4993265431133c200d`;
  source attestation
  `c67ceb8ed8388416e620f1c95b04dbde0d55699c339eece25091f1564e38bc22`;
  short canary
  `e99b061991030b064b35f870d7f0d2253adabf11b0671d161806d90b642a60ba`;
  integrated wave
  `1a85803669656c9e647a924fe01463e289e087565263b4bb0e7bbe3300abc685`.

Immediately after audit, a fresh direct-route snapshot showed no physical
NPU0–3 processes and no listener on port 8223. The same-source HYPIC-only
candidate offline preflight passed and was launched under
`exec-0000000000000392` into its prospectively frozen new root. Poll that
exact controller; do not restart it for a slow batch. The candidate,
paired LongBench verdict, GSM8K off-path safety pair, and repaired-source
performance adoption evidence are not yet complete.
