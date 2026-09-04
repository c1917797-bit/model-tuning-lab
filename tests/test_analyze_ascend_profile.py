import csv
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_ascend_profile import analyze, categorize


def test_category_precedence():
    assert categorize("aclnnMatmul_MatMulV3Common") == "matmul"
    assert categorize("recompute_w_u_fwd_kernel") == "gdn_prefill"
    assert categorize("hcom_allReduce__503") == "collective"


def test_aggregate_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "rank0" / "ASCEND_PROFILER_OUTPUT" / "kernel_details.csv"
        path.parent.mkdir(parents=True)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["Name", "Duration(us)"])
            writer.writeheader()
            writer.writerows(
                [
                    {"Name": "aclnnMatmul_MatMulV3Common", "Duration(us)": "20"},
                    {"Name": "aclnnMatmul_MatMulV3Common", "Duration(us)": "30"},
                    {"Name": "recompute_w_u_fwd_kernel", "Duration(us)": "25"},
                    {"Name": "hcom_allReduce__503", "Duration(us)": "25"},
                ]
            )
        result = analyze([tmp], top=2)
        summary = result["summary"]
        assert summary["file_count"] == 1
        assert summary["kernel_calls"] == 4
        assert summary["total_kernel_duration_us"] == 100.0
        assert summary["top_kernels"][0]["duration_us"] == 50.0
        assert result["measurement_semantics"]["not_wall_time"]
        categories = {row["name"]: row for row in summary["categories"]}
        assert categories["matmul"]["share_pct"] == 50.0
        assert categories["gdn_prefill"]["share_pct"] == 25.0


def test_msprof_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mindstudio_profiler_output" / "op_summary_test.csv"
        path.parent.mkdir(parents=True)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=["Op Name", "Task Duration(us)"]
            )
            writer.writeheader()
            writer.writerows(
                [
                    {"Op Name": "MatMulV2_ND", "Task Duration(us)": "40.5"},
                    {"Op Name": "hcom_allReduce", "Task Duration(us)": "9.5"},
                ]
            )
        result = analyze([tmp], top=2)
        assert result["summary"]["total_kernel_duration_us"] == 50.0
        assert result["files"][0]["source_format"] == "cann-msprof-op-summary"
        categories = {
            row["name"]: row for row in result["summary"]["categories"]
        }
        assert categories["matmul"]["duration_us"] == 40.5
        assert categories["collective"]["duration_us"] == 9.5


if __name__ == "__main__":
    test_category_precedence()
    test_aggregate_fixture()
    test_msprof_fixture()
    print("PASS: analyze_ascend_profile")
