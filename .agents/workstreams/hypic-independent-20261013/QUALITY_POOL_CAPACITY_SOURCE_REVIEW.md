# Quality pool capacity: source and real-shape evidence

036c r7rank0 real state receipts: transition and zero-state each[12,128,128].
CPU affine data FP32 gives48layers*2*12*128*128*4=75,497,472bytes
per segment/rank plus conv tails. FullKV BF16 body16376*1*256*2parts*2bytes
times16layers=268,304,384bytes per segment/rank. These are tensor payload
estimates; actual pool accounting/layout and everyrank must independently check.

Canary capacities256MiBstate/512MiBKV cannot promise10complete segments
resident. Historical readiness receipts cannot prove unevicted current entries.
Never count native fallback as hot quality. Existing10sample schedule remains
draft, not accepted capacity protocol.

Prospective10segment budget:1GiBstate+3GiBKV perrank (~16GiB fourrank),
plus staging/private/device buffers. Host036c MemAvailable77,809,092kB,
MemTotal2,113,084,888kB; a snapshot is not reservation or future admission.
Do not change global memory or running services. Freeze actual bounded budgets,
verify exact accounting/eviction/current-generation readiness and host availability
before new quality contract. Full127x3denominator stays unchanged.
NPUc16 performance ruler remains unchanged; CPU memory planning is separate.
