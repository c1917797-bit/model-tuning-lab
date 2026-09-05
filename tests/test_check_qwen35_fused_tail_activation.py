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
                "MMAR copy normalization diagnostics={'copy_candidates': 64, 'copy_reject_unresolved_destination': 64, 'mmar_nodes': 128} copy_targets={'aten.copy_.default': 64}",
                "Normalized 64 full-tensor MMAR attention copies",
                "Fused 128 decode MMAR+Add+RMSNorm patterns",
                "Decode MMAR+Add+RMSNorm compile_range=(17, 32768) applicable=False",
            ]
        )
        log.write_text("\n".join([rank] * 4) + "\n", encoding="utf-8")
        result = check(log, 4, 64, 128)
        assert result["passed"]
        assert len(result["diagnostics"]) == 4
        assert result["diagnostics"][0]["rejections"] == {
            "copy_candidates": 64,
            "copy_reject_unresolved_destination": 64,
            "mmar_nodes": 128,
        }
        assert result["diagnostics"][0]["copy_targets"] == {
            "aten.copy_.default": 64
        }
        assert not check(log, 4, 64, 64)["passed"]
    print("PASS: Qwen3.5 fused-tail activation checker")


if __name__ == "__main__":
    main()
