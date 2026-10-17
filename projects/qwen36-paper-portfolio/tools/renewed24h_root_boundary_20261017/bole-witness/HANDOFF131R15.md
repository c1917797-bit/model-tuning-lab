# R15 — renewed authorized window + exact ABI Ref/value correction

Independent source/output identity; R14 and all prior failures stay immutable.
New user-authorized window2026-10-17T08:43:20Z to2026-10-18T08:43:20Z,
1792226600..1792313000, exact RENEW24H authority3012/cdba3464...; no conditional
extension is consumed and no historical component authority/clock is rewritten.
Only active contract/binder/worker/025 scoped clock values change. Whole3600 and
cleanup180 remain; memory32+reserve8+host.5, original output/disk/raw caps remain.

Exact actual paged component reader returns a Ref3. Previously Bridge preserved
that identity but passed it directly to adapter.native, which expects the opened
ABI object; it deterministically failed before native FA. Now self.fia_ref retains
exactRef3 and self.fia independently C.obj reopens the source-bound ABI value.
At each real _fa call, the same Ref is reopened again, source/schema/CPUreceipt
checked, immutable value equality checked, then passed to unchanged adapter.
UnknownRef/ref2/hash/source/schema cannot pass. The original Ref equality guard
is retained. Conv references already had MC/C.obj joins and remain unchanged.

Software controls execute actual producer reference extraction, real Ref IO,
actual Bridge._fa with CPU tensor inputs and unchanged adapter.native up to the
real dispatcher-schema lookup boundary. No fake NPU schema/HAL/operator result
is substituted; boundary is deliberately not executed. OldRef reproduces failure
before that boundary. Constructor callsite/field and full actual Ref/value chain
are checked, including negative mutated bytes/source/defaultOFF. Not NPU proof.

Original90 controls retained plus4, source94. Original independent oracles,
epsilon,131/C1/3nodes,HTTP10,all64/TP4 and source/lifecycle gates stay unchanged.
No publication or performance claim: old pubR3 still has three unresolved P1s
(server ON flag, preflight expected numspec8 vs2, server receipt numspec8).
After real model success, repeated production cycles and fixed1024 must be proven;
one publication then restore/plain-MTP cannot be counted as BOLE E2E benefit.
