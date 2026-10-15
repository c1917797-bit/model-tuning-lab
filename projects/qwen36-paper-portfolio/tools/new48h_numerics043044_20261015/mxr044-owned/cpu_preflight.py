"""Reuse original042 CPU preflight then actual044 Meta-layout/CLI controls."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);out=Path(a.output);C.need(out.parent.is_dir()and not out.exists(),'new CPU output')
 C.need(not list(Path('/dev').glob('davinci*')),'actual Devices[] CPU')
 old=C.obj(m['owned042_source']);component=C.obj(m['component044_source']);original=out.with_name('ORIGINAL042_SOFTWARE.json');argv=[sys.executable,'-I','-B',old['files']['cpu_preflight.py']['path'],'--execute','--source-ref',json.dumps(m['owned042_source']),'--output',str(original)]
 r=subprocess.run(argv,capture_output=True,text=True,timeout=180);C.need(r.returncode==0,'actual original042 preflight: '+r.stderr);base=C.obj(C.ref(original));C.need(base['pass_software']is True,'actual original bootstrap and immutable seeds preflight')
 argv2=[sys.executable,'-I','-B',str(P/'software_controls.py'),'--execute','--source-ref',json.dumps(sr),'--output',str(out.with_name('CONTROLS044.json'))]
 s=subprocess.run(argv2,capture_output=True,text=True,timeout=90);C.need(s.returncode==0,'actual adapter/Meta cold controls: '+s.stderr);control=C.ref(out.with_name('CONTROLS044.json'))
 C.write(out,dict(schema='mxr.block-refinement-devicefree/v044',source=sr,pass_software=True,Devices=[],NPU=False,selection=base['selection'],original042_result=C.ref(original),controls=control,commands=[dict(argv=argv,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr),dict(argv=argv2,returncode=s.returncode,stdout=s.stdout,stderr=s.stderr)],Meta_scope='Torch Meta pack/scatter shape only; ctypes037 has no registered dispatcher Meta; no NPU numeric qualification'))
 return 0
if __name__=='__main__':raise SystemExit(main())
