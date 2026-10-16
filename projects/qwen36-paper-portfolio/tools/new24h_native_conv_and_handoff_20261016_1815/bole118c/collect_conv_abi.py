"""Only inside MAIN's admitted Devices[] child. Reads ABI; never calls the op."""
import argparse,hashlib,importlib.machinery,importlib.util,json,os,sys,traceback
from pathlib import Path
HELPER=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-direct-d8-fp32-model-boundary-r87-v1-011/cann_python.py',bytes=4503,sha256='cee927f1107fe6714e86ab1dceecafeff800980a00b8df9fcc47ff6831ba5104')
GDN=dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py',bytes=21887,sha256='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816')

def ref(p):
    p=Path(p);body=p.read_bytes();return dict(path=str(p),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
def checked(r):
    p=Path(r['path'])
    if not p.is_absolute()or p.is_symlink()or ref(p)!=r:raise ValueError('exact native ABI source '+str(p))
    return p

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--script-sha256');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    if ref(__file__)['sha256']!=a.script_sha256:raise ValueError('MAIN reviewed script SHA required')
    if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci*')):raise ValueError('actual admitted Devices[] environment required')
    if a.output.exists()or not a.output.parent.is_dir():raise ValueError('fresh owned output file')
    value=dict(schema='bole.actual-customconv-ABI/v118',script=ref(__file__),NPU=False,operator_executed=False,qualified=False,primary=None)
    try:
        spec=importlib.util.spec_from_file_location('_118_actual_CANN',checked(HELPER));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
        helper.cached();helper.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf')
        direct=helper.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[helper.ROOT]));sys.path.insert(0,helper.ROOT)
        if helper.spec_identity(importlib.util.find_spec('acl'))!=direct:raise ValueError('actual ACL extension resolution')
        value['CANN']=dict(helper=HELPER,actual_ACL=direct);checked(GDN)
        import torch,torch_npu
        torch.set_num_threads(1)
        import vllm_ascend.ops.gdn as gdn
        if ref(gdn.__file__)!=GDN:raise ValueError('actual normal GDN registration import source')
        family=torch.ops._C_ascend.npu_causal_conv1d_custom._schemas
        if not isinstance(family,dict)or not family:raise ValueError('actual nonempty registered custom-conv overload family')
        rows={name:dict(schema=str(schema),name=schema.name,argument_names=[arg.name for arg in schema.arguments],is_mutable=schema.is_mutable)for name,schema in family.items()}
        fds=[]
        for path in Path('/proc/self/fd').iterdir():
            try:target=os.readlink(path)
            except FileNotFoundError:continue
            if any(k in target for k in('davinci','devmm_svm','hisi_hdc')):fds.append(target)
        if fds:raise ValueError('device FD opened during CPU ABI import '+repr(fds))
        value.update(gdn=GDN,torch_python=ref(torch.__file__),torch_npu_python=ref(torch_npu.__file__),torch_version=torch.__version__,actual_schema_family=rows,no_device_fds=True)
    except BaseException as e:value.update(primary=repr(e),traceback=traceback.format_exc())
    with a.output.open('x',encoding='utf8',newline='\n')as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
    print(json.dumps(ref(a.output)));return 0 if value['primary']is None else 3

if __name__=='__main__':raise SystemExit(main())
