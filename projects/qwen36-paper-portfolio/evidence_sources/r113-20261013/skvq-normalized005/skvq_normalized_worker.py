"""Actual spawn resolver; source-qualified normalization only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bridge
bridge.worker(globals())
