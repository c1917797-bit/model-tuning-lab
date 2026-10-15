"""Read-only local source/CLI integration; no remote substitutions as runtime PASS."""
import argparse,ast,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location('_audit007_'+n[:-3],P/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 a=argparse.ArgumentParser();a.add_argument('--original-host',type=Path,required=True);a.add_argument('--launch-root',type=Path,required=True);v=a.parse_args()
 m=json.loads((P/'SOURCE_MANIFEST.json').read_bytes());n=0
 for name,x in m['files'].items():
  b=(P/name).read_bytes();assert (len(b),hashlib.sha256(b).hexdigest())==(x['bytes'],x['sha256']),name;n+=1
 H=load('host_ticket.py');text,pairs=H.adapt(v.original_host.read_bytes().decode(),{},{});ast.parse(text)
 E=load('entry.py');old=E.OLD;E.OLD=v.launch_root
 try:
  ov=E.overlay();E.private('guest_capture_entry.py',ov);E.private('capture_client.py',ov)
 finally:E.OLD=old
 cli=[]
 for name in('host_ticket.py','entry.py','parser_probe.py','consume.py','software.py'):
  z=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=15);assert z.returncode==0,(name,z.stderr);x=json.loads(z.stdout);assert x.get('enabled',x.get('default_enabled'))is False;cli.append(dict(file=name,exit_code=0,result=x))
 assert not any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules)
 print(json.dumps(dict(schema='mxr.once007.local-integration/v1',ownfiles_verified=n,original008_registered_inverse_deltas=len(pairs),actual003_private_guest_and_client_AST_bound=True,default_off_isolated_cli=cli,Devices=[],NPU=False,sameimage=False,resource_admitted=False)))
if __name__=='__main__':main()
