"""Bind actual013 successful owners to a NEW source; no container/torch."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--template-sha256');ap.add_argument('--numeric-owner-ref');ap.add_argument('--cpu-owner-ref');a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 raw=(P/'SOURCE_TEMPLATE.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=a.template_sha256:raise ValueError('exact template')
 m=json.loads(raw);p=P/'SOURCE_MANIFEST.json'
 if p.exists()or m['root']!=str(P)or m['default_enabled']is not False:raise ValueError('new absent final source')
 for r in m['files'].values():
  b=Path(r['path']).read_bytes()
  if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('source closure')
 spec=importlib.util.spec_from_file_location('_dl004_bind_prereq',P/'prerequisite.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
 nr,cr=json.loads(a.numeric_owner_ref),json.loads(a.cpu_owner_ref);ready=R.admission(m,nr,cr)
 template_ref=R.ref(P/'SOURCE_TEMPLATE.json');m['dependencies'].append(template_ref)
 m.update(numeric_owner_ref=nr,CPU_owner_ref=cr,component_readset=ready['readset'],bound_actual016=True,binding_template_ref=template_ref)
 with p.open('x',encoding='utf8')as f:json.dump(m,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(R.ref(p)))
if __name__=='__main__':main()
