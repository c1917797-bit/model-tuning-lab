# Quality input reuse review

Read-only probes02de/02e2/02e5 examined old contracts and sample-report schema,
not prior HYPIC treatment implementation. Old outcome roots remain immutable.

The old LongBench-v2 dataset identity is127 samples, SHA256
cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a.
GSM8K identity is1319 samples, SHA256
3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14.
Declared evaluator SHA256 is
9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0.
These are historical identity leads, NOT freshly verified data/scorer files.
Original datasets and evaluator locations remain unresolved by current probes.

Old r19 nonthinking arms use2048, while current user ruler is1024.
Thus old baselines cannot supply this campaign's matched denominator.
Sample reports preserve identity/reference/scores/segment ends, not raw prompts;
never reconstruct input from answers or assume reported prompt hashes suffice.
Same raw dataset/template may be reused only after actual files and tokenizer
are independently verified; new prompt/token/segment receipts must be frozen.

Capacity planning must cover the full denominator, not only hot-friendly rows.
LongBench127 x3 gives381 scored requests per arm, plus public producers/retries.
GSM8K1319 x3 gives3957 scored requests per arm before any warmups/retries.
Current runtime request ledger bound4096 cannot blindly cover both combined
with public producers. Phase-separated contracts need derived quotas.
Catalog bound128 admits127 distinct LongBench segments, not arbitrary1319
distinct GSM segments. Bounded catalog/pool batches may be used without dropping
samples; freeze ordering, capacity/eviction and all fallback reasons beforehand.
No cap changes, sample reduction, runtime launch or quality verdict made here.

Next: resolve actual immutable dataset/evaluator files, review generic prompt/
scoring workflow without importing old algorithm/runner patches, generate
fresh full inputs with official tokenizer in CPU-only image, and independently
verify127 identities, exact segment membership and generation/end policy.
