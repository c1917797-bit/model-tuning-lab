"""v12 differences: real isolated whole-component replay, strict cache negatives.
Foreign modules below are rejected metadata fixtures, NOT runtime substitutes.
"""
import hashlib,json,os,subprocess,sys,types,unittest
from pathlib import Path
import source_contract as c,component_bootstrap as b
COMPONENT=dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-sparq005-consumer-mounts-whole-user72h-20261009-001.json",
 sha256="5614469e833ada86ad9f2f5869d084752a7262d0ac1f3701b7246e9701df7a74")
class ComponentBootstrap(unittest.TestCase):
 def reject(self,name,path):
  previous=sys.modules.get(name);bad=types.ModuleType(name)
  if path is not None:bad.__file__=path
  sys.modules[name]=bad
  try:
   with self.assertRaisesRegex(ValueError,"cached"):b.verify_cached(c)
   self.assertIs(sys.modules[name],bad) # production guard must NOT delete/rebind it
  finally:
   if previous is None:sys.modules.pop(name,None)
   else:sys.modules[name]=previous
 def test_foreign_contract_rejected(self):self.reject("contract",str(c.ROOT/"source_contract.py"))
 def test_foreign_receipt_rejected(self):self.reject("receipt",str(c.ROOT/"source_contract.py"))
 def test_foreign_shard_rows_rejected(self):self.reject("shard_rows",str(c.ROOT/"source_contract.py"))
 def test_foreign_native_package_rejected(self):self.reject("sparq_token_v4",str(c.ROOT/"source_contract.py"))
 def test_missing_cached_source_rejected(self):self.reject("contract",None)
 def test_different_whole_reader_rejected(self):self.reject("original_terminal",str(c.ROOT/"source_contract.py"))
 def test_identical_full_whole_reader_allowed(self):
  import original_terminal
  self.assertIn(Path(original_terminal.__file__).resolve(),(c.ROOT/"original_terminal.py",c.KERNEL/"original_terminal.py"))
  self.assertIn("original_terminal",b.verify_cached(c))
 def test_complete_native_and_shard_explicit_choices(self):
  wants=b.expected(c)
  for name in (*b.NATIVE_NAMES,"shard_contract","shard_rows","shard_proof","shard_host"):
   self.assertIn(name,wants);self.assertEqual(len(wants[name]),1)
  self.assertEqual(len(wants["original_terminal"]),2)
 def test_actual_clean_I_whole_component_replay(self):
  source_sha=c.sha(c.ROOT/"SOURCE_MANIFEST.json");env=dict(os.environ,PYTHONPATH="",PYTHONDONTWRITEBYTECODE="1",TORCH_DEVICE_BACKEND_AUTOLOAD="0")
  argv=[sys.executable,"-I","-B",str(c.ROOT/"component_bootstrap.py"),"--execute","--source-manifest-sha256",source_sha,
   "--component",COMPONENT["path"],"--component-sha256",COMPONENT["sha256"]]
  r=subprocess.run(argv,cwd="/",env=env,capture_output=True,text=True,timeout=180)
  self.assertEqual(r.returncode,0,r.stdout+"\n"+r.stderr)
  lines=[x for x in r.stdout.splitlines() if x.startswith("SPARQ_COMPONENT_BOOTSTRAP ")]
  self.assertEqual(len(lines),1);p=json.loads(lines[0].split(" ",1)[1])
  source=dict(path=str(c.ROOT/"SOURCE_MANIFEST.json"),sha256=source_sha)
  self.assertTrue(b.verify_probe(c,dict(component_bootstrap=p),source,COMPONENT))
  self.assertFalse(p["npu_rerun"]);self.assertFalse(p["model_executed"])
 def test_actual_clean_I_default_OFF(self):
  r=subprocess.run([sys.executable,"-I","-B",str(c.ROOT/"component_bootstrap.py")],cwd="/",
   env=dict(os.environ,PYTHONPATH=""),capture_output=True,text=True,timeout=10)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),
   dict(status="disabled",ready=False,npu_executed=False))

class ExactOwnedWorkdir(unittest.TestCase):
 def fixture(self,root):
  import host_run as h,service_contract as service,consume_model
  source=c.bound(c.ROOT/"SOURCE_MANIFEST.json",c.sha(c.ROOT/"SOURCE_MANIFEST.json"))
  files=c.obj(source)["files"];cid="a"*64;arm="cpu-preflight"
  e=dict(cid=cid,name="source-workdir-positive",image=service.IMAGE,arm=arm,source=source,host_sha256=files["host_run.py"],
   guest_cpus=[0],mounts={str(c.ROOT):(str(c.ROOT),False),str(root):(str(root),True)})
  argv=h.create_argv(e)
  created=c.write(root/"create.json",dict(exit_code=0,stdout=cid+"\n",requested_argv=argv))
  owned=c.write(root/"OWNED.json",dict(e,sources=files,create_receipt=created))
  x=dict(Id=cid,Image=service.IMAGE,Name="/"+e["name"],ExecIDs=None,
   State=dict(Running=False,Pid=0,OOMKilled=False),HostConfig=dict(Privileged=False,Memory=8*1024**3,MemorySwap=8*1024**3,
    NanoCpus=10**9,CpusetCpus="0",IpcMode="private",NetworkMode="none",ShmSize=4*1024**3,PidsLimit=2048,
    DeviceRequests=None,DeviceCgroupRules=None,CapDrop=["ALL"],SecurityOpt=["no-new-privileges"],Devices=[]),
   Config=dict(Image=service.IMAGE,Entrypoint=["/bin/bash"],Cmd=["-c","exec /bin/sleep infinity"],
    Labels=h.labels(e),Env=[k+"="+v for k,v in h.environment(True).items()],WorkingDir=argv[argv.index("--workdir")+1]),
   Mounts=[dict(Type="bind",Destination=n,Source=p,RW=rw) for n,(p,rw) in e["mounts"].items()])
  return h,consume_model,source,files,cid,e,owned,x
 def check(self,mutation=None):
  import tempfile
  with tempfile.TemporaryDirectory(prefix="full-v12-exact-workdir-") as folder:
   root=Path(folder);h,m,source,files,cid,e,owned,x=self.fixture(root)
   h.validate_inspect(x,e) # Real unchanged complete producer predicate first.
   if mutation is not None:mutation(x)
   observed=c.write(root/"inspect.json",dict(exit_code=0,requested_argv=["/usr/bin/docker","inspect",cid],
    stdout=json.dumps([x])))
   if mutation is None:
    self.assertEqual(m.stopped(observed,cid,owned,source,files,True),x)
   else:
    with self.assertRaises(ValueError):h.validate_inspect(x,e)
    with self.assertRaises(ValueError):m.stopped(observed,cid,owned,source,files,True)
 def test_real_complete_producer_to_consumer_workdir(self):self.check()
 def test_wrong_workdir_hard_rejected(self):self.check(lambda x:x["Config"].update(WorkingDir=str(c.ROOT)))
 def test_foreign_CID_hard_rejected(self):self.check(lambda x:x.update(Id="b"*64))

# Actual05b5 raw capture, not a fabricated SMI layout. The full stdout is
# immutable here so same-image tests need no extra evidence mount.
HBM_RAW_REF=dict(path="/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-full-v12-diagnostic-user72h-20261009-002/cpu-preflight/observation-raw-1791571902397561240.json",sha256="ab66a7d96c3dd1d10e86f6c9ce7cf3b6e0ef9a52a3dca9a22d5144505a9e7c68")
HBM_RAW_SMI="+------------------------------------------------------------------------------------------------+\n| npu-smi 25.2.0                   Version: 25.2.0                                               |\n+---------------------------+---------------+----------------------------------------------------+\n| NPU   Name                | Health        | Power(W)    Temp(C)           Hugepages-Usage(page)|\n| Chip                      | Bus-Id        | AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)        |\n+===========================+===============+====================================================+\n| 0     910B4               | OK            | 92.3        37                0    / 0             |\n| 0                         | 0000:C1:00.0  | 0           0    / 0          2870 / 32768         |\n+===========================+===============+====================================================+\n| 1     910B4               | OK            | 83.6        36                0    / 0             |\n| 0                         | 0000:C2:00.0  | 0           0    / 0          2872 / 32768         |\n+===========================+===============+====================================================+\n| 2     910B4               | OK            | 88.4        37                0    / 0             |\n| 0                         | 0000:81:00.0  | 0           0    / 0          2870 / 32768         |\n+===========================+===============+====================================================+\n| 3     910B4               | OK            | 86.7        39                0    / 0             |\n| 0                         | 0000:82:00.0  | 0           0    / 0          2868 / 32768         |\n+===========================+===============+====================================================+\n| 4     910B4               | OK            | 93.9        43                0    / 0             |\n| 0                         | 0000:01:00.0  | 0           0    / 0          2867 / 32768         |\n+===========================+===============+====================================================+\n| 5     910B4               | OK            | 96.3        41                0    / 0             |\n| 0                         | 0000:02:00.0  | 0           0    / 0          2866 / 32768         |\n+===========================+===============+====================================================+\n| 6     910B4               | OK            | 94.8        42                0    / 0             |\n| 0                         | 0000:41:00.0  | 0           0    / 0          2866 / 32768         |\n+===========================+===============+====================================================+\n| 7     910B4               | OK            | 85.7        43                0    / 0             |\n| 0                         | 0000:42:00.0  | 0           0    / 0          2861 / 32768         |\n+===========================+===============+====================================================+\n+---------------------------+---------------+----------------------------------------------------+\n| NPU     Chip              | Process id    | Process name             | Process memory(MB)      |\n+===========================+===============+====================================================+\n| No running processes found in NPU 0                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 1                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 2                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 3                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 4                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 5                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 6                                                            |\n+===========================+===============+====================================================+\n| No running processes found in NPU 7                                                            |\n+===========================+===============+====================================================+\n"
HBM_RAW_SMI_SHA="db267de32ce3b8d8f0c0eb028611011d254523e83bb380713b7487ae20db79cf"
class ActualHbmColumns(unittest.TestCase):
 @staticmethod
 def parse(text,card=4):
  # Actual production function/module, never an AST copy or stub controller.
  import host_run as h
  return h.actual_hbm(text,card)
 @staticmethod
 def metric(value):
  old="0           0    / 0          2867 / 32768"
  assert HBM_RAW_SMI.count(old)==1
  return HBM_RAW_SMI.replace(old,value,1)
 def reject(self,text,card=4):
  with self.assertRaises(ValueError):self.parse(text,card)
 def test_original_bytes_and_first_ratio_regression(self):
  import re
  self.assertEqual(hashlib.sha256(HBM_RAW_SMI.encode()).hexdigest(),HBM_RAW_SMI_SHA)
  line=next(l for l in HBM_RAW_SMI.splitlines() if "0000:01:00.0" in l)
  self.assertEqual(re.search(r"\b(\d+)\s*/\s*(\d+)\b",line.split("|")[3]).groups(),("0","0"))
  self.assertEqual(self.parse(HBM_RAW_SMI)["used_mib"],2867)
 def test_actual_all_four_owned_cards(self):
  for card,used in ((4,2867),(5,2866),(6,2866),(7,2861)):
   with self.subTest(card=card):
    self.assertEqual(self.parse(HBM_RAW_SMI,card),dict(physical=card,used_mib=used,total_mib=32768,
     reserve_mib=3072,full_actual_physical_hbm=True))
 def test_memory_ratio_cannot_be_substituted_for_HBM(self):
  self.assertEqual(self.parse(self.metric("99.5 30000 / 32768 2867 / 32768"))["used_mib"],2867)
 def test_exact_original_reserve_boundary_passes(self):
  self.assertEqual(self.parse(self.metric("0 0 / 0 29696 / 32768"))["used_mib"],29696)
 def test_one_MiB_below_original_reserve_rejected(self):
  self.reject(self.metric("0 0 / 0 29697 / 32768"))
 def test_original_physical_capacity_stays_exact(self):
  for total in ("0","32767","32769","65536"):
   with self.subTest(total=total):self.reject(self.metric("0 0 / 0 2867 / "+total))
 def test_header_missing_units_and_order_hard_rejected(self):
  old="AICore(%)   Memory-Usage(MB)  HBM-Usage(MB)"
  for new in ("AICore(%) HBM-Usage(MB) Memory-Usage(MB)","AICore(%) Memory-Usage(MB) HBM-Usage(GB)",
   "AICore(%) Memory-Usage(MB)","AICore(%) Memory-Usage(MB) HBM-Usage(MB) Extra"):
   with self.subTest(header=new):self.reject(HBM_RAW_SMI.replace(old,new,1))
 def test_duplicate_or_missing_header_hard_rejected(self):
  header=next(l for l in HBM_RAW_SMI.splitlines() if "| Chip " in l)
  self.reject(HBM_RAW_SMI.replace(header,header+"\n"+header,1))
  self.reject(HBM_RAW_SMI.replace(header,"",1))
 def test_unknown_metric_count_and_nonfinite_hard_rejected(self):
  for value in ("0 2867 / 32768","0 0 / 0 2867 / 32768 1 / 2","nan 0 / 0 2867 / 32768",
   "inf 0 / 0 2867 / 32768","101 0 / 0 2867 / 32768","-1 0 / 0 2867 / 32768",
   "0 1 / 0 2867 / 32768","0 0 / 0 -1 / 32768","0 0 / 0 2867.0 / 32768"):
   with self.subTest(value=value):self.reject(self.metric(value))
 def test_unique_card_and_health_hard_rejected(self):
  import re
  row=next(l for l in HBM_RAW_SMI.splitlines() if re.match(r"\|\s*4\s+910B4\s*\|",l))
  detail=next(l for l in HBM_RAW_SMI.splitlines() if "0000:01:00.0" in l)
  self.reject(HBM_RAW_SMI.replace(row,"",1))
  self.reject(HBM_RAW_SMI.replace(row,row+"\n"+detail+"\n"+row,1))
  self.reject(HBM_RAW_SMI.replace(row,row.replace("OK","Warning"),1))
 def test_chip_bus_and_pipe_schema_hard_rejected(self):
  detail=next(l for l in HBM_RAW_SMI.splitlines() if "0000:01:00.0" in l)
  self.reject(HBM_RAW_SMI.replace(detail,detail.replace("| 0 ","| 1 ",1),1))
  self.reject(HBM_RAW_SMI.replace("0000:01:00.0","unknown",1))
  self.reject(HBM_RAW_SMI.replace(detail,detail+" |",1))
  self.reject(HBM_RAW_SMI.replace(detail,"",1))
 def test_owned_cards_and_bool_identity_not_expanded(self):
  for card in (0,1,2,3,8,True,"4"):
   with self.subTest(card=card):self.reject(HBM_RAW_SMI,card)

if __name__=="__main__":unittest.main()
