"""Exclusive primitive-only actual AR capture, original aggregate bound retained."""
import os
from pathlib import Path
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C


def publish(*, t, source_ref, rank, payload, primary):
    m=C.source(source_ref)
    C.need(C.ref(__file__)==m['files']['native_ar_capture.py'] and type(rank)is int and rank in range(4),
           'exact actual rank exporter')
    root=Path(os.environ['BOLE_MODEL_RAW_ROOT'])
    C.need(str(root)==m['model_receipt_root'] and root.is_dir()
           and not any(p.is_symlink() for p in (root,*root.parents)), 'precreated sole-owned AR output')
    used=0
    def walk(value):
        nonlocal used
        if isinstance(value,t.Tensor):
            used+=value.numel()*value.element_size()
            C.need(used+64*2**20 <= C.CAP,'bounded aggregate AR tensor capture plus metadata reserve')
            return value.detach().cpu().contiguous()
        if value is None or type(value)in(str,int,float,bool):return value
        if type(value)in(list,tuple):return [walk(x)for x in value]
        C.need(type(value)is dict and all(type(k)in(str,int)for k in value),'primitive-only actual evidence')
        return {k:walk(v)for k,v in value.items()}
    raw=walk(payload)
    export=dict(schema='bole.model-diagnostic-primitives/v1',payload=raw,
                logical_tensor_bytes=used,cap_bytes=C.CAP,model_ready=False)
    path=root/('NATIVE-AR-RANK-%d.pt'%rank)
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as f:t.save(export,f);f.flush();os.fsync(f.fileno())
    C.need(path.stat().st_size+8*2**20+65536 <= C.CAP+2**20,
           'AR raw, full future process journal and receipt bounded by original aggregate cap')
    return C.write(root/('NATIVE-AR-RANK-%d.json'%rank),dict(
        schema='bole.actual-native-ar-worker-receipt/v1',source=source_ref,rank=rank,pid=os.getpid(),
        stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),
        raw=C.ref(path),primary=primary,logical_tensor_bytes=used,cap_bytes=C.CAP,
        future_rank_journal_reserve=8*2**20,receipt_reserve=65536,model_ready=False))
