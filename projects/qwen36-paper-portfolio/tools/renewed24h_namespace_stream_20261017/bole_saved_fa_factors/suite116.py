import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import entry
if __name__=='__main__':
 sys.argv=[sys.argv[0],'--software'];raise SystemExit(entry.main())
