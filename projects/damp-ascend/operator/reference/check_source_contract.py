"""Read-only source contract; not a compile or NPU numerical result."""
from pathlib import Path
import argparse
import hashlib

PIN = "96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b"

def check(native_path):
    raw = Path(native_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PIN, "native identity drift"
    native = raw.decode("utf-8").replace("\r\n", "\n")
    root = Path(__file__).resolve().parent
    ref = (root / "op_kernel/native_sr_reference.h").read_text()
    start = native.index("    __aicore__ inline void MatVecMul")
    end = native.index("    __aicore__ inline void Compute(", start)
    assert native[start:end] in ref, "native matvec/reduction methods were changed"
    start = end
    end = native.index("        LocalTensor<stateType> stateOutLocal =", start)
    assert native[start:end] in ref, "native Compute pre-rounding expression/order changed"
    assert ref.count("deltaInUb = vInUb[curVOffset] - deltaInUb;") == 1
    assert "Sub(deltaInUb" not in ref
    assert "Div(vScaled_, vOriginal_, srLocal_, DIM);" in ref
    restore = ref.index("Gather(readoutOriginal_, readoutReordered_, inverseBytes_")
    multiply = ref.index("Mul(readoutOriginal_, readoutOriginal_, srLocal_", restore)
    cast = ref.index("Cast(bf, readoutOriginal_, RoundMode::CAST_RINT", multiply)
    assert restore < multiply < cast
    cmake = (root / "CMakeLists.txt").read_text()
    assert "DAMP_BUILD_NATIVE_REFERENCE" in cmake and "--npu-arch=dav-2201" in cmake
    assert "../op_kernel/qwen36_gdn_damp" not in cmake
    for p in (root / "op_kernel").glob("*"):
        assert "PackStore" not in p.read_text(), "candidate quantizer dependency"
    print("source_contract PASS: native methods and pre-rounding Compute exact; not NPU validation")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-header", required=True)
    args = parser.parse_args()
    check(args.native_header)
