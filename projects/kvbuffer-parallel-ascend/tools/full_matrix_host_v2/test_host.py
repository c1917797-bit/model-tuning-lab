"""Pure stdlib fixtures only; no subprocess, Docker, Torch or NPU execution."""
import ast,copy,hashlib,io,json,types,unittest
from contextlib import redirect_stdout,redirect_stderr
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
import host as h
class MemoryPath:
    def __init__(self,s):self.s=str(s)
    def __truediv__(self,s):return MemoryPath(self.s+"/"+str(s))
    def __str__(self):return self.s
    def open(self,mode):assert mode=="x";return io.StringIO()
class HostTests(unittest.TestCase):
    def own(self):return {str(h.HERE/"host.py"):"a"*64}
    def inspect(self,arm):
        cfg=h.ARMS[arm]
        return {"Id":"b"*64,"Name":"/"+cfg["name"],"Image":h.IMAGE,
          "Config":{"Labels":{"model-tuning-lab.owner":h.OWNER,"model-tuning-lab.joint-sha256":"c"*64,
                  "model-tuning-lab.arm":arm,"model-tuning-lab.run":cfg["name"],
                  "model-tuning-lab.producer-sha256":"a"*64}},
          "HostConfig":{"Privileged":False,"Memory":h.MEM,"MemorySwap":h.MEM,"NanoCpus":10**9,
              "NetworkMode":"none","DeviceRequests":[],"DeviceCgroupRules":[],"PidsLimit":512,
              "CapDrop":["ALL"],"SecurityOpt":["no-new-privileges"],
              "Devices":[{"PathOnHost":a,"PathInContainer":b,"CgroupPermissions":"rwm"}
                          for a,b in h.expected_devices(arm).items()]},
          "Mounts":[{"Destination":d,"Source":s,"RW":rw,"Type":"bind"}
                     for d,(s,rw) in h.expected_mounts(arm).items()]}
    def check_inspect(self,x,arm):return h.validate_inspect(x,"b"*64,arm,"c"*64,self.own())
    def test_actual64_and_three_artifact_refs_only_read(self):
        c,r,m,s=h.legacy().source()
        self.assertEqual(len(s),64);self.assertEqual(r,h.SOURCE_REF);self.assertEqual(h.legacy().REFS,h.REFS)
        c.artifacts(h.REFS,m)
    def test_default_off_no_command_and_no_output(self):
        with patch.object(h,"sources",side_effect=AssertionError("unexpected IO")),patch.object(
                 h,"run",side_effect=AssertionError("unexpected command")),redirect_stdout(io.StringIO()) as f:
            h.main([])
        value=json.loads(f.getvalue());self.assertFalse(value["default_enabled"]);self.assertFalse(value["npu_executed"])
    def test_cli_modes_and_unknown_arm_rejected(self):
        for argv in (["--prepare","--execute"],["--execute","--arm","b2"]):
            with self.subTest(argv=argv),redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):h.main(argv)
    def test_joint_sum_not_one_arm_cap(self):
        x=h.resource_floor(24*1024**3,4,18*1024**3)
        self.assertEqual(x["ordinary_ram_floor"],24*1024**3)
        self.assertEqual(x["full_model_floor_unchanged"],72*1024**3)
    def test_joint_short_ram_rejected(self):
        with self.assertRaises(ValueError):h.resource_floor(24*1024**3-1,4,18*1024**3)
    def test_joint_short_cpu_rejected(self):
        with self.assertRaises(ValueError):h.resource_floor(24*1024**3,3,18*1024**3)
    def test_joint_short_disk_rejected(self):
        with self.assertRaises(ValueError):h.resource_floor(24*1024**3,4,18*1024**3-1)
    def test_start_ticks_real_proc_field22(self):
        self.assertEqual(h.start_ticks("123 (x) complicated ) S "+" ".join(str(i) for i in range(4,40))),22)
        with self.assertRaises(ValueError):h.start_ticks("1 (short) S 0")
    def test_b1_physical5_exact_mapping(self):self.check_inspect(self.inspect("b1"),"b1")
    def test_b16_physical6_exact_mapping(self):self.check_inspect(self.inspect("b16"),"b16")
    def test_inspect_raw_original_list_not_command_wrapper(self):
        x=self.inspect("b1");raw=json.dumps([x],indent=1)+"\n";stored=[]
        def write_raw(path,data):
            stored.append(data);return {"path":str(path),"sha256":hashlib.sha256(data).hexdigest()}
        with patch.object(h,"capture",return_value=({"stdout":raw},{"path":"/command","sha256":"d"*64})),patch.object(h,"write_raw",write_raw):
            _,ref=h.inspected(MemoryPath("memory"),"b"*64,"b1","c"*64,self.own())
        self.assertEqual(stored,[raw.encode()]);self.assertIs(type(json.loads(stored[0])),list)
        self.assertNotEqual(ref["path"],"/command")
    def test_actual_consumer_flags_real_runner_suffix(self):
        p=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/kvbuffer-native-order-followup-v2-reviewed-draft-20261007.patch")
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),"c680bb8836e705fdef53d7430a26ece14092db2740843b094f888578ea9305bf")
        section=next(x for x in p.read_text().split("*** Add File: ")[1:] if x.splitlines()[0].endswith("/consumer.py"))
        source="\n".join(x[1:] for x in section.splitlines()[1:] if x.startswith("+"))+"\n"
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),"a264001bbd2f73ee9fdd7a0f0552835d77d02f3150f68ec3df9572e4ea2a8b2b")
        node=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=="flags")
        env={"b":types.SimpleNamespace(require=h.require)}
        exec(compile(ast.Module(body=[node],type_ignores=[]),"<actual-frozen-consumer-flags>","exec"),env)
        args=["--execute","--batch","16","--physical-device","6","--identity","/identity",
              "--output-dir","/kvbuffer-results/gate","--source-manifest",h.SOURCE_REF["path"],
              "--source-manifest-sha256",h.SOURCE_REF["sha256"]]
        for key,flag in (("library","library"),("build","build-receipt"),("meta","meta-receipt")):
            args+=["--"+flag,h.REFS[key]["path"],"--"+flag+"-sha256",h.REFS[key]["sha256"]]
        value=env["flags"](args);self.assertEqual(value["--batch"],"16");self.assertEqual(value["--physical-device"],"6")
        self.assertEqual(value["--output-dir"],"/kvbuffer-results/gate");self.assertEqual(value["--library-sha256"],h.REFS["library"]["sha256"])
        with self.assertRaises(ValueError):env["flags"](args+["--batch","16"])
    def test_swapped_physical_not_inferred_from_logical0(self):
        x=self.inspect("b16");x["HostConfig"]["Devices"][0]["PathOnHost"]="/dev/davinci5"
        with self.assertRaises(ValueError):self.check_inspect(x,"b16")
    def test_extra_devices_or_mounts_rejected(self):
        for field in ("Devices","Mounts"):
            x=self.inspect("b1")
            if field=="Devices":x["HostConfig"][field].append(dict(PathOnHost="/dev/davinci0",PathInContainer="/dev/davinci9",CgroupPermissions="rwm"))
            else:x[field].append(dict(Source="/tmp",Destination="/tmp",RW=True,Type="bind"))
            with self.subTest(field=field),self.assertRaises(ValueError):self.check_inspect(x,"b1")
    def test_owner_joint_name_image_caps_permissions_must_match(self):
        for change in ("owner","joint","name","image","memory","cpus","permissions","security"):
            x=self.inspect("b1")
            if change=="owner":x["Config"]["Labels"]["model-tuning-lab.owner"]="external"
            elif change=="joint":x["Config"]["Labels"]["model-tuning-lab.joint-sha256"]="d"*64
            elif change=="name":x["Name"]="/different"
            elif change=="image":x["Image"]="other"
            elif change=="memory":x["HostConfig"]["Memory"]=0
            elif change=="cpus":x["HostConfig"]["NanoCpus"]=0
            elif change=="permissions":x["HostConfig"]["Devices"][0]["CgroupPermissions"]="rw"
            else:x["HostConfig"]["SecurityOpt"]=[]
            with self.subTest(change=change),self.assertRaises(ValueError):self.check_inspect(x,"b1")
    def test_peer_actual_pid_physical6_allowed_not_any_compute(self):
        proof={"pid":9,"start_ticks":123,"cgroup":"0::/docker/"+("b"*64),"argv":[],"namespace_pids":[9,3]}
        with patch.object(h,"gate_process",return_value=proof):
            self.assertEqual(h.validate_pid(6,0,9,"b16","b"*64,"9 1 "+str(h.HERE/"host.py"))["pid"],9)
            for card,chip,top,cid in ((5,0,"9 1 "+str(h.HERE/"host.py"),"b"*64),
                                    (6,1,"9 1 "+str(h.HERE/"host.py"),"b"*64),
                                    (6,0,"9 1 external.py","b"*64),
                                    (6,0,"9 1 "+str(h.HERE/"host.py"),"d"*64)):
                with self.subTest(card=card,chip=chip,top=top,cid=cid),self.assertRaises(ValueError):
                    h.validate_pid(card,chip,9,"b16",cid,top)
    def joint_fixture(self):
        now=h.CUTOFF-timedelta(hours=2)
        r=h.SOURCE_REF;s={"source":"hash"};pr={"path":"/producer","sha256":"f"*64};own=self.own()
        rr={"path":"/resources","sha256":"e"*64}
        j={"schema":"kvbp.full-matrix-joint/v2","status":"prepared-not-executed","npu_executed":False,
          "source_manifest":r,"sources":s,"producer_manifest":pr,"producer_sources":own,"artifact_refs":h.REFS,
          "arms":h.ARMS,"image":h.IMAGE,"owner":h.OWNER,"output_root":str(h.OUTROOT),
          "phase_seconds":5400,"cleanup_seconds":90,"cutoff_utc":h.CUTOFF.isoformat(),
          "budgets":{"ram":24*1024**3,"cpu":4,"disk":18*1024**3},"prepared_utc":now.isoformat(),
          "resource_receipt":rr,"protected0_3":[]}
        receipt={"protected0_3":[],"smi":{"exit_code":0},"resources":{"memory":{"MemAvailable":24*1024**3},
          "engine":{"stdout":json.dumps({"NCPU":4})},"disk_free":18*1024**3}}
        return now,r,s,pr,own,j,receipt
    def test_joint_age600_exact_pass_601_future_reject(self):
        now,r,s,pr,own,j,rr=self.joint_fixture()
        with patch.object(h,"checked_ref",side_effect=lambda x:json.dumps(rr if x["path"]=="/resources" else j).encode()):
            h.load_joint(h.OUTROOT/"JOINT.json","d"*64,r,s,pr,own,now+timedelta(seconds=600))
            for t in (now+timedelta(seconds=601),now-timedelta(seconds=1)):
                with self.subTest(t=t),self.assertRaises(ValueError):h.load_joint(h.OUTROOT/"JOINT.json","d"*64,r,s,pr,own,t)
    def test_joint_changed_budget_source_phase_rejected(self):
        now,r,s,pr,own,j,rr=self.joint_fixture()
        for key,value in (("budgets",{"ram":16*1024**3,"cpu":2,"disk":13*1024**3}),("phase_seconds",9999),
                          ("sources",{}),("owner","external"),("npu_executed",True)):
            bad={**j,key:value}
            with patch.object(h,"checked_ref",side_effect=lambda x:json.dumps(rr if x["path"]=="/resources" else bad).encode()),self.subTest(key=key),self.assertRaises(ValueError):
                h.load_joint(h.OUTROOT/"JOINT.json","d"*64,r,s,pr,own,now)
    def test_cleanup90_shared_not_per_command(self):
        with patch.object(h,"_CLEANUP_DEADLINE",None),patch.object(h,"time",types.SimpleNamespace(monotonic=lambda:0)):
            self.assertEqual(h.cleanup_timeout(40),40)
            with patch.object(h,"time",types.SimpleNamespace(monotonic=lambda:89)):self.assertEqual(h.cleanup_timeout(30),1)
            with patch.object(h,"time",types.SimpleNamespace(monotonic=lambda:90)),self.assertRaises(ValueError):h.cleanup_timeout(30)
    def child_fixture(self,mode="running",inspect_error=False,write_error=False,wait_error=False):
        rows=[];commands=[]
        class Child:
            returncode=1 if mode=="nonzero" else None
            def poll(self):return self.returncode
            def wait(self,timeout):
                if wait_error:raise RuntimeError("wait-secondary")
                self.returncode=-15;return -15
        ch=Child()
        def inspected(*a,**k):
            if inspect_error:raise RuntimeError("owner-secondary")
        def run(argv,timeout):commands.append(argv);return {"argv":argv,"exit_code":0}
        def write(p,v):
            if write_error:raise OSError("evidence-secondary")
            rows.append(v);return {"path":str(p),"sha256":"0"*64}
        stack=[patch.object(h,"subprocess",types.SimpleNamespace(Popen=lambda *a,**k:ch)),
               patch.object(h,"time",types.SimpleNamespace(monotonic=lambda:0,sleep=lambda x:None)),
               patch.object(h,"inspected",inspected),patch.object(h,"run",run),
               patch.object(h,"write",write),patch.object(h,"sha",lambda p:"0"*64),
               patch.object(h,"cleanup_timeout",lambda cap:cap)]
        for p in stack:p.start()
        try:
            with redirect_stdout(io.StringIO()):
                try:h.observed_child(MemoryPath("memory"),"b"*64,"fixture",["never-executed"],"target",0,
                                     "b1",{},{"sha256":"c"*64},{},self.own())
                except BaseException as e:return e,rows,commands
            raise AssertionError("fixture unexpectedly passed")
        finally:
            for p in reversed(stack):p.stop()
    def test_primary_timeout_survives_owner_cleanup(self):
        e,rows,commands=self.child_fixture(inspect_error=True)
        self.assertIs(type(e),ValueError);self.assertIn("bounded child timeout",str(e))
        self.assertIsNone(rows[0]["exit_code"]);self.assertFalse(rows[0]["child_termination_observed"]);self.assertEqual(commands,[])
    def test_timeout_keeps_observed_fake_exit_not_success(self):
        e,rows,commands=self.child_fixture()
        self.assertIn("bounded child timeout",str(e));self.assertEqual(rows[0]["exit_code"],-15)
        self.assertEqual(commands,[[h.DOCKER,"stop","--time","15","b"*64]])
    def test_primary_timeout_survives_wait_and_evidence(self):
        e,rows,_=self.child_fixture(wait_error=True)
        self.assertIn("bounded child timeout",str(e));self.assertIsNone(rows[0]["exit_code"])
        e,rows,_=self.child_fixture(write_error=True)
        self.assertIn("bounded child timeout",str(e));self.assertEqual(rows,[])
    def test_nonzero_original_child_retained(self):
        e,rows,_=self.child_fixture(mode="nonzero")
        self.assertEqual(str(e),"real child failed; raw stdout/stderr retained");self.assertEqual(rows[0]["exit_code"],1)
if __name__=="__main__":unittest.main()
