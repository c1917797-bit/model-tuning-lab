"""Small source-bound owner glue; no second controller or resource admission."""
import importlib.util,json,sys
from pathlib import Path
def load(O,r,name):
 p=O.obj_file(r);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def lease(O,m,sr):
 import model_snapshot_budget as B
 contract=m['firstdecode_contract'];O.need(contract['schema']=='deltalog.firstdecode-model-contract/v1','explicit new diagnostic source')
 seal_sr=contract['closed_source_ref'];sm=O.obj(seal_sr);seal=load(O,sm['files']['capture_closed2.py'],'_firstdecode_closed_two_actual')
 O.need(sm['root']==str(Path(seal.__file__).parent),'actual sole closed source')
 import renewed_closed_reader101r19 as renewal
 renewal.install(seal,sm['files']['capture_closed2.py'])
 import ipc_controls
 scanner=ipc_controls.load_scanner()
 def opt_usage(root):
  root=Path(root);parents=[root/n for n in('cpu-preflight','candidate','cpu-consumer')]
  value=scanner.scan(root,socket_parent=parents,ipc_source=scanner.IPC_SOURCE)
  return scanner.consume(value,root)
 return B.Lease(seal,seal_sr,contract['closed_evidence_ref'],sr,contract['payload_source'],m['output_root'],opt_usage)
def bootstrap(O,m):
 sr=m['firstdecode_contract']['payload_source'];p=O.obj(sr)
 for r in p['files'].values():O.obj_file(r)
 root=Path(sr['path']).parent
 if str(root)in sys.path:sys.path.remove(str(root))
 sys.path.insert(0,str(root));return root
def budget(h,c,ctl,sr,m,storage):
 import model_snapshot_budget as B
 O=__import__('owner_overlay');loaded=c.obj(c.ref(ctl.out/'ALL4-LOADED.json'))
 O.need(loaded['source']==sr and len(loaded['rows'])==4 and ctl.cid,'real source-bound all4/CID before budget')
 proof=storage.check()
 value=dict(schema='deltalog.first-decode-owned-budget/v1',source=sr,payload_source=m['firstdecode_contract']['payload_source'],cid=ctl.cid,host_stage_root=ctl.out.as_posix(),guest_stage_root='/adakv-results',host_payload_root=B.LEAF.as_posix(),guest_payload_root='/adakv-results/model/capture',workspace_cap_bytes=B.CAP,per_worker_cap_bytes=8*B.G,allocated_worker_cap_bytes=15*B.G//2,opt_total_cap_bytes=B.OPT_CAP,payload_total_cap_bytes=B.PAYLOAD_CAP,total_cap_bytes=B.LIMIT,disk_reserve_bytes=int(8.5*B.G),storage_proof=proof,ledger_advanced=False)
 # c.write is inherited exclusive write; fsync the new receipt before worker.
 p=ctl.out/'FIRST-DECODE-BUDGET.json';O.need(not p.exists(),'one non-overwritten budget')
 body=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();storage.prewrite(p,len(body))
 with p.open('xb')as f:f.write(body);f.flush();__import__('os').fsync(f.fileno())
 return c.ref(p)
