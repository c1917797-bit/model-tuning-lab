"""Bounded metadata ticket preparation; NOT a numerical consumer or resource owner."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path

MODEL_TEMPLATE={'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair22-repair1-20261017-001/SOURCE_TEMPLATE.json', 'bytes': 249107, 'sha256': 'b9b7c916d1d4cdb4a91068c2659d905be2802736dd0f0b43bf47a97ae7d23ef2'}
PAYLOAD={'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-selected-firstdecode-renew24h-20261017-001/SOURCE_MANIFEST.json', 'bytes': 17250, 'sha256': '413dfbf5b8dd3444cfafc19c6ce3e1e49cbb5414fb4ee1202f91a924cb232a29'}
MODEL_COMMANDS={'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair22-repair1-20261017-001/COMMANDS_FINAL.json', 'bytes': 8590, 'sha256': 'b897da469add19de08a633f69e948d88643ee030111749c3c0671ee680203fa1'}
IMAGE='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'
OUTPUT=Path('/opt/host/vnf/austinov/run-dl-firstdecode-input-R22-MAIN-001')
KEYS={'schema','model_source','payload_source','owner_ref','inspect_ref','loaded_ref','reports_ref'}

def need(v,m):
 if not v:raise ValueError(m)

def ref(path):
 p=Path(path);need(p.is_absolute()and '..'not in p.parts and all(not x.is_symlink()for x in(p,*p.parents)),'absolute ordinary no-symlink exact evidence path')
 a=p.stat();need(p.is_file(),'regular metadata evidence');h=hashlib.sha256();n=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);n+=len(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns),'stable evidence while hashing')
 return dict(path=p.as_posix(),bytes=n,sha256=h.hexdigest())

def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact actual Ref3, never future/null')
 return Path(r['path'])

def obj(r):
 p=checked(r);need(r['bytes']<=4*1024**2,'small metadata only; no raw tensor replay');body=p.read_bytes()
 need(len(body)==r['bytes']and hashlib.sha256(body).hexdigest()==r['sha256']and ref(p)==r,'exact stable parsed metadata bytes');return json.loads(body)

def load(r,name):
 p=checked(r);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def validate_rows(model_sr,payload_sr,parent,x,loaded,budget,reports,payload_root):
 need(parent['source']==model_sr and parent['status']=='failed'and parent['primary']is not None and parent['secondary']==[]and parent['all_created_containers_release_verified']is True,'preserve actual failed model owner with all original release/source gates')
 post=parent['post_work_verification'];need(post['source_after']is True and post['metadata_after_hash']is True and post['registered_cap_seconds']==900 and 0<post['actual_cap_seconds']<=900 and 0<=parent['elapsed']<=3600 and 0<=parent['cleanup_seconds']<=270,'complete actual post-work fence and newly registered R22 whole3600/original cleanup270')
 need(x['Image']==IMAGE and x['State']['Status']=='exited'and x['State']['Running']is False and x['State']['Pid']==0 and x['State']['OOMKilled']is False and not x.get('ExecIDs'),'fresh exact stopped/noExec/noOOM model inspect')
 candidates=[v for v in parent['owned_containers']if Path(v['stage']).name=='candidate']
 need(len(candidates)==1 and candidates[0]['cid']==x['Id']and candidates[0]['exact_owned_release_verified']is True,'actual candidate, not old CPU CID or unrelated old PASS')
 need(loaded['source']==model_sr and len(loaded['rows'])==4,'source-bound all4 before HTTP')
 rows={r['rank']:r for r in loaded['rows']};need(set(rows)==set(range(4))and len({r['namespace_pid']for r in rows.values()})==4,'four distinct ranks/namespaces')
 need(len({r['actual_host_process']['pid']for r in rows.values()})==4 and len({(r['actual_host_process']['pid'],r['actual_host_process']['start_ticks'])for r in rows.values()})==4,'four actual host worker identities, never namespace/host PID conflation')
 need(len(reports)==4,'no missing report or three-rank fallback');seen=set()
 for rr,r in reports:
  rank=r['domain']['rank'];need(rank in rows and rank not in seen,'no duplicate/foreign rank');seen.add(rank);b=rows[rank];p=b['actual_host_process']
  need(b['logical']==rank and b['physical']==rank+4 and r['source']==payload_sr and r['model_source']==model_sr,'actual source/logical/physical rank')
  need(r['domain']==dict(cid=x['Id'],host_pid=p['pid'],start_ticks=p['start_ticks'],physical=b['physical'],rank=rank)and r['namespace_pid']==b['namespace_pid'],'strong actual PID/start/CID/report join')
  need(Path(rr['path'])==Path(payload_root)/('FIRST-DECODE-'+str(b['namespace_pid']))/'FIRST-DECODE-REPORT.json','exact host payload report, not control alias or old run')
 need(budget['cid']==x['Id'],'actual budget CID')

def validate_registration(m,template,commands):
 need(commands['template']==MODEL_TEMPLATE and commands['payload_source']==commands['postconsumer_input_ticket']['payload_source']==PAYLOAD,'exact immutable model command/template/payload join')
 expected=dict(template['files']);need('COMMANDS_FINAL.json'not in expected,'R22 prepared spec avoids ticket self-reference');expected['COMMANDS_FINAL.json']=MODEL_COMMANDS
 bound=m['command_ticket_binding']
 need(m['root']==template['root']and m['files']==expected and m['runtime_identity']==template['runtime_identity']and m['output_root']==template['output_root']==commands['model_output_root'],'exact R22 template plus sole bound-only final ticket/files/runtime/output')
 need(bound['schema']=='deltalog.cheap-prebind-own-closure/v021'and bound['template']==MODEL_TEMPLATE and bound['ticket']==MODEL_COMMANDS and bound['resources_admitted']is bound['qualified']is bound['NPU']is False and bound['source_root_alias_is_preparation_only']is False and bound['physical_source_root']==m['root'],'real exact-root binder command phase, not preparation replay or manual file exception')
 phase=dict(schema='deltalog.r21-new-experiment-clock/v1',whole_seconds=3600,cleanup_seconds=270,postverify_seconds=900,margin_seconds=90,work_seconds=2340,cutoff_epoch=1792313000,not_retroactive=True)
 need(m['phase_budget_registration']==template['phase_budget_registration']==commands['phase_budget_registration']==phase and m['budgets']['phase_seconds']==commands['whole_seconds']==3600,'source-bound new experiment3600, fixed portfolio cutoff/no historical extension')
 need((OUTPUT/'INPUT.json').as_posix()==commands['postconsumer_input_ticket']['exclusive_new_path'],'dedicated actual registered INPUT parent')

def validate_journal(model_sr,m,commands,parent,budget,journal_ref,journal):
 expected=Path(commands['payload_leaf']).parent/'MODEL_SNAPSHOTS_LEDGER.R22repair1.json'
 need(Path(journal_ref['path'])==expected and budget['storage_proof']['model_snapshots_reservation_ref']==journal_ref and parent['post_work_verification']['storage']['model_snapshots_reservation_ref']==journal_ref,'same initial/final exact R22 snapshot journal')
 need(journal['schema']=='deltalog.model-snapshots-reservation/v1'and journal['source']==model_sr and journal['payload_source']==PAYLOAD and journal['leaf']==commands['payload_leaf']and journal['combined_opt_root']==m['output_root'],'actual new journal identity, not old R19')
 need(journal['budget_bytes']==32*2**30 and journal['payload_total_cap_bytes']==30*2**30 and journal['opt_total_cap_bytes']==2*2**30 and journal['allocated_worker_cap_bytes']==15*2**29 and journal['legacy_ledger_written']is journal['numeric_qualified']is False,'original snapshot partitions/legacy flags unchanged')
 need(journal['closed_overlay_ref']==m['firstdecode_contract']['closed_evidence_ref']==commands['required_actual_closed_evidence_ref']and journal['closed_source_ref']==m['firstdecode_contract']['closed_source_ref'],'actual typed original15 storage evidence retained, never numerical PASS')
 bound=m['firstdecode_contract']['closed_readset']['prior_released_empty_attempt']
 need(journal['prior_released_empty_attempt']==bound and bound['schema']=='deltalog.closed-released-empty-attempt/v021'and bound['numeric_qualified']is False and bound['candidate_created']is False and bound['prior_lease_terminal']is True and bound['actual_payload_bytes']==0,'same original R20r1 soleCPU released-empty typed predecessor in bound source/journal, no fabricated old PASS')

def validate_extra_prior(journal,prior):
 need(journal['prior_released_empty_r21']=={k:v for k,v in prior.items()if not k.startswith('current_')},'actual R22 extra R21 closure journal join')

def prepare(model_sr,owner_ref,inspect_ref):
 m=obj(model_sr);need(m['prepared_only']is False and m['prepared_template']==MODEL_TEMPLATE,'exact bound R22, not template/R19/old R18')
 template=obj(MODEL_TEMPLATE);commands=obj(MODEL_COMMANDS);validate_registration(m,template,commands)
 p=obj(PAYLOAD);need(m['firstdecode_contract']['payload_source']==PAYLOAD,'same immutable renewed payload')
 for r in p['files'].values():checked(r)
 root=Path(m['output_root']);need(Path(owner_ref['path'])==root/'RESULT.json','actual owner at exact registered output')
 parent=obj(owner_ref);x=obj(inspect_ref)
 if type(x)is list:need(len(x)==1,'one exact inspect row');x=x[0]
 loaded_ref=ref(root/'candidate/ALL4-LOADED.json');loaded=obj(loaded_ref)
 budget_ref=ref(root/'candidate/FIRST-DECODE-BUDGET.json');budget=obj(budget_ref)
 journal_ref=budget['storage_proof']['model_snapshots_reservation_ref'];journal=obj(journal_ref)
 validate_journal(model_sr,m,commands,parent,budget,journal_ref,journal)
 prior_module=load(m['files']['prior_released_empty_r21.py'],'_postinput_actual_prior_r21')
 import types
 prior=prior_module.documents(types.SimpleNamespace(obj=obj,need=need))
 validate_extra_prior(journal,prior)
 # Reuse the exact frozen alias and budget predicates. This import does not
 # execute consume(), Torch, engine construction, or any numerical gate.
 saved=list(sys.path);sys.path.insert(0,str(Path(PAYLOAD['path']).parent))
 try:
  for n in('firstdecode_gate','firstdecode_consume'):
   old=sys.modules.get(n)
   need(old is None or Path(old.__file__).resolve()==checked(p['files'][n+'.py']),'no ambient payload namespace')
  cli=load(p['files']['firstdecode_cli.py'],'_postinput_exact_payload_cli')
  for n in('firstdecode_gate','firstdecode_consume'):
   need(Path(sys.modules[n].__file__).resolve()==checked(p['files'][n+'.py']),'actual imported defining dependency is exact frozen payload')
  need('torch'not in sys.modules and 'torch_npu'not in sys.modules,'stdlib-only collection, not sameimage numeric execution')
  cli.Q.validate_budget(budget,model_sr,PAYLOAD,x['Id']);alias=cli.AliasIO(x,budget,None)
  need(budget['host_stage_root']==str(root/'candidate'),'registered control host root')
  reports=[]
  for row in sorted(loaded['rows'],key=lambda z:z['rank']):
   mapped=alias.mounts[Path('/adakv-results/model/capture')]/('FIRST-DECODE-'+str(row['namespace_pid']))/'FIRST-DECODE-REPORT.json'
   rr=ref(mapped);reports.append((rr,obj(rr)))
  validate_rows(model_sr,PAYLOAD,parent,x,loaded,budget,reports,budget['host_payload_root'])
  # Original R17/R18 run_owned explicitly opens this exact file; do not guess
  # worker-specific log names. Missing/truncated stop evidence hard-refuses.
  log_refs=[];joined=False
  for name in('server.stdout','server.stderr'):
   log_ref=ref(root/'candidate'/name);need(log_ref['bytes']<=64*1024**2,'bounded original actual server log')
   text=checked(log_ref).read_text(encoding='utf8',errors='replace');need(ref(log_ref['path'])==log_ref,'actual stopped log stable through content check');log_refs.append(log_ref)
   joined |= 'DiagnosticStop'in text and 'DL_FIRST_DECODE_COMPLETE_OBSERVATION_NOT_MODEL_QUALIFICATION'in text and p['files']['firstdecode.py']['path']in text
  need(joined,'actual causally source-joined stop in real stdout/stderr, not arbitrary parent failure')
  ticket=dict(schema='deltalog.firstdecode-all4-report-refs/v1',source=model_sr,payload_source=PAYLOAD,reports=[r for r,_ in reports],expected_stop_logs=log_refs)
  return ticket,dict(schema='deltalog.firstdecode-postconsumer-input/v1',model_source=model_sr,payload_source=PAYLOAD,owner_ref=owner_ref,inspect_ref=inspect_ref,loaded_ref=loaded_ref),dict(budget_ref=budget_ref,snapshot_journal_ref=journal_ref,model_commands_ref=MODEL_COMMANDS,actual_RW_aliases={str(k):str(v)for k,v in alias.mounts.items()},raw_aliases_not_rewritten=True,numerical_executed=False,qualified=False)
 finally:sys.path[:]=saved

def write(path,value):
 b=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=65536,'small control ticket cap64KiB')
 with path.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(path)

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('model-source-ref','owner-ref','inspect-ref'):p.add_argument('--'+n)
 a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 need(all(getattr(a,n.replace('-','_'))for n in('model-source-ref','owner-ref','inspect-ref')),'actual three Ref3 required')
 need(OUTPUT.is_dir()and not any(OUTPUT.iterdir()),'existing dedicated empty evidence parent, no overwrite')
 ticket,inputs,audit=prepare(*(json.loads(getattr(a,n.replace('-','_')))for n in('model-source-ref','owner-ref','inspect-ref')))
 inputs['reports_ref']=write(OUTPUT/'REPORT_REFS.json',ticket);need(set(inputs)==KEYS,'exact seven-key INPUT, no comments')
 ir=write(OUTPUT/'INPUT.json',inputs);ar=write(OUTPUT/'COLLECTION_AUDIT.json',audit)
 print(json.dumps(dict(input_ref=ir,audit_ref=ar,numerical_executed=False,qualification=False)));return 0

if __name__=='__main__':raise SystemExit(main())
