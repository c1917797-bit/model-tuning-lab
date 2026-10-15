"""Freeze actual guard result identities; never creates a qualification/PASS."""
import argparse,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256',required=True);p.add_argument('--guard-owner-ref',required=True);p.add_argument('--reviewed-guard-template-ref',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 s=importlib.util.spec_from_file_location('_composite022_bind',HERE/'composite.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
 t=HERE/'SOURCE_TEMPLATE.json';b=t.read_bytes();C.need(C.hashlib.sha256(b).hexdigest()==a.template_sha256,'reviewed exact022 template');m=json.loads(b);C.need(m['prepared_only']is True and m['default_enabled']is False and m['root']==str(HERE),'defaultOFF prepared-only022')
 for r in m['files'].values():C.checked(r)
 read=C.Reader();gr=json.loads(a.guard_owner_ref);g=read(gr);C.terminal(g,g['source'],'numeric',cpu=False,physical=[4]);C.need(g['schema']=='deltalog.lifecycle-actual-owned-host/v007'and g['lifecycle_gate_pass']is True,'actual new physical4 terminal guard')
 gm=read(g['source']);reviewed=json.loads(a.reviewed_guard_template_ref);read(reviewed)
 C.need(gm['prepared_template']==reviewed and Path(gm['root']).name.startswith('deltalog-regression137-guard-new48h-v1-020-physical4'),'MAIN reviewed exact physical4 successor template, not old pending020')
 m['prepared_only']=False;m['policy'].update(owner020=gr,guard_source=g['source'],guard_template=gm['prepared_template'],guard_physical=[4]);m['prepared_template']=dict(path=str(t),bytes=len(b),sha256=a.template_sha256)
 def refs(x):
  if type(x)is dict:
   if set(x)=={'path','bytes','sha256'}:yield x
   else:
    for v in x.values():yield from refs(v)
  elif type(x)is list:
   for v in x:yield from refs(v)
 closure=list(refs(m['policy']))+[m['prepared_template']]
 for r in(m['policy']['source016'],m['policy']['source019'],g['source'],g['result'],g['independent_consumer']):closure.extend(refs(read(r)))
 stage=read(g['result']);closure.extend(refs(read(stage['actual_result'])))
 unique={}
 for r in closure:
  C.checked(r);C.need(r['path']not in unique or unique[r['path']]==r,'no path alias/overwrite in closed readset');unique[r['path']]=r
 m['diagnostic_input_refs']=list(unique.values())
 # Full source/Meta/numeric/raw qualification occurs only in entry.consume.
 out=Path(a.output);C.need(out.parent==HERE and not out.exists(),'new immutable bound022 source')
 with out.open('x',encoding='utf8')as f:json.dump(m,f,sort_keys=True,allow_nan=False);f.write('\n')
 print(json.dumps(dict(path=str(out),bytes=out.stat().st_size,sha256=C.hashlib.sha256(out.read_bytes()).hexdigest())))
 return 0
if __name__=='__main__':raise SystemExit(main())
