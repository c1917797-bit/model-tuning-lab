"""Persist actual loaded-vs-calibrated DSO operands BEFORE exact identity gate.

No subset allowance, address-equality test, ABI override or numerical permission.
"""
import json,os
from pathlib import Path

def need(v,m):
 if not v:raise ValueError(m)

def refs(registration):
 extension=registration['actual_extension_ref'];opapi=[r['ref']for r in registration['actual_opapi_mappings']]
 for r in(extension,*opapi):need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact loaded/calibrated library Ref3')
 return extension,opapi

def compare(actual,calibrated):
 ae,ao=refs(actual);ce,co=refs(calibrated)
 return dict(extension_equal=ae==ce,opapi_ordered_equal=ao==co,
  actual_extension=ae,calibrated_extension=ce,actual_opapi=ao,calibrated_opapi=co,
  unexpected_actual=[r for r in ao if r not in co],missing_actual=[r for r in co if r not in ao],
  exact_pass=ae==ce and ao==co)

def persist(C,source_ref,own,actual,abi_ref,abi,rank,*,maps_path='/proc/self/maps'):
 need(C.obj(source_ref)==own and C.ref(__file__)==own['files']['registration_audit131r11.py'],'exact source-owned loaded library observer')
 need(C.obj(abi_ref)==abi and type(rank)is int and rank in range(4),'actual source-bound calibrated ABI and TP rank')
 result=compare(actual,abi['registration'])
 # Calibrated identities are authenticated by the exact ABI receipt. Do not
 # require an old expected library path to be current before saving mismatch.
 for r in(result['actual_extension'],*result['actual_opapi']):C.checked(r)
 need(maps_path=='/proc/self/maps','actual current process mapping source only')
 with Path(maps_path).open('rb')as f:maps=f.read(4*2**20+1)
 need(len(maps)<=4*2**20,'bounded full actual process DSO mapping before assert')
 maps=maps.decode('utf8','strict')
 for r in(result['actual_extension'],*result['actual_opapi']):
  need(any(line.split()[-1]==r['path']for line in maps.splitlines()if line.split()),'each observed actual library is mapped now')
 value=dict(schema='bole.actual-native-library-identity-before-gate/v131r11',source=source_ref,rank=rank,pid=os.getpid(),
  calibrated_abi_ref=abi_ref,actual_registration=actual,calibrated_registration=abi['registration'],comparison=result,
  actual_process_maps=maps,phase='after native prefill, BEFORE existing exact library identity gate',gate_relaxed=False,model_ready=False)
 root=Path(os.environ['BOLE_MODEL_RAW_ROOT']);need(str(root)==own['model_receipt_root']and root.is_dir()and all(not p.is_symlink()for p in(root,*root.parents)),'exact existing owned receipt root')
 raw=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();need(len(raw)<=5*2**20,'bounded complete library evidence')
 p=root/('BOLE-NATIVE-LIBRARY-IDENTITY-RANK-%d.json'%rank)
 with p.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(root,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return C.ref(p),result['exact_pass']
