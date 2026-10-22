"""Default-OFF exact three-round source set for the existing paired owner. No admission."""
import argparse,ast,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_strict_timing as T
P=Path(__file__).resolve().parent
SCHEMA='bole.prepared-exact-three-trial-source-set/v1'
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 b=p.read_bytes();return T.ref(p,b)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and 0<=r['bytes']<=128*2**20,'bounded whole Ref3')
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(z.is_symlink()for z in(p,*p.parents)),'ordinary absolute exact Ref')
 need(ref(p)==r,'whole file actual Ref');return p
def obj(r):return json.loads(checked(r).read_bytes())
def helpers():
 return {n:ref(P/n)for n in ('three_trial_sources.py','render_strict_timing.py','strict_token_timing.py')}
def output_inverse(raw,output):
 text=raw.decode()
 for name,value in (('OUTPUT_POSIX',output),('CPU_OUTPUT_POSIX',output+'-CPU')):
  nodes=[n for n in ast.parse(text).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
  need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and nodes[0].value.value==value,'actual exact owned output constant '+name)
  text=T.once(text,ast.get_source_segment(text,nodes[0]),name+'='+repr('<SAME-ARM-TRIAL-OUTPUT>'+('-CPU'if name=='CPU_OUTPUT_POSIX'else '')))
 return text.encode()
def verify_equivalence(trials):
 need(len(trials)==3,'exact3 trial source pairs')
 for arm in ('native_ar','bole'):
  base=trials[0]['arms'][arm];baseline=base['files']
  for trial in trials:
   part=trial['arms'][arm];m=part['manifest'];files=part['files']
   need(set(files)==set(baseline),'exact complete same-arm source file set')
   for n,raw in files.items():
    if n=='contract090.py':
     need(output_inverse(raw,m['output_root'])==output_inverse(baseline[n],base['manifest']['output_root']),'whole contract differs ONLY two owned output constants')
    else:need(raw==baseline[n],'all same-arm mathematical/operator/optimization/observer bytes identical '+n)
 # Manifest identity/Ref differences are not hand-waved away: validate() compares
 # each COMPLETE manifest against the actual same renderer at its exact trial root.
 return True
def render(base,*,permit_materialized=False):
 base=Path(base);need(base.is_absolute()and base.parent==P and '..'not in base.parts,'explicit direct-child preparation set')
 trials=[T.render(base/('trial-'+str(i)),permit_materialized=permit_materialized)for i in range(3)]
 verify_equivalence(trials)
 return trials
def materialize(base):
 base=Path(base);need(not base.exists(),'exclusive new set, no overwrite')
 trials=render(base);base.mkdir(mode=0o700);rows=[]
 for i,b in enumerate(trials):
  t=base/('trial-'+str(i));t.mkdir(mode=0o700);arms={}
  for arm,part in b['arms'].items():
   m=part['manifest'];root=Path(m['root']);root.mkdir(mode=0o700)
   for n,raw in part['files'].items():
    f=root/n;f.parent.mkdir(parents=True,exist_ok=True)
    with f.open('xb')as stream:stream.write(raw)
   path=root/'PREPARED_MANIFEST.json'
   with path.open('xb')as stream:stream.write(json.dumps(m,sort_keys=True,allow_nan=False).encode()+b'\n')
   arms[arm]=ref(path)
  rows.append(dict(pair_index=i,arms=arms))
 v=dict(schema=SCHEMA,base=str(base),trials=rows,helpers=helpers(),source_bound=False,formal_performance=False,
        numerical_qualified=False,authority_ref=None,HTTP=False,NPU=False)
 path=base/'THREE_TRIAL_SOURCES.json'
 with path.open('xb')as stream:stream.write(json.dumps(v,sort_keys=True,allow_nan=False).encode()+b'\n')
 return ref(path)
def validate(source_set_ref):
 v=obj(source_set_ref)
 need(set(v)=={'schema','base','trials','helpers','source_bound','formal_performance','numerical_qualified','authority_ref','HTTP','NPU'}and
      v['schema']==SCHEMA and v['helpers']==helpers()and v['source_bound']is False and v['formal_performance']is False and
      v['numerical_qualified']is False and v['authority_ref']is None and v['HTTP']is False and v['NPU']is False,'exact current source-only set, never qualification')
 expected=render(Path(v['base']),permit_materialized=True)
 need(type(v['trials'])is list and len(v['trials'])==3,'allthree trials required')
 seen=set()
 for i,(row,trial)in enumerate(zip(v['trials'],expected)):
  need(set(row)=={'pair_index','arms'}and type(row['pair_index'])is int and row['pair_index']==i and set(row['arms'])=={'native_ar','bole'},'ordered explicit six source identities')
  for arm in ('native_ar','bole'):
   m=obj(row['arms'][arm]);e=trial['arms'][arm]
   need(m==e['manifest'],'complete actual renderer manifest equality, not caller recipe PASS or ignored fields')
   need(row['arms'][arm]['path']==str(Path(m['root'])/'PREPARED_MANIFEST.json')and m['root']not in seen and m['output_root']not in seen,'exact distinct own trial source/output roots')
   seen.update((m['root'],m['output_root']))
   for n,raw in e['files'].items():
    need(checked(m['files'][n]).read_bytes()==raw,'complete actual six-source bytes at exact root')
 return v
def refs(v):return [dict(pair_index=x['pair_index'],native_ar=x['arms']['native_ar'],bole=x['arms']['bole'])for x in v['trials']]
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--validate-ref');a=p.parse_args()
 need(not(a.prepare and a.validate_ref),'one explicit source-only mode')
 if a.prepare:need(a.output,'new output required');print(json.dumps(materialize(a.output)))
 elif a.validate_ref:
  v=validate(json.loads(a.validate_ref));print(json.dumps(dict(trials=3,sources=6,source_refs=refs(v),formal_performance=False,HTTP=False,NPU=False)))
 else:need(a.output is None,'explicit mode');print('{"enabled":false,"formal_performance":false,"HTTP":false,"NPU":false}')
if __name__=='__main__':main()
