"""Default-OFF exact source13 to G3 layer4; source preparation only."""
import argparse,ast,hashlib,json,os,stat
from pathlib import Path
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
SP=(994678,'545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345');MP=(17849,'f02c246647df27615be5f39c48f485bad9af819ef273bebc6fa9dc123e110095')
PMP=(4706,'df541572473f72e1984692496c99dad181221a7768b55e440a7d10cf5a42b8a5');PIP=(27012,'1d3c7243aae9945445668de5e5cf0cf5c21127c1a2414e44b20116976aeacd77')
BP={'service_runner.py':(47053,'e1267ccc0120cad55979fcaef10abea292ac9f88aaab2fb4f7a393a14281e9bc'),'g2_state.py':(15173,'9a3e70e865fd9807e0d9de7e8f43b7b06d8431fc4b23b0877cb3d0b57eefc228'),'live_owner.py':(11473,'23374dc2867199bdd8279bc5fd6ea7176b8d8d1c5a8d569a87a1cc1ebdf9817e'),'worker_bootstrap.py':(6344,'817eb87e60b887099117b6865b70685a80ebe622228a72f1cd245c046da3c7b6'),'server090.py':(2439,'6cc98b337284ec4e123833da7f8a2af30d4487a4cbe811c41fd13b7f20f7b6e7'),'g2_channel.py':(16728,'f52484f64a63f4dd679c554006adba580b0edec341e35e0bceae039c4ac2e1af')}
DP={'service_runner.py':(46205,'aa312ee3f0ff9edd6f98717e025f85f47f8821dd7a3a4611d13aaad9bbd81796'),'g2_state.py':(14686,'25c8aadf64b3bd9cae345959527389bf2b9e5ad4ca8fea7995de0294855fad29'),'live_owner.py':(11771,'73aa423a172acee41080887863b818ef976238163b12fd7dbc400bd6af7e2bc9'),'worker_bootstrap.py':(6402,'ee51872e185a92e2ffcd88917019719e340bf432e5aac7988c4a87781caaed1d'),'server090.py':(2439,'dd326a1a584ca8b935ee726c7aba2d0ab0b563f394ade9609d6a1cc275404794'),'g2_channel.py':(9536,'f7eb4b071d8427e5db933f87ac81e91f0e201d1382b020a70004d9351b2b758e')}
BUDGET_PIN=(3371,'393993b390f87b0a57b149f45b74c8c97873445e37f2a67cd647197eeb895eae');IDENTITY_PIN=(1373,'1e34183361db6bd19dcbba777895d4e23a492004cb2d31260c73d642a6528c7c')
PRIOR_NAMES={'host_service.py','g2_finalize.py','service_client.py','g2_numeric.py','g3_readset.py','g3_fia_contract.py','g3_fa_consumer.py','g2_contract.py','g2_coverage.py','service_fia.py'}
def need(v,s):
 if not v:raise ValueError(s)
def H(b):return hashlib.sha256(b).hexdigest()
def read(p):
 p=Path(p);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute/no symlink:'+str(p));a=p.stat();need(stat.S_ISREG(a.st_mode),'regular file');b=p.read_bytes();z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and len(b)==a.st_size,'stable read:'+str(p));return b
def ref(p,b=None):
 b=read(p)if b is None else b;return dict(path=str(p),bytes=len(b),sha256=H(b))
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64 and all(c in'0123456789abcdef'for c in r['sha256']),'typed Ref3');b=read(r['path']);need(ref(r['path'],b)==r,'exact full Ref3:'+r['path']);return b
def pin(p,pair):
 b=read(p);need((len(b),H(b))==pair,'full pin:'+str(p));return b
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p,b)
def dump(p,v):return write(p,(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
def ad(n):return ast.dump(n,include_attributes=False)
def start(n):return min([n.lineno,*[x.lineno for x in getattr(n,'decorator_list',[])]])
def seg(s,n):return ''.join(s.splitlines(keepends=True)[start(n)-1:n.end_lineno])
def index(s):
 tree=ast.parse(s);out={}
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
   need(n.name not in out,'unique top node');out[n.name]=n
   if isinstance(n,ast.ClassDef):
    for c in n.body:
     if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef)):
      key=n.name+'.'+c.name;need(key not in out,'unique class method');out[key]=c
 return tree,out
def splice(s,replacements):
 _,ns=index(s);need(set(replacements)<=set(ns),'all selected nodes exist');spans=sorted((start(ns[k]),ns[k].end_lineno,k)for k in replacements)
 for a,b in zip(spans,spans[1:]):need(a[1]<b[0],'nonoverlapping selected nodes')
 lines=s.splitlines(keepends=True)
 for lo,hi,k in reversed(spans):
  part=replacements[k];need(part.endswith('\n'),'complete node source');lines[lo-1:hi]=[part]
 return ''.join(lines)
def import_node(text):
 body=ast.parse(text).body;need(len(body)==1 and isinstance(body[0],(ast.Import,ast.ImportFrom)),'one explicit import');return body[0]
def without_imports(s,import_texts):
 wanted={ad(import_node(x))for x in import_texts};tree=ast.parse(s);found=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))and ad(n)in wanted]
 need(len(found)==len(wanted)and {ad(n)for n in found}==wanted,'exact unique added imports');lines=s.splitlines(keepends=True)
 for n in sorted(found,key=lambda n:n.lineno,reverse=True):
  need(n.col_offset==0 and n.lineno==n.end_lineno,'one full top import line');lines[n.lineno-1:n.end_lineno]=[]
 return ''.join(lines)
def closed_donor_layer(base,donor,selected,extra_imports,allow_module_doc=False):
 bt,bn=index(base);dt,dn=index(donor);need(set(selected)<=bn.keys()and set(selected)<=dn.keys(),'reviewed selected nodes exist')
 wanted={ad(import_node(x))for x in extra_imports};newimports=[n for n in dt.body if isinstance(n,(ast.Import,ast.ImportFrom))and ad(n)in wanted]
 need(len(newimports)==len(wanted)and {ad(n)for n in newimports}==wanted,'exact donor imports');need(not any(isinstance(n,(ast.Import,ast.ImportFrom))and ad(n)in wanted for n in bt.body),'imports are new in actual13')
 filtered=[n for n in dt.body if not(isinstance(n,(ast.Import,ast.ImportFrom))and ad(n)in wanted)];need(len(bt.body)==len(filtered),'closed module statement count');ignored_doc=[]
 for position,(b,d)in enumerate(zip(bt.body,filtered)):
  if isinstance(b,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))and b.name in selected:need(type(b)is type(d)and b.name==d.name,'same selected top slot')
  elif allow_module_doc and position==0 and isinstance(b,ast.Expr)and isinstance(d,ast.Expr)and isinstance(b.value,ast.Constant)and isinstance(d.value,ast.Constant)and type(b.value.value)is str and type(d.value.value)is str:
   if ad(b)!=ad(d):ignored_doc.append(dict(before=b.value.value,donor=d.value.value,applied=False))
  else:
   need(ad(b)==ad(d),'unreviewed top AST difference at '+str(position))
   if isinstance(b,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):need(seg(base,b)==seg(donor,d),'unselected whole node unchanged:'+b.name)
 replacements={name:seg(donor,dn[name])for name in selected};result=splice(base,replacements);tree=ast.parse(result);groups={};slot=0
 for n in dt.body:
  if isinstance(n,(ast.Import,ast.ImportFrom))and ad(n)in wanted:
   need(n.col_offset==0 and n.lineno==n.end_lineno,'single donor import line');groups.setdefault(slot,[]).append(seg(donor,n))
  else:slot+=1
 for slot,parts in sorted(groups.items(),reverse=True):
  offset=sum(map(len,result.splitlines(keepends=True)[:start(tree.body[slot])-1]))if slot<len(tree.body)else len(result);result=result[:offset]+''.join(parts)+result[offset:]
 stripped=without_imports(result,extra_imports)if extra_imports else result
 recovered=splice(stripped,{name:seg(base,bn[name])for name in selected});need(recovered==base,'whole node/import inverse to actual13');_,rn=index(result)
 for name in selected:need(ad(rn[name])==ad(dn[name]),'exact donor AST applied:'+name)
 for name,n in bn.items():
  top=name.split('.',1)[0]
  if top not in selected:need(seg(base,n)==seg(result,rn[name]),'all other whole definitions retained:'+name)
 return result,dict(selected_nodes=list(selected),added_imports=extra_imports,ignored_module_doc=ignored_doc,whole_inverse_verified=True)
p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--prepare',action='store_true');p.add_argument('--source-ref');p.add_argument('--old-packet',type=Path);p.add_argument('--prior-manifest-ref');p.add_argument('--new-layer',type=Path);a=p.parse_args()
if not a.prepare:print(json.dumps(dict(enabled=False,NPU=False,source_only=True),sort_keys=True));raise SystemExit(0)
need(all(v is not None for k,v in vars(a).items()if k!='prepare'),'all exact refs and paths required')
sr=json.loads(a.source_ref);sb=checked(sr);need((len(sb),H(sb))==SP,'actual SOURCE13 pin');m=json.loads(sb);root=Path(m['root'])
need(root==Path(sr['path']).parent and Path(sr['path']).name=='SOURCE_BOUND.json'and m['service_required_sameimage_software_cases']==349,'exact owned source13/349')
need(a.old_packet==T/'g3_long_output_v2'and a.new_layer==T/'g3_source13_layer_v4'and not a.new_layer.exists(),'exclusive exact donor/new leaf');need(a.new_layer.parent.is_dir(),'existing T')
pr=json.loads(a.prior_manifest_ref);need(Path(pr['path'])==T/'g3_source13_layer_v3'/'LAYER_MANIFEST.json','actual layer3 manifest path');pmb=checked(pr);need((len(pmb),H(pmb))==PMP,'actual layer3 manifest full pin');pm=json.loads(pmb)
need(pm['schema']=='bole.G3-source13-layer3-preparation/v1'and pm['baseline_source']==sr and pm['formal_frozen']is False,'same partial source13 layer3');need(set(pm['files'])==PRIOR_NAMES,'exact prior ten files')
pir=pm['whole_inverse'];need(Path(pir['path'])==T/'g3_source13_layer_v3'/'WHOLE_INVERSE.json','actual layer3 inverse path');pib=checked(pir);need((len(pib),H(pib))==PIP,'actual layer3 inverse full pin')
outputs={};previous={}
for name,r in pm['files'].items():
 need(Path(r['path'])==T/'g3_source13_layer_v3'/name,'owned previous source operand');outputs[name]=checked(r);previous[name]=r
omb=pin(a.old_packet/'MANIFEST.json',MP);om=json.loads(omb);base={};before_refs={};donor={};donor_refs={}
for name in BP:
 r=m['files'][name];need(Path(r['path'])==root/name,'actual source-owned actor');b=checked(r);need((len(b),H(b))==BP[name],'actual13 actor full pin');base[name]=b;before_refs[name]=r
 d=pin(a.old_packet/name,DP[name]);iv=om['inventory'][name];need(type(iv)is dict and set(iv)=={'path','bytes','sha256'}and Path(iv['path']).name==name and(iv['bytes'],iv['sha256'])==DP[name],'exact donor inventory bytes; advisory path lineage only');donor[name]=d;donor_refs[name]=ref(a.old_packet/name,d)
changes={}
plans={'service_runner.py':(('install',),['import g3_fia_contract as DOMAIN\n','import g3_budget as BUDGET\n'],True),'g2_state.py':(('open_rank','Consumer'),['import g3_fia_contract as DOMAIN\n','import g3_fa_consumer as FAJOIN\n','import g3_budget as BUDGET\n'],False),'live_owner.py':(('LiveOwner',),['import g3_fia_contract as DOMAIN\n'],False),'worker_bootstrap.py':(('publish',),[],False)}
for name,(selected,imports,allow_doc)in plans.items():
 result,proof=closed_donor_layer(base[name].decode(),donor[name].decode(),selected,imports,allow_doc);outputs[name]=result.encode();changes[name]=proof
name='server090.py';bs=base[name].decode();ds=donor[name].decode();old='BOLE_G2_STREAM_CHANNEL_PATH';new='BOLE_G3_STREAM_CHANNEL_PATH'
need(bs.count(old)==1 and new not in bs,'unique server channel literal');result=bs.replace(old,new,1);need(result==ds and result.replace(new,old,1)==bs,'exact server literal-only donor and whole inverse');outputs[name]=result.encode();changes[name]=dict(unique_literal_before=old,unique_literal_after=new,anchor_count=1,whole_inverse_verified=True)
name='g2_channel.py';bs=base[name].decode();ds=donor[name].decode();_,bn=index(bs);_,dn=index(ds);key='Sender.metadata_bytes';need(key in bn and key in dn,'unique Sender metadata method')
expected=ast.parse("def metadata_bytes(self):\n    import g3_budget\n    C=self.C;m=C.obj(self.source)\n    return g3_budget.actual(C,m,self.rank)['bytes']\n").body[0]
need(ad(dn[key])==ad(expected),'exact approved metadata method AST');part=seg(ds,dn[key]);result=splice(bs,{key:part})
cap_before="rr['bytes']+payload['logical_tensor_bytes']+self.metadata_bytes()<=G2.RAW_CAP";cap_after="rr['bytes']+payload['logical_tensor_bytes']+G2.CHECKPOINT_CAP+self.metadata_bytes()<=G2.RAW_CAP"
need(bs.count(cap_before)==2 and cap_after not in bs and result.count(cap_before)==2,'exact two original checkpoint cap sites')
for method in('Sender.send','Sender.retain_failure'):need(method in bn and seg(bs,bn[method]).count(cap_before)==1,'one cap site in '+method)
result=result.replace(cap_before,cap_after);need(result.count(cap_after)==2,'two cap sites applied');restored=splice(result.replace(cap_after,cap_before),{key:seg(bs,bn[key])});need(restored==bs,'complete actual13 channel inverse')
_,rn=index(result);need(bn.keys()==rn.keys(),'all actual13 channel definitions retained');changed_methods={key,'Sender.send','Sender.retain_failure'}
for k,n in bn.items():
 if k=='Sender'or k in changed_methods:continue
 need(seg(bs,n)==seg(result,rn[k]),'whole channel definition retained:'+k)
for method in('Sender.send','Sender.retain_failure'):need(seg(result,rn[method]).replace(cap_after,cap_before)==seg(bs,bn[method]),'only checkpoint term changed in '+method)
need('contract'in bn and seg(bs,bn['contract'])==seg(result,rn['contract']),'actual13 metadata contract whole retained')
outputs[name]=result.encode();changes[name]=dict(selected_method=key,method_source=part,cap_before=cap_before,cap_after=cap_after,cap_anchor_count=2,contract_whole_unchanged=True,other_actual13_definitions_whole_unchanged=True,ACK_v3_and_strictfields_and_atomic_metadata_unchanged=True,whole_inverse_verified=True)
identity_ref=m['files']['identity_journal.py'];need(Path(identity_ref['path'])==root/'identity_journal.py','source-owned identity journal');identity=checked(identity_ref);need((len(identity),H(identity))==IDENTITY_PIN,'identity journal actual13 pin')
budget=pin(a.old_packet/'g3_budget.py',BUDGET_PIN);iv=om['inventory']['g3_budget.py'];need(type(iv)is dict and set(iv)=={'path','bytes','sha256'}and Path(iv['path']).name=='g3_budget.py'and(iv['bytes'],iv['sha256'])==BUDGET_PIN,'budget inventory full pin');budget_ref=ref(a.old_packet/'g3_budget.py',budget);outputs['g3_budget.py']=budget
need(set(outputs)==(PRIOR_NAMES|set(BP)|{'g3_budget.py'})and len(outputs)==17,'exact seventeen source files')
for name,b in outputs.items():compile(b,str(a.new_layer/name),'exec')
checked(sr);checked(pr);checked(pir);pin(a.old_packet/'MANIFEST.json',MP)
for r in[*previous.values(),*before_refs.values(),*donor_refs.values(),identity_ref,budget_ref]:checked(r)
a.new_layer.mkdir(mode=0o700);after_refs={name:write(a.new_layer/name,b)for name,b in outputs.items()}
rows={name:dict(before=before_refs[name],after=after_refs[name],edits=[dict(before=base[name].decode(),after=outputs[name].decode())])for name in BP}
inverse=dict(schema='bole.actual13-to-G3-fixed1024-layer4-wholeinverse/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',baseline=sr,prior_manifest=pr,prior_inverse=pir,files=rows,donor_refs=donor_refs,bounded_changes=changes,previous_files_whole_equal={name:dict(before=previous[name],after=after_refs[name])for name in previous},added_budget=dict(authority=budget_ref,after=after_refs['g3_budget.py'],whole_equal=True),unchanged_actual13_refs={'identity_journal.py':identity_ref},identity_journal_change=False,complete_actual13_channel_metadata_contract_and_ACK_v3_retained=True,known_frozen_source_whitespace_preserved=True,whole_inverse_verified=True,parent_qualification_bound=False,actual_G3_executed=False)
ir=dump(a.new_layer/'WHOLE_INVERSE.json',inverse)
manifest=dict(schema='bole.G3-source13-layer4-preparation/v1',status='PARTIAL_SOURCE_LAYER_ONLY_UNQUALIFIED',formal_frozen=False,baseline_source=sr,prior_manifest=pr,prior_inverse=pir,files=after_refs,whole_inverse=ir,parent_owner_result=None,parent_numerical_qualification=None,parent_consumer_exit=None,parent_source_audit=None,parent_qualification_bound=False,current_G3_original_cases=32,prospective_parent_fresh_cases=349,prospective_total_before_additional_controls=381,actual_sameimage_executed=False,model_ready=False,formal_timing=False,resource_execution=False)
mr=dump(a.new_layer/'LAYER_MANIFEST.json',manifest);print(json.dumps(dict(layer_manifest=mr,whole_inverse=ir,file_count=len(after_refs),files=after_refs,status=manifest['status']),sort_keys=True))
