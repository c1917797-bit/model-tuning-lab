# Live collector smoke gate

Predeclared before NPU launch: two distinct smoke prompts, native tokenizer with
thinking disabled, nine forced output tokens, TP4 physical NPU4-7, same image,
same eager native FP32 recurrence, separate capture-off/on processes. No
performance or task-accuracy claim is permitted from this diagnostic.

Require exact equality of every output token ID; all four workers must observe
all 48 GDN layers, correct request/slot/position ownership, both anchors (updates
2/4), and both next-two-decay horizons. Every saved tensor has an immutable
checksum. Reject partial workers, changed source, incomplete requests and old
output directories. Capture must call the original gating/core and never write
model tensors. Full 36-row training-domain calibration is a separate gate.

Launcher: `projects/damp-ascend/tools/run_collector_smoke.py` on the canonical
host checkout. It creates only its uniquely named nonprivileged TP4 container,
preserves CANN PYTHONPATH, records image/devices/mounts/source identity, performs
same-image import plus bounded canary, preserves failures and stops/retains its
owned container. It cannot stop external containers or touch physical NPU0-3.

Raw non-overwriting launch root:
`/cache/cch/qwen36-damp-20261006/smoke-hook-v1-launch`.
Off/on outputs: `smoke-hook-v1-off` and `smoke-hook-v1-on` under the same root.
