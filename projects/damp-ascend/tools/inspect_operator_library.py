"""Same-image NO-device compiled-library/Meta gate; not NPU correctness."""
import argparse
import glob
import hashlib
import json
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if os.environ.get("DAMP_OPERATOR_NO_DEVICE") != "1" or glob.glob("/dev/davinci[0-9]*"):
        raise RuntimeError("explicit NO-device process required")
    library = Path(args.library).resolve()
    actual = hashlib.sha256(library.read_bytes()).hexdigest()
    if actual != args.sha256:
        raise RuntimeError("compiled library identity changed")
    import torch
    import torch_npu
    torch.ops.load_library(str(library))
    decode = torch.ops.qwen36_damp.decode.default
    prepare = torch.ops.qwen36_damp.prepare.default
    schema = decode._schema
    mutable = [i for i, arg in enumerate(schema.arguments)
               if arg.alias_info is not None and arg.alias_info.is_write]
    assert len(schema.arguments) == 14 and mutable == [5, 6, 7]
    assert len(prepare._schema.arguments) == 6
    assert all(ret.alias_info is None for ret in schema.returns)
    checked = []
    for batch in (1, 16):
        slots = batch + 3
        q = torch.empty((batch, 4, 128), dtype=torch.bfloat16, device="meta")
        v = torch.empty((batch, 12, 128), dtype=torch.bfloat16, device="meta")
        g = torch.empty((batch, 12), dtype=torch.float32, device="meta")
        beta = torch.empty_like(g, dtype=torch.bfloat16)
        hi = torch.empty((slots,12,128,16), dtype=torch.float16, device="meta")
        lo = torch.empty((slots,12,128,112), dtype=torch.int8, device="meta")
        scales = torch.empty((slots,12,4,112), dtype=torch.float32, device="meta")
        plan = torch.empty((12,128), dtype=torch.int32, device="meta")
        sr = torch.empty((12,128), dtype=torch.float32, device="meta")
        lengths = torch.empty(batch+1, dtype=torch.int32, device="meta")
        indices = torch.empty(batch, dtype=torch.int32, device="meta")
        prepare(q, hi, plan, plan, plan, sr)
        output = decode(q,q,v,g,beta,hi,lo,scales,plan,plan,plan,sr,lengths,indices)
        assert output.device.type == "meta" and output.dtype == torch.bfloat16
        assert tuple(output.shape) == (batch,12,128)
        checked.append(batch)
    print(json.dumps(dict(status="pass",scope="compiled-library-schema-Meta-only",
          library=str(library),sha256=actual,torch=torch.__version__,
          torch_npu=torch_npu.__version__,mutable_arguments=mutable,
          decode_schema=str(schema),prepare_schema=str(prepare._schema),batches=checked,
          not_proven=["actual NPU format","numerical correctness","graph","service","performance","task accuracy"])))

if __name__ == "__main__":
    main()
