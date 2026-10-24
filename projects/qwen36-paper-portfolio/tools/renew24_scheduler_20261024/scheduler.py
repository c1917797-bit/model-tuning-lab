"""Pure MAIN portfolio decisions. No subprocess, Docker, NPU, signal or authority creation."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

LEGACY={'path':'/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/main_serial_handoff_v1/serial_batch.py',
 'bytes':18451,'sha256':'5db00aadd87482fde4647c7b04d34dea6922cc0178f719f146b64a2820b11a59'}
MAX_NODES=128
HOLD=('admitted','running','unknown','terminal-awaiting-release')
EXCLUSIVE=('tp4','model','profiling','formal')
def need(v,s):
 if not v:raise ValueError(s)
def integer(v,minimum=0):
 return type(v)is int and v>=minimum
def io():
 p=Path(LEGACY['path'])
 need(p.is_absolute()and p.is_file()and all(not q.is_symlink()for q in(p,*p.parents)),'ordinary pinned parent')
 data=p.read_bytes()
 need(len(data)==LEGACY['bytes']and hashlib.sha256(data).hexdigest()==LEGACY['sha256'],'actual parent source SHA')
 spec=importlib.util.spec_from_file_location('_renew24_original_handoff',p)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module
def ref_key(r):
 return (r['path'],r['bytes'],r['sha256'])
def nodes_checked(nodes):
 need(type(nodes)is list and len(nodes)<=MAX_NODES,'bounded finite DAG')
 by={n['id']:n for n in nodes}
 need(len(by)==len(nodes),'unique node IDs')
 roots=set()
 for n in nodes:
  need(type(n['id'])is str and n['id'] and type(n['paper'])is str and n['paper'],'named paper/node')
  need(n['kind']in('prepare','cpu','single',*EXCLUSIVE),'paper stage, not model scheduler')
  need(type(n['deps'])is list and len(set(n['deps']))==len(n['deps'])and all(d in by for d in n['deps']),'known unique DAG predecessors')
  need(n['state']in('preparing','ready','passed','repair','blocked',*HOLD,'result-pending'),'explicit separate state')
  if n.get('output_root'):
   need(n['output_root']not in roots,'unique output per attempt');roots.add(n['output_root'])
  physical=n['physical']
  need(type(physical)is list and all(type(p)is int and p in(4,5,6,7)for p in physical)and len(set(physical))==len(physical),'physical4-7 only')
  need((n['kind']in('prepare','cpu')and physical==[])or
       (n['kind']=='single'and len(physical)==1)or
       (n['kind']in EXCLUSIVE and physical==[4,5,6,7]),'exact stage mapping')
  b=n['budget']
  need(set(b)=={'ram','cpu_millis','disk'}and integer(b['ram'])and integer(b['cpu_millis'])and
       type(b['disk'])is dict and all(type(k)is str and integer(v)for k,v in b['disk'].items()),'typed joint resource demand')
  need(integer(n['wall_seconds'],1)and integer(n['critical_seconds'],1)and
       integer(n['deadline_epoch'],1)and integer(n['ready_at']),'finite stage including cleanup')
 visiting=set();done=set()
 def visit(k):
  need(k not in visiting,'acyclic paper DAG')
  if k in done:return
  visiting.add(k)
  for dep in by[k]['deps']:visit(dep)
  visiting.remove(k);done.add(k)
 for k in by:visit(k)
 return by
def readiness(n,by,reader=None,now=None):
 """READY only offers a MAIN-reviewed gate to queue; it is NOT resource admission."""
 B=reader or io()
 need(n['state']=='ready','preparing is not READY')
 for dep in n['deps']:
  parent=by[dep]
  need(parent['state']=='passed'and parent.get('acceptance_ref')is not None,'actual predecessor consumer pending '+dep)
  B.checked(parent['acceptance_ref'])
 packet=B.obj(n['packet_ref'])
 if packet.get('schema')=='bole.scheduler-stage-metadata/v1':
  need(packet.get('missing_registration')==[],'original BOLE resource registration still pending')
  helper=Path(__file__).parent/'bole_metadata.py'
  need(B.reference(helper)==packet['normalizer_ref'],'fixed source-bound BOLE metadata normalizer')
  spec=importlib.util.spec_from_file_location('_renew24_bole_metadata',helper)
  mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  need(n['gate']=={'CPU':'image-preflight','model':'model-screen','consume':'npu-numerical'}[packet['stage']],'original BOLE stage, not task/formal promotion')
  actual=mod.normalize(B,source_ref=packet['source_ref'],commands_ref=packet['commands_ref'],
   stage=packet['stage'],now=now,cpu_millis=packet['budget']['cpu_millis'],
   docker_write_bound=packet['budget']['disk']['docker'])
  need(actual==packet,'exact original BOLE metadata, not scheduler-issued permission')
  for k in('physical','budget','kind','output_root','wall_seconds','deadline_epoch'):
   need(n[k]==packet[k],'original BOLE stage '+k)
  rows=n.get('prerequisite_refs')
  need(type(rows)is list and rows and n['deps'],'MAIN consumes original source audit/current predecessor, not normalizer READY')
  for row in rows:
   need(set(row)=={'artifact_ref','consumer_ref','acceptance_ref'},'actual BOLE producer/consumer edge')
   for r in row.values():B.checked(r)
  accepted={ref_key(r['acceptance_ref'])for r in rows}
  need(all(ref_key(by[d]['acceptance_ref'])in accepted for d in n['deps']),'exact BOLE DAG predecessor consumed')
  need(not Path(n['output_root']).exists(),'fresh original BOLE role output')
  return packet
 for key in('source_ref','entry_ref','adapter_ref'):
  B.checked(packet[key])
 need(packet['id']==n['id']and packet['physical']==n['physical']and
      packet['protected']==[0,1,2,3]and packet['output_root']==n['output_root']and
      packet['wall_seconds']==n['wall_seconds']and packet['cutoff_epoch']==n['deadline_epoch'],'packet identity/mapping/budget/cutoff')
 review=B.obj(packet['review_ref'])
 need(review['schema']=='main.reviewed-stage-admission/v1'and review['reviewed_by']=='MAIN'and
      review['gate']==n['gate']and review['gate']in('image-preflight','npu-numerical','model-screen','formal-pair','final-tasks')and
      review['ready_for_gate']is True and review['state']=='ACTUAL_PREREQUISITES_CONSUMED'and review['missing']==[],'real source-specific reviewed gate, not authored READY')
 for k in('source_ref','entry_ref','adapter_ref','argv','output_root','owner'):
  need(review[k]==packet[k],'review binds exact '+k)
 need(review['ticket_id']==n['id']and review['stage_policy']=={k:packet[k]for k in
      ('image','physical','protected','wall_seconds','cutoff_epoch','result_name')},'unchanged original stage policy')
 need(review['joint_demand']==n['budget']and review['stage_kind']==n['kind'],'reviewed actual aggregate demand/kind')
 rows=review['actual_prerequisites']
 need(type(rows)is list and rows,'actual independent prerequisite consumption required')
 for row in rows:
  need(set(row)=={'artifact_ref','consumer_ref','acceptance_ref'},'original producer/consumer/acceptance triple')
  for r in row.values():B.checked(r)
 accepted={ref_key(r['acceptance_ref'])for r in rows}
 need(all(ref_key(by[d]['acceptance_ref'])in accepted for d in n['deps']),'actual DAG edge receipts consumed by original consumer')
 need(not Path(n['output_root']).exists(),'fresh attempt, no unchanged retry')
 return packet
def leases_checked(leases,by):
 need(type(leases)is list,'explicit lease list; unknowns never omitted')
 ids=set();used=set()
 for l in leases:
  need(l['id']not in ids and l['node']in by and l['state']in HOLD and
       by[l['node']]['state']in HOLD,'unique live/unknown lease; leased node cannot remain READY')
  ids.add(l['id']);n=by[l['node']]
  need(l['physical']==n['physical']and l['budget']==n['budget']and
       l['packet_ref']==n['packet_ref']and l['kind']==n['kind']and integer(l['latest_release_epoch'],1),'lease exact frozen packet/resources')
  need(not used.intersection(l['physical']),'existing leases cannot overlap')
  used.update(l['physical'])
 return leases
def fit(n,leases,snapshot,now,policy):
 need(policy['start_epoch']<=now<policy['cutoff_epoch'],'current explicit window; no renewal')
 need(0<=now-snapshot['at']<=policy['fresh_seconds'],'fresh resource observation')
 need(now+n['wall_seconds']<=min(policy['cutoff_epoch'],n['deadline_epoch']),'full phase and cleanup fit cutoff')
 need(snapshot['unknown_operations']==[],'unreconciled external operation holds admission')
 need(set(snapshot['usage'])=={l['id']for l in leases},'all live/unknown lease usages observed')
 own=set(p for l in leases for p in l['physical'])
 need(not own.intersection(n['physical']),'overlapping device lease')
 if n['kind']in EXCLUSIVE:
  need(not leases,'TP4/model/profile/formal exclusive of CPU and devices')
 elif any(l['kind']in EXCLUSIVE for l in leases):
  need(False,'exclusive comparison already reserved')
 if n['physical']:
  need(all(snapshot['cards'].get(str(p))=='idle'for p in n['physical']),'fresh actual per-card ownership, not HBM-only')
  if any(l['physical']for l in leases):
   need(policy['allow_disjoint']is True and n['kind']=='single'and
        all(l['kind']in('single','cpu')for l in leases),'explicit compatible disjoint authority')
 return _resources(n,leases,snapshot,policy)
def _resources(n,leases,snapshot,policy):
 committed_ram=n['budget']['ram']+sum(l['budget']['ram']for l in leases)+policy['scheduler_ram']
 committed_cpu=n['budget']['cpu_millis']+sum(l['budget']['cpu_millis']for l in leases)
 need(committed_ram<=snapshot['portfolio_ram_cap']and committed_cpu<=snapshot['portfolio_cpu_millis'],'ONE summed cgroup/CPU budget')
 remaining_ram=n['budget']['ram']+policy['scheduler_ram']
 for l in leases:
  u=snapshot['usage'][l['id']]
  need(integer(u['ram'])and integer(u['cpu_millis'])and all(integer(x)for x in u['disk'].values()),'typed real usage')
  remaining_ram+=max(0,l['budget']['ram']-u['ram'])
 need(remaining_ram+policy['ram_reserve']<=snapshot['mem_available'],'fresh ordinary RAM plus unspent commitments and reserve')
 fs=set(n['budget']['disk'])|set(policy['disk_reserve'])
 for l in leases:fs.update(l['budget']['disk'])
 for k in fs:
  need(k in snapshot['disk_free']and k in policy['disk_reserve'],'actual daemon/output filesystem separately observed')
  residual=n['budget']['disk'].get(k,0)+sum(max(0,l['budget']['disk'].get(k,0)-snapshot['usage'][l['id']]['disk'].get(k,0))for l in leases)
  need(residual+policy['disk_reserve'][k]<=snapshot['disk_free'][k],'summed future writes plus unchanged disk reserve '+k)
 return True
def plan(nodes,leases,snapshot,now,policy,reader=None):
 by=nodes_checked(nodes);leases_checked(leases,by)
 reader=reader or io()
 candidates=[];missing={}
 for n in nodes:
  if n['kind']=='prepare':continue
  try:readiness(n,by,reader,now=now)
  except (ValueError,KeyError,OSError)as e:missing[n['id']]=str(e);continue
  candidates.append(n)
 candidates.sort(key=lambda n:(n['critical_seconds'],n['deadline_epoch']-n['wall_seconds'],n['ready_at'],n['id']))
 exclusive=[n for n in candidates if n['kind']in EXCLUSIVE]
 # Reserve the earliest safe start of a ready exclusive edge; unknown leases make it unbounded.
 reserved=None;pending=None
 for x in exclusive:
  try:fit(x,leases,snapshot,now,policy)
  except (ValueError,KeyError)as error:
   # A future release is not observed idleness or guaranteed free RAM/disk.
   # Pending backfill boundary is separate from an ACTUALLY safe-now reservation.
   try:
    need(leases and not any(l['state']=='unknown'for l in leases),'no known finite release boundary')
    need(policy['start_epoch']<=now<policy['cutoff_epoch']and
         0<=now-snapshot['at']<=policy['fresh_seconds']and snapshot['unknown_operations']==[],'fresh known current window')
    latest=min(x['deadline_epoch'],policy['cutoff_epoch'])-x['wall_seconds']
    need(now<=latest,'full exclusive stage still fits')
    need(set(snapshot['usage'])=={l['id']for l in leases},'complete observed commitments')
    _resources(x,[],snapshot,policy)
    held=set(p for l in leases for p in l['physical'])
    need(all(p in held or snapshot['cards'].get(str(p))=='idle'for p in x['physical']),'external card state prevents future-start estimate')
    end=max(l['latest_release_epoch']for l in leases)
    need(now<=end<=latest,'finite bounded release fits latest start')
    if pending is None:pending={'node':x['id'],'backfill_until':end,'latest_epoch':latest,
     'safe_start_proven':False,'reason':str(error)}
   except (ValueError,KeyError):pass
   continue
  reserved={'node':x['id'],'earliest_epoch':now,'latest_epoch':min(x['deadline_epoch'],policy['cutoff_epoch'])-x['wall_seconds']}
  break
 chosen=[];virtual=copy.deepcopy(leases);snap=copy.deepcopy(snapshot)
 for n in candidates:
  if (reserved or pending)and n['kind']not in EXCLUSIVE:
   boundary=reserved['earliest_epoch']if reserved else pending['backfill_until']
   if now+n['wall_seconds']>boundary:
    missing[n['id']]='backfill would delay ready exclusive stage';continue
  try:fit(n,virtual,snap,now,policy)
  except (ValueError,KeyError)as e:missing[n['id']]=str(e);continue
  chosen.append({'node':n['id'],'packet_ref':n['packet_ref'],'decision':'PROPOSE_TO_MAIN_NOT_DISPATCH'})
  lid='proposal:'+n['id']
  virtual.append(dict(id=lid,node=n['id'],physical=n['physical'],budget=n['budget'],packet_ref=n['packet_ref'],kind=n['kind'],state='admitted',latest_release_epoch=now+n['wall_seconds']))
  snap['usage'][lid]={'ram':0,'cpu_millis':0,'disk':{}}
 return {'schema':'main.renew24-dispatch-proposal/v1','at':now,'ready_for_queue':len(candidates),
  'proposals':chosen,'blocked':missing,'exclusive_reservation':reserved,'exclusive_pending':pending,'dispatch_executed':False,
  'idle_sample':{'at':snapshot['at'],'cards':snapshot['cards'],'continuous_utilization_claimed':False},
  'idle_reason':'MAIN admission required'if chosen else('no reviewed READY packet'if not candidates else'actual resource/release/window gate')}
def released(nodes,leases,lease_id,terminal_ref,release_ref,reader=None):
 """Consume original serial child/release contract; never infer release from missing handle."""
 B=reader or io();out=copy.deepcopy(nodes);remaining=copy.deepcopy(leases);by=nodes_checked(out)
 leases_checked(remaining,by)
 l=next(x for x in remaining if x['id']==lease_id);n=by[l['node']];packet=B.obj(l['packet_ref'])
 terminal=B.obj(terminal_ref);release=B.obj(release_ref)
 need(terminal['schema']=='main.serial-child-terminal/v1'and terminal['reaped']is True and
      type(terminal['exit_code'])is int and terminal['source_ref']==packet['source_ref']and
      terminal['argv']==packet['argv']and terminal['AW_terminal_claimed']is False,'actual exact reaped original child, not unknown operation')
 need(release['schema']=='main.serial-exact-owned-release/v1'and release['source_ref']==packet['source_ref']and
      release['owner']==packet['owner']and release['child_terminal_ref']==terminal_ref and
      release['exact_owned_release']is True and release['physical_idle']==n['physical']and
      release['external_stopped']is False and release['AW_terminal_claimed']is False,'original source-qualified own release before reuse')
 B.checked(release['original_result_ref'])
 need(Path(release['original_result_ref']['path'])==Path(packet['output_root'])/packet['result_name'],
      'original result belongs to this exact owned output, not another passed run')
 n['state']='repair'if terminal['exit_code']or release['original_failed']else'result-pending'
 n['terminal_ref']=terminal_ref;n['release_ref']=release_ref
 remaining.remove(l)
 return out,remaining
def overlap(a,b):
 a=tuple(Path(a).parts);b=tuple(Path(b).parts)
 return a[:len(b)]==b or b[:len(a)]==a
def refill(nodes,agents):
 """Return follow-up proposals; never messages/spawns. No duplicate active edit scopes."""
 by=nodes_checked(nodes)
 need(len({a['id']for a in agents})==len(agents),'unique actual agent handles')
 busy={a['node']for a in agents if a['status']in('running','unknown')and a.get('node')}
 scopes={by[k]['edit_scope']for k in busy}
 papers={by[k]['paper']for k in busy}
 delivered={a['node']for a in agents if a['status']=='completed'and a.get('node')}
 assigned=[];seen=set(busy)|delivered
 for a in agents:
  if a['status']not in('idle','completed'):continue
  choices=[n for n in nodes if n['id']not in seen and n['kind']=='prepare'and
   n['state']in('preparing','repair')and not any(overlap(n['edit_scope'],s)for s in scopes)and
   all(by[d]['state']=='passed'for d in n['deps'])]
  choices.sort(key=lambda n:(n['paper']in papers,n['critical_seconds'],n['id']))
  if not choices:continue
  n=choices[0];assigned.append({'agent':a['id'],'node':n['id'],'action':'FOLLOWUP_REQUIRED_NOT_SENT'})
  seen.add(n['id']);scopes.add(n['edit_scope']);papers.add(n['paper'])
 return assigned
def main():
 p=argparse.ArgumentParser(allow_abbrev=False,description=__doc__)
 p.add_argument('--plan-ref',help='JSON Ref3 of immutable MAIN decision input; no execution switch')
 a=p.parse_args()
 if a.plan_ref is None:
  print(json.dumps({'default_enabled':False,'dispatch_executed':False}));return
 B=io();v=B.obj(json.loads(a.plan_ref))
 print(json.dumps(plan(**v,reader=B),sort_keys=True))
if __name__=='__main__':main()
