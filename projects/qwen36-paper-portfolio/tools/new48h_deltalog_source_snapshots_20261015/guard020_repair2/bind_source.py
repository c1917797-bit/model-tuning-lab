"""Bind real016 actual DSO fields to independent020 source, never a numerical PASS."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256',required=True);p.add_argument('--actual016-source-ref',required=True);a=p.parse_args()
 tr=C.ref(P/'SOURCE_MANIFEST.json');C.need(tr['sha256']==a.template_sha256,'reviewed new020template');m=C.obj(tr);oldref=json.loads(a.actual016_source_ref);old=C.obj(oldref)
 C.need(old['root'].endswith('/deltalog-precast-empirical-new48h-v1-016')and old['default_enabled']is False and old['libraries']==m['libraries']and old['kernel_source_ref']==m['kernel_source_ref']and old['validation_contract']==m['original_validation_contract']and old['regression_refs']==m['regression_refs'],'exact016 math/raw contract')
 from input_contract import require
 require(old,C.checked);require(m,C.checked)
 for k in('debug_build_ref','debug_kernel_source_ref','debug_library'):
  C.need(old.get(k)is not None,'actual015 real binding exists');C.checked(old[k]);m[k]=old[k]
 m['prepared_template']=tr;m['actual016_source_ref']=oldref;C.write(P/'BOUND_NUMERIC_SOURCE.json',m);C.source(C.ref(P/'BOUND_NUMERIC_SOURCE.json'));print(json.dumps(C.ref(P/'BOUND_NUMERIC_SOURCE.json')))
 return 0
if __name__=='__main__':raise SystemExit(main())
