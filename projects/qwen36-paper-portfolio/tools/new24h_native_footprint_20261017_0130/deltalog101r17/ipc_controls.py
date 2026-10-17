"""Real Linux AF_UNIX regression against unchanged source-qualified scanner."""
import hashlib,importlib.util,os,socket,sys,tempfile,uuid
from pathlib import Path
SCANNER_REF={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/adakv030-fa-physical-layout-observation-v6-user72h-20261010/output_budget.py","bytes":16355,"sha256":"44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad"}
def need(v,m):
 if not v:raise ValueError(m)
def load_scanner():
 p=Path(SCANNER_REF["path"])
 if os.name=="nt":p=Path("C:/Users/Huawei/AppData/Local/Temp/mxr043r1-resource-actual/output_budget.py")
 b=p.read_bytes();need((len(b),hashlib.sha256(b).hexdigest())==(SCANNER_REF["bytes"],SCANNER_REF["sha256"]),"original actual scanner unchanged")
 s=importlib.util.spec_from_file_location("_original011_IPC_scanner",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def run(parent):
 need(sys.platform=="linux"and hasattr(socket,"AF_UNIX"),"actual Linux AF_UNIX controls required; no Windows substitute")
 parent=Path(parent);need(os.environ.get('TMPDIR')=='/adakv-results'and parent==Path("/adakv-results")and parent.is_dir()and not parent.is_symlink(),"existing exact owned alias and actual TMPDIR only")
 S=load_scanner();held=[];paths=[]
 with tempfile.TemporaryDirectory(prefix=".ipc-",dir=parent)as d:
  root=Path(d);stage=root/"candidate";stage.mkdir();nested=stage/".runtime"/"tmp";nested.mkdir(parents=True)
  def bind(path):
   need(len(os.fsencode(path))<108,"actual Unix socket path bound")
   sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);sock.bind(str(path));held.append(sock);paths.append(path)
  try:
   direct=stage/str(uuid.uuid4());bind(direct)
   value=S.scan(root,socket_parent=[stage],ipc_source=S.IPC_SOURCE);used=S.consume(value,root)
   need(value["socket_count"]==1 and value["sockets"][0]["actual_socket_parent"]==str(stage)and used==direct.stat().st_size,"actual direct UUID4 socket scanned and independently consumed")
   wrong=nested/str(uuid.uuid4());bind(wrong)
   try:S.scan(root,socket_parent=[stage],ipc_source=S.IPC_SOURCE)
   except ValueError as error:need(str(error)=="Unix socket outside actual TMPDIR-owned stage","nested rejected by original exact socket guard")
   else:raise ValueError("nested Unix socket incorrectly accepted")
   held.pop().close();paths.pop().unlink()
   bad=stage/"not-a-uuid";bind(bad)
   try:S.scan(root,socket_parent=[stage],ipc_source=S.IPC_SOURCE)
   except ValueError as error:need("canonical UUID4"in str(error),"bad basename original guard")
   else:raise ValueError("bad basename accepted")
  finally:
   for sock in held:sock.close()
   for path in paths:path.unlink()
 return dict(schema="mxr.actual-Linux-IPC-original-scan-controls/v043-repair2",actual_Linux_AF_UNIX=True,original_scanner=SCANNER_REF,direct_UUID4_scan_consume_pass=True,nested_original_rejection_pass=True,bad_basename_original_rejection_pass=True,scanner_unchanged=True,NPU=False)
