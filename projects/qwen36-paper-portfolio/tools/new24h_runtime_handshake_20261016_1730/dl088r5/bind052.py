"""Actual051 build is mandatory. No fabricated DSO or Meta receipt."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import bridge_io as C,split_build052
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-ref');p.add_argument('--original035-source-ref');p.add_argument('--build-ref');p.add_argument('--storage-authority-ref');p.add_argument('--storage-seal-evidence-ref');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 import storage_bridge121 as seal093
 evidence_ref=seal093.require_evidence(C,a.storage_seal_evidence_ref)
 C.window(__import__('window056').AUTH)
 tr=json.loads(a.template_ref);C.need(C.ref(P/'SOURCE_TEMPLATE.json')==tr,'exact052 template');m=C.obj(tr)
 for r in m['files'].values():C.checked(r)
 storage_ref=json.loads(a.storage_authority_ref);__import__('storage061').authority(storage_ref,C.obj);m['storage_authority_ref']=storage_ref
 old=C.obj(json.loads(a.original035_source_ref));C.need(old['prepared_only']is False and old['library_ref']==m['state_predecessor_library_ref'],'actual old state/ABI provenance only')
 api=C.load(m['composite_api_ref'],'_actual022_prior');receipt=__import__('historical022056').admit(m['composite_api_ref'],old['composite_source_ref'],old['composite_cpu_owner_ref'])
 C.need(receipt['library']==m['state_predecessor_library_ref']and receipt['model_ready']is False,'old certificate not new-library qualification')
 br=json.loads(a.build_ref);build=C.obj(br);arts=build['artifacts']
 C.need([x['arm']for x in arts]==list(split_build052.ARMS),'actual051 ordered arms')
 m.update(prepared_only=False,prepared_template=tr,split_build_ref=br,debug_build_ref=br,library_ref=arts[0]['library'],debug_library=arts[1]['library'],debug_kernel_source_ref=m['split_kernel_source_ref'],composite_source_ref=old['composite_source_ref'],composite_cpu_owner_ref=old['composite_cpu_owner_ref'],lifecycle_source_ref=old['composite_source_ref'],composite_certificate_ref=receipt['certificate_ref'])
 split_build052.admit(m,C.obj,C.ref);C.checked(m['firstfault_ref'])
 m['storage_seal_evidence_ref']=evidence_ref;m['storage_seal_generation_ref']=seal093.accept_existing(C,m,evidence_ref,storage_ref)
 C.write(P/'SOURCE_MANIFEST.json',m);print(json.dumps(C.ref(P/'SOURCE_MANIFEST.json')));return 0
if __name__=='__main__':raise SystemExit(main())
