# T23 upstream Triton GDN gating opportunity budget

Status: rejected before device testing; no NPU was used.

## Upstream candidate

vLLM-Ascend commit `c794923e62b4050b8e812ec8f0d0b635088e064d`
routes the 910B/A2 `BaseDeviceAdaptor.fused_gdn_gating` call from the
AscendC `torch.ops._C_ascend.npu_fused_gdn_gating` implementation to the
already-present Triton `fused_gdn_gating_patch` implementation. It is a
small removable monkeypatch candidate and reuses upstream code.

The upstream evidence is weak for promotion: the change reports no hardware
performance measurement, and its focused end-to-end pytest was explicitly not
run in the author environment. It therefore remains experimental even though
it was later merged.

## Exact T16 budget

The four original T16 `op_summary` files contain 5,136
`FusedGdnGating` calls per rank. Of those, 5,040 are decode shape
`12;1,12;1,12;12`; the remaining 96 are prefill shapes. The decode count is
exactly 105 tokens times 48 GDN layers.

Across ranks, the median call duration is `4.38 us` and P95 is
`4.62-4.74 us`. Translating the complete measured duration of every gating
call gives an optimistic zero-cost bound of only
`0.22316-0.22375 ms/token`.

The exact T16 c1 gap requires `6.098465 ms/token`. Even deleting the entire
operator would cover only about `3.67%` of the gap. A replacement cannot do
better than that impossible zero-cost bound.

## Decision

`reject-before-device-test`.

Do not service-test or promote the Triton routing change as a TPOT candidate.
It cannot meet the gate by itself and would add a numerically distinct kernel
without adequate upstream validation. Retain the audit only as evidence that
this accepted upstream change was considered rather than reimplemented.
