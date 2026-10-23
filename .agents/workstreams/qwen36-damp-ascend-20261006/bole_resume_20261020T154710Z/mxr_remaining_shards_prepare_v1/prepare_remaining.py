"""Prepare remaining actual rank0 MXR shards; source-only, default OFF."""
import argparse,ast,hashlib,json,os,subprocess,sys
from pathlib import Path
W=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
P=W/'mxr_remaining_shards_prepare_v1'
BASE=W/'mxr48_complete_successor_prepare_v1/revision4'
MATERIAL=P/'materialized'
PINS={
 'prepare_successor.py':dict(path=str(BASE/'prepare_successor.py'),bytes=12886,sha256='ad5d8ea3012a1dfd590266ff0255e84b19b148fb130a1aa8877fa0baa697b028'),
 'successor_bindings.py':dict(path=str(BASE/'successor_bindings.py'),bytes=4270,sha256='df95cba24ded7381c2a35034ef3558b0399ecf02de8b00e830755754cb57eccd'),
}
def need(v,s):
 if not v:raise ValueError(s)
def ref(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary source Ref')
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'actual complete pinned Ref');return Path(r['path']).read_bytes()
def once(s,a,b):
 need(s.count(a)==1,'one exact shard successor seam '+a[:70]);return s.replace(a,b,1)
def render(shard):
 need(type(shard)is int and shard in(1,2,3),'remaining shard1/2/3 only')
 root=MATERIAL/('shard-'+str(shard))
 b=checked(PINS['prepare_successor.py']).decode();h=checked(PINS['successor_bindings.py']).decode()
 a="PREP=WORK/'mxr48_complete_successor_prepare_v1'/'revision4'"
 replacement="PREP=Path("+repr(str(root))+")"
 b=once(b,a,replacement);h=once(h,a,replacement)
 b=once(b," files=dict(files)\n"," files=dict(files)\n binding=json.loads(files['INPUT.json']);need(binding['shard']==0,'actual original shard0 binding')\n binding['shard']="+str(shard)+"\n files['INPUT.json']=(json.dumps(binding,sort_keys=True)+'\\n').encode()\n")
 b=b.replace('CURRENT24H_MXR48CTX1_CPU_001','CURRENT24H_MXR48CTX1_S%d_CPU_001'%shard)
 b=b.replace('CURRENT24H_MXR48CTX1_NPU_001','CURRENT24H_MXR48CTX1_S%d_NPU_001'%shard)
 b=once(b,"mxr48-current24h-context1-20261023-v1","mxr48-current24h-context1-s%d-20261023-v1"%shard)
 b=once(b,"selected_shard=0,rank0_real2048_layers=12","selected_shard=%d,rank0_real2048_layers=12"%shard)
 b=once(b,"if n not in('event_probe.py','event_contract.py','event_host.py')","if n not in('event_probe.py','event_contract.py','event_host.py','INPUT.json')")
 b=once(b,"prep=[PARENT_REF,REPAIR_REF,WINDOW_REF,*parent['files'].values(),","prep=[PARENT_REF,REPAIR_REF,WINDOW_REF,"+repr(PINS['prepare_successor.py'])+","+repr(PINS['successor_bindings.py'])+","+repr(ref(P/'prepare_remaining.py'))+",*parent['files'].values(),")
 out={'prepare_successor.py':b.encode(),'successor_bindings.py':h.encode()}
 for n,v in out.items():compile(v,str(root/n),'exec')
 # The complete cloned producer remains independently reversible to the same
 # original69 sources. Preserve a byte-exact inverse of this outer derivation.
 delta={n:dict(before=checked(PINS[n]).decode(),after=v.decode())for n,v in out.items()}
 inverse={}
 for n,d in delta.items():
  need(out[n].decode()==d['after'],'exact derived source');inverse[n]=d['before'].encode()
 need(inverse=={n:checked(r)for n,r in PINS.items()},'actual complete producer inverse')
 return root,out,delta
def write(path,data):
 with Path(path).open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 return ref(path)
def invoke(args):
 v=subprocess.run(['/usr/bin/python3','-I','-B',*args],capture_output=True,text=True,timeout=30)
 need(v.returncode==0,'source-only producer failed '+repr((args,v.returncode,v.stdout,v.stderr)))
 return dict(argv=args,exit=v.returncode,stdout=v.stdout,stderr=v.stderr)
def prepare():
 need(not MATERIAL.exists(),'new independent remaining-shard root, never overwrite')
 plans=[render(s)for s in(1,2,3)];MATERIAL.mkdir(mode=0o700);rows=[]
 for shard,(root,files,delta)in zip((1,2,3),plans):
  root.mkdir()
  for n,b in files.items():write(root/n,b)
  dr=write(root/'DERIVATION.json',(json.dumps(dict(schema='mxr.remaining-shard-source-delta/v1',base_refs=PINS,shard=shard,files=delta),sort_keys=True)+'\n').encode())
  ops=[invoke([str(root/'prepare_successor.py'),'--check']),invoke([str(root/'prepare_successor.py'),'--prepare'])]
  actual=json.loads(ops[-1]['stdout']);template=actual['template']
  ops.append(invoke([str(root/'prepared-source/prepare_successor.py'),'--audit-template','--template-ref',json.dumps(template)]))
  m=json.loads(checked(template));binding=json.loads(checked(m['actual_input_ref']))
  need(binding['shard']==shard and m['authority_ref']is None and m['prepared_only']is True,'actual distinct unbound shard input')
  rows.append(dict(shard=shard,derivation_ref=dr,template_ref=template,prepared=actual,operations=ops,source_files=m['files'],outputs=m['outputs']))
 index=dict(schema='mxr.remaining-rank0-shards-prepared/v1',rows=rows,parent_refs=PINS,phase_seconds_each=600,child_seconds_each=300,cleanup_seconds_each=90,serial_same_physical6=True,NPU=False,authority_created=False,qualification=False,performance=False,task=False)
 ir=write(MATERIAL/'INDEX.json',(json.dumps(index,sort_keys=True)+'\n').encode())
 return dict(index_ref=ir,templates=[r['template_ref']for r in rows],NPU=False,actual_sameimage97=False,launch_ready=False)
def check():
 for s in(1,2,3):
  _,files,_=render(s);tree=ast.parse(files['prepare_successor.py'])
  need(b"compile(checked(helper),helper['path'],'exec')"in files['prepare_successor.py'],'fixed inherited bytes reader ABI')
 return dict(three_source_derivations=True,exact_inverse=True,NPU=False,authority_created=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);g=p.add_mutually_exclusive_group();g.add_argument('--check',action='store_true');g.add_argument('--prepare',action='store_true');a=p.parse_args()
 print(json.dumps(prepare()if a.prepare else check()if a.check else dict(enabled=False,NPU=False)))
if __name__=='__main__':main()
