#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,stat
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SP=(994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
MP=(17849,'f02c246647df27615be5f39c48f485bad9af819ef273bebc6fa9dc123e110095')
LMP=(2533,'220f1aedc78f0424a595c18edbf933a8d3acfc0c77d4a4cff60b7d810f883014')
LIP=(100504,'a5efceffe2113e4bccadbbfaaa85a6ee33aa42b5f2a41477b5a285003d089b83')
KEEP={'host_service.py':(16159,'acc91d44a158921d965a99a650c0a8955d0fd35abebd0b862c19015efacd27c1'),'g2_finalize.py':(17565,'58bf0e8964bd7e1e27f7d1334ceb2c9dcfc333dbd48d657e0b63beef7ffa9de1')}
BASE={'service_client.py':(3120,'5173eed3d830c598eb769ca9226345be80ffc060b10b25d771ba55719bee6a3e'),'g2_numeric.py':(24756,'2e100b2f69c9c40a5022eaa067e015b184f86da37759ca904468e8f975d6996e')}
DONOR={'service_client.py':(3064,'269a3c262205fdb699abda488b0ca3bbdaa2d16281192dd2da509d423ef5b422'),'g2_numeric.py':(24956,'e2b66454b354175e1b00708ebbb70cd562a707acce34e8678ea581d7b6c2da91')}
ADDED={'g3_readset.py':(5646,'82cb2ffb494f5ece0b2f1cc728416f82795188ebcc9c72ac0e67f536c415b0a3'),'g3_fia_contract.py':(1334,'dba6a3d251b74277af4679502bc8242da63027ff379f2cb9cb0ea4f355e98400'),'g3_fa_consumer.py':(2289,'eb535e8c67e70118cd22d0c6a97a1649674252c54e05269a05231b3b87211d86')}
def need(v,s):
 if not v:raise ValueError(s)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);need(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary absolute path');a=p.stat();need(stat.S_ISREG(a.st_mode),'regular file');b=p.read_bytes();z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size,'stable read');return b
def ref(p,b=None):
 b=read(p)if b is None else b;return dict(path=str(p),bytes=len(b),sha256=H(b))
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int,'exact Ref3');b=read(r['path']);need(ref(r['path'],b)==r,'full Ref3');return b
def pin(p,pair):
 b=read(p);need((len(b),H(b))==pair,'pin:'+str(p));return b
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p,b)
def dump(p,v):return write(p,(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def funcs(s):
 out={}
 for n in ast.parse(s).body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   need(n.name not in out and not n.decorator_list,'unique undecorated function');out[n.name]=n
 return out
def seg(s,n):return ''.join(s.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def ad(n):return ast.dump(n,include_attributes=False)
p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');p.add_argument('--source-ref');p.add_argument('--old-packet',type=Path);p.add_argument('--prior-layer',type=Path);p.add_argument('--new-layer',type=Path);a=p.parse_args()
if not a.prepare:print(json.dumps(dict(enabled=False,NPU=False,source_only=True)));raise SystemExit(0)
need(all(v is not None for k,v in vars(a).items()if k!='prepare'),'all exact source/layer paths required')
sr=json.loads(a.source_ref);sb=checked(sr);need((len(sb),H(sb))==SP,'SOURCE13 pin');m=json.loads(sb);root=Path(m['root']);need(root==Path(sr['path']).parent,'source root');need(m['service_required_sameimage_software_cases']==349,'parent349')
need(a.old_packet==T/'g3_long_output_v2'and a.prior_layer==T/'g3_source13_layer_v1','exact donor/prior');need(a.new_layer==T/'g3_source13_layer_v2'and not a.new_layer.exists(),'exclusive new layer');need(a.new_layer.parent.is_dir(),'existing T')
oldmb=pin(a.old_packet/'MANIFEST.json',MP);oldm=json.loads(oldmb)
lmb=pin(a.prior_layer/'LAYER_MANIFEST.json',LMP);lm=json.loads(lmb);lib=pin(a.prior_layer/'WHOLE_INVERSE.json',LIP)
need(lm['baseline_source']==sr and lm['formal_frozen']is False,'same unqualified source layer');need(lm['whole_inverse']==ref(a.prior_layer/'WHOLE_INVERSE.json',lib),'prior inverse ref')
outputs={};lineage={}
for name,pair in KEEP.items():
 b=pin(a.prior_layer/name,pair);need(lm['actors'][name]==ref(a.prior_layer/name,b),'prior actor exact');outputs[name]=b;lineage[name]=ref(a.prior_layer/name,b)
base={};br={};donor={};dr={}
for name in BASE:
 r=m['files'][name];need(Path(r['path'])==root/name,'owned base file');b=checked(r);need((len(b),H(b))==BASE[name],'base pin');base[name]=b;br[name]=r
 d=pin(a.old_packet/name,DONOR[name]);inv=oldm['inventory'][name];need((inv['bytes'],inv['sha256'])==DONOR[name]and Path(inv['path']).name==name,'donor inventory lineage');donor[name]=d;dr[name]=ref(a.old_packet/name,d)
changes=[("for label,count in(('tree-1',G1.SCOPE['max_output_tokens']),('tree-2',G1.SCOPE['max_output_tokens']),('retirement-barrier',1)):","for label,count in(('tree-1',G1.SCOPE['max_output_tokens']),('retirement-barrier',1)):"),('bole-g2-131','bole-g3-131'),('open_url(request,timeout=600)','open_url(request,timeout=2400)')]
cs=base['service_client.py'].decode();newcs=cs
for before,after in changes:
 need(newcs.count(before)==1 and after not in newcs,'unique client anchor:'+before);newcs=newcs.replace(before,after,1)
recovered=newcs
for before,after in reversed(changes):
 need(recovered.count(after)==1,'unique client inverse');recovered=recovered.replace(after,before,1)
need(recovered==cs,'whole client inverse');cf=funcs(cs);nf=funcs(newcs);df=funcs(donor['service_client.py'].decode());need(cf.keys()==nf.keys()and 'run'in cf and 'run'in df,'run function');need(ad(nf['run'])==ad(df['run']),'new run equals reviewed G3 donor semantics')
for name in cf:
 if name!='run':need(seg(cs,cf[name])==seg(newcs,nf[name]),'unchanged client function:'+name)
outputs['service_client.py']=newcs.encode()
bs=base['g2_numeric.py'].decode();ds=donor['g2_numeric.py'].decode();bf=funcs(bs);df=funcs(ds);need('fa_math'in bf and 'fa_math'in df,'fa_math exists');d=df['fa_math'];b=bf['fa_math']
expected=ast.parse("import g3_fa_consumer\nC.need(C.ref(g3_fa_consumer.__file__)==m['files']['g3_fa_consumer.py'], 'exact independent long-prefix scratch consumer')\ng3_fa_consumer.consume(t,row,anchor,length)\n").body
need(len(d.body)==len(b.body)+3 and [ad(x)for x in d.body[:3]]==[ad(x)for x in expected]and [ad(x)for x in d.body[3:]]==[ad(x)for x in b.body],'exact scratch join followed by whole original math AST')
need(d.body[0].lineno==d.lineno+1 and d.body[2].end_lineno==d.lineno+3,'exact three immediate source lines')
block=''.join(ds.splitlines(keepends=True)[d.lineno:d.lineno+3]);need(all(x.startswith('    ')for x in block.splitlines()),'four-space donor insertion')
sig='def fa_math(t, m, row, anchor, length):\n';need(bs.count(sig)==1,'unique numeric signature');newbs=bs.replace(sig,sig+block,1);need(newbs==ds,'only numeric delta is exact three lines');need(newbs.replace(sig+block,sig,1)==bs,'whole numeric inverse');outputs['g2_numeric.py']=newbs.encode()
added_from={}
for name,pair in ADDED.items():
 b=pin(a.old_packet/name,pair);inv=oldm['inventory'][name];need((inv['bytes'],inv['sha256'])==pair and Path(inv['path']).name==name,'new module inventory');outputs[name]=b;added_from[name]=ref(a.old_packet/name,b)
for name,b in outputs.items():compile(b,str(a.new_layer/name),'exec')
checked(sr);pin(a.prior_layer/'LAYER_MANIFEST.json',LMP);pin(a.prior_layer/'WHOLE_INVERSE.json',LIP);pin(a.old_packet/'MANIFEST.json',MP)
for r in [*br.values(),*dr.values(),*lineage.values(),*added_from.values()]:checked(r)
a.new_layer.mkdir(mode=0o700);orr={name:write(a.new_layer/name,b)for name,b in outputs.items()}
rows={name:dict(before=br[name],after=orr[name],edits=[dict(before=base[name].decode(),after=outputs[name].decode())])for name in BASE}
inverse=dict(schema='bole.actual13-to-G3-fixed1024-layer2-wholeinverse/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',baseline=sr,prior_layer_manifest=ref(a.prior_layer/'LAYER_MANIFEST.json',lmb),prior_layer_inverse=ref(a.prior_layer/'WHOLE_INVERSE.json',lib),files=rows,donor_refs=dr,client_exact_changes=[dict(before=x,after=y,anchor_count=1)for x,y in changes],numeric_insertion=block,numeric_original_entire_math_body_whole_unchanged=True,added_modules={name:dict(authority=added_from[name],after=orr[name],whole_equal=True)for name in ADDED},prior_actors={name:dict(before=lineage[name],after=orr[name],whole_equal=True)for name in KEEP},whole_inverse_verified=True,actual_G3_executed=False,parent_MODEL_qualified=False)
ir=dump(a.new_layer/'WHOLE_INVERSE.json',inverse)
manifest=dict(schema='bole.G3-source13-layer2-preparation/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',formal_frozen=False,baseline_source=sr,prior_layer_manifest=ref(a.prior_layer/'LAYER_MANIFEST.json',lmb),prior_layer_inverse=ref(a.prior_layer/'WHOLE_INVERSE.json',lib),files=orr,whole_inverse=ir,parent_owner_result=None,parent_numerical_qualification=None,parent_consumer_exit=None,parent_source_audit=None,current_G3_original_cases=32,prospective_parent_fresh_cases=349,prospective_total_before_additional_controls=381,actual_sameimage_executed=False,model_ready=False,formal_timing=False)
mr=dump(a.new_layer/'LAYER_MANIFEST.json',manifest);print(json.dumps(dict(layer_manifest=mr,whole_inverse=ir,files=orr,status=manifest['status']),sort_keys=True))
