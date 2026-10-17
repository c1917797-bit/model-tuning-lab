"""No Docker/NPU calls: exercise the controller finally path with mocked boundaries."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import formal_quality_r23_tp4 as controller

class InterruptedControllerTests(unittest.TestCase):
    def exercise(self,duplicate=False):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);model=base/"model";model.mkdir();(model/"config.json").write_text("{}")
            raw=base/"new-raw"
            cid="b"*64
            devices=[{"PathOnHost":"/dev/davinci"+str(i)} for i in range(4)]
            meta={"Id":cid,"Image":"image","Config":{"Labels":{"model-tuning-lab.task":controller.TASK}},
                  "HostConfig":{"Devices":devices},"State":{"Running":True,"Pid":1}}
            snap={"processes":[],"foreign":[],"owners":[]}
            def command(args,timeout=30):
                if args[:3]==["docker","image","inspect"]:return json.dumps([{"Config":{"Env":[]}}])
                if args[:3]==["docker","run","-d"]:return cid
                if args[:2]==["git","rev-parse"]:return "test"
                return ""
            def workload(spec,**kw):
                row=dict(event="quality-scored-response",scored=True,index=0,repetition=1,
                         sample_id="s",segment_sha256="a"*64,ok=True,request_id="req",
                         response_text="answer",finish_reason="length",completion_tokens=1024,correct=False)
                kw["record"](row)
                if duplicate:kw["record"](row)
                raise TimeoutError("frozen test interruption")
            class NoThread:
                def __init__(self,*a,**kw):pass
                def start(self):pass
                def join(self,timeout=None):pass
            contract=dict(absolute_stop_utc="2099-01-01T00:00:00Z",image="image",model=str(model),
                port=8233,raw_root=str(raw),model_config_sha256=hashlib.sha256(b"{}").hexdigest(),
                formal_quality=True,quality_workload={"inputs":{},"catalog":{"path":str(base/"catalog.json")}},hccl_ports=[26300,26300],
                container_name="mock-only",cpu_set="0",startup_timeout_seconds=1)
            with patch.object(controller,"command",side_effect=command),patch.object(controller,"snapshot",return_value=snap),\
                 patch.object(controller,"port_free"),patch.object(controller,"inspect",return_value=meta),\
                 patch.object(controller,"request",return_value=200),patch.object(controller.threading,"Thread",NoThread),\
                 patch.object(controller.subprocess,"run"),\
                 patch("independent_quality_workload.read_bound",return_value={"requests":[]}),\
                 patch("independent_quality_workload.run_quality_workload",side_effect=workload):
                with self.assertRaises(SystemExit) as stop:controller.run_contract(contract)
            self.assertEqual(stop.exception.code,1)
            result=json.loads((raw/"result.json").read_text())
            self.assertFalse(result["valid"]);self.assertEqual(result["error"],{"type":"TimeoutError","message":"frozen test interruption"})
            rows=json.loads((raw/"responses.json").read_text())
            self.assertFalse((raw/"quality-unit.json").exists())
            self.assertEqual(result["responses"],len(rows))
            if duplicate:
                self.assertEqual(rows,[])
                self.assertIn("duplicate",result["release"]["partial_response_recovery_error"])
            else:
                self.assertEqual(len(rows),1);self.assertEqual(rows[0]["response_text"],"answer")
                self.assertFalse(rows[0]["correct"]);self.assertEqual(rows[0]["finish_reason"],"length")
    def test_interruption_retains_response_but_remains_failed(self):self.exercise()
    def test_recovery_rejects_corrupt_identity_but_preserves_failure(self):self.exercise(duplicate=True)

if __name__=="__main__":unittest.main()
