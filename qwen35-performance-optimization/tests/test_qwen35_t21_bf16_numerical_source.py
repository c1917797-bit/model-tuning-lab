#!/usr/bin/env python3
"""Static contract checks for the T21 exact-shape BF16 numerical gate."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools" / "qwen35_t21_bf16_numerical_gate.cpp"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for required in (
        "constexpr int64_t kHidden = 5120;",
        "constexpr int64_t kIntermediate = 4352;",
        "constexpr int64_t kGateUp = 2 * kIntermediate;",
        "constexpr int64_t kOutput = 5120;",
        "aclnnSwigluGatedMlpGetWorkspaceSize(",
        "aclnnMatmulGetWorkspaceSize(",
        "aclnnSwiGluGetWorkspaceSize(",
        "nonFinite == 0",
        "maxAbs <= kMaxAbsLimit",
        "relativeL2 <= kRelativeL2Limit",
        'rows != 1 && rows != 5 && rows != 8 && rows != 16',
        '"passed\\":%s',
    ):
        assert required in text, required

    # The reference must remain an official operator chain. A local sigmoid
    # or activation implementation would silently weaken upstream-first.
    for forbidden in (
        "aclnnSiluGetWorkspaceSize",
        "aclnnMulGetWorkspaceSize",
        "std::exp(",
        "1.0F / (1.0F +",
    ):
        assert forbidden not in text, forbidden

    tensor_scope_end = text.index("ACL_CHECK(aclrtDestroyStream(stream));")
    last_tensor = text.rindex("DeviceTensor activated", 0, tensor_scope_end)
    assert last_tensor < tensor_scope_end
    assert text.index("ACL_CHECK(aclrtResetDevice(0));") > tensor_scope_end

    print("PASS: T21 BF16 source contract")


if __name__ == "__main__":
    main()
