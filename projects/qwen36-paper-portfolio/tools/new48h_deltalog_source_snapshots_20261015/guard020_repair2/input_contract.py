"""Pure CPU required regression input contract; reject before Torch/device."""
EXPECTED=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-precast-empirical-new48h-v1-016/REGRESSION_INPUTS.json',bytes=51545,sha256='3d24eabdd0ecdc0f76c2d8eb414a3436bd25f9f06f407db0f9751016c3ab2ed1')
def require(m,checked):
 if m.get('files',{}).get('REGRESSION_INPUTS.json')!=EXPECTED:raise ValueError('required original016 REGRESSION_INPUTS.json exact Ref missing/drift')
 checked(EXPECTED)
 return EXPECTED
