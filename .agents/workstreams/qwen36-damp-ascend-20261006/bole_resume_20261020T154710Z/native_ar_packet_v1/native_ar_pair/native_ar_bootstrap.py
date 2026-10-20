"""General-plugin hook for native AR only; no model call or device initialization."""
import os
import json
import time
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C


def register():
    if os.environ.get('BOLE_NATIVE_AR_PAIR_ENABLE')!='1':return None
    sr=json.loads(os.environ['BOLE_NATIVE_AR_PAIR_SOURCE_REF']);m=C.source(sr)
    C.need(C.ref(__file__)==m['files']['native_ar_bootstrap.py'],'exact AR plugin source')
    authority=C.obj(m['authority_ref'])
    C.need(authority['start_epoch']<=time.time()<authority['cutoff_epoch'],
           'actual current separately authorized admission window')
    import worker_entry
    from vllm_ascend.worker.worker import NPUWorker
    def loaded(worker,receipt):
        import torch
        import native_ar_observer,native_ar_capture,identity_journal
        from vllm.forward_context import get_forward_context
        import vllm_ascend.spec_decode.llm_base_proposer as proposer
        rank=proposer.get_tp_group().rank_in_group
        root=Path(m['model_receipt_root'])
        C.need(root.is_dir()and torch.npu.matmul.allow_hf32 is False,
               'actual original HF32OFF process and precreated owned receipt root')
        C.write(root/('NATIVE-AR-SNAPSHOT-RANK-%d.json'%rank),dict(
            source_ref=sr,pid=os.getpid(),proc_stat=Path('/proc/self/stat').read_text(),
            cgroup=Path('/proc/self/cgroup').read_text(),allow_hf32=False,
            actual_allow_hf32=torch.npu.matmul.allow_hf32,rank=rank,
            registry=receipt,speculative_config=None,model_ready=False))
        identity_journal.install_worker(sr,worker,rank)
        native_ar_observer.install(worker,torch,source_ref=sr,
            get_forward_context=get_forward_context,native_proposer=proposer,
            native_get_tp_group=proposer.get_tp_group,publish=native_ar_capture.publish)
    return worker_entry.install_after_load(NPUWorker,C,worker_ref=m['runtime_sources']['worker'],
        qwen35_ref=m['runtime_sources']['qwen35'],qwen_next_ref=m['runtime_sources']['qwen_next'],
        patch_ref=m['runtime_sources']['qwen_patch'],emit=loaded)
