"""Read-only exact-source MODEL owner reconstruction; never creates resources."""
import ast
import re
from pathlib import Path
from types import SimpleNamespace as NS
def model_role_validator(R,m,mods,c,C):
 R.need(R.ref(C.__file__)==m['files']['contract090.py'],'exact original contract090 role environment globals')
 v=R.safety_validator(m,mods,c);scope=v.create.__globals__
 R.need(scope is v.validate.__globals__,'original create/inspect share one fresh source-derived scope')
 R.need(scope['MEM']==32*2**30 and scope['PHYSICAL']==(4,5,6,7)and scope['OWNER']=='bole-root-r6-20261017-001'and scope['DOCKER']=='/usr/bin/docker','exact original dense physical4..7/logical0..3 and cap32 globals')
 R.need(mods.external025.OUT==R.OUT and R.CPU_OUT==R.OUT,'explicit MODEL context for original nonconsumer environment')
 profile=dict(schema='bole.untimed-stream-CPU-budget/v1',host=[166],model=[0,1,2],consumer=[145],reserve=[3,144],host_budget=1,model_budget=3,consumer_budget=1,reserve_budget=2,total_budget=7,TP_world_size=4,formal_timing=False)
 R.need(m['stream_resource_profile']==profile==mods.g2_host_adapter.CPU_PROFILE,'exact source-bound untimed diagnostic CPU profile')
 source_ref=m['files']['g2_host_adapter.py'];R.need(R.ref(mods.g2_host_adapter.__file__)==source_ref,'actual complete role adapter source')
 tree=ast.parse(R.checked(source_ref).read_text());installs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='install'];R.need(len(installs)==1,'one actual adapter installer')
 envs=[n for n in installs[0].body if isinstance(n,ast.FunctionDef)and n.name=='environment']
 R.need(len(envs)==1 and len(envs[0].args.args)==1 and envs[0].args.args[0].arg=='e'and not envs[0].decorator_list,'one exact original nested role environment')
 receipt=Path(m['model_receipt_root']);channel=Path(m['stream_channel_root'])
 R.need(receipt==R.OUT/'dense/receipts'and channel==receipt/'STREAM','only original MODEL receipt and stream capability paths')
 env_scope=dict(C=C,Path=Path,m=m,channel=channel,receipt=receipt,external=mods.external025)
 exec(compile(ast.Module(body=[envs[0]],type_ignores=[]),source_ref['path']+'#readonly-original-role-environment','exec'),env_scope)
 scope['_EXTERNAL']=NS(environment=env_scope['environment'],LOG=mods.external025.LOG)
 return NS(create=v.create,validate=v.validate,source=v.source,derive_pairs=v.derive_pairs,role_environment_source=source_ref,role_environment_original_AST=ast.dump(envs[0],include_attributes=False))
def ordered_model_owner_expected(R,m,sr,leaf,owned,c,mods,role):
 leaves={'dense':R.OUT/'dense','stream-consumer':R.OUT/'cpu-consumer'}
 R.need(role in leaves and Path(leaf)==leaves[role],'only two exact MODEL role leaves');leaf=Path(leaf)
 R.need(m['root']==str(R.ROOT)and m['output_root']==str(R.OUT)and R.ref(mods.owned_create.__file__)==m['files']['owned_create.py'],'actual source-bound original MODEL creator')
 name='adakv-tp4-'+leaf.parent.name+'-'+leaf.name;R.need(owned['name']==name,'original Controller name expression, no arbitrary retained name')
 profile=m['stream_resource_profile'];cpus=profile['consumer']if role=='stream-consumer'else profile['model']
 R.need(cpus==([145]if role=='stream-consumer'else[0,1,2]),'actual declared role CPU set')
 refs=mods.actual_ordered_readset
 R.need(type(refs)is list and refs and all(type(r)is dict and set(r)=={'path','bytes','sha256'}for r in refs),'full original ordered attachments including duplicates')
 calls=[]
 def boundary(label,argv,**kwargs):
  R.need(label=='unique-name'and argv==['/usr/bin/docker','ps','-a','--filter','name=^/'+name+'$','--format','{{.ID}}']and not kwargs,'exact original first unique-name boundary; no Docker/resource execution')
  calls.append((label,argv));raise R.ReadonlyCreateBoundary('original MODEL creator stopped before first resource call')
 ctl=NS(out=leaf,name=name,cpu={'guest_cpus':list(profile['model'])},expected=None,call=boundary)
 original=m['g2_callee_contract_v10']['original025_sources']['safety_host'];R.checked(original);S=NS(__file__=original['path'],DOCKER='/usr/bin/docker')
 try:mods.owned_create.create(c,S,ctl,sr,refs,role,R.ROOT)
 except R.ReadonlyCreateBoundary:pass
 else:raise ValueError('original MODEL creator did not stop at exact first boundary')
 R.need(len(calls)==1 and type(ctl.expected)is dict and ctl.expected['cid']is None,'one genuine source-owned precreate expected; no create/inspect/start')
 expected=ctl.expected
 R.need(set(expected)=={'cid','name','image','arm','source','host_sha256','guest_cpus','mounts'}and expected['arm']==role and expected['source']==sr and expected['guest_cpus']==cpus and all(owned[k]==v for k,v in expected.items()if k not in('cid','mounts')),'original complete role-specific expected core equals actual retained OWNED')
 R.need(all(type(k)is str and type(v)is tuple and len(v)==2 and type(v[0])is str and type(v[1])is bool for k,v in expected['mounts'].items()),'original creator mount tuple types')
 R.need({k:list(v)for k,v in expected['mounts'].items()}==owned['mounts'],'all original mount keys/values/readonly modes, with original insertion order retained')
 mounts=expected['mounts'];R.need(mounts[str(R.ROOT)]==(str(R.ROOT),False),'complete MODEL source remains RO')
 if role=='dense':
  R.need(mounts[str(leaf)]==(str(leaf),True)and mounts['/adakv-results']==(str(leaf),True)and all(not rw or Path(src)==leaf for src,rw in mounts.values()),'dense sole original owned RW payload')
 else:
  receipt=Path(m['model_receipt_root']);channel=Path(m['stream_channel_root'])
  R.need(mounts[str(receipt)]==(str(receipt),False)and mounts[str(channel)]==(str(channel),True)and mounts['/adakv-results']==(str(channel),True)and all(not rw or Path(src)==channel for src,rw in mounts.values()),'consumer only original nested channel RW; receipt parent RO')
 return dict(expected,cid=owned['cid'])
def model_role_owner_chain(R,m,sr,role,release_ref,c,validator,mods):
 leaves={'dense':R.OUT/'dense','stream-consumer':R.OUT/'cpu-consumer'};R.need(role in leaves,'only original dense or stream-consumer audit role');leaf=leaves[role]
 owned_ref=R.ref(leaf/'OWNED.json');owned=R.obj(owned_ref);cid=owned['cid'];cpus=[145]if role=='stream-consumer'else[0,1,2];capacity=1 if role=='stream-consumer'else 3
 R.need(type(cid)is str and re.fullmatch('[0-9a-f]{64}',cid)and owned['source']==sr and owned['arm']==role and owned['image']==c.IMAGE and owned['name']=='adakv-tp4-'+leaf.parent.name+'-'+leaf.name and owned['guest_cpus']==cpus and owned['host_sha256']==validator.source['sha256']and owned['sources']=={'safety_host.py':validator.source['sha256']},'actual complete original MODEL role/source/name/image/controller')
 expected=ordered_model_owner_expected(R,m,sr,leaf,owned,c,mods,role)
 create_ref=R.normalize(owned['create_receipt']);create=R.obj(create_ref);R.create_gate(create,owned,expected,validator)
 guest_ref=R.ref(leaf/'GUEST_CPU.json');guest=R.obj(guest_ref)
 R.need(guest['effective_cpus']==cpus and guest['effective_capacity']==capacity and guest['cgroup']=='/docker/'+cid and '/docker/'+cid in guest['process']['cgroup']and type(guest['process']['pid'])is int and guest['process']['pid']>0,'actual role-specific original CPU/cgroup/init identity')
 release_ref=R.normalize(release_ref);release=R.obj(release_ref)
 R.need(release['container']==cid and release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and release['primary_error']is None and release['protected_boundary']['own_on_protected']is False,'actual clean stopped-retained role release, no protected owner')
 before_ref,before_raw,before=R.inspect_row(release['before_inspect'],cid);after_ref,after_raw,after=R.inspect_row(release['after_inspect'],cid)
 for actual in(before,after):validator.validate(actual,expected)
 R.need(before['State']['Running']is True and before['State']['Pid']==guest['process']['pid']and not before['State'].get('OOMKilled')and after['State']['Running']is False and after['State']['Pid']==0 and not after.get('ExecIDs')and not after['State'].get('OOMKilled'),'actual role init running to stopped, no remaining exec or OOM')
 stop_ref=R.normalize(release['stop_receipt']);stop=R.obj(stop_ref)
 R.need(stop['exit_code']==0 and stop['requested_argv']==['/usr/bin/docker','stop','--time','15',cid],'actual original exact own-CID stop, never a foreign stop')
 smi_ref=R.normalize(release['release_smi']);smi=R.obj(smi_ref)
 R.need(smi['exit_code']==0 and smi['requested_argv']==['/usr/local/sbin/npu-smi','info'],'original readonly release observation retained')
 deadlines=[]
 for value in(before_raw,after_raw,stop,smi):
  R.need(value['cleanup_safety_only']is True and value['original_admission_failures']==[]and value['formal_cutoff']==R.CUTOFF and R.finite(value['formal_deadline_monotonic'])and 0<=value['cleanup_remaining_seconds']<=180 and value['cleanup_resource_snapshot']['formal_limit_bytes']==512*2**20 and value['cleanup_resource_snapshot']['aggregate_peak_rss_kib']<=512*1024,'original cleanup shared deadline/cutoff and 512MiB host bound')
  deadlines.append(value['formal_deadline_monotonic'])
 R.need(len(set(deadlines))==1,'one original controller clock across role cleanup')
 return dict(role=role,owner_ref=owned_ref,guest_ref=guest_ref,create_ref=create_ref,release_ref=release_ref,before_inspect_ref=before_ref,after_inspect_ref=after_ref,stop_ref=stop_ref,release_smi_ref=smi_ref,cid=cid,formal_deadline_monotonic=deadlines[0],role_environment_source=validator.role_environment_source,source_owned_original_inspect_and_create_reexecuted=True,resources_executed_by_readback=False,actual_live_identity_reobserved=False,numerical_model_qualification=False),owned,before
