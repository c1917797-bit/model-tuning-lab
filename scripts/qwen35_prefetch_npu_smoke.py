"""Numerical smoke only: not a service benchmark or model correctness gate."""
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, required=True)
    args = parser.parse_args()
    import torch
    import torch_npu
    torch.npu.set_device(args.device)
    torch.manual_seed(1024)
    weight = torch.randn(8704, 5120, device="npu", dtype=torch.bfloat16)
    for batch in (1, 5, 8, 16):
        x = torch.randn(batch, 5120, device="npu", dtype=torch.bfloat16)
        reference = x @ weight.T
        torch.npu.synchronize()
        torch_npu.npu_prefetch(weight, x, int(weight.numel() * weight.element_size() * 0.1), 0)
        actual = x @ weight.T
        torch.npu.synchronize()
        equal = torch.equal(reference, actual)
        print(json.dumps({"batch": batch, "device": args.device, "dtype": "bfloat16",
                          "equal": equal, "max_abs_error": (reference.float() - actual.float()).abs().max().item(),
                          "performance_evidence": False}), flush=True)
        if not equal:
            raise RuntimeError("prefetch numerical smoke failed")


if __name__ == "__main__":
    main()
