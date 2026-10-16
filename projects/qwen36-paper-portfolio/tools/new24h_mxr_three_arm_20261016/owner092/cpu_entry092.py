"""Devices[] control tests then unchanged084 actual saved-frame extraction."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'exact source file');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=obj(sr);need(m['root']==str(HERE)and m['schema']=='mxr.prefill-three-arm-owned-source/v092','actual092 source');[checked(r)for r in m['files'].values()];need(m['files']['cpu_entry092.py']==ref(__file__),'actual092 child')
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','Devices[] controls')
 need(not a.output.exists()and a.output.parent.is_dir(),'fresh exclusive output');a.output.mkdir()
 tests=load(m['files']['test_guard092.py'],'_092_actualcontrols');count=tests.run_controls();need(count==m['guard_control_cases'],'same producer/consumer software count')
 gm=obj(m['guest_source']);g=load(gm['files']['guest_core.py'],'_092_unchanged084');old=sys.argv
 try:
  sys.argv=[gm['files']['guest_core.py']['path'],'--cpu-preflight','--source-ref',json.dumps(m['guest_source']),'--output',str(a.output/'frame')];code=g.main()
 finally:sys.argv=old
 need(code==0,'actual084 saved frame CPU preflight');stage=ref(a.output/'frame/STAGE_RESULT.json');v=obj(stage)
 need(v['schema']=='mxr.prefill-three-arm-stage/v084'and v['source']==m['guest_source']and v['primary']is None and v['NPU']is False and v['result']['actual_saved_frame_extracted']is True,'actual unchanged084 nested receipt')
 result=dict(schema='mxr.bounded-top-guard-mounted-preflight/v092',source=sr,guest_source=m['guest_source'],actual_guard_controls_pass=True,guard_control_cases=count,actual_saved_frame_preflight_pass=True,frame_stage_ref=stage,NPU=False,qualified=False)
 with(a.output/'PREFLIGHT092.json').open('x',encoding='utf8',newline='\n')as f:json.dump(result,f,sort_keys=True,allow_nan=False);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
