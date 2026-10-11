"""Real source byte diff, original pair predicates and complete file/terminal fixture chain.
The operation records below are explicit inert fixtures, never actual remote success.
"""
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
import source_pair as P
OLD=None;NEW=None;READER=None
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m;spec.loader.exec_module(m);return m
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=load(NEW/"screen_contract.py","_pair003_contract")
  cls.w=load(NEW/"screen_whole.py","_pair003_whole")
  cls.r=load(READER/"cost_owner_adapter.py","_pair003_dense_identity")
  P.c=cls.c
 def resolver(self,r):
  for ref,root in((P.DENSE,OLD),(P.CANDIDATE,NEW),(P.DENSE_READER,READER)):
   if r["path"].startswith(ref["path"].rsplit("/",1)[0]+"/"):return root/Path(r["path"]).name
  return Path(r["path"])
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
  self.index=0;self.d,self.k=self.row("dense"),self.row("candidate")
 def put(self,value):
  self.index+=1;p=self.root/(str(self.index)+".json")
  with p.open("x",encoding="utf8")as f:json.dump(value,f)
  return self.c.ref(p)
 def row(self,arm):
  argv=self.c.native_argv(8250,"kivi_firstdecode_bootstrap.FirstDecodeWorker")
  result=self.put(dict(cpu=dict(report=self.put(dict(native_argv=argv))),npu=dict(canary=self.put(dict(native_argv=argv)))))
  prereq=self.put(dict(consumed={"actual_fixture":"same"}))
  recipe=self.put(dict(cache_bytes=6*1024**3,screen_output_counts=[2,2,129],container_id=arm,
   firstdecode_prerequisite_ref=prereq))
  return dict(schema="kivi.b1-cost129-arm-consumed/v1",arm=arm,source=P.DENSE if arm=="dense"else P.CANDIDATE,
   actual_source_cleanup_resource_checked=True,model_ready=False,performance_accepted=False,
   full1024_numerically_verified=False,run_authority=False,original_result=result,
   original_terminal=self.put(dict(fixture=True)),prerequisite=prereq,recipe=recipe,
   stopped_inspect=dict(State=dict(FinishedAt="2026-10-11T01:00:00Z",StartedAt="2026-10-11T02:00:00Z")),
   same_actual_config=dict(actual_scalar_policy={"same":True}),
   metrics=dict(output_tokens_per_second=1.,wall_seconds=129.,mean_ttft_seconds=1.,mean_tpot_seconds=1.))
 def mutate_recipe(self,row,**values):
  v=self.c.read(row["recipe"]);v.update(values);row["recipe"]=self.put(v)
 def test01_actual_all_source_bytes_and_only_three_differences(self):
  proof=P.qualify(self.resolver);self.assertTrue(proof["mathematics_monitor_sync_capacity_budget_unchanged"])
  self.assertEqual(proof["changed_files"],["runtime_owner.py","screen_whole.py","software_check.py"])
 def test02_modified_original_bytes_fail(self):
  bad=self.root/"bad.py";bad.write_text("wrong")
  r=next(r for r in json.loads((OLD/"SOURCE_MANIFEST.json").read_bytes())["files"]if r["path"].endswith("/runtime_owner.py"))
  with self.assertRaisesRegex(ValueError,"exact source bytes"):
   P.qualify(lambda q:bad if q==r else self.resolver(q))
 def test03_actual_owner_source_literal_same_safety(self):
  def owner(p):
   nodes=ast.parse(p.read_bytes()).body
   return [ast.literal_eval(n.value)for n in nodes if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=="OWNER"for x in n.targets)]
  self.assertEqual(owner(NEW/"safety_host.py"),["kivi-b1-matched1024-v2"])
  wire=(NEW/"screen_whole.py").read_text()
  self.assertIn('OWNER="kivi-b1-matched1024-v2"',wire)
  self.assertNotIn('OWNER="kivi-b1-cost129-v2"',wire)
 def test04_complete_original_pair_checks_preserve_both_sources(self):
  with patch.dict(sys.modules,screen_whole=self.w):value=P.consume(self.d,self.k)
  self.assertEqual(value["dense_source"],P.DENSE);self.assertEqual(value["candidate_source"],P.CANDIDATE)
  self.assertFalse(value["performance_accepted"])
 def test05_same_source_forgery_rejected(self):
  self.k["source"]=P.DENSE
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def dense_module(self,row,name):
  local=self.resolver(row);wire=P.bytes_of(row,self.resolver)
  return load(local,name)
 def test21_complete_dense002_terminal_identity_file_chain(self):
  a,tr=self.terminal("dense",self.d);self.addCleanup(sys.modules.pop,"_cost003_dense_reader_identity",None)
  original=P.bytes_of
  with patch.object(P,"bytes_of",side_effect=lambda r,resolver=None:original(r,self.resolver if resolver is None else resolver)),patch.object(P,"module",side_effect=self.dense_module):
   self.assertEqual(P.arm_value("dense",a,self.w)["source"],P.DENSE)
 def test22_dense_wrong_adaptation_rejected(self):
  a,tr=self.terminal("dense",self.d);self.addCleanup(sys.modules.pop,"_cost003_dense_reader_identity",None)
  value=self.c.read(self.c.ref(a.dense));value["reader_adaptation"]["reader_source"]=P.CANDIDATE
  rr=self.put(value);a.dense=rr["path"];a.dense_sha256=rr["sha256"]
  rec=self.c.read(tr);rec["result"]["record"]["args"][-1]=rr["path"];rec["result"]["record"]["stdout"]=json.dumps(rr)
  tr=self.put(rec);a.dense_terminal=tr["path"];a.dense_terminal_sha256=tr["sha256"]
  original=P.bytes_of
  with patch.object(P,"bytes_of",side_effect=lambda r,resolver=None:original(r,self.resolver if resolver is None else resolver)),patch.object(P,"module",side_effect=self.dense_module),self.assertRaises(ValueError):
   P.arm_value("dense",a,self.w)
 def test23_real_main_arguments_complete_two_reader_publication(self):
  da,unused=self.terminal("dense",self.d);ka,unused=self.terminal("candidate",self.k)
  self.addCleanup(sys.modules.pop,"_cost003_dense_reader_identity",None)
  argv=["--execute","--source-manifest-sha256","fixture-reader"]
  for name,a in(("dense",da),("candidate",ka)):
   for suffix in("","_sha256","_terminal","_terminal_sha256","_operation","_peer"):
    argv+=["--"+name+suffix.replace("_","-"),getattr(a,name+suffix)]
  output=self.root/"PAIR.json";argv+=["--output",str(output)]
  original=P.bytes_of
  with patch.dict(sys.modules,screen_contract=self.c):
   transport=load(NEW/"transport.py","_pair003_transport")
  with patch.object(P,"source",return_value={"fixture":"reader"}),patch.object(P,"configure",return_value=self.w),\
   patch.object(P,"bytes_of",side_effect=lambda r,resolver=None:original(r,self.resolver if resolver is None else resolver)),\
   patch.object(P,"module",side_effect=self.dense_module),patch.dict(sys.modules,screen_whole=self.w,transport=transport):
   self.assertEqual(P.main(argv),0)
  result=json.loads(output.read_bytes())
  self.assertEqual(result["dense_source"],P.DENSE);self.assertEqual(result["candidate_source"],P.CANDIDATE)
  self.assertFalse(result["performance_accepted"])
 def test06_wrong_dense_version_rejected(self):
  self.d["source"]=P.CANDIDATE
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test07_short_or1024_protocol_rejected(self):
  for outputs in([2,2,128],[2,2,1024]):
   self.mutate_recipe(self.k,screen_output_counts=outputs)
   with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test08_budget_change_rejected(self):
  self.mutate_recipe(self.k,cache_bytes=10*1024**3)
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test09_different_numeric_predecessor_rejected(self):
  self.mutate_recipe(self.k,firstdecode_prerequisite_ref=self.put(dict(consumed={"other":True})))
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test10_overlap_lease_rejected(self):
  self.k["stopped_inspect"]["State"]["StartedAt"]="2026-10-11T00:00:00Z"
  with patch.dict(sys.modules,screen_whole=self.w),self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test11_engine_policy_drift_rejected(self):
  self.k["same_actual_config"]["actual_scalar_policy"]={"changed":True}
  with patch.dict(sys.modules,screen_whole=self.w),self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test12_CPU_N1_argv_drift_rejected(self):
  result=self.c.read(self.k["original_result"]);result["npu"]["canary"]=self.put(dict(native_argv=["bad"]))
  self.k["original_result"]=self.put(result)
  with patch.dict(sys.modules,screen_whole=self.w),self.assertRaises(ValueError):P.consume(self.d,self.k)
 def test13_scope_promotion_rejected(self):
  self.k["performance_accepted"]=True
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
 def terminal(self,name,value):
  mf=P.DENSE_READER if name=="dense"else P.CANDIDATE
  entry=str(Path(mf["path"]).parent/("arm.py"if name=="dense"else"screen_whole.py"))
  if name=="dense":value["reader_adaptation"]=self.r.identity(P.DENSE_READER)
  rr=self.put(value);args=self.put(dict(result=value["original_result"]["path"],terminal=value["original_terminal"]["path"]))
  cmd=["/usr/bin/python3","-I","-B",entry,"--execute","--source-manifest-sha256",mf["sha256"],
   "--arguments",args["path"],"--arguments-sha256",args["sha256"],"--output",rr["path"]]
  operation="exec-000000000000000"+("1"if name=="dense"else"2")
  record=dict(id=operation,state="completed",exitCode=0,cancelled=False,timedOut=False,error=None,
   stdout=json.dumps(rr)+"\n",stderr="",command=cmd[0],args=cmd[1:],cwd=None,durationMs=1)
  tr=self.put(dict(operationId=operation,targetPeerId="fixture-peer",routeDecision="peer_direct",result=dict(record=record)))
  a=types.SimpleNamespace(**{name:rr["path"],name+"_sha256":rr["sha256"],name+"_terminal":tr["path"],
   name+"_terminal_sha256":tr["sha256"],name+"_operation":operation,name+"_peer":"fixture-peer"})
  return a,tr
 def test14_actual_candidate_terminal_file_chain(self):
  a,tr=self.terminal("candidate",self.k)
  self.assertEqual(P.arm_value("candidate",a,self.w)["source"],P.CANDIDATE)
 def test15_old_candidate_reader_CLI_rejected(self):
  a,tr=self.terminal("candidate",self.k);v=self.c.read(tr);v["result"]["record"]["args"][2]=str(Path(P.DENSE_READER["path"]).parent/"arm.py")
  q=self.put(v);a.candidate_terminal=q["path"];a.candidate_terminal_sha256=q["sha256"]
  with self.assertRaises(ValueError):P.arm_value("candidate",a,self.w)
 def test16_failed_terminal_rejected(self):
  a,tr=self.terminal("candidate",self.k);v=self.c.read(tr);v["result"]["record"]["exitCode"]=1
  q=self.put(v);a.candidate_terminal=q["path"];a.candidate_terminal_sha256=q["sha256"]
  with self.assertRaises(ValueError):P.arm_value("candidate",a,self.w)
 def test17_forged_output_marker_rejected(self):
  a,tr=self.terminal("candidate",self.k);v=self.c.read(tr);v["result"]["record"]["stdout"]="{}"
  q=self.put(v);a.candidate_terminal=q["path"];a.candidate_terminal_sha256=q["sha256"]
  with self.assertRaises(ValueError):P.arm_value("candidate",a,self.w)
 def test18_original_pair_body_only_source_predicate_and_result_changed(self):
  old=(OLD/"pair.py").read_text();old=old[old.index("def consume("):old.index("def main(")]
  new=Path(P.__file__).read_text();new=new[new.index("def consume("):new.index("def arm_value(")]
  want=old.replace('and dense["source"]==candidate["source"]','and dense["source"]==DENSE and candidate["source"]==CANDIDATE').replace(
   '"same source actual dense then candidate"','"exact001 dense then protocol-repaired003 candidate"').replace(
   'schema="kivi.b1-cost129-pair/v1",source=dense["source"],protocol=c.PROTOCOL,',
   'schema="kivi.b1-cost129-dual-source-pair/v1",dense_source=dense["source"],candidate_source=candidate["source"],protocol=c.PROTOCOL,')
  self.assertEqual(new,want)
 def test19_real_defaultOFF_CLI(self):
  p=subprocess.run([sys.executable,"-I","-B",str(Path(P.__file__))],capture_output=True,text=True,timeout=15)
  self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),dict(enabled=False,NPU=False))
 def test20_tampered_original_file_rejected(self):
  q=self.k["original_result"]
  with Path(q["path"]).open("ab")as f:f.write(b" ")
  with self.assertRaises(ValueError):P.consume(self.d,self.k)
