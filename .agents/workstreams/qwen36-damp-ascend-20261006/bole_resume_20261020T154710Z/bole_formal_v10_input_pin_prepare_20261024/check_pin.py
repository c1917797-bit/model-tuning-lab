"""V10 exact short-source pin regression, source-only; no actual qualification."""
from pathlib import Path
import sys,importlib.util,json
P=Path(__file__).resolve().parent
def module(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
 R=module(P/'formal_runtime.py','formal_composer')
 S=module(P/'short8_source_pin.py','_formal_V10_pin_control')
 with R.isolated():
  C=R.module(S.CPU_RENDERER,'_actual_V10_short_renderer')
  b=C.render();C.inverse(b)
  D=R.module(R.DELTA,'_actual_original_performance_delta')
  old_m,old_files=D.parent()
  changed=S.unchanged(old_files,b['files'],old_m,b['manifest'])
  target=next(n for n in old_files if n not in S.ALLOWED and n.endswith('.py'))
  broken=dict(b['files']);broken[target]+=b'\n'
  try:S.unchanged(old_files,broken,old_m,b['manifest'])
  except ValueError:pass
  else:raise AssertionError('unreviewed source/math change accepted')
 for p in('bole_textonly_v8_prepare_20261024/prepared-source-short8-v8','bole_client_input_v9_prepare_20261024/prepared-source-short8-v9'):
  try:S.exact_target(dict(path=str(R.WS/p/'SOURCE_BOUND.json'),bytes=1,sha256='0'*64))
  except ValueError:pass
  else:raise AssertionError('old source accepted')
 try:S.consume(dict(formal_prerequisites=None))
 except ValueError:pass
 else:raise AssertionError('missing actual predecessor accepted')
 print(json.dumps(dict(exact_current_short_source_delta=True,changed_files=len(changed),wrong_V8_V9_rejected=True,unreviewed_source_change_rejected=True,missing_actual_prerequisite_rejected=True,NPU=False,numerical_qualified=False)))
if __name__=='__main__':main()
