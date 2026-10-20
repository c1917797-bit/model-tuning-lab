"""Source-bound general-plugin entry; only the existing native worker loads."""
import os,json,inspect,hashlib
from pathlib import Path
import sourceio as C


def publish(*,source_ref,rank,payload,primary):
 m=C.obj(source_ref);root=Path(os.environ['BOLE_MODEL_RAW_ROOT'])
 C.need(str(root)==m['model_receipt_root']and root.is_dir()and
        not any(p.is_symlink()for p in(root,*root.parents)), 'exact precreated sole-owned model receipt root')
 C.need(type(rank)is int and rank in range(4), 'actual TP4 rank')
 import torch
 import g1_contract as G1
 C.need(m['service_experiment']==G1.SCOPE,'explicit G1 publisher profile')
 calroot=root/('CONV-MODEL-CALIBRATION-RANK-%d'%rank)
 calibration_paths=sorted(calroot.iterdir())if calroot.is_dir()else []
 calibration_bytes=sum(p.stat().st_size for p in calibration_paths)
 C.need(calibration_bytes<=32*2**20 and (primary is not None or calroot.is_dir()),'one original32MiB same-model calibration per actual rank')
 operand_paths=[root/('BOLE-LOGITS-OPERAND-RANK-%d%s'%(rank,suffix))for suffix in('.pt','.json')]
 C.need(sum(p.stat().st_size for p in operand_paths if p.exists())<=4*2**20,'original logits operands within4MiB')
 evidence_paths=[]
 for pattern,cap in (('BOLE-PREFILL-CACHE-REQUEST-??-RANK-%d.json'%rank,4*2**20),
                     ('BOLE-FA-PREFILL-MAPPING-REQUEST-??-RANK-%d.json'%rank,4*2**20),
                     ('BOLE-NATIVE-LIBRARY-IDENTITY-REQUEST-??-RANK-%d.json'%rank,10*2**20),
                     ('IDENTITY-rank%d-*.json'%rank,8*2**20)):
  paths=sorted(root.glob(pattern))
  C.need(sum(p.stat().st_size for p in paths)<=cap,'bounded aggregate request/process metadata '+pattern)
  evidence_paths.extend(paths)
 journal_bytes=sum(p.stat().st_size for p in evidence_paths if p.name.startswith('IDENTITY-'))
 evidence_paths.extend(p for p in operand_paths if p.exists())
 evidence_paths.extend(calibration_paths)
 C.need(all(p.is_file()and not p.is_symlink()for p in evidence_paths),'owned regular bounded rank evidence files')
 evidence_bytes=sum(p.stat().st_size for p in evidence_paths)
 C.need(payload['logical_tensor_bytes']+G1.RESERVE_BYTES<=G1.CAP_BYTES,'both requests and all original calibration/metadata reserve inside aggregate1GiB')
 path=root/('BOLE-TREE-RANK-%d.pt'%rank)
 fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:
  torch.save(payload,f);f.flush();os.fsync(f.fileno())
 remaining_journal_reserve=8*2**20-journal_bytes
 C.need(path.stat().st_size+evidence_bytes+remaining_journal_reserve+65536<=G1.CAP_BYTES+2**20,
        'combined actual rank raw/calibration/all evidence plus remaining process journal reserve under original cap and headers')
 raw=payload['payload']
 request_capture_refs=[r for item in raw.get('requests',raw.get('completed_requests',[]))
                       for r in item.get('request_capture_refs',{}).values()]
 v=dict(schema='bole.actual-worker-two-request-receipt/v1',source=source_ref,
    rank=rank,pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),
    cgroup=Path('/proc/self/cgroup').read_text(),raw=C.ref(path),primary=primary,
    model_calibration_ref=C.ref(calroot/'ABI.json')if(calroot/'ABI.json').is_file()else None,
    request_capture_refs=request_capture_refs,
    rank_evidence_refs=[C.ref(p)for p in evidence_paths],
    byte_accounting=dict(cap_bytes=G1.CAP_BYTES,serialization_header_allowance=2**20,
       logical_tensor_bytes=payload['logical_tensor_bytes'],raw_bytes=path.stat().st_size,
       evidence_bytes=evidence_bytes,reserved_metadata_bytes=G1.RESERVE_BYTES,
       remaining_journal_reserve=remaining_journal_reserve,receipt_reserve=65536),
    scheduler_committed=False,model_ready=False)
 target=root/('BOLE-TREE-RANK-%d.json'%rank)
 with target.open('x',encoding='utf8',newline='\n')as f:
  body=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n');C.need(len(body.encode())<=65536,'bounded aggregate rank receipt');f.write(body);f.flush();os.fsync(f.fileno())
 fd=os.open(str(root),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return C.ref(target)


def after_load(worker,receipt):
 # This runs ONLY after the actual original NPUWorker.load_model completed.
 import torch,torch_npu
 import worker_entry,model_smoke,context_adapter
 sr=json.loads(os.environ['BOLE_MODEL_SOURCE_REF']);m=C.obj(sr)
 # Shared short module names must never resolve to an earlier plugin's cache.
 import sys
 for name in('worker_entry','model_smoke','model_entry','cache_registry','prefill_tail','mtp_entry',
             'tp_consensus','diagnostic_export','core112','adapter','treeconv118','tree_metadata111',
             'predecessor118t','component_gate','registration118','acceptance','native_logits','context_adapter','sourceio'):
  module=sys.modules.get(name)
  C.need(module is not None and C.ref(module.__file__)==m['files'][name+'.py'],'exact private source-bound module '+name)
 from vllm.forward_context import get_forward_context
 from vllm.model_executor.layers.attention.attention import get_attention_context
 from vllm_ascend.spec_decode.llm_base_proposer import get_tp_group
 import identity_journal
 group=get_tp_group();identity_journal.install_worker(sr,worker,group.rank_in_group)
 context_adapter.configure(worker,C,sr)
 if m.get('service_experiment')is not None:
  import g1_contract as G1
  C.need(os.environ.get(G1.FLAG)=='1'and m['service_experiment']==G1.SCOPE,'explicit G1 two-request opt-in')
  import service_runner
  for name in('service_runner','service_bridge','service_fia','live_owner','transaction','eligibility','g1_contract','model_process_calibration'):
   module=sys.modules.get(name)
   C.need(module is not None and C.ref(module.__file__)==m['files'][name+'.py'],'exact private service module '+name)
  install=service_runner.install
 else:install=model_smoke.install
 install(worker,torch,torch_npu,C,source_ref=sr,
    component_refs=m['component_refs'],get_forward_context=get_forward_context,
    get_attention_context=get_attention_context,enter_context=context_adapter.enter,
    native_get_tp_group=get_tp_group,publish=publish)


def register():
 if os.environ.get('BOLE_THREE_NODE_MODEL_ENABLE')!='1':return None
 C.need(all(os.environ.get(k)=='1'for k in('BOLE_MODEL_OBJECT_AUDIT_ENABLE','BOLE_MTP_TREE_CAPTURE_ENABLE','BOLE_PAGED_TREE_ENABLE')),
        'all explicit bounded diagnostic entry switches')
 sr=json.loads(os.environ['BOLE_MODEL_SOURCE_REF']);m=C.obj(sr)
 import g1_contract as G1
 C.need(m.get('service_experiment')==G1.SCOPE and os.environ.get(G1.FLAG)=='1',
        'explicit G1 profile and opt-in before installing any worker load hook')
 C.need(m['schema']=='bole.actual-model-three-node-entry/source-prep-v1'and
        m.get('component_refs')is not None and m.get('prepared_only')is False and m['root']==str(Path(__file__).resolve().parent),
        'actual bound model entry source and component receipt refs')
 import time
 authority=C.obj(m['authority_ref'])
 C.need(authority['start_epoch']==1792511230 and authority['cutoff_epoch']==1792597630 and
        1792511230<=time.time()<1792597630,'actual current batch hardware window')
 for r in m['files'].values():C.checked(r)
 for key in('qwen_patch','worker_patch_init','qwen_next_mtp_patch'):C.checked(m['runtime_sources'][key])
 import worker_entry
 from vllm_ascend.worker.worker import NPUWorker
 return worker_entry.install_after_load(NPUWorker,C,worker_ref=m['runtime_sources']['worker'],
      qwen35_ref=m['runtime_sources']['qwen35'],qwen_next_ref=m['runtime_sources']['qwen_next'],emit=after_load,patch_ref=m['runtime_sources']['qwen_patch'])
