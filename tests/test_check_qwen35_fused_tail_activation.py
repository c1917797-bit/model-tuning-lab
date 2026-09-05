#!/usr/bin/env python3

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_qwen35_fused_tail_activation import check


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        log = Path(directory) / "service.log"
        rank = "\n".join(
            [
                "Decode MMAR+Add+RMSNorm compile_range=(1, 16) applicable=True",
                "Normalized 56 full-tensor MMAR attention copies",
                "Fused 112 decode MMAR+Add+RMSNorm patterns",
                "Decode MMAR+Add+RMSNorm compile_range=(17, 32768) applicable=False",
            ]
        )
        log.write_text("\n".join([rank] * 4) + "\n", encoding="utf-8")
        assert check(log, 4, 56, 112)["passed"]
        assert not check(log, 4, 64, 128)["passed"]
    print("PASS: Qwen3.5 fused-tail activation checker")


if __name__ == "__main__":
    main()
