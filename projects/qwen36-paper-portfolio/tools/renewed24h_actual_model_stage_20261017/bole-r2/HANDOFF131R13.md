# R13 first native vocabulary operand diagnostic

R12 actual1154 failed raw finite FP32 canonical guard, before tree raw. Its
original composite predicate does not identify dtype vs finite vs dimensions.
Do not reinterpret this as model math FAIL, or assume BF16 without actual data.
Source of base logits_processor and vocab_parallel_embedding confirms no base
FP32 contract; active Ascend PluggableLayer still needs its exact source identity.

First canonical input is saved BEFORE old canonical as complete original-dtype
CPU tensor, shape/stride/dtype, NaN/+Inf/-Inf/finite counts whole and provisional
canonical rank-major valid/pad regions, and live processor/quantmethod sources.
Only exact finite BF16/FP32 accepted; source-bound actual Ascend processor and
unquantized method must match exact class/receiver/function/file identity.
Finite BF16 promotes exactly toFP32 with bitwise roundtrip/unchanged-input gate,
then the old canonical body runs unchanged. Native compute_logits return is never
changed. No finite relaxation, padding mask, epsilon or gather arithmetic changes.
4MiB/rank reserved WITHIN original1GiB plus32MiB private calibration reservation.
Original TP4/3600/180/48GiB and all owner/source/output safeguards remain.
This packet is diagnostic ONLY: actual old failure and no model qualification.
