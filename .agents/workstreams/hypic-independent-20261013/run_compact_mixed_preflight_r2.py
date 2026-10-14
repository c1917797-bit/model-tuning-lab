"""New root after audited foreign-interruption r1; same mixed class probe."""
from pathlib import Path
import run_runner_preflight as controller
if __name__=='__main__':
    controller.ROOT=Path('/cache/cch/hypic-independent-20261013/compact-mixed-preflight-r2')
    controller.NAME='hypic-independent-compact-mixed-preflight-r2'
    controller.PROBE='independent_compact_npu_preflight.py'
    controller.main()
