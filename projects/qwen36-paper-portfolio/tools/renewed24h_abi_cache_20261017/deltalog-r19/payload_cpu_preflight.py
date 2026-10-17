"""Actual payload subprocesses inside the original150s Devices[] source phase."""
import json,subprocess,sys,time
from pathlib import Path
def run(O,m,output,started):
 sr=m['firstdecode_contract']['payload_source'];p=O.obj(sr);root=Path(sr['path']).parent
 snapshot=O.obj(m['files']['payload_cold_readset_preflight.json']);O.need(snapshot['schema']=='deltalog.firstdecode-owned-cold-plan/v1'and snapshot['payload_source']==sr,'own exact ancillary command snapshot bound to frozen payload')
 plan=snapshot['plan'];reports=[]
 commands=[('PAYLOAD-SOFTWARE',[sys.executable,'-I','-B',str(O.obj_file(p['files']['software.py']))]),('PAYLOAD-COLD-READSET',plan['cold_source_tiny_loader_preflight'])]
 for label,argv in commands:
  O.need(argv[0]==sys.executable and argv[1:3]==['-I','-B'],'actual sameimage isolated Python only')
  remaining=min(60.,150.-(time.monotonic()-started)-5.);O.need(remaining>0,'originalCPU150 retains terminal margin')
  timeout=None
  try:r=subprocess.run(argv,capture_output=True,text=True,timeout=remaining)
  except subprocess.TimeoutExpired as e:
   timeout=e
   def text(v):return v.decode('utf8','replace')if isinstance(v,bytes)else(v or '')
   r=type('Terminal',(),dict(returncode=None,stdout=text(e.stdout),stderr=text(e.stderr)))()
  value=dict(argv=argv,source=sr,timeout_seconds=remaining,timed_out=timeout is not None,exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
  path=Path(output)/(label+'.json')
  with path.open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True);f.write('\n')
  rr=dict(path=path.as_posix(),bytes=path.stat().st_size,sha256=__import__('hashlib').sha256(path.read_bytes()).hexdigest());O.obj_file(rr);reports.append(rr)
  if timeout is not None:raise timeout
  O.need(r.returncode==0,'actual payload CPU child failed; original stdout/stderr retained')
 return dict(source=sr,software_cases=p['software_cases'],actual_sameimage_subprocesses=reports,NPU=False,HAL=False,qualification=False)
