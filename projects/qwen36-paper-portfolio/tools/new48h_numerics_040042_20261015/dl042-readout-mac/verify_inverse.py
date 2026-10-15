"""Single final-readout delta only; independently recover all original math files."""
import hashlib,importlib.util,json,re
from pathlib import Path
OLD_BLOCK='        Muls(vUb_, deltaUb_, currentKeyQuery, rows);\n        PipeBarrier<PIPE_V>();\n        Add(attnUb_, attnUb_, vUb_, rows);\n'
NEW_BLOCK='        // DL_FINAL_COMPOUND_BEGIN: one local final multiply-add organization only.\n        Duplicate(vUb_, currentKeyQuery, rows);\n        PipeBarrier<PIPE_V>();\n        MulAddDst(attnUb_, deltaUb_, vUb_, static_cast<uint64_t>(rows), 1,\n                  {1, 1, 1, 8, 8, 8});\n        // DL_FINAL_COMPOUND_END\n'
def load015(root):
 s=importlib.util.spec_from_file_location('_042_original_inverse015',root/'originals/inverse015.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def verify(root):
 old=json.loads((root/'B010_ORIGINAL_SOURCE.json').read_bytes());rows=[];v=load015(root)
 for arm in ('production','debug'):
  for r in old['files']:
   if r['path']=='build_pair.py':continue
   name=r['path'];p=name.replace('key_projection','readout_mac042'if arm=='production'else'readout_mac042_debug');t=(root/'kernel'/p).read_text(encoding='utf8')
   if arm=='production':t=t.replace('readout_mac042','key_projection').replace('ReadoutMac042','KeyProjection').replace('READOUT_MAC042','KEY_PROJECTION')
   else:
    t=t.replace('readout_mac042_debug','readout_sidecar_v015').replace('ReadoutMac042Debug','ReadoutSidecarV015').replace('READOUT_MAC042_DEBUG','READOUT_SIDECAR_V015');t=v.normalized(name,t)
   if name.endswith('key_projection.h'):
    if t.count(NEW_BLOCK)!=1:raise ValueError('exact one readout MAC block')
    t=t.replace(NEW_BLOCK,OLD_BLOCK)
   b=t.encode()
   if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('inverse changes other arithmetic/IO '+arm+'/'+name)
   rows.append(dict(arm=arm,original=r,recovered=True))
 expected=(root/'originals/build015.py').read_text(encoding='utf8').replace('deltalog-readout-sidecar-source/v015','deltalog-readout-mac-source/v042').replace('deltalog-readout-sidecar-actual-build/v015','deltalog-readout-mac-actual-build/v042').replace("('readout_sidecar_v015',)","('readout_mac042','readout_mac042_debug')")
 if expected!=(root/'kernel/build_pair.py').read_text(encoding='utf8'):raise ValueError('only two-arm builder identity/loop changes')
 b=(root/'originals/build010.py').read_bytes();r=next(x for x in old['files']if x['path']=='build_pair.py')
 if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('actual original build010 provenance')
 return rows+[dict(builder_source_rewrite_exact=True),dict(original_builder_recovered=True)]
if __name__=='__main__':
 import sys
 if '--execute'in sys.argv:print(json.dumps(verify(Path(__file__).resolve().parent)))
 else:print('disabled')
