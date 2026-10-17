"""Independent pure-metadata check; no numerical or alias qualification API."""
import argparse,hashlib,json
from pathlib import Path
def need(x,m):
 if not x:raise ValueError(m)
def obj(r):
 need(set(r)=={'path','bytes','sha256'},'exact Ref3 only');p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact complete observation Ref');return json.loads(b)
def evaluate(v):
 need(v['schema']=='deltalog.native-postprepare-footprint/v101R12'and v['all64_complete']is True and v['errors']==[],'complete native observation, not partial')
 need(v['decoder_forward_invoked']is v['candidate_math_invoked']is v['qualified']is False,'observation cannot become model/candidate PASS')
 need(v['num_scheduled_tokens']=={v['request_ids'][0]:2048}and len(v['request_ids'])==1,'actual one fixed2K request')
 need(v['native_source_proof']['runner']['sha256']=='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'and v['native_source_proof']['block_table']['sha256']=='8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a','actual installed runner/table source')
 prefixes=set();groups={g['gid']:g for g in v['groups']};selected=[];derived=[]
 for g in groups.values():
  expected=[p*g['blocks_per_phys_block']+j for p in g['physical_blocks']for j in range(g['blocks_per_phys_block'])]
  need(expected==g['CPU_table']==g['GPU_table'],'independent physical/kernel expansion and actual GPU commit')
 for layer in v['layers']:
  p=layer['prefix'];need(p not in prefixes and p in groups[layer['gid']]['layer_names'],'exact prefix/group join');prefixes.add(p)
  g=groups[layer['gid']];need(len(layer['views'])==2,'actual two state/cache views')
  for a in layer['views']:
   n=1
   for size in a['shape']:need(type(size)is int and size>0,'shape integers');n*=size
   step=1
   for size,stride in zip(reversed(a['shape']),reversed(a['stride'])):
    need(size==1 or stride==step,'independent contiguous logical stride');step*=size
   need(n==a['numel']and a['start']==a['data_ptr']==a['storage_ptr']+a['storage_offset']*a['element_size']and a['end']==a['start']+n*a['element_size']<=a['storage_ptr']+a['storage_nbytes'],'independent complete geometry arithmetic')
  if g['is_mamba']:
   slots=layer['GDN_indices']['non_spec_state_indices'];need(slots==g['physical_blocks'][:1]and len(layer['selected'])==2,'actual GDN request slot ownership')
   for view,role in zip(layer['views'],('conv','SSM')):
    s=slots[0];need(0<=s<view['shape'][0],'selected state within actual arena')
    size=view['stride'][0]*view['element_size'];derived.append(dict(prefix=p,gid=g['gid'],role=role,request_id=v['request_ids'][0],index=s,device=view['device'],start=view['start']+s*size,end=view['start']+(s+1)*size))
  else:
   m=layer['FA_indices'];bs=g['logical_block_size'];expected=[g['GPU_table'][i//bs]*bs+i%bs for i in range(2048)]
   need(m['block_tables']==[g['GPU_table']]and m['slot_mapping']==expected,'independent FA token/request kernel slot mapping')
   writes=[]
   for view,role in zip(layer['views'],('K','V')):
    need(view['shape'][1]==bs,'ND hypothesis block axis')
    size=view['stride'][0]*view['element_size']
    for s in g['GPU_table']:
     need(0<=s<view['shape'][0],'selected FA kernel page within actual arena');derived.append(dict(prefix=p,gid=g['gid'],role=role+'-whole-block-conservative-read',request_id=v['request_ids'][0],index=s,device=view['device'],start=view['start']+s*size,end=view['start']+(s+1)*size))
    tokenbytes=view['stride'][1]*view['element_size'];part=[]
    for s in sorted(expected):
     start=view['start']+s*tokenbytes;end=start+tokenbytes
     if part and part[-1]['end']==start:part[-1]['end']=end
     else:part.append(dict(role=role+'-current-write',request_id=v['request_ids'][0],start=start,end=end,device=view['device']))
    writes.extend(part)
   need(layer['current_write_intervals']==writes,'independent exact current-write byte union')
  selected.extend(layer['selected'])
 need(len(prefixes)==64 and selected==derived,'all64 independently recomputed selected byte intervals exact')
 collisions=[]
 for i,a in enumerate(derived):
  for b in derived[:i]:
   if a['prefix']!=b['prefix']and a['device']==b['device']and max(a['start'],b['start'])<min(a['end'],b['end']):collisions.append(dict(left=a,right=b,same_gid=a['gid']==b['gid']))
 need(collisions==v['collisions'],'independent collision enumeration')
 physical=all(g['npu_format_code']==2 for layer in v['layers']for g in layer['views'])
 need(v['physical_layout_valid']==physical,'actual layout flag agrees with every recorded format')
 if physical:need(v['native_source_proof'].get('acl_header_sha256')=='4055d6b9d3a96face0efb5d68aafb68900a1d9c78c6a877ae21381688dd8b529','source-bound actual ACL enum')
 return dict(observation_complete=True,all64_metadata_join=True,CPU_GPU_committed_tables=True,logical_footprint_recomputed=True,observed_conservative_logical_collisions=len(collisions),physical_layout_valid=physical,qualified=False,numeric=False,model_correctness=False,performance=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);p.add_argument('--owner-ref',required=True);p.add_argument('--loaded-ref',required=True);p.add_argument('--report-ref',action='append',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 sr=json.loads(a.source_ref);source=obj(sr);owner=obj(json.loads(a.owner_ref));loaded=obj(json.loads(a.loaded_ref))
 for ref in source['files'].values():
  p=Path(ref['path']);b=p.read_bytes();need(len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256'],'full own source consumer fence')
 need(Path(__file__).resolve()==Path(source['files']['consume_native101r12.py']['path']).resolve(),'actual source-bound independent reader')
 need(owner['source']==sr and owner['primary']is not None and owner['secondary']==[]and owner['all_created_containers_release_verified']is True and owner['elapsed']<=2700 and owner['cleanup_seconds']<=270,'original diagnostic-stop owner failure retained and completely released within original budget')
 need(loaded['source']==sr and loaded['schema']=='deltalog.actual-all4-loaded/v004'and [x['rank']for x in loaded['rows']]==[0,1,2,3],'actual owned four-rank loaded receipts')
 need(len(a.report_ref)==4,'exact all4 observation report Refs');results=[];ranks=set()
 for raw_ref in a.report_ref:
  rref=json.loads(raw_ref);need(rref['bytes']<=8*1024**2,'bounded observation8MiB');v=obj(rref);need(v['tp_rank']in range(4)and v['tp_rank']not in ranks,'exact unique actual rank');ranks.add(v['tp_rank'])
  row=loaded['rows'][v['tp_rank']];need(v['source']==sr and v['run_id']==source['runtime_identity']['run_id']and v['pid']==row['namespace_pid'],'source/run/rank actual guest PID join')
  native=obj(row['loaded_receipt']);proof=row['actual_host_process'];need(native['pid']==v['pid']==proof['namespace_pids'][-1]and row['physical']==row['logical']+4==proof['physical']and proof['start_ticks']==int(native['stat'][native['stat'].rfind(')')+2:].split()[19]),'actual host-to-guest PID/start/physical worker proof')
  need(any(x['cid']and x['cid']in proof['cgroup']for x in owner['owned_containers']),'actual stopped owned CID, not arbitrary rank PID')
  need(v['native_source_proof']['layout_source_ref']==source['files']['LAYOUT_SOURCE_EVIDENCE101R12.json'],'exact source-owned actual layout evidence')
  results.append(evaluate(v))
  del v
 need(ranks=={0,1,2,3},'all4 actual observed ranks')
 obj(sr)
 for ref in source['files'].values():
  p=Path(ref['path']);b=p.read_bytes();need(len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256'],'complete final own source fence')
 need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'one explicit new consumer output')
 with a.output.open('x',encoding='utf8')as f:json.dump(dict(schema='deltalog.native-footprint-independent-observation/v101R12',source=sr,owner=json.loads(a.owner_ref),loaded=json.loads(a.loaded_ref),reports=[json.loads(x)for x in a.report_ref],results=results,qualified=False),f,sort_keys=True);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
