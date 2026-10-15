"""Devices[]: unchanged strict result first, then independent diagnostic030."""
import argparse,json,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for n in('source-ref','producer-ref','output'):p.add_argument('--'+n,required=True)
 a=p.parse_args();sr,pr=map(json.loads,(a.source_ref,a.producer_ref));m=C.source(sr);producer=C.obj(pr);out=Path(a.output)
 C.need(not out.exists()and out.parent.is_dir(),'exclusive CPU output')
 C.need(producer['source']==sr and producer['primary']is None and producer['steps']in(16,160),'actual completed producer')
 started=time.monotonic();strict=out.with_name('ORIGINAL_INDEPENDENT.json');domain=out.with_name('DOMAIN035.json')
 C.need(not strict.exists()and not domain.exists(),'retain unique strict/domain outputs')
 commands=[]
 def child(script,extra):
  argv=[sys.executable,'-I','-B',str(P/script),'--execute','--source-ref',json.dumps(sr),'--producer-ref',json.dumps(pr),*extra]
  left=590-(time.monotonic()-started);C.need(left>0,'shared original600s CPU budget')
  r=subprocess.run(argv,capture_output=True,text=True,timeout=left);receipt=dict(argv=argv,returncode=r.returncode,stdout=r.stdout[-8192:],stderr=r.stderr[-8192:]);commands.append(receipt)
  C.need(r.returncode==0,'actual source-bound independent child failed; outputs retained')
 child('consume.py',['--output',str(strict)]);old=C.obj(C.ref(strict))
 C.need(old['producer']==pr and old['source']==sr and type(old['pass_gate'])is bool,'actual original strict result')
 child('domain_entry.py',['--strict-consumer-ref',json.dumps(C.ref(strict)),'--output',str(domain)]);d=C.obj(C.ref(domain))
 # Anchors are extra raw not record rows: explicitly retain and validate both.
 anchors=d['anchors'];C.need(set(anchors)=={'1','16'},'both immutable initial-anchor refs in CPU closure')
 for r in anchors.values():C.checked(r)
 complete=bool(d['domain_checks_pass']and not d['missing_evidence']and not d['failures'])
 C.write(out,dict(schema='deltalog.diagnostic-consumption/v035',source=sr,actual_result=pr,producer=pr,original_strict_consumer=C.ref(strict),original_strict_result_preserved=dict(pass_gate=old['pass_gate'],primary=old['primary']),domain_consumer=C.ref(domain),validation_contract=d['validation_contract'],domain_checks_pass=d['domain_checks_pass'],diagnostic_capture_complete=complete,initial_anchor_refs=anchors,observation_complete=True,pass_gate=False,complete_proof=False,model_ready=False,performance_ready=False,commands=commands,NPU_reexecuted=False))
 return 0
if __name__=='__main__':raise SystemExit(main())
