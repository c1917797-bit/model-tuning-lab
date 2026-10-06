# Frozen FP32 scale contract, revision 2

The first real-NPU run failed bitwise scale equality and is retained at
/cache/cch/qwen36-damp-20261006/equation-packing-npu-v1/report.json.
Both shapes passed FP16 payload and INT8 codes; no recurrence case was reached.

Independent diagnostic /cache/cch/qwen36-damp-20261006/scale-lowering-diagnostic-v1/report.json:
amax matches bitwise. NPU max/127 versus CPU division differs for86 and255 scales,
at most1 ULP (2.3283064365386963e-10 absolute). NPU division exactly matches CPU
FP32 reciprocal multiplication; explicit multiplication matches both devices.

Revision2 freezes s=RNE_FP32(max_abs * reciprocal_fp32), reciprocal bits0x3c010204,
value0.007874015718698502. Exact-zero groups use s=1 and codes0. INT8 uses
ties-to-even then clamp[-127,127]. All payload and FP32 scales still require
bitwise independent CPU oracle parity. No limit is relaxed. This is an explicit
finite-precision equation-derived implementation, not author-code fidelity.
Use a new output directory and source hashes; never overwrite/relabel v1.

This gate is packing plus lossless coordinate recurrence only. Compressed
recurrent accumulation, graph, serving lifecycle, task quality and performance
are separate mandatory gates.
