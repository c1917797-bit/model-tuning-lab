"""Read existing boundR3 refs, print exact newR4 bind argv; never execute."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import bridge_io as C
ORIGINAL035=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-diagnostic-bridge-owned-new48h-v1-035-repair4/SOURCE_MANIFEST.json',bytes=26248,sha256='e5566351d02b04792b871f67092876f69b7fb58bbc81c36d21360fb328ec6524')
OLD_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair3/SOURCE_TEMPLATE.json',bytes=60281,sha256='fd65bdc409c241e6e133931e64cb862a73ca41a6a85844a91103191934711253')
def main():
 p=argparse.ArgumentParser();p.add_argument('--old-bound-source-ref',required=True);a=p.parse_args();sr=json.loads(a.old_bound_source_ref);m=C.obj(sr)
 C.need(m['prepared_only']is False and m['prepared_template']==OLD_TEMPLATE and sr['path']==m['root']+'/SOURCE_MANIFEST.json'and m['root']==str(Path(OLD_TEMPLATE['path']).parent),'exact actual boundR3 predecessor metadata, not numeric qualification')
 template=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));root=template['root'];tr=dict(C.ref(P/'SOURCE_TEMPLATE.json'),path=root+'/SOURCE_TEMPLATE.json')
 for r in(ORIGINAL035,m['split_build_ref'],m['storage_authority_ref'],m['storage_seal_evidence_ref'],m['storage_seal_generation_ref']):C.checked(r)
 C.need(Path(m['storage_seal_generation_ref']['path']).name=='STORAGE_LEDGER061.12.json','same actual119seal12')
 j=lambda r:json.dumps(r,separators=(',',':'))
 argv=['/usr/bin/python3','-I','-B',root+'/run052.py','--execute','--phase','bind','--template-ref',j(tr),'--original035-source-ref',j(ORIGINAL035),'--build-ref',j(m['split_build_ref']),'--storage-authority-ref',j(m['storage_authority_ref']),'--storage-seal-evidence-ref',j(m['storage_seal_evidence_ref'])]
 print(json.dumps(dict(argv=argv,executes=False,sourceonly=True,old_R3_numeric_qualification_reused=False)))
if __name__=='__main__':main()
