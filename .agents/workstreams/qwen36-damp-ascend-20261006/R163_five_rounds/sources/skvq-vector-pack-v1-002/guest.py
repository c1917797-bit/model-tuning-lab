"""Same660 CPU128 / single-device original256 GLOBAL matrix. OFF by default."""
import argparse,hashlib,json,os,sys,time,types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import common as C
def identity(cid):
 tail=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split();group=Path('/proc/self/cgroup').read_text();C.need(len(cid)==64 and cid in group,'real own CID/process')
 return dict(pid=os.getpid(),start_ticks=int(tail[19]),cgroup=group,argv=list(sys.argv),cmdline_sha256=hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest())
def main():
 started=time.monotonic();epoch=time.time();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source');p.add_argument('--source-sha256');p.add_argument('--mode',choices=('software','quantize','full-launch'));p.add_argument('--output',type=Path);p.add_argument('--expected-cid');p.add_argument('--physical',type=int);p.add_argument('--inspection-ref-json',type=Path);p.add_argument('--remaining-seconds',type=int);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 own,m=C.boot(a.source,a.source_sha256);C.need(a.mode and type(a.remaining_seconds)is int and 0<a.remaining_seconds<=180 and C.START<=epoch and epoch+a.remaining_seconds<C.CUT,'same remaining/window')
 ident=identity(a.expected_cid);out=a.output;C.need(out.is_absolute()and not out.exists()and out.parent.is_dir(),'fresh owned child');out.mkdir()
 result=dict(schema='skvq.vector256-owned-child/v1',source=own,mode=a.mode,identity=ident,actual_cid=a.expected_cid,actual_argv=[sys.executable,'-I','-B',*sys.argv],python_version=list(sys.version_info[:3]),primary=None,raw_ref=None,NPU=a.mode!='software',model_ready=False,performance_ready=False,task_ready=False,cutoff=C.CUT)
 try:
  if a.mode=='software':
   C.need(not any(Path('/dev/davinci'+str(n)).exists()for n in range(8))and not Path('/dev/davinci_manager').exists(),'real Devices[]')
   check=C.load('_vector_CPU_controls',m['files']['software_check.py']);result['software']=check.run(m)
  else:
   C.need(a.physical in(4,5,6,7)and a.remaining_seconds<=120 and a.inspection_ref_json,'exact single card/gate120')
   B,A,Q=C.contract(m,[own,*m['files'].values(),*m['dependencies']]);ir=json.loads(a.inspection_ref_json.read_bytes());ins=Q.load(ir);owned=Q.load(ins['owned_ref']);raw=Q.load(ins['raw_inspect_ref'])
   C.need(ins['schema']=='skvq.vector256-owned-inspection/v1'and ins['source']==own and raw['requested_argv']==['/usr/bin/docker','inspect',a.expected_cid]and raw['exit_code']==0,'actual source-qualified internal inspect')
   xs=json.loads(raw['stdout']);C.need(len(xs)==1,'one inspect');x=Q.inspect_owned(xs[0],owned)
   C.need(owned['source']==own and owned['physical']==a.physical and owned['numeric_sha256']==m['files']['guest.py']['sha256']and x['Id']==a.expected_cid and x['State']['Running']is True and x['State']['Pid']>0 and owned['output']==str(out.parent),'actual current source/CID/leaf')
   C.need(out.parent.name=='physical-single'and out.parent.parent.parent==B.OUTPUT_PARENT,'bounded actual cohort output')
   W=C.load('writer',m['files']['writer.py']);G=C.load('_vector_original_matrix',m['original_gate']);G.ROOT=C.P;G.CUT=C.CUT
   def inspected(unused,logical,physical):
    C.need(logical==0 and physical==a.physical and a.expected_cid in Path('/proc/self/cgroup').read_text(),'same real mapping/cgroup');return ir,a.expected_cid,out.parent
   G.original_inspect=inspected
   args=types.SimpleNamespace(inspection_ref_json=None,logical_device=0,physical_card=a.physical,seconds=a.remaining_seconds,stage=a.mode,output=out.parent/'run-skvq-writer-shift-native-vector')
   G.run(args,own,dict(m,files=list(m['files'].values())),started,epoch);result['raw_ref']=C.ref(args.output/'RESULT.json')
   until=time.monotonic()+3
   while time.monotonic()<until:C.need(time.monotonic()-started<a.remaining_seconds and time.time()<C.CUT,'same observation budget');time.sleep(.1)
  C.need(identity(a.expected_cid)==ident,'real child identity stable')
 except BaseException as e:result['primary']=repr(e)
 result['elapsed_seconds']=time.monotonic()-started;rr=C.publish(out/'RESULT.json',result);print('SKVQ_VECTOR256_CHILD '+json.dumps(rr),flush=True);C.need(result['primary']is None,'real vector child failed');return 0
if __name__=='__main__':raise SystemExit(main())
