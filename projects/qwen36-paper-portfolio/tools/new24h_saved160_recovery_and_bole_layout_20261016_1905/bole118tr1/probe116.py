"""Only under an existing MAIN-owned singleton controller and actual ARM."""
import argparse,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import tree_fa115 as F

REQUIRED=('query','key','value','atten_mask','actual_seq_lengths','actual_seq_lengths_kv','num_heads','num_key_value_heads','input_layout','scale','sparse_mode','pre_tokens','next_tokens','inner_precise')


def ref(path):
    p=Path(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def checked(r):
    if type(r)is not dict or set(r)!={'path','bytes','sha256'}:raise ValueError('actual Ref3 required')
    p=Path(r['path'])
    if not p.is_absolute()or not p.is_file()or any(x.is_symlink()for x in(p,*p.parents))or ref(p)!=r:raise ValueError('ordinary exact immutable source/ABI')
    return p


def write(path,v):
    with Path(path).open('x',encoding='utf8',newline='\n')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')


def require_abi(abi_ref):
    if abi_ref is None:raise ValueError('actual9.1 installed ABI/header receipt missing; execution forbidden')
    abi=json.loads(checked(abi_ref).read_bytes())
    if abi['schema']!='bole.actual-FIA-installed-ABI/v115'or abi['NPU']is not False or abi['operator']!='npu::npu_fused_infer_attention_score':raise ValueError('actual installed CPU ABI receipt')
    if not set(REQUIRED)<=set(abi['argument_names']):raise ValueError('required complete-mask actual ABI unsupported')
    checked(abi['header_ref']);checked(abi['torch_npu_python_ref'])
    return abi


def run(t,torch_npu,m,out,deadline,*,actual_arm_verified):
    if actual_arm_verified is not True:raise ValueError('existing actual singleton owner ARM prerequisite')
    abi=require_abi(m['actual_abi_ref'])
    import abi116
    abi116.runtime(t,abi)
    if ref(torch_npu.__file__)!=abi['torch_npu_python_ref']:raise ValueError('actual TorchNPU module identity')
    for r in m['files'].values():checked(r)
    if not out.is_dir()or any(out.iterdir()):raise ValueError('fresh empty owned leaf')
    rows=[]
    for case,(batch,prefixes,witness)in enumerate(((1,[0],True),(1,[7],False),(16,[i%9 for i in range(16)],False))):
        cpu=F.recipe(t,batch,prefixes,witness)
        for mode in(1,0):
            if time.time()>=deadline:raise TimeoutError('FIA115 bounded whole guest')
            device={k:(v.to('npu:0')if isinstance(v,t.Tensor)else v)for k,v in cpu.items()}
            readback={k:(v.cpu()if isinstance(v,t.Tensor)else v)for k,v in device.items()}
            t.save(dict(source=m['_actual_source'],case=case,mode=mode,inputs=readback),out/('INPUT-%02d-mode%d.pt'%(case,mode)))
            result=None;primary=None
            try:
                pair=F.call_fia(torch_npu,device,sparse_mode=mode);t.npu.synchronize();result=pair[0].cpu()
            except BaseException as e:primary=dict(error=repr(e),traceback=traceback.format_exc())
            raw=dict(schema='bole.FIA-raw/v115',source=m['_actual_source'],case=case,mode=mode,inputs=readback,output=result,primary=primary,FA_layout='BNSD',mask_polarity='True/1 forbids',tree_FIA_model_qualified=False)
            path=out/('case-%02d-mode%d.pt'%(case,mode));t.save(raw,path);rr=ref(path);row=dict(case=case,mode=mode,raw=rr,primary=primary)
            write(out/('case-%02d-mode%d.json'%(case,mode)),row);rows.append(row)
            if sum(p.stat().st_size for p in out.iterdir()if p.is_file())>64*2**20:raise ValueError('raw64MiB hard bound')
    result=dict(schema='bole.FIA-stage/v115',source=m['_actual_source'],actual_abi_ref=m['actual_abi_ref'],rows=rows,NPU=True,qualified=False,model_ready=False)
    write(out/'STAGE_RESULT.json',result);return result


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--source-audit',action='store_true');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false}');return 0
    sr=json.loads(a.source_ref);m=json.loads(checked(sr).read_bytes())
    if m['schema']!='bole.FIA-source/v115':raise ValueError('actual FIA source')
    for r in m['files'].values():checked(r)
    if a.source_audit:print(json.dumps(dict(source=sr,NPU=False,actual_ABI_pending=m['actual_abi_ref']is None)));return 0
    require_abi(m['actual_abi_ref'])
    raise ValueError('direct bare-device CLI forbidden; MAIN existing owned singleton adapter must call run after actual mapping/ARM')

if __name__=='__main__':raise SystemExit(main())
