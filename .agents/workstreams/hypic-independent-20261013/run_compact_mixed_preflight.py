"""Fresh immutable mixed-class preflight using reviewed exact-CID controller."""
from pathlib import Path
import run_runner_preflight as controller
if __name__=='__main__':
    controller.ROOT=Path('/cache/cch/hypic-independent-20261013/compact-mixed-preflight-r1')
    controller.NAME='hypic-independent-compact-mixed-preflight-r1'
    controller.PROBE='independent_compact_npu_preflight.py'
    controller.main()
