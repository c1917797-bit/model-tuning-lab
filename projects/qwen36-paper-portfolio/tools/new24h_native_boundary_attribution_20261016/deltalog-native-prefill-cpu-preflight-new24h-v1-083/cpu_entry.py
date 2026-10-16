"""Devices[] mounted079 audit and actual saved raw CPU extract. No native import."""
import argparse,contextlib,hashlib,importlib.util,io,json,os,sys,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and all(not q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'exact ordinary RO source/input');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def cpu_environment():
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('ASCEND_VISIBLE_DEVICES')=='','actual explicit CPU environment')
 need(not any(n=='torch_npu'or n.startswith(('torch_npu.','vllm.','vllm_ascend.'))or n=='acl'for n in sys.modules),'no native/NPU initialization')
 maps=Path('/proc/self/maps').read_text();need(not any(t in maps.lower()for t in('libascend_hal','libascendcl','libtorch_npu','/acl.so')),'no mapped NPU backend')
 fds=[]
 for p in Path('/proc/self/fd').iterdir():
  try:s=os.readlink(p)
  except FileNotFoundError:continue
  need(not s.startswith(('/dev/davinci','/dev/devmm','/dev/hisi')),'no NPU device FD');fds.append(s)
 return dict(backend_autoload='0',visibility='',mapped_NPU_backend=False,NPU_device_FDs=False,fd_count=len(fds))
def import_guard(event,args):
 if event=='import':
  n=str(args[0]);need(not(n in('acl','torch_npu','vllm','vllm_ascend')or n.startswith(('torch_npu.','vllm.','vllm_ascend.'))),'CPU preflight cannot import hardware/native package '+n)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--producer-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);own=obj(sr);need(own['schema']=='deltalog.native-prefill-cpu-source/v083'and own['root']==str(HERE),'actual083 source');[checked(r)for r in own['files'].values()];need(own['files']['cpu_entry.py']==ref(__file__),'actual child bytes')
 out=a.output;need(out.parent.is_dir()and not out.exists(),'exclusive new CPU receipt');primary=None;details={}
 try:
  details['cpu_before']=cpu_environment();sys.addaudithook(import_guard);gm=obj(own['guest_source']);g=load(gm['files']['guest_core.py'],'_083_actual079_guest')
  original=sys.argv;capture=io.StringIO()
  try:
   sys.argv=[gm['files']['guest_core.py']['path'],'--source-audit','--source-ref',json.dumps(own['guest_source'])]
   with contextlib.redirect_stdout(capture):need(g.main()==0,'actual079 source-audit exit0')
  finally:sys.argv=original
  details['mounted_source_audit']=json.loads(capture.getvalue());need(details['mounted_source_audit']['source']==own['guest_source']and details['mounted_source_audit']['NPU']is False,'actual mounted079 audit identity')
  import torch
  torch.set_num_threads(1);details['torch_version']=torch.__version__;m=g.obj(g.SOURCE);pr=json.loads(a.producer_ref);need(pr==g.PRODUCER,'exact retained producer')
  rows=g.select_records(g.obj(pr));codec=g.load(m['files']['raw_codec.py'],'_083_actual_lossless_raw_codec');codec.install(torch)
  values=[torch.load(g.checked(r['raw']),map_location='cpu',weights_only=False)for r in rows];x,sc,sn,pc=g.extract(torch,*values)
  details.update(extract_pass=True,selected=rows,initial_C=g.fingerprints(torch,sc),initial_N=g.fingerprints(torch,sn),captured_inputs={n:g.fingerprints(torch,v)for n,v in x.items()if torch.is_tensor(v)},cpu_after=cpu_environment())
 except BaseException as e:primary=repr(e);details['traceback']=traceback.format_exc()
 result=dict(schema='deltalog.native-prefill-cpu-preflight/v083',source=sr,guest_source=own['guest_source'],producer=json.loads(a.producer_ref),primary=primary,extract_pass=details.get('extract_pass',False),details=details,qualification=False,NPU_reexecuted=False,bootstrap_invoked=False)
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 return 3 if primary else 0
if __name__=='__main__':raise SystemExit(main())
