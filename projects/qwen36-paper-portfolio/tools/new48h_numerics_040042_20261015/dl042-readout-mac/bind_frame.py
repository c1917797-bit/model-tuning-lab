"""Actual completed build -> immutable 042 frame source, no containers/devices."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
 if set(r)!={'path','bytes','sha256'}or ref(r['path'])!=r:raise ValueError('exact actual Ref3')
 return json.loads(Path(r['path']).read_bytes())
def bind(template,owner_ref):
 m=obj(template);owner=obj(owner_ref)
 if owner['schema']!='deltalog.owned-kdma-build-host/v1'or owner['source']!=m['build_owner_source_ref']or owner['primary']is not None or owner['secondary']!=[]or owner['NPU']is not False:raise ValueError('actual042 completed Devices[] owner, never failed160 admission')
 c=obj(owner['cleanup'])
 if c['stopped']is not True or c['retained']is not True or c['errors']!=[]:raise ValueError('actual042 released owner')
 child=obj(owner['child']);result=child['result'];br=result['build_result_ref'];v=obj(br)
 if child['source']!=owner['source']or child['primary']is not None or result['build_complete']is not True or child['NPU']is not False:raise ValueError('actual042 CPU child identity')
 if v['schema']!='deltalog-readout-mac-actual-build/v042'or v['source_manifest']!=m['new_kernel_source_ref']or v['primary']is not None or v['Devices']!=[]or v['NPU']is not False or [x['arm']for x in v['artifacts']]!=['readout_mac042','readout_mac042_debug']:raise ValueError('actual042 both artifacts only')
 if not all(x['exit_code']==0 and x['error']is None for x in v['commands']):raise ValueError('actual build command failure')
 m=dict(m,new_build_ref=br,build_owner_ref=owner_ref,production_ref=v['artifacts'][0]['library'],debug_library=v['artifacts'][1]['library'],debug_build_ref=br,prepared_only=False)
 for r in [m['production_ref'],m['debug_library']]:
  if ref(r['path'])!=r:raise ValueError('new library bytes')
 m['dependencies']+= [owner_ref,owner['cleanup'],owner['child'],br,m['production_ref'],m['debug_library']]
 return m
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--build-owner-ref',required=True);a=p.parse_args();m=bind(ref(P/'frame/SOURCE_TEMPLATE.json'),json.loads(a.build_owner_ref));out=P/'frame/SOURCE_MANIFEST.json'
 with out.open('x',encoding='utf8',newline='\n')as f:json.dump(m,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(ref(out)));return 0
if __name__=='__main__':raise SystemExit(main())
