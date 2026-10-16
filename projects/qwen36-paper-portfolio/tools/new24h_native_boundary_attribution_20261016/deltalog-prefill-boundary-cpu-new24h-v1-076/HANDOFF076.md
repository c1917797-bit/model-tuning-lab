# CPU076: old069R1 B1 step89 to90 prefill boundary attribution

Source-only. Reuses successful074repair2 Owned CPU implementation, including
exact Docker-only prlimit AS lifting, sealed069 verification, existing storage
lock, untracked1GiB accounting and complete output/stop-retain gates. The only
owner differences are own source/name/output identities, DIAGNOSIS076 filename
and the typed two-row diagnostic receipt instead of the old91-row receipt.
No new resource framework, NPU run or kernel change. MAIN schedules after the
TP4 experiment releases; no blind RAM/CPU overlap. All original80GiB/100GiB
storage and8guest+.5host+8reserve=16.5GiB, child600/cleanup90/whole1000 remain.

Exact actual069R1 source and failed producer are frozen in owned_cpu.py. The
producer's records supply exact step89 and90 rawRefs; only those two mixed raw
files and their blob references are decoded. Original N160 failure is untouched.

At B1 step90 the fixed source swaps decode1/prefill0 to decode0/prefill1;
it is not a reset step. Crucially, the helper flushes the selected prefill slot
before entering native GDN. The diagnostic therefore requires six-array byte
continuity for OTHER slots, selected live K/U and lambda preservation, and
selected length/decay zero. Dead K/U NaN poisoning is expected and not compared
as live payload. Captured chunk initial must equal the actual flushed base;
the final captured native state must equal the base written back.

It decomposes initial-state difference into prior lazy-logical difference and
FP32 flush rounding, retaining vectors' alignment rather than treating two L2
numbers as equal vectors. Per-head metrics include CPU BF16 cast changes and
two-initial same-operands independent CPU64 recurrence. Spectral factor products
are floating diagnostic estimates, not certified bounds or a new acceptance.
Exact chunk callable/source/operand-before-after/returned fingerprints are
rechecked from each retained actual capture.

Captured prefill q/k/v/g/beta belong to the candidate call to the UNMODIFIED
native chunk. The baseline's transformed prefill operands were not captured.
CPU32 normalization is an independent reference boundary, not a claim that its
bits equal native Triton normalization. CPU076 cannot claim an actual same-native
NPU counterfactual or prove a BF16 quantization explanation. Those missing items
are explicit false fields. MAIN/gdn's079 independently prepares the genuine
native chunk two-initial/repeat/common-initial counterfactual; no076 controller
or fake native call substitutes for it.

Qualification is always false; old thresholds/results are unchanged. Software
controls use synthetic CPU tensors only to test dead-NaN/live-payload/bitwise
joins and capture ABI corruption. Real two-frame numerical evidence requires
the new MAIN-owned Devices[] run, and full model/performance/task gates remain
unqualified regardless of this diagnosis.
