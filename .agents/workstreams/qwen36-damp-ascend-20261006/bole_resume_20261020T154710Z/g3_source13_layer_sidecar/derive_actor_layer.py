#!/usr/bin/env python3
"""SOURCE ONLY: bounded actual13 -> fixed1024 two-actor layer, no resources."""
import argparse,ast,hashlib,json,os,stat
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SOURCE_PIN=(994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
MANIFEST_PIN=(17849,'f02c246647df27615be5f39c48f485bad9af819ef273bebc6fa9dc123e110095')
HOST_PIN=(16157,'62b963b1b96b37d4320bfae5757d7526628c8613e31f6c6a75b5d24687022c41')
BASE_FINAL_PIN=(17504,'8d8b3a9af2c069792a3d923af0a43ff6ba7b8e4effba5681a17cdfb2bbcccfda')
DONOR_FINAL_PIN=(17563,'5d1ca04df1a3b108a8edce7fc46ac4a8dcf391052ea1dab1dd1c14607b4292c4')
HOST_BEFORE='until=time.monotonic()+min(900,ctl.remaining(cap=900))'
HOST_AFTER='until=time.monotonic()+min(3000,ctl.remaining(cap=3000))'
ACK_BEFORE="ack=C.obj(event['ack'])"
ACK_AFTER="ack=CH.load(event['ack'])"
TARGETS=('identity_join','finalize')
def need(v,s):
 if not v:raise ValueError(s)
def h(b):return hashlib.sha256(b).hexdigest()
def ordinary(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute/no symlink:'+str(p))
 a=p.stat();need(stat.S_ISREG(a.st_mode),'regular:'+str(p));b=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size,'stable read:'+str(p));return b
def ref(p,b=None):
 b=ordinary(p)if b is None else b;return dict(path=str(p),bytes=len(b),sha256=h(b))
def typed_ref(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64 and all(c in'0123456789abcdef'for c in r['sha256']),'typed exact Ref3')
 return r
def checked(r):
 typed_ref(r);b=ordinary(r['path']);need(ref(r['path'],b)==r,'full Ref3 drift:'+r['path']);return b
def pin(p,pair):
 b=ordinary(p);need((len(b),h(b))==pair,'whole pin:'+str(p));return b
def write_bytes(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p,b)
def write_json(p,v):return write_bytes(p,(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def parsed(text):
 tree=ast.parse(text);funcs={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   need(n.name not in funcs,'unique top function:'+n.name);need(not n.decorator_list,'no hidden function decorator:'+n.name);funcs[n.name]=n
 return tree,funcs
def segment(text,node):
 return ''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def splice(text,replacements):
 _,nodes=parsed(text);lines=text.splitlines(keepends=True)
 need(set(replacements)<=set(nodes),'existing replacement functions')
 for name in sorted(replacements,key=lambda x:nodes[x].lineno,reverse=True):
  n=nodes[name];part=replacements[name];pt,pn=parsed(part)
  need(len(pt.body)==1 and name in pn and part.endswith('\n'),'one complete same-name source function:'+name)
  lines[n.lineno-1:n.end_lineno]=[part]
 return ''.join(lines)
p=argparse.ArgumentParser(allow_abbrev=False)
p.add_argument('--prepare',action='store_true')
p.add_argument('--source-ref')
p.add_argument('--old-packet',type=Path)
p.add_argument('--new-layer',type=Path)
a=p.parse_args()
if not a.prepare:
 print(json.dumps(dict(enabled=False,NPU=False,source_only=True),sort_keys=True))
 raise SystemExit(0)
need(a.source_ref is not None and a.old_packet is not None and a.new_layer is not None,'--prepare requires exact source Ref and old/new packet paths')
sr=typed_ref(json.loads(a.source_ref));sb=checked(sr);need((len(sb),h(sb))==SOURCE_PIN,'actual13 SOURCE pin');m=json.loads(sb)
root=Path(m['root']);need(root==Path(sr['path']).parent and Path(sr['path']).name=='SOURCE_BOUND.json','actual source-owned root');need(m['service_required_sameimage_software_cases']==349,'actual13 cases349')
need(a.old_packet==T/'g3_long_output_v2','exact old-v2 donor packet');need(a.new_layer==T/'g3_source13_layer_v1'and not a.new_layer.exists(),'exclusive new layer leaf');need(a.new_layer.parent.is_dir(),'existing T')
mb=pin(a.old_packet/'MANIFEST.json',MANIFEST_PIN);old_manifest=json.loads(mb)
donor_path=a.old_packet/'g2_finalize.py';db=pin(donor_path,DONOR_FINAL_PIN)
inv=old_manifest['inventory']['g2_finalize.py'];typed_ref(inv);need(Path(inv['path']).name=='g2_finalize.py'and(inv['bytes'],inv['sha256'])==DONOR_FINAL_PIN,'manifest donor lineage bytes/hash')
files=m['files'];need(type(files)is dict,'source files')
base={};base_refs={}
for name,pair in [('host_service.py',HOST_PIN),('g2_finalize.py',BASE_FINAL_PIN)]:
 r=typed_ref(files[name]);need(Path(r['path'])==root/name,'source-owned actor:'+name);b=checked(r);need((len(b),h(b))==pair,'actual13 actor pin:'+name);base[name]=b;base_refs[name]=r
kept={}
for name in('g2_channel.py','g2_consumer.py'):
 r=typed_ref(files[name]);need(Path(r['path'])==root/name,'source-owned kept actor');checked(r);kept[name]=r
host=base['host_service.py'].decode();need(host.count(HOST_BEFORE)==1 and HOST_AFTER not in host,'unique one host time line');new_host=host.replace(HOST_BEFORE,HOST_AFTER,1)
need(new_host.replace(HOST_AFTER,HOST_BEFORE,1)==host,'whole host inverse');need(len(new_host.encode())==16159,'only two one-byte literal expansions');ast.parse(new_host)
before=base['g2_finalize.py'].decode();donor=db.decode();bt,bn=parsed(before);dt,dn=parsed(donor)
need(set(TARGETS)<=bn.keys()and set(TARGETS)<=dn.keys(),'two explicit donor/base functions');need({'owned_channel','main'}<=bn.keys(),'actual13 owned-channel/main functions')
donor_parts={name:segment(donor,dn[name])for name in TARGETS}
need(sum(v.count(ACK_BEFORE)for v in donor_parts.values())==1,'one old ACK decode seam in donor functions');need(sum(v.count(ACK_AFTER)for v in donor_parts.values())==0,'donor is the reviewed legacy seam')
replacements={name:value.replace(ACK_BEFORE,ACK_AFTER)for name,value in donor_parts.items()}
after=splice(before,replacements);at,an=parsed(after)
need(list(bn)==list(an),'same top function names/order');need(len(bt.body)==len(at.body),'same top statement count')
for left,right in zip(bt.body,at.body):
 if isinstance(left,(ast.FunctionDef,ast.AsyncFunctionDef))and left.name in TARGETS:
  need(isinstance(right,type(left))and right.name==left.name,'same replacement slot');expected=ast.parse(replacements[left.name]).body[0]
  need(ast.dump(right,include_attributes=False)==ast.dump(expected,include_attributes=False),'exact donor-plus-CH.load AST:'+left.name)
 else:need(ast.dump(left,include_attributes=False)==ast.dump(right,include_attributes=False),'unchanged actual13 top AST')
unchanged=[]
for name in bn:
 if name in TARGETS:continue
 need(segment(before,bn[name])==segment(after,an[name]),'whole unchanged function:'+name);unchanged.append(name)
need(splice(after,{name:segment(before,bn[name])for name in TARGETS})==before,'whole finalizer inverse')
need(sum(segment(after,an[name]).count(ACK_AFTER)for name in TARGETS)==1 and all(ACK_BEFORE not in segment(after,an[name])for name in TARGETS),'single source-owned CH.load seam')
outputs={'host_service.py':new_host.encode(),'g2_finalize.py':after.encode()}
for name,b in outputs.items():compile(b,str(a.new_layer/name),'exec')
checked(sr);pin(a.old_packet/'MANIFEST.json',MANIFEST_PIN);pin(donor_path,DONOR_FINAL_PIN)
for r in [*base_refs.values(),*kept.values()]:checked(r)
a.new_layer.mkdir(mode=0o700)
out_refs={name:write_bytes(a.new_layer/name,b)for name,b in outputs.items()}
rows={name:dict(before=base_refs[name],after=out_refs[name],edits=[dict(before=base[name].decode(),after=outputs[name].decode())])for name in outputs}
inverse=dict(schema='bole.actual13-to-G3-fixed1024-two-actor-wholeinverse/v1',status='SOURCE_LAYER_ONLY_UNQUALIFIED',baseline=sr,files=rows,donor=dict(packet_manifest=ref(a.old_packet/'MANIFEST.json',mb),finalizer=ref(donor_path,db),functions={name:dict(source=donor_parts[name],applied=replacements[name])for name in TARGETS}),host_exact_literal_change=dict(before=HOST_BEFORE,after=HOST_AFTER,anchor_count=1,literals_changed=2),finalizer_replaced_functions=list(TARGETS),unchanged_finalizer_functions=unchanged,owned_channel_and_main_whole_unchanged=True,finalizer_imports_and_top_statements_unchanged=True,source_owned_ACK_decoder='g2_channel.load',ACK_legacy_seam_count=1,kept_actual13_actor_refs=kept,whole_inverse_verified=True,actual_parent_MODEL_qualified=False,actual_G3_executed=False)
ir=write_json(a.new_layer/'WHOLE_INVERSE.json',inverse)
manifest=dict(schema='bole.G3-source13-two-actor-layer-preparation/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',formal_frozen=False,baseline_source=sr,donor_manifest=ref(a.old_packet/'MANIFEST.json',mb),actors=out_refs,kept_actual13_actor_refs=kept,whole_inverse=ir,parent_owner_result=None,parent_numerical_qualification=None,parent_consumer_exit=None,parent_source_audit=None,additional_G3_modules_pending=True,current_G3_original_cases=32,prospective_parent_fresh_cases=349,prospective_total_before_additional_controls=381,actual_sameimage_executed=False,actual_scheduler_executed=False,formal_timing=False,model_ready=False)
mr=write_json(a.new_layer/'LAYER_MANIFEST.json',manifest)
print(json.dumps(dict(layer_manifest=mr,whole_inverse=ir,actors=out_refs,kept_actual13_actors=kept,status=manifest['status']),sort_keys=True))
