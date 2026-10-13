"""Read-only original-operation + dual original oracle + exact owned release conjunction."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
PREFIX='MAIN_KIVI_DUAL_DOMAIN_R156 '
def need(v,m):
 if not v:raise ValueError(m)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true')
 for n in('source','result','terminal','output','cohort'):p.add_argument('--'+n,type=Path)
 for n in('source','result','terminal','cohort'):p.add_argument('--'+n+'-sha256')
 for n in('peer','operation','run-id','expected-command','expected-args'):p.add_argument('--'+n)
 p.add_argument('--physical',type=int);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(default_enabled=False,NPU=False)));return 0
 s=importlib.util.spec_from_file_location('_dual_actual_host',Path(__file__).with_name('host.py'));H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
 own,m,bm,B,refs=H.prepare(a);C,E=H.runtime(own,m,bm,B,refs,0)
 tr=B.ref(a.terminal);need(tr['sha256']==a.terminal_sha256,'exact actual complete operation original');record=B.original(B.load(tr),a.peer,a.operation)
 need(record['command']==a.expected_command and record['args']==json.loads(a.expected_args)and record['cwd']==str(B.CANONICAL)and 0<record['durationMs']<=1800000,'exact terminal host command/args/cwd/1800')
 rr=B.ref(a.result);need(rr['sha256']==a.result_sha256,'actual host complete RESULT')
 lines=record['stdout'].splitlines();need(len(lines)==1 and lines[0].startswith(PREFIX),'one real exact stdout marker')
 def pairs(items):
  out={}
  for k,v in items:need(k not in out,'duplicate original marker key');out[k]=v
  return out
 need(json.loads(lines[0][len(PREFIX):],object_pairs_hook=pairs)==rr,'actual host marker whole Ref')
 v=C.load(rr);need(v['schema']=='kivi.r156.dual-domain-host/v1'and v['source']==own and v['status']=='DUAL_DOMAIN_PENDING_ORIGINAL_CONSUMPTION'and v['primary']is None and v['secondary']==[],'actual successful new host, not prefix/unknown/partial')
 need(v['actual_host_argv']==[record['command'],*record['args']]==m['_runtime'].exact_host_argv(own,m['_cohort']['ref'],m['_cohort']['row']),'actual source-bound cohort argv')
 need(v['cohort']==m['_cohort']['ref']and v['run_id']==a.run_id and v['physical']==a.physical and v['authority']==m['authority']and v['start_epoch']==1791916056 and v['cutoff']==1792002456,'exact current R156/card/cohort')
 need(v['created_monotonic']==v['started_monotonic']and v['deadline_monotonic']==v['started_monotonic']+1800 and v['phase_seconds']==1800 and v['cleanup_seconds']==90 and 0<=v['cumulative_cleanup_seconds']<=90,'shared original cold-start/stop budget')
 need(v['actual_writer']==m['actual_writer']and v['active_source']==m['active_source']and v['observer_receipt']['original']==m['idle_helper']and v['observer_receipt']['adapter_path']==m['observer']['path'],'actual source-pinned writer and R162 observer')
 need([s['mode']for s in v['stages']]==['software','graph','active','independent']and len(v['cleanups'])==4 and set(v['raw_refs'])=={'graph','active'},'all ordered four stages and raw domains')
 cids=set();ind=None
 for stage in v['stages']:
  owned=C.load(stage['owned']);cid=owned['cid'];card=a.physical if stage['mode']in('graph','active')else None
  need(cid not in cids and owned['source']==own and owned['physical']==card and owned['numeric_sha256']==m['files']['guest.py']['sha256'],'unique actual same-source stage mapping');cids.add(cid)
  child=C.load(stage['child']);argv=stage['argv'];need(child['exit_code']==0 and child['child_termination_observed']is True and child['primary_error']is None and child['expected_image_python_argv']==argv and child['requested_argv']==['/usr/bin/docker','exec',cid,*argv]and child['actual_host_argv']==['/usr/bin/prlimit','--as=unlimited','--',*child['requested_argv']],'actual complete child argv/termination')
  C.read(child['stdout_ref']);C.read(child['stderr_ref']);value=C.load(stage['result'])
  need(value['schema']=='kivi.r156.dual-domain-child/v1'and value['source']==own and value['mode']==stage['mode']and value['actual_cid']==cid and value['primary']is None and value['authority']==m['authority']and value['start_epoch']==1791916056 and value['cutoff']==1792002456 and value['python_version'][:2]==[3,12],'actual new child source/clock/identity')
  if card is not None:
   B.validate_process(value,stage['process_proofs'],argv);need(value['raw_ref']==v['raw_refs'][stage['mode']],'exact native child raw Ref')
  if stage['mode']=='software':
   r=C.load(value['raw_ref']);need(r['tests']==36 and r['successful']is True and r['source']==m['graph_source']and r['no_backend_import']is True,'actual same-image original36')
   w=C.load(value['writer_software_ref']);q=C.load(value['atomic_software_ref']);need(w['tests']==16 and w['successful']is True and w['source']==m['writer_repair']and q['tests']==26 and q['successful']is True and q['writer_ref']==m['actual_writer'],'original writer16 and unchanged address26 source controls')
   need(value['dual_software']['tests']==21 and value['dual_software']['successful']is True and value['dual_software']['NPU']is False,'new software negative controls not NPU evidence')
  if stage['mode']=='independent':ind=value['independent']
  matches=[C.load(r)for r in v['cleanups']if C.load(r)['container']==cid];need(len(matches)==1,'one unique own cleanup');clean=matches[0]
  need(clean['stopped']is clean['retained']is True and clean['deleted']is False and clean['errors']==[],'complete own stop-retain no delete')
  for key in('before_inspect','after_inspect'):
   receipt=C.load(clean[key]);need(receipt['exit_code']==0,'actual lossless inspect');xs=json.loads(receipt['stdout']);need(len(xs)==1,'one exact inspect');C.inspect_owned(xs[0],owned)
   if key=='after_inspect':need(not xs[0]['State']['Running']and xs[0]['State']['Pid']==0 and not xs[0].get('ExecIDs')and not xs[0]['State']['OOMKilled'],'actual stopped/P0/noOOM/noExec')
  stop=C.load(clean['stop_receipt']);need(stop['requested_argv']==['/usr/bin/docker','stop','--time','15',cid]and stop['exit_code']==0,'exact own stop');C.read(clean['release_smi'])
  need(clean['cohort_release']['cohort']==v['cohort'],'same original release cohort')
 G=C.load(v['raw_refs']['graph']);A=C.load(v['raw_refs']['active']);D=H.load('_dual_readonly_decision',m['files']['decision.py']);D.graph_receipt(G,m['actual_writer'])
 need(G['source']==m['graph_source']and G['runtime_window']==dict(start_epoch=1791916056,cutoff=1792002456,overlay_source=m['files']['graph_evidence.py']),'actual saved graph source/new private clock')
 need(A['source']==m['active_source']and A['primary']is None and A['actual_graph_captured']is True and len(A['cases'])==2,'actual two active epochs, not metadata')
 need(ind is not None and ind['graph']['raw_ref']==v['raw_refs']['graph']and ind['active']['raw_ref']==v['raw_refs']['active']and ind['active']['source']==m['active_source'],'two independent consumers exact actual raw edges')
 need(ind['graph']['graph_source']==m['graph_source']and ind['graph']['overlay_source']==m['files']['graph_evidence.py']and ind['graph']['oracle_ref']==m['oracle'],'original independent oracle identity')
 qualification=D.numeric(ind['graph'],ind['active'])
 for r in refs:H.checked(r)
 result=C.write(a.output,dict(schema='kivi.r156.dual-domain-original-consumed/v1',source=own,original_terminal=tr,operation=a.operation,peer=a.peer,host_result=rr,raw_refs=v['raw_refs'],independent=ind,component=qualification,actual_writer=m['actual_writer'],cohort=v['cohort'],physical=a.physical,model_ready=False,performance_ready=False,task_ready=False,native_scheduler_qualified=False,full640_qualified=False,run_authority=False))
 print(json.dumps(result));return 0
if __name__=='__main__':raise SystemExit(main())
