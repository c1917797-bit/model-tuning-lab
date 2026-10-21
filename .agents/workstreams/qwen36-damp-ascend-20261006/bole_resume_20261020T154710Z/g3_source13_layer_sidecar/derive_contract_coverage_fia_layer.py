#!/usr/bin/env python3
import argparse,ast,hashlib,json,os,stat
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SP=(994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
MP=(17849,'f02c246647df27615be5f39c48f485bad9af819ef273bebc6fa9dc123e110095')
BP={'g2_contract.py':(1636,'4c64e6417ffc652d62504ddd981c4e1c16028d6567299441543dbc8129c76093'),'g2_coverage.py':(4102,'7b84655015b4e944087e775c15e4a73bc7a9e5c935b4d916a57b418bf67d3c2c'),'service_fia.py':(2629,'6fab4d9af7307bd4b4aa8371dd7d8e38431a7a0dc0ff8e907cb89b786278bf24')}
DP={'g2_contract.py':(1746,'f9e545876a0e922f22408d88c997195abd3ffb4f023b9b2954e168988f47de0a'),'g2_coverage.py':(4128,'5ca09d1eda66be9c6f30cfc28880c98a6a74a662988f9d99809fe0a339da4321'),'service_fia.py':(3357,'256090262833945812d1f3c4f919f7f407209ca81f4df5ce6156c0ac90a8a417')}
PRIOR_NAMES={'host_service.py','g2_finalize.py','service_client.py','g2_numeric.py','g3_readset.py','g3_fia_contract.py','g3_fa_consumer.py'}
def need(v,s):
 if not v:raise ValueError(s)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'absolute ordinary');a=p.stat();need(stat.S_ISREG(a.st_mode),'regular');b=p.read_bytes();z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size,'stable read');return b
def ref(p,b=None):
 b=read(p)if b is None else b;return dict(path=str(p),bytes=len(b),sha256=H(b))
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int,'exact Ref3');b=read(r['path']);need(ref(r['path'],b)==r,'full Ref drift');return b
def pin(p,pair):
 b=read(p);need((len(b),H(b))==pair,'pin:'+str(p));return b
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p,b)
def dump(p,v):return write(p,(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def ad(n):return ast.dump(n,include_attributes=False)
def nodes(s):
 tree=ast.parse(s);out={}
 for n in tree.body:
  k=None
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   need(not n.decorator_list,'no decorator');k=('definition',n.name)
  elif isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):k=('assignment',n.targets[0].id)
  if k is not None:need(k not in out,'unique top definition:'+repr(k));out[k]=n
 return tree,out
def seg(s,n):return ''.join(s.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def splice(s,replacements):
 _,ns=nodes(s);need(set(replacements)<=set(ns),'existing exact node slots');ls=s.splitlines(keepends=True)
 for k in sorted(replacements,key=lambda k:ns[k].lineno,reverse=True):
  n=ns[k];part=replacements[k];need(part.endswith('\n'),'complete node line');ls[n.lineno-1:n.end_lineno]=[part]
 return ''.join(ls)
def line_end_offset(s,lineno):return sum(map(len,s.splitlines(keepends=True)[:lineno]))
p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');p.add_argument('--source-ref');p.add_argument('--old-packet',type=Path);p.add_argument('--prior-manifest-ref');p.add_argument('--new-layer',type=Path);a=p.parse_args()
if not a.prepare:print(json.dumps(dict(enabled=False,NPU=False,source_only=True)));raise SystemExit(0)
need(all(v is not None for k,v in vars(a).items()if k!='prepare'),'all exact refs/paths')
sr=json.loads(a.source_ref);sb=checked(sr);need((len(sb),H(sb))==SP,'SOURCE13');m=json.loads(sb);root=Path(m['root']);need(root==Path(sr['path']).parent and m['service_required_sameimage_software_cases']==349,'owned source13/349')
need(a.old_packet==T/'g3_long_output_v2'and a.new_layer==T/'g3_source13_layer_v3'and not a.new_layer.exists(),'exclusive exact paths');need(a.new_layer.parent.is_dir(),'existing T')
pr=json.loads(a.prior_manifest_ref);need(Path(pr['path'])==T/'g3_source13_layer_v2'/'LAYER_MANIFEST.json','explicit actual layer2 manifest');pmb=checked(pr);pm=json.loads(pmb)
need(pm['schema']=='bole.G3-source13-layer2-preparation/v1'and pm['baseline_source']==sr and pm['formal_frozen']is False,'exact unqualified layer2 context');need(set(pm['files'])==PRIOR_NAMES,'exact prior seven files')
prior_inverse=pm['whole_inverse'];need(Path(prior_inverse['path'])==T/'g3_source13_layer_v2'/'WHOLE_INVERSE.json','prior inverse path');checked(prior_inverse)
outputs={};prior_refs={}
for name,r in pm['files'].items():
 need(Path(r['path'])==T/'g3_source13_layer_v2'/name,'owned prior operand');outputs[name]=checked(r);prior_refs[name]=r
omb=pin(a.old_packet/'MANIFEST.json',MP);om=json.loads(omb);base={};br={};donor={};dr={}
for name in BP:
 r=m['files'][name];need(Path(r['path'])==root/name,'owned base actor');b=checked(r);need((len(b),H(b))==BP[name],'base actor pin');base[name]=b;br[name]=r
 d=pin(a.old_packet/name,DP[name]);iv=om['inventory'][name];need((iv['bytes'],iv['sha256'])==DP[name]and Path(iv['path']).name==name,'donor inventory');donor[name]=d;dr[name]=ref(a.old_packet/name,d)
bs=base['g2_contract.py'].decode();ds=donor['g2_contract.py'].decode();bt,bn=nodes(bs);dt,dn=nodes(ds)
values={'PROFILE_NAME':('smoke4','fixed1024'),'PROFILES':({'smoke4':4,'fixed1024':1024},{'fixed1024':1024}),'FLAG':('BOLE_G2_STREAM_ENABLE','BOLE_G3_STREAM_ENABLE'),'REPORT_CAP':(8192,4000)}
repls={}
for name,(before,after)in values.items():
 k=('assignment',name);need(k in bn and k in dn,'contract assignment');need(ast.literal_eval(bn[k].value)==before and ast.literal_eval(dn[k].value)==after,'exact constant delta:'+name);repls[k]=seg(ds,dn[k])
sk=('definition','scope');need(sk in bn and sk in dn,'scope function');counts={'schema':0,'request_count':0,'error_text':0}
def scope_delta(x,y,context=None):
 need(type(x)is type(y),'same scope structure')
 if isinstance(x,ast.Constant)and x.value!=y.value:
  if x.value=='bole.c1-two-request-stream-service/v2'and y.value=='bole.c1-single-request-fixed1024-stream-service/v3':counts['schema']+=1
  elif context=='request_count'and type(x.value)is int and x.value==2 and y.value==1:counts['request_count']+=1
  elif type(x.value)is str and 'G2'in x.value and y.value==x.value.replace('G2','G3'):counts['error_text']+=1
  else:raise ValueError('unreviewed scope literal')
 elif isinstance(x,ast.AST):
  need(x._fields==y._fields,'same AST fields')
  for field in x._fields:scope_delta(getattr(x,field),getattr(y,field),x.arg if isinstance(x,ast.keyword)and field=='value'else None)
 elif isinstance(x,list):
  need(len(x)==len(y),'same scope list length')
  for xx,yy in zip(x,y):scope_delta(xx,yy)
 else:need(x==y,'unchanged scope value')
scope_delta(bn[sk],dn[sk]);need(counts=={'schema':1,'request_count':1,'error_text':1},'exact scope literal counts');repls[sk]=seg(ds,dn[sk])
phase=splice(bs,repls)
newnames=('CALIBRATION_ALLOCATION','OTHER_EVIDENCE_ALLOCATION','FINAL_EVIDENCE_ALLOCATION')
expected=ast.parse('CALIBRATION_ALLOCATION=16*2**20\nOTHER_EVIDENCE_ALLOCATION=3*2**20\nFINAL_EVIDENCE_ALLOCATION=16*2**20\n').body
for name,e in zip(newnames,expected):
 k=('assignment',name);need(k not in bn and k in dn and ad(dn[k])==ad(e),'exact new allocation:'+name)
ek=('assignment','EVENT_METADATA_CAP');need(ek in bn and ek in dn and seg(bs,bn[ek])==seg(ds,dn[ek]),'EVENT cap expression whole unchanged')
i=dt.body.index(dn[ek]);need(dt.body[i+1:i+4]==[dn[('assignment',n)]for n in newnames],'three constants immediately after event allocation')
block=''.join(ds.splitlines(keepends=True)[dn[ek].end_lineno:dn[('assignment',newnames[-1])].end_lineno]);_,pn=nodes(phase);offset=line_end_offset(phase,pn[ek].end_lineno);newcontract=phase[:offset]+block+phase[offset:]
need(newcontract==ds,'only reviewed contract deltas whole equal donor');_,nn=nodes(newcontract);reverse=splice(newcontract,{k:seg(bs,bn[k])for k in repls})
need(reverse.count(block)==1,'unique allocation block');reverse=reverse.replace(block,'',1);need(reverse==bs,'whole contract inverse');outputs['g2_contract.py']=newcontract.encode()
bs=base['g2_coverage.py'].decode();ds=donor['g2_coverage.py'].decode();_,bn=nodes(bs);_,dn=nodes(ds);ak=('definition','audit');need(ak in bn and ak in dn,'coverage audit');newcoverage=splice(bs,{ak:seg(ds,dn[ak])});need(newcoverage==ds,'coverage sole audit delta');need(splice(newcoverage,{ak:seg(bs,bn[ak])})==bs,'whole coverage inverse');outputs['g2_coverage.py']=newcoverage.encode()
bs=base['service_fia.py'].decode();ds=donor['service_fia.py'].decode();_,bn=nodes(bs);dt,dn=nodes(ds);ck=('definition','ServiceFiaBoundary');need(ck in bn and ck in dn and isinstance(bn[ck],ast.ClassDef)and isinstance(dn[ck],ast.ClassDef),'FIA class')
phase=splice(bs,{ck:seg(ds,dn[ck])});want=ast.parse('import g3_fia_contract as DOMAIN\n').body[0];imports=[n for n in dt.body if isinstance(n,ast.Import)and ad(n)==ad(want)];need(len(imports)==1,'single exact DOMAIN import');im=imports[0];imp=seg(ds,im);need(ds.count(imp)==1 and imp not in bs,'new import exactly once');need(ds.replace(imp,'',1)==phase,'sole class and import FIA deltas')
offset=sum(map(len,ds.splitlines(keepends=True)[:im.lineno-1]));need(phase[:offset]==ds[:offset],'exact import insertion boundary');newfia=phase[:offset]+imp+phase[offset:];need(newfia==ds,'FIA construction whole donor');without=newfia.replace(imp,'',1);need(splice(without,{ck:seg(bs,bn[ck])})==bs,'whole FIA inverse');outputs['service_fia.py']=newfia.encode()
for name,b in outputs.items():compile(b,str(a.new_layer/name),'exec')
checked(sr);checked(pr);checked(prior_inverse);pin(a.old_packet/'MANIFEST.json',MP)
for r in [*prior_refs.values(),*br.values(),*dr.values()]:checked(r)
a.new_layer.mkdir(mode=0o700);orr={name:write(a.new_layer/name,b)for name,b in outputs.items()}
rows={name:dict(before=br[name],after=orr[name],edits=[dict(before=base[name].decode(),after=outputs[name].decode())])for name in BP}
inverse=dict(schema='bole.actual13-to-G3-fixed1024-layer3-wholeinverse/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',baseline=sr,prior_manifest=pr,prior_inverse=prior_inverse,files=rows,donor_refs=dr,contract_changed_assignments=list(values),contract_scope_literal_changes=counts,contract_added_allocation_constants=list(newnames),coverage_changed_functions=['audit'],FIA_changed_class='ServiceFiaBoundary',FIA_added_import=imp,previous_files_whole_equal={name:dict(before=prior_refs[name],after=orr[name])for name in prior_refs},whole_inverse_verified=True,ACKwire_and_channel_untouched=True,actual_G3_executed=False,parent_MODEL_qualified=False)
ir=dump(a.new_layer/'WHOLE_INVERSE.json',inverse)
manifest=dict(schema='bole.G3-source13-layer3-preparation/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',formal_frozen=False,baseline_source=sr,prior_manifest=pr,prior_inverse=prior_inverse,files=orr,whole_inverse=ir,parent_owner_result=None,parent_numerical_qualification=None,parent_consumer_exit=None,parent_source_audit=None,current_G3_original_cases=32,prospective_parent_fresh_cases=349,prospective_total_before_additional_controls=381,actual_sameimage_executed=False,model_ready=False,formal_timing=False)
mr=dump(a.new_layer/'LAYER_MANIFEST.json',manifest);print(json.dumps(dict(layer_manifest=mr,whole_inverse=ir,files=orr,status=manifest['status']),sort_keys=True))
