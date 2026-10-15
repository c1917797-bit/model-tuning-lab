"""Explicit actual022 light receipt binding; template cannot authorize devices."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import bridge_io as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256')
 for n in('composite-source-ref','composite-cpu-owner-ref'):p.add_argument('--'+n)
 a=p.parse_args()
 if not a.execute:print('disabled');return 0
 tr=C.ref(P/'SOURCE_TEMPLATE.json');C.need(tr['sha256']==a.template_sha256,'MAIN-reviewed exact new024 template');m=C.obj(tr)
 C.need(m['root']==str(P)and m['prepared_only']is True,'actual immutable deployment')
 cs,co=map(json.loads,(a.composite_source_ref,a.composite_cpu_owner_ref))
 api=C.load(m['composite_api_ref'],'_actual022_light');receipt=api.admit_receipt(cs,co)
 C.need(receipt['library']==m['library_ref']and receipt['model_ready']is False,'actual same B010 component receipt, not model certificate')
 m.update(prepared_only=False,composite_source_ref=cs,composite_cpu_owner_ref=co,lifecycle_source_ref=cs,composite_certificate_ref=receipt['certificate_ref'],prepared_template=tr)
 C.write(P/'SOURCE_MANIFEST.json',m)
 print(json.dumps(dict(source=C.ref(P/'SOURCE_MANIFEST.json'),component_only=True,model_ready=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
