import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common116 as C


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--reviewed-template-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    tr=json.loads(a.reviewed_template_ref);m=C.obj(tr)
    C.need(tr==C.ref(P/'SOURCE_TEMPLATE.json')and m['schema']=='bole.tree-fa-owned-source/vFAfactor'and m['root']==str(P)and m['prepared_only']is True,'actual reviewed deployed116 template')
    for rr in m['files'].values():C.checked(rr)
    import decision_gate as R
    proof=R.consume(C,m['actual_diagnostic_source'],m['actual_diagnostic_owner']);abi=R.abi_provenance(C)
    C.need(abi['header']==m['header_ref'],'same actual canonical9.1 header, image-internal not host-mounted')
    m['calibration_readset']=proof['readset']+abi['readset'];m['original_fia_abi_ref']=abi['abi']
    C.window(m);m['prepared_only']=False;m['profile']='factors';m['prepared_template']=tr;m['output_root']+='/factors'
    target=P/'SOURCE_MANIFEST.json';C.write(target,m);print(json.dumps(C.ref(target)));return 0

if __name__=='__main__':raise SystemExit(main())
