"""Typed host dependencies; runtime/image paths are never guessed host mounts."""
from pathlib import Path
import importlib.util,sys,time
def refs(O,m):
 contract=m['firstdecode_contract'];ps=contract['payload_source'];p=O.obj(ps)
 import renewed_closed_reader101r19 as renewal
 import prior_empty_r19
 renewal.check();out=[renewal.AUTHORITY,*prior_empty_r19.refs(),ps,*p['files'].values(),*p['numerical_ro_readset']]
 # Explicit frozen tiny ABI reader closure. Its output directory contains the
 # original owner/stage/evidence; the reader itself authenticates all Ref3s.
 tiny=p['tiny_source'];tm=O.obj(tiny);out +=[tiny,*tm['files'].values(),p['tiny_independent']]
 ss=contract['closed_source_ref'];sm=O.obj(ss);out +=[ss,*sm['files'].values()]
 fp=O.obj_file(sm['files']['capture_closed2.py']);s=importlib.util.spec_from_file_location('_firstdecode_seal_readset',fp);seal=importlib.util.module_from_spec(s);sys.modules[s.name]=seal;s.loader.exec_module(seal)
 value=contract['closed_readset'];O.need(value['source']==ss and value['evidence']==contract['closed_evidence_ref']and value['closed_count']==15 and value['numeric_qualified']is False,'bound actual full13+2 storage-only closure');out+=value['refs']
 unique={}
 for r in out:O.obj_file(r);unique[(r['path'],r['bytes'],r['sha256'])]=r
 return list(unique.values())
def bind_closed(O,contract,readonly_guard=None):
 ss=contract['closed_source_ref'];sm=O.obj(ss);fp=O.obj_file(sm['files']['capture_closed2.py'])
 s=importlib.util.spec_from_file_location('_firstdecode_bind_seal',fp);seal=importlib.util.module_from_spec(s);sys.modules[s.name]=seal;s.loader.exec_module(seal)
 if readonly_guard is not None:readonly_guard.install(seal)
 import stream_seal_adapter
 stream_seal_adapter.install(seal,sm['files']['capture_closed2.py'])
 import renewed_closed_reader101r19 as renewal
 renewal.install(seal,sm['files']['capture_closed2.py'])
 # Fail source/argv/writer identity BEFORE expensive closed-data verification.
 # The complete original readset()/validate() and terminal gates still follow.
 early,_=seal.canonical(ss);early.no_writers()
 import prior_empty_r19
 prior=prior_empty_r19.validate(O,early)
 value=seal.readset(contract['closed_evidence_ref'],ss)
 O.need(value['closed_count']==15 and value['numeric_qualified']is False,'actual reviewed complete closed15')
 return dict(value,source=ss,evidence=contract['closed_evidence_ref'],prior_failed_empty_attempt={k:v for k,v in prior.items()if k!='current_no_writers'},renewal_validation=dict(renewal.check(),validated_at_epoch=time.time(),historical_source=ss,historical_evidence=contract['closed_evidence_ref']))
def payload_roots(O,m):
 ps=m['firstdecode_contract']['payload_source'];p=O.obj(ps)
 roots=[Path(ps['path']).parent,Path(p['tiny_source']['path']).parent,Path(p['tiny_independent']['path']).parent]
 for r in p['numerical_ro_readset']:roots.append(Path(r['path']).parent)
 return tuple(sorted({x.as_posix()for x in roots}))
def post(O,m,ir):
 x=O.obj(ir);O.need(x['schema']=='deltalog.firstdecode-postconsumer-input/v1'and set(x)=={'schema','model_source','payload_source','owner_ref','inspect_ref','loaded_ref','reports_ref'},'small exact typed actual postconsumer input')
 O.need(x['payload_source']==m['firstdecode_contract']['payload_source'],'same frozen payload')
 out=[ir,x['model_source']]+[x[k]for k in('owner_ref','inspect_ref','loaded_ref','reports_ref')]
 report=O.obj(x['reports_ref']);O.need(report['schema']=='deltalog.firstdecode-all4-report-refs/v1'and report['source']==x['model_source']and report['payload_source']==x['payload_source']and len(report['reports'])==4,'four actual typed report roots')
 out +=report['reports']+report['expected_stop_logs']
 owner=O.obj(x['owner_ref']);O.need(owner['source']==x['model_source']and owner['status']=='failed'and owner['primary']is not None and owner['secondary']==[]and owner['all_created_containers_release_verified']is True,'deliberate-stop original FAIL retained/all released')
 for r in out:O.obj_file(r)
 return x,out
