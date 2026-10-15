"""Devices[]: original035 consume_pair over saved40raw+2anchors; no NPU rerun."""
import argparse,json,os,pathlib,subprocess,sys,time
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def main():
 if '--execute'not in sys.argv:print('disabled');return
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--stage',choices=('cpu-preflight',),required=True)
 for n in('source-ref','authority-ref','lifecycle-ref','output'):p.add_argument('--'+n,required=True)
 p.add_argument('--steps',type=int,choices=(16,),default=16);a=p.parse_args();sr=json.loads(a.source_ref);ar=json.loads(a.authority_ref);m=C.source(sr);C.window(ar)
 C.need(not list(pathlib.Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual no-device CPU environment')
 original=C.obj(m['original_source_ref']);producer=C.obj(m['original_producer_ref']);failed=C.obj(m['original_failed_owner_ref']);cleanup=C.obj(m['original_cleanup_ref'])
 C.need(failed['schema']=='deltalog.diagnostic-owned-host/v035'and failed['target_source']==m['original_source_ref']and failed['primary']is not None and failed['bridge_primitive_gate_pass']is False,'old035 owned FAIL remains unchanged')
 C.need(cleanup['resource_release_verified']is cleanup['stopped']is cleanup['retained']is True and cleanup['errors']==[]and cleanup['secondary_guard_cleanup']==[]and cleanup['unresolved_active_cid']is None,'actual saved035 stop-retain-release proof')
 C.need(producer['source']==m['original_source_ref']and producer['steps']==16 and producer['primary']is None and producer['NPU']is True and len(producer['records'])==40,'actual complete035 saved40 raw')
 out=pathlib.Path(a.output);C.need(not out.exists()and out.parent.is_dir(),'new CPU-only leaf');out.mkdir()
 consumer=original['files']['consume_pair.py'];C.checked(consumer);argv=[sys.executable,'-I','-B',consumer['path'],'--execute','--source-ref',json.dumps(m['original_source_ref']),'--producer-ref',json.dumps(m['original_producer_ref']),'--output',str(out/'PAIR_CONSUMPTION.json')]
 with(out/'consumer.stdout').open('x')as so,(out/'consumer.stderr').open('x')as se:r=subprocess.run(argv,stdout=so,stderr=se,timeout=min(440,1792135097-time.time()-90))
 C.write(out/'CONSUMER_EXEC.json',dict(argv=argv,exit_code=r.returncode,stdout=C.ref(out/'consumer.stdout'),stderr=C.ref(out/'consumer.stderr')));C.need(r.returncode==0,'actual035 pair CPU execution failed; preserve outputs')
 ir=C.ref(out/'PAIR_CONSUMPTION.json');v=C.obj(ir)
 C.need(v['schema']=='deltalog.diagnostic-consumption/v035'and v['source']==m['original_source_ref']and v['actual_result']==m['original_producer_ref'],'actual original035 pair source/raw join')
 for r in[v['original_strict_consumer'],v['domain_consumer'],*v['initial_anchor_refs'].values()]:C.checked(r)
 C.write(out/'STAGE_RESULT.json',dict(schema='deltalog035.savedraw-CPU-recovery/v038',source=sr,authority=ar,pass_gate=True,NPU=False,model_ready=False,diagnostic_complete=True,original_consumer=ir,original_numerical_pass=False,domain_checks_pass=v['domain_checks_pass'],diagnostic_capture_complete=v['diagnostic_capture_complete'],original_strict_result_preserved=v['original_strict_result_preserved'],original_failed_owner=m['original_failed_owner_ref'],old_host_failure_unchanged=True,numeric16_qualified=False,numeric160_qualified=False))
if __name__=='__main__':main()
