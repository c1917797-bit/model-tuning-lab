"""Actual same660 graph software/raw/Devices[] independent child. DEFAULT OFF."""
import argparse,hashlib,importlib.util,json,os,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 p=Path(r['path']);need(set(r)=={'path','bytes','sha256'}and p.resolve()==p and p.is_file()and not p.is_symlink(),'strict ordinary Ref');b=p.read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'whole source/input');return b
def load(name,r):
 s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s);sys.modules[name]=m;exec(compile(checked(r),r['path'],'exec',dont_inherit=True),m.__dict__);return m
def identity(cid):
 tail=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split();group=Path('/proc/self/cgroup').read_text();need(len(cid)==64 and cid in group,'actual own CID/process namespace');return dict(pid=os.getpid(),start_ticks=int(tail[19]),cgroup=group,argv=list(sys.argv),cmdline_sha256=hashlib.sha256(Path('/proc/self/cmdline').read_bytes()).hexdigest())
def main():
 started=time.monotonic();p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--mode',choices=('software','graph','active','independent'));p.add_argument('--source');p.add_argument('--source-sha256');p.add_argument('--output');p.add_argument('--expected-cid');p.add_argument('--remaining-seconds',type=int);p.add_argument('--raw-ref-json');a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 cap=600 if a.mode in('graph','active')else 180;need(type(a.remaining_seconds)is int and 0<a.remaining_seconds<=cap and time.time()+a.remaining_seconds<=1792002456,'shared original remaining/cutoff')
 own=dict(path=a.source,bytes=Path(a.source).stat().st_size,sha256=a.source_sha256);mf=json.loads(checked(own));need(mf['schema']=='kivi.direct-fp32.graph-single4-owner-sources/v3'and mf['root']==str(P),'exact new source')
 for r in mf['files'].values():checked(r)
 W=load('_graph_r156_guest_window',mf['files']['window.py']);W.validate(checked(mf['authority']));need(mf['start_epoch']==W.START and mf['cutoff']==W.CUT and time.time()>=W.START,'actual authorized R156 window')
 ident=identity(a.expected_cid);out=Path(a.output);need(out.is_absolute()and not out.exists()and out.parent.is_dir(),'fresh child output');out.mkdir()
 graph=json.loads(checked(mf['graph_source']));result=dict(schema='kivi.r156.dual-domain-child/v1',source=own,writer_repair=mf['writer_repair'],mode=a.mode,identity=ident,actual_cid=a.expected_cid,python_version=list(sys.version_info[:3]),authority=mf['authority'],start_epoch=W.START,cutoff=W.CUT,primary=None,model_ready=False,performance_ready=False,run_authority=False)
 try:
  if a.mode=='independent':
   need(not Path('/dev/davinci0').exists()and not Path('/dev/davinci_manager').exists(),'actual Devices[] independent namespace')
   I=load('_graph_independent_leaf',mf['files']['independent.py']);raw_refs=json.loads(Path(a.raw_ref_json).read_bytes());need(set(raw_refs)=={'graph','active'},'both actual domains required');report=I.replay(raw_refs['graph'],mf['graph_source'],mf['files']['graph_evidence.py'],mf['oracle'])
   R=load('_active_independent_reference',mf['files']['active_reference.py']);active=R.replay(raw_refs['active'],mf['active_source']);D=load('_dual_actual_decision',mf['files']['decision.py']);D.numeric(report,active);result['independent']=dict(graph=report,active=active)
  elif a.mode=='active':
   os.environ['MAIN_OWNED_CID']=a.expected_cid;os.environ['KIVI_ACTIVE128_CASES_ENABLE']='1'
   A=load('_actual_active128',mf['files']['active_producer.py']);sr=out/'ACTIVE_SOURCE_REF.json';sr.write_text(json.dumps(mf['active_source']),encoding='utf-8')
   args=[mf['files']['active_producer.py']['path'],'--execute','--source-ref-json',str(sr),'--expected-cid',a.expected_cid,'--remaining-seconds',str(float(a.remaining_seconds-(time.monotonic()-started)-10)),'--output',str(out/'raw')]
   old=sys.argv;sys.argv=args
   try:need(A.main()==0,'actual original active128 graph returned zero')
   finally:sys.argv=old
   target=out/'raw'/'RESULT.json';wire=target.read_bytes();rr=dict(path=str(target),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest());value=json.loads(wire)
   need(value['source']==mf['active_source']and value['actual_cid']==a.expected_cid and value['primary']is None and value['actual_graph_captured']is True,'actual active128 owned graph result')
   result['raw_ref']=rr
   until=time.monotonic()+10
   while time.monotonic()<until:need(time.monotonic()-started<a.remaining_seconds and time.time()<1792002456,'same stage hold');time.sleep(min(.25,max(0,until-time.monotonic())))
  else:
   script=graph['files']['software_check.py'if a.mode=='software'else'standalone_graph.py'];G=load('_graph_original_entry',script)
   if a.mode=='graph':
    os.environ['MAIN_OWNED_CID']=a.expected_cid
    E=load('_graph_evidence_overlay',mf['files']['graph_evidence.py']);A=load('_graph_r156_adapter',mf['files']['graph_seam.py']);G=A.bind(G,script,E,mf['files']['graph_evidence.py'],mf['actual_writer'],mf['writer_repair'])
   output=out/('SOFTWARE.json'if a.mode=='software'else'raw');args=[script['path'],'--execute','--source-sha256',mf['graph_source']['sha256'],'--output',str(output)]
   if a.mode=='graph':
    remaining=a.remaining_seconds-(time.monotonic()-started)-10;need(remaining>0,'actual prelude+hold debited, no budget renewal')
    args+=['--expected-cid',a.expected_cid,'--remaining-seconds',str(float(remaining))]
   old=sys.argv;sys.argv=args
   try:need(G.main()==0,'actual full original graph entry returned zero')
   finally:sys.argv=old
   raw=output if a.mode=='software'else output/'RESULT.json';wire=raw.read_bytes();rr=dict(path=str(raw),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest());v=json.loads(wire)
   if a.mode=='software':
    need(v['tests']==36 and v['successful']is True and v['no_backend_import']is True and v['python_version'][:2]==[3,12],'actual same660 source36 no backend')
    cold=load('_channel32_source_controls',mf['files']['writer_check.py']);result['writer_software_ref']=cold.run(mf['writer_repair'],out/'WRITER-SOFTWARE.json',lambda:need(time.monotonic()-started<a.remaining_seconds and time.time()<1792002456,'same software child budget'))
    prefix=json.loads(checked(mf['prefix_source']));atomic=load('_unchanged_address_atomic_controls',prefix['files']['atomic_check.py']);result['atomic_software_ref']=atomic.run(prefix,out/'ATOMIC-SOFTWARE.json')
    T=load('_dual_new_controls',mf['files']['test_dual.py']);result['dual_software']=T.run(mf)
   else:
    need(v['actual_r156_writer']==mf['actual_writer'],'actual replacement writer Ref');need(v['actual_cid']==a.expected_cid and v['writer_full_pool_byte_parity']is True and v['full_outputs']==1536 and v['channel32_writer_source']==mf['writer_repair'],'actual graph raw exact owned parity')
    until=time.monotonic()+10
    while time.monotonic()<until:need(time.monotonic()-started<a.remaining_seconds and time.time()<1792002456,'same stage observation hold');time.sleep(min(.25,until-time.monotonic()))
   result['raw_ref']=rr
  need(identity(a.expected_cid)==ident,'same actual child identity')
 except BaseException as e:result['primary']=repr(e);result['traceback']=__import__('traceback').format_exc()
 wire=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode();target=out/'RESULT.json';target.write_bytes(wire);print('DIRECT_FP32_GRAPH_OWNED_CHILD_R156 '+json.dumps(dict(path=str(target),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())));need(result['primary']is None,'actual graph child failed')
 return 0
if __name__=='__main__':raise SystemExit(main())
