"""Independent normalized common independent entry; default OFF."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bridge
if __name__=='__main__':bridge.route('independent')
