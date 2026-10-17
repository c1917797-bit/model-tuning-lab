"""Same frozen payload consume API; owner-controlled opt result prewrite guard."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for name in('model-source-ref','payload-source-ref','owner-ref','inspect-ref','loaded-ref','reports-ref'):p.add_argument('--'+name)
 p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 import owner_overlay as O,ipc_controls
 args=[json.loads(getattr(a,n.replace('-','_')))for n in('model-source-ref','payload-source-ref','owner-ref','inspect-ref','loaded-ref','reports-ref')]
 model,payload=args[:2];m=O.current(model);pm=O.obj(payload)
 O.need(m['firstdecode_contract']['payload_source']==payload and O.obj_file(m['files']['postconsume_entry.py'])==Path(__file__).resolve(),'actual owner/source/payload CLI')
 fp=O.obj_file(pm['files']['firstdecode_cli.py']);sys.path.insert(0,str(fp.parent))
 spec=importlib.util.spec_from_file_location('firstdecode_cli',fp);M=importlib.util.module_from_spec(spec);sys.modules[spec.name]=M;spec.loader.exec_module(M)
 value=M.consume(*args)
 O.need(a.output==Path('/adakv-results/FIRST-DECODE-INDEPENDENT.json'),'one exact owned CPU result')
 body=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
 scanner=ipc_controls.load_scanner();used=0
 for root in(m['output_root'],m['postconsumer_output_root']):
  root=Path(root);observation=scanner.scan(root,socket_parent=[root/n for n in('cpu-preflight','candidate','cpu-consumer')],ipc_source=scanner.IPC_SOURCE);used+=scanner.consume(observation,root)
 O.need(used+len(body)+64*2**20<=2*2**30,'same combined opt2GiB retains terminal64MiB before actual CPU report write')
 with a.output.open('xb')as f:f.write(body);f.flush();__import__('os').fsync(f.fileno())
 print(json.dumps(dict(path=a.output.as_posix(),bytes=len(body),sha256=hashlib.sha256(body).hexdigest())))
 return 0 if value['diagnostic_complete']else 3
if __name__=='__main__':raise SystemExit(main())
