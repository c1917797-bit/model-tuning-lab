"""Owned single5 graph16 replay entry; no admission or physical-map guessing."""
import argparse,importlib.machinery,importlib.util,json,os,sys,time,traceback
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C
def bootstrap(m):
 h=C.load(m['cann_helper_ref'],'_095actualcann');root='/usr/local/Ascend/cann-9.1.0/python/site-packages';C.need(h.ROOT==root,'actualCANNroot');h.file_identity('/usr/local/Ascend/cann-9.1.0/set_env.sh',5112,'de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf');direct=h.spec_identity(importlib.machinery.PathFinder.find_spec('acl',[root]));sys.path.insert(0,root);active=h.spec_identity(importlib.util.find_spec('acl'));C.need(active==direct,'actual acl extension');return dict(direct=direct,active=active)
def execute(t,m,out,deadline):
 import graph094 as G,recipe094,oracle as R,precast as PRE,raw_codec as RC
 for lib in(m['production_library'],m['debug_library']):t.ops.load_library(str(C.checked(lib)))
 prod=t.ops.qwen36_deltalog_split_scale_v051.decode;debug=t.ops.qwen36_deltalog_split_scale_sidecar_v051.decode
 for ns,op,count in(('qwen36_deltalog_split_scale_v051',prod,13),('qwen36_deltalog_split_scale_sidecar_v051',debug,14)):
  C.need(op.default._schema.name==ns+'::decode'and len(op.default._schema.arguments)==count and t._C._dispatch_has_kernel_for_dispatch_key(ns+'::decode','PrivateUse1'),'actual loaded schema/dispatch')
 maps=Path('/proc/self/maps').read_text();C.need(all(r['path']in maps for r in(m['production_library'],m['debug_library'])),'both actual mapped DSOs')
 C.write(out/'ACTUAL_LIBRARIES.json',dict(libraries=[m['production_library'],m['debug_library']],actual_schemas=[str(prod.default._schema),str(debug.default._schema)],NPU=True))
 store=RC.Store(t,out,768*2**20);cases=[]
 for batch in(1,16):
  initial,events=recipe094.recipe(t,batch,16);slots=initial.shape[0];dev='npu:0'
  args=[events[0]['inputs'][n].to(dev)for n in G.INPUTS]+[initial.to(dev),t.zeros((slots,4,7,128),dtype=t.bfloat16,device=dev),t.zeros((slots,12,7,128),dtype=t.float32,device=dev)]+[t.zeros((slots,12,16),dtype=d,device=dev)for d in(t.float32,t.float32,t.int32)]+[events[0]['sequence'].to(dev),events[0]['ids'].to(dev)]
  anchor=store.write(out/('INITIAL-B%d.pt'%batch),dict(initial=initial,seed=2610169401+batch))
  result=G.run_admitted(t,prod,debug,args,events,R,PRE,lambda step,value:store.write(out/('graph-B%d-%03d.pt'%(batch,step)),value),deadline)
  cases.append(dict(batch=batch,initial=anchor,rows=result['rows']))
 return dict(cases=cases,raw_bytes=store.used,raw_cap=768*2**20,full_mixed_graph_qualified=False,qualified=False)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--plan-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);C.window(m);C.build(m);pr=json.loads(a.plan_ref);plan=C.obj(pr)
 C.need(plan['schema']=='deltalog.graph-plan/v095'and plan['source']==sr and plan['physical']==5 and plan['logical']==0 and plan['steps']==16 and plan['qualification']is False,'actual single5 plan')
 cpu=C.obj(plan['cpu_stage']);C.need(cpu['schema']=='deltalog.graph-CPU-stage/v095'and cpu['source']==sr and cpu['actual_meta']['pass_gate']is True,'actual same095 CPU Meta prerequisite')
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='0'and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('VLLM_PLUGINS')=='ascend','actual scope env')
 out=a.output;C.need(not out.exists()and out.parent.is_dir(),'unique graph output');out.mkdir();result=None;primary=None;attempted=False;start=time.monotonic()
 try:
  C.write(out/'CANN.json',bootstrap(m));from early_vendor import before_device,after_enable
  C.write(out/'EARLY_VENDOR.json',before_device())
  import torch as t,torch_npu
  t.set_num_threads(1);torch_npu.npu.set_compile_mode(jit_compile=False);attempted=True;t.npu.set_device(0);C.need(t.npu.device_count()==1,'actual singleton')
  canary=(t.tensor([1.,2.],device='npu:0')+3).cpu().tolist();C.need(canary==[4.,5.],'actual canary')
  C.write(out/'DEVICE.json',dict(pid=os.getpid(),stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),logical=0,physical_declared_by_plan=5,plan=pr,canary=canary,physical_proof_must_be_host_owned=True))
  until=time.monotonic()+30
  while not(out/'MAIN_ARM.json').exists():C.need(time.monotonic()<until,'actual MAIN ARM30');time.sleep(.1)
  C.need(C.obj(C.ref(out/'MAIN_ARM.json'))==dict(schema='deltalog.graph-arm/v095',pid=os.getpid(),plan_sha256=pr['sha256'],physical=5),'exact actual owner ARM')
  from native_bootstrap import actual
  imported=actual();C.write(out/'NATIVE_IMPORT.json',imported);C.need(imported['import_pass']is True,'actual official native package import')
  import vllm_ascend.utils as utils
  C.need(C.ref(utils.__file__)['sha256']=='575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02'and utils.enable_custom_op()is True,'actual official vendor registration');C.write(out/'VENDOR.json',after_enable(utils))
  remaining=560-(time.monotonic()-start);C.need(remaining>0,'charged startup leaves graph work budget')
  result=execute(t,m,out,min(1792220533,time.time()+remaining))
 except BaseException as e:primary=repr(e);C.write(out/'FAILURE.json',dict(primary=primary,traceback=traceback.format_exc()))
 C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.graph-stage/v095',source=sr,authority=m['authority_ref'],plan=pr,result=result,primary=primary,NPU=attempted,qualified=False,full_mixed_graph_qualified=False,elapsed=time.monotonic()-start));return 0 if primary is None else 3
if __name__=='__main__':raise SystemExit(main())
