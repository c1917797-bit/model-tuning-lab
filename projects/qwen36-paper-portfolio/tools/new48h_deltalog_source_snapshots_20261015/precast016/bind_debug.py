"""Exclusive source binder: real015 build and CPU Meta first, never invented PASS."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--debug-build-ref');p.add_argument('--template-sha256');a=p.parse_args()
 if not a.execute:print('disabled');return
 t=C.ref(P/'SOURCE_MANIFEST.json');C.need(t['sha256']==a.template_sha256,'actual reviewed016 template');m=C.obj(t);br=json.loads(a.debug_build_ref);b=C.obj(br);C.need(b['source_manifest']['sha256']==m['expected015_kernel_source']['sha256']and b['source_manifest']['bytes']==m['expected015_kernel_source']['bytes'],'actual exact015 kernel source')
 C.need(b['schema']=='deltalog-readout-sidecar-actual-build/v015'and b['primary']is None and len(b['artifacts'])==1 and b['artifacts'][0]['arm']=='readout_sidecar_v015','actual015 build');lib=b['artifacts'][0]['library'];C.checked(lib)
 m.update(debug_build_ref=br,debug_kernel_source_ref=b['source_manifest'],debug_library=lib,prepared_template=t)
 C.write(P/'BOUND_NUMERIC_SOURCE.json',m);print(json.dumps(C.ref(P/'BOUND_NUMERIC_SOURCE.json')))
if __name__=='__main__':main()
