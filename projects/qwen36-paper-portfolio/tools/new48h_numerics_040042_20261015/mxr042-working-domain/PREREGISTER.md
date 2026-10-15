# MXR working-storage domain 042 (source only)

Original 027/041 results and original ideal CPU64 failures remain unchanged. This is a new empirical working-DAG contract, not a retroactive tolerance change. Original metrics implementation and .002 Frobenius / .02 RMSE-mean / .999 R2 thresholds are unchanged. No universal CANN accumulation/Exp accuracy theorem is asserted.

## Frozen inputs and intervention

Fixed real rank0 model frames: language_model.model.layers.16.linear_attn and .40.linear_attn, each 129 tokens (64+64+1), three repeats. They were not used for the 027 maximum-error frame56 or 041 calibration; they are NOT globally unseen because the original all48 consumer previously measured them. No selection by new metrics is permitted. Exact RAW refs are fixed in SOURCE, selector additionally validates original FRAME/source/producer association. BF16 q/k/v, FP32 initial-state, real captured g/beta/scale and cu=[0,129] remain unchanged. If real captured state is not FP32, the witness branch refuses rather than silently changing ABI.

Four arms retain original native, legacy MXR candidate, unchanged original-A32 residual-refined candidate, and independent CPU64 inverse operational BF16 cast injected into the same NPU fullGDN. The intended candidate is a32_refined; legacy candidate is a negative/diagnostic arm, not required to pass. The same FP32 HF32-off policy is applied to all arms. No further order/iteration/epsilon tuning is allowed.

Separate calibration row derives only geometry from layer16 and explicitly zeros q/k/v/g/beta, fills FP32 initial state with 1.003. Three native-path repeats must return zero output and state byte-equal to initial.bfloat16().float(); all four arms are checked. This witness establishes actual supported initial-state rounding only; it does not count as a nontrivial heldout frame or validate every arithmetic boundary.

## Independent reference and decision

Reuse exact independent boundary_oracle.py 4691B/7fd2e64783f4516a99f116dc66502ff8e6b6d5591f7a1076e7ed1e6cfa9a408a. It builds its inverse from immutable inputs, never consumes candidate/native B/W/U/output/state. It includes source-documented FP32/BF16 storage boundaries, and is a canonical CPU operational model rather than instruction-exact native emulation. Original unrounded token CPU64 reference continues to be reported for every arm and for canonical-vs-ideal.

For each of the six real rows: native AND a32_refined output/state must pass original metrics against canonical; a32_refined solve-vs-independent inverse must pass; original a32_refined/native output/state peer gates must pass; every arm input/initial/cu must remain unchanged. New-domain evidence is accepted only if ALL six rows and ALL three calibration rows pass, exact raw cardinality9 / candidate hits18 / source & cleanup pass. Failed native calibration invalidates this proposed domain; it does not authorize relaxing .002. Old ideal FAIL is retained separately, not promoted. Any successful new result is bounded to these two B1 real frame shapes, not a model/graph/lifecycle/performance/task certificate.

## Budget and stop

Existing027 Owned singleton physical4 logical0, then Devices[] independent CPU, no model weight load. Phase2400 = child900 + consumer600 + cleanup90 + setup810. Guest8GiB + host512MiB + reserve8GiB; disk4GiB; raw cap256MiB (9 prior-size rows about193.2MiB). Cutoff1792135097 unchanged. CPU preflight and sourceaudit must finish before MAIN authorizes NPU; no partial or failed CPU receipt can be reused. Unknown device ownership/foreign processes and old controller observation errors remain fail-closed. No retry/search is automatic.

## Source-to-binary scope

Pinned actual Python chunk routes solve_tril -> WY -> _C_ascend fullGDN h/o at PCP1. Reviewed C++ HType=INPUT_TYPE, initial CAST_RINT, BF16 vnew/decayed-update, nonfinal BF16 state/final FP32 match the canonical model's intended boundaries. Current source-to-native-DSO build provenance is not fully established. SOURCE records this gap explicitly; actual native witness and canonical-vs-native heldout comparison calibrate the executable path empirically, not by claiming the inspected C++ HEAD produced that DSO.
