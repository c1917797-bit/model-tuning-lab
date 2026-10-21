"""Source-bound general-plugin entry; only the existing native worker loads."""
import os,json,inspect,hashlib
from pathlib import Path
import sourceio as C


def publish(*,source_ref,rank,payload,primary):
 import torch
 import g2_contract as G2,g2_channel as CH
 m=C.obj(source_ref);root=Path(os.environ['BOLE_MODEL_RAW_ROOT'])
 C.need(str(root)==m['model_receipt_root']and root.is_dir()and
     not any(p.is_symlink()for p in(root,*root.parents))and type(rank)is int and rank in range(4),
     'exact owned G2 rank output')
 C.need(payload['logical_tensor_bytes']==0,'final G2 worker output is metadata; every real tensor frame was independently consumed')
 channel=Path(m['stream_channel_root']);pending=list(channel.glob('FRAME-RANK-%d-*.pt'%rank))
 C.need((primary is not None or not pending)and len(pending)<=1,'at most one retained failed/unACK raw frame per rank')
 raw_bytes=sum(p.stat().st_size for p in pending)
 logical_failed=sum(C.obj(C.ref(p.with_suffix('.json')))['logical_tensor_bytes']for p in pending)
 C.need(raw_bytes<=G2.FRAME_WIRE_CAP,'retained failed-frame original raw budget')
 files=set(root.glob('*RANK-%d.json'%rank));files.update(root.glob('IDENTITY-rank%d-*.json'%rank))
 files.update(channel.glob('*RANK-%d-*.json'%rank));files.update(channel.glob('*RANK-%d.json'%rank))
 files.update(p for p in channel.glob('*.json')if 'RANK-'not in p.name)
 cal=root/('CONV-MODEL-CALIBRATION-RANK-%d'%rank)
 if cal.is_dir():files.update(cal.iterdir())
 import g3_budget
 accounting=g3_budget.actual(C,m,rank)
 existing=accounting['bytes']
 C.need(existing+8*2**20<=G2.METADATA_CAP,'retain final summary/exit/journal headroom inside aggregate64MiB metadata/calibration')
 path=root/('BOLE-TREE-RANK-%d.pt'%rank)
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:torch.save(payload,f);f.flush();os.fsync(f.fileno())
 C.need(path.stat().st_size<=4*2**20 and path.stat().st_size+existing+raw_bytes+logical_failed+G2.CHECKPOINT_CAP<=G2.RAW_CAP,
     'actual bounded metadata plus any retained failed complete raw under original1GiB')
 value=dict(schema='bole.actual-worker-stream-receipt/v2',source=source_ref,rank=rank,pid=os.getpid(),
     stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),
     raw=C.ref(path),primary=primary,evidence_refs=[C.ref(p)for p in sorted(files)],
     model_calibration_ref=C.ref(cal/'ABI.json')if(cal/'ABI.json').exists()else None,
     retained_unACK_raw=[C.ref(p)for p in pending],successful_raw_replay_available=False,
     metadata_bytes=existing+path.stat().st_size,metadata_cap=G2.METADATA_CAP,raw_cap=G2.RAW_CAP,
     scheduler_committed=False,model_ready=False)
 target=root/('BOLE-TREE-RANK-%d.json'%rank)
 with target.open('x')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
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
