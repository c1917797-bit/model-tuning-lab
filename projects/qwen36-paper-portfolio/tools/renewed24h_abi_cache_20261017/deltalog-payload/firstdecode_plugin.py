"""Explicit new diagnostic EP only. Public production default remains OFF."""
import json
import os
from pathlib import Path
import sys
_registration_state='disabled'
_installed_result=None
_collector=None

def register():
    global _registration_state,_installed_result,_collector
    if os.environ.get('DL_FIRST_REAL_DECODE_DIAGNOSTIC_ENABLE')!='1':return
    here=Path(__file__).resolve().parent
    if str(here) not in sys.path:sys.path.insert(0,str(here))
    import firstdecode_gate as Q
    payload_sr=json.loads(os.environ['DL_FIRST_DECODE_PAYLOAD_SOURCE_REF'])
    p=Q.source(payload_sr);Q.need(Q.checked(p['files']['firstdecode_plugin.py'])==Path(__file__).resolve(),'actual sole new plugin source')
    for name in('firstdecode_gate','firstdecode','firstdecode_capture','live_adapter','byteaudit','selected_core','lifecycle','native_entries'):
        expected=Q.checked(p['files'][name+'.py']);old=sys.modules.get(name)
        Q.need(old is None or Path(old.__file__).resolve()==expected,'source-bound namespace, no ambient same-name module')
    model_sr=json.loads(os.environ['DL_FIRST_DECODE_MODEL_SOURCE_REF']);gate=Q.Gate(model_sr,payload_sr)
    m=gate.model
    # Original source-bound bootstrap is retained by the new owner. Both the
    # package and callbacks are checked against exact original defining bytes.
    import owner_overlay as O,bootstrap101r9 as B
    O.current(model_sr);B.install(m,Path(O.__file__).resolve().parent)
    Q.need(os.environ.get('QWEN36_DELTALOG_SERVICE023_ENABLE')=='1'
        and os.environ.get('QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE')=='1'
        and os.environ.get('QWEN36_DELTALOG_TENSOR026_ENABLE')=='0'
        and os.environ.get('DL101R12_NATIVE_OBSERVATION_ENABLE')=='0','explicit candidate+mirror, no old native observer/tensor installer')
    from vllm_ascend.utils import enable_custom_op
    import vllm_ascend.ops.gdn as G
    from vllm.v1.worker import mamba_utils
    from vllm_ascend.worker import model_runner_v1 as runner
    from qwen36_deltalog_service import runtime as R
    import firstdecode as D,firstdecode_capture as C,live_adapter as V,selected_core as F,lifecycle as LC
    reader=V.NativeReader(m['files']['LAYOUT_SOURCE_EVIDENCE101R12.json'],Q.obj)
    reader.native_torch_sources=p['native_torch_sources']
    component=Q.obj(m['plugin_source'])
    Q.need(component['library_ref']==m['library_ref'],'same actual13arg production library')
    allocation_ref=F.Ref(**payload_sr);binding_ref=F.Ref(**payload_sr)
    # No current weights/native cache exist during plugin discovery. These
    # factories are used once at actual execute after source-proven native load.
    def make(lazy,bridge):
        global _collector
        Q.need(_collector is None,'one cold actual collector factory')
        _collector=C.Collector(lazy,bridge,gate.root_factory,payload_sr,model_sr,m['library_ref'],m['debug_library'],Q.checked)
        return _collector
    value=D.install_actual(R,F,LC,reader,lambda r:gate.actual_worker(F,r),allocation_ref,binding_ref,make)
    _installed_result=value
    _registration_state='diagnostic-firstdecode-installed'
    print('DL_FIRSTDECODE_INSTALLED '+json.dumps(dict(source=payload_sr,model_source=model_sr,result=value,pid=os.getpid())),flush=True)

def validate_registration(R,payload_sr,model_sr):
    """Parser-side real callable/source/DSO facts; NOT geometry permission."""
    import firstdecode_gate as Q
    p=Q.source(payload_sr);m=Q.obj(model_sr)
    Q.need(_registration_state=='diagnostic-firstdecode-installed' and _collector is not None and _installed_result is not None,'actual new plugin registration occurred')
    Q.need(R._OP is _collector.dispatch and R._SOURCE==m['plugin_source'] and _collector.production is not None
        and _collector.debug is not None and _collector.lazy.value is None,'real source-owned capture dispatch, no fabricated live pool/worker binding before weights')
    expected='qwen36_deltalog_split_scale_v051::decode(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, Tensor actual_seq_lengths, Tensor state_indices) -> Tensor'
    Q.need(str(_collector.production.default._schema)==expected and str(_collector.production.default._schema)==Q.obj(m['plugin_source'])['operator_schema'],'actual original production13arg operator schema')
    Q.need(any(m['library_ref']['path'] in s for s in Path('/proc/self/maps').read_text().splitlines())
        and any(m['debug_library']['path'] in s for s in Path('/proc/self/maps').read_text().splitlines()),'actual mapped production/debug DSOs')
    return dict(registration_state=_registration_state,payload_source=payload_sr,model_source=model_sr,production_schema=expected,actual_live_geometry=False,engine_constructed=False,model_math_executed=False,qualification=False)
