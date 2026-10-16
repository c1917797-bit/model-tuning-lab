"""Actual same-image Devices[] load+13/14arg Meta; no device initialization."""
import argparse,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);C.window(m);C.build(m)
 C.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not list(Path('/dev').glob('davinci*')),'actual Devices[] CPU environment')
 C.need(not a.output.exists()and a.output.parent.is_dir(),'exclusive CPU output');a.output.mkdir()
 import torch as t
 t.set_num_threads(1)
 C.need(C.ref('/usr/local/Ascend/cann-9.1.0/set_env.sh')==dict(path='/usr/local/Ascend/cann-9.1.0/set_env.sh',bytes=5112,sha256='de50f1bf5b960f8305792ef407e3bfc3fc1b6d82931d0feae39ac4c965690aaf'),'actual CPU CANN environment source')
 import meta051
 v=meta051.run(t,m['build_ref'],m['kernel_source_ref'])
 C.need('torch_npu'not in sys.modules,'no backend import/device runtime invocation')
 fds=[]
 for f in Path('/proc/self/fd').iterdir():
  try:vf=os.readlink(f)
  except FileNotFoundError:continue
  if any(n in vf for n in('davinci','devmm_svm','hisi_hdc')):fds.append(vf)
 C.need(not fds,'no actual device FD afterDSOload')
 maps=Path('/proc/self/maps').read_text();C.need(all(r['path']in maps for r in(m['production_library'],m['debug_library'])),'actual DSOs mapped')
 C.write(a.output/'DSO_MAPS.json',dict(mapped_libraries=[r for r in(m['production_library'],m['debug_library'])if r['path']in maps],runtime_maps=[line for line in maps.splitlines()if any(x in line for x in('libascendcl','libtorch_npu','libopapi'))],runtime_maps_are_not_device_execution=True,no_device_fds=True))
 C.write(a.output/'STAGE_RESULT.json',dict(schema='deltalog.graph-CPU-stage/v095',source=sr,actual_meta=v,maps=C.ref(a.output/'DSO_MAPS.json'),NPU=False,qualified=False));return 0
if __name__=='__main__':raise SystemExit(main())
