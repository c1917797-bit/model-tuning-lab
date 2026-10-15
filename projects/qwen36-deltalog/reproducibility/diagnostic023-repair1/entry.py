"""Cold actual package import; defaultOFF must not import a compute backend."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from qwen36_deltalog_service import register
register()
assert 'torch'not in sys.modules and 'torch_npu'not in sys.modules
print(json.dumps(dict(default_OFF=True,compute_imported=False,NPU=False)))
