"""Existing066 Devices[] entry seam, only saved160 anchor-PID recovery."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import bridge_io as C,provenance127 as V
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--execute',action='store_true');ap.add_argument('--stage',choices=('cpu-preflight',),required=True);ap.add_argument('--steps',choices=(16,),type=int,default=16)
 for n in ('source-ref','authority-ref','lifecycle-ref','output'):ap.add_argument('--'+n,required=True)
 a=ap.parse_args()
 if not a.execute:print('disabled');return 0
 sr,ar=json.loads(a.source_ref),json.loads(a.authority_ref);m=C.source(sr);C.window(ar)
 C.need(json.loads(a.lifecycle_ref)==m['lifecycle_source_ref'],'same historical ABI component')
 C.need(not list(Path('/dev').glob('davinci*'))and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','actual Devices[] CPU-only')
 evidence=C.obj(m['actual_fault_evidence_ref']);V.validate(evidence,C.obj)
 original=C.obj(m['original_source_ref']);producer=C.obj(m['original_producer_ref'])
 V.arm(C.obj(m['original_arm_ref']),C.obj(m['original_device_ref']),C.obj(m['original_handshake_ref']),m['original_plan_ref'],C.obj(m['original_plan_ref']),producer,original,evidence['small_documents']['numeric_cleanup']['cid'])
 policy=C.load(original['files']['collection_policy.py'],'_127_original_collection_policy');policy.require_complete(C,producer,m['original_source_ref'])
 C.need(m['bound']is True and m['original_timeout_seconds']==V.TIMEOUT and m['allowed_fault']=='exact-original-domain-TimeoutExpired-shared590','bound exact timeout category')
 out=Path(a.output);C.need(not out.exists()and out.parent.is_dir(),'new recovery output');out.mkdir();start=time.monotonic()
 argv=[sys.executable,'-I','-B',str(P/'entry127.py'),'--execute','--consumer-source-ref',json.dumps(sr),'--producer-source-ref',json.dumps(m['original_source_ref']),'--producer-ref',json.dumps(m['original_producer_ref']),'--strict-ref',json.dumps(m['original_strict_ref']),'--output',str(out/'DOMAIN127.json')]
 # Keep even the original residual 585.611s sub-budget. Do not add the saved
 # strict child's 4.389s back to the domain consumer or extend the fixed cutoff.
 left=min(V.TIMEOUT,590-(time.monotonic()-start),1792220533-time.time()-90);C.need(left>0,'original590/585.611 +cleanup90/fixedcut')
 try:
  r=subprocess.run(argv,capture_output=True,text=True,timeout=left)
  receipt=dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr,timeout_seconds=left)
 except subprocess.TimeoutExpired as exc:
  C.write(out/'CHILD127.json',dict(argv=argv,returncode=None,timeout_seconds=left,primary=repr(exc)))
  raise
 C.write(out/'CHILD127.json',receipt);C.need(r.returncode==0,'recovery CPU child failed; all reports preserved')
 domain=C.obj(C.ref(out/'DOMAIN127.json'));envelope=C.obj(C.ref(out/'DOMAIN127.json.consumer127.json'))
 C.need(domain['source']==m['original_source_ref']and domain['producer']==m['original_producer_ref']and domain['steps']==160 and domain['primary']is None and domain['domain_checks_pass']is True and domain['failures']==domain['missing_evidence']==[]and len(domain['rows'])==328 and len(domain['sidecar_results'])==351,'complete actual operational328/351 domain, not collection-only')
 C.need(envelope['consumer_source']==sr and envelope['producer_source']==m['original_source_ref']and envelope['original_domain_exit']==0 and envelope['qualification']is envelope['model_admitted']is False,'explicit independent consumer identity/no promotion')
 C.write(out/'STAGE_RESULT.json',dict(schema='deltalog.anchor-consumer-CPU-recovery/v127',source=sr,authority=ar,pass_gate=True,producer_source=m['original_source_ref'],actual_original_producer=m['original_producer_ref'],original_failed_owner=m['original_failed_owner_ref'],preserved_original_strict=m['original_strict_ref'],actual_fault_evidence=m['actual_fault_evidence_ref'],domain=C.ref(out/'DOMAIN127.json'),consumer_envelope=C.ref(out/'DOMAIN127.json.consumer127.json'),domain_checks_pass=True,diagnostic_capture_complete=True,old_failure_unchanged=True,NPU=False,NPU_reexecuted=False,model_ready=False,model_admitted=False,performance_ready=False))
 return 0
if __name__=='__main__':raise SystemExit(main())
