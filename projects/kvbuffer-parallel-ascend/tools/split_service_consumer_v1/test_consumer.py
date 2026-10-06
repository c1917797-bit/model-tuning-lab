"""Synthetic producer-shaped regressions only. No Torch, Docker, NPU, or launch."""
import ast
import copy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
import consumer as c
import launch as l

BASE = Path(__file__).resolve().parent

class FakeDispatch:
    PYTHON = "/usr/local/python3.12.13/bin/python3"
    RUNNER = str(c.PROJECT/"tools/split_gate_v1/run.py")
    CARDS = {1:5,16:6}

class ProcessParser:
    @staticmethod
    def parse_processes(raw):
        # Producer-shaped stand-in for the separately source-pinned real parser.
        return c.clean(raw)

def proc_fixture(batch=1):
    cid = "a"*64
    pid = 777
    protected = {str(n):[] for n in range(4)}
    p = dict(pid=pid,start_ticks=100,cgroup="0::/docker/"+cid,
             namespace_pids=[pid,23],observed_role="actual_gate_python",
             argv=[FakeDispatch.PYTHON,"-B",FakeDispatch.RUNNER,"--batch",str(batch),
                   "--physical-device",str(FakeDispatch.CARDS[batch]),"--identity",
                   "/kvbuffer-launch/identity.json","--output-dir","/kvbuffer-results/gate"])
    # parse_processes returns int keys in the actual parser.
    rows = {n:[] for n in range(8)}
    rows[FakeDispatch.CARDS[batch]]=[dict(pid=pid,name="python",memory_mib=128)]
    class Parser:
        @staticmethod
        def parse_processes(raw):
            return rows
    observed = dict(process=p,physical_card=FakeDispatch.CARDS[batch],canary_same_process=False,npu_smi="SYNTHETIC")
    waiting = dict(pid=pid,start_ticks=100,cgroup=p["cgroup"],observed_role="prelaunch_wait_bash_not_native")
    return cid,observed,waiting,protected,Parser,rows

class Contracts(unittest.TestCase):
    def test_default_off(self):
        with self.assertRaisesRegex(ValueError,"default OFF"):
            c.validate({}, {}, enabled=False)

    def test_real_gate_role_pid_card_and_argv(self):
        cid,o,w,p,h,rows=proc_fixture()
        result=c.exact_process(o,w,cid,1,FakeDispatch,h,p)
        self.assertEqual(result["host_pid"],777)
        for change in ("role","pid","start","namespace","cgroup","argv","card","canary","foreign"):
            oo,ww=copy.deepcopy(o),copy.deepcopy(w)
            if change=="role":oo["process"]["observed_role"]="prelaunch_wait_bash_not_native"
            if change=="pid":oo["process"]["pid"]=778
            if change=="start":oo["process"]["start_ticks"]=101
            if change=="namespace":oo["process"]["namespace_pids"]=[23]
            if change=="cgroup":oo["process"]["cgroup"]="0::/docker/"+cid+"0"
            if change=="argv":oo["process"]["argv"][3]="--fake-batch"
            if change=="card":oo["physical_card"]=4
            if change=="canary":oo["canary_same_process"]=True
            rr=copy.deepcopy(rows)
            if change=="foreign":rr[5].append(dict(pid=888,name="external",memory_mib=128))
            parser=SimpleNamespace(parse_processes=lambda raw, rr=rr:rr)
            with self.subTest(change=change),self.assertRaises(ValueError):
                c.exact_process(oo,ww,cid,1,FakeDispatch,parser,p)

    def test_protected_raw_pid_change_rejected(self):
        cid,o,w,p,h,rows=proc_fixture(16)
        rows[0]=[dict(pid=9,name="external",memory_mib=1)]
        with self.assertRaisesRegex(ValueError,"protected"):
            c.exact_process(o,w,cid,16,FakeDispatch,h,p)

    def test_command_receipts_bind_original_streams(self):
        files={}
        audit=Path("/synthetic/software-only/b1/run-arm")
        def put(path,value):
            data=value if isinstance(value,bytes) else c.canonical(value)+b"\n"
            files[str(path)]=data
            return dict(path=str(path),sha256=c.digest(data))
        out=put(audit/"0001-stopped-inspect.stdout",b"[]\n")
        err=put(audit/"0001-stopped-inspect.stderr",b"")
        path=audit/"0001-stopped-inspect.receipt.json"
        row=dict(argv=["/usr/bin/docker","inspect","a"*64],command="/usr/bin/docker",cwd=str(c.ROOT),
                 exit_code=0,error=None,automatic_retry=False,stdout=out["path"],stderr=err["path"],
                 stdout_sha256=out["sha256"],stderr_sha256=err["sha256"])
        put(path,row)
        listing=lambda p:[str(path)]
        read=lambda p:files[p]
        self.assertEqual(len(c.command_receipts(audit,"stopped-inspect",read,listing)),1)
        files[out["path"]]=b"changed"
        with self.assertRaisesRegex(ValueError,"byte drift"):
            c.command_receipts(audit,"stopped-inspect",read,listing)

    def test_runtime_samples_recompute_real_producer_budget(self):
        path=c.DISPATCH/"contracts.py"
        wanted="ceb8e84b43620c38189fed27577a0e008ca1f0f00f83c1b82360cf260ad4f081"
        d=c.module(path,wanted,"kvbp_test_frozen_resource_contract",c.read_file)
        files={};audit=Path("/synthetic/software-only/b1/run-arm")
        jobs={b:dict(container_id=("%x"%b)*64,job_root="/synthetic/software-only/b%d"%b,
                     output_root="/synthetic/software-only/b%d/results"%b,phase_timeout_seconds=1800)
              for b in (1,16)}
        groups={str(b):dict(container_id=jobs[b]["container_id"],running=True,memory_limit_bytes=8*c.GIB,
                memory_current_bytes=c.GIB,memory_peak_bytes=2*c.GIB,cpu_quota=1) for b in jobs}
        def put(path,value):
            data=c.canonical(value)+b"\n";files[str(path)]=data
            return dict(path=str(path),sha256=c.digest(data))
        refs=[]
        for i,elapsed in enumerate((1.,32.),1):
            x=dict(observed_ns=i*32000000000,meminfo="MemAvailable: %d kB\n"%(32*c.GIB//1024),
                   free_disk_bytes=20*c.GIB,remaining_seconds=1800,
                   own_elapsed_seconds=elapsed,own_remaining_seconds=1800-elapsed,
                   peer_remaining_upper_bound_seconds=1800,cgroups=groups,docker_info=dict(NCPU=7))
            ir=put(audit/("RUNTIME_BUDGET_INPUTS-%04d.json"%i),x)
            result=d.runtime_budget(32*c.GIB,20*c.GIB,1800,{int(k):v for k,v in groups.items()})
            result.update(inputs=ir,raw_checkpoint_observations=[])
            refs.append(put(audit/("RUNTIME_BUDGET-%04d.json"%i),result))
        reader=lambda p:files[p]
        self.assertEqual(c.budget_samples(refs,audit,jobs,dict(elapsed_seconds=40.),d,reader)["samples"],2)
        with self.assertRaises(ValueError):
            c.budget_samples(refs[::-1],audit,jobs,dict(elapsed_seconds=40.),d,reader)
        value=c.obj(refs[0],reader);value["ordinary_ram_reserve_bytes"]=0
        broken=put(Path(refs[0]["path"]),value)
        with self.assertRaisesRegex(ValueError,"recomputed"):
            c.budget_samples([broken,refs[1]],audit,jobs,dict(elapsed_seconds=40.),d,reader)

    def test_min_width_command_indices_above_9999(self):
        files={};audit=Path("/synthetic/software-only/b1/run-arm")
        stdout=audit/"10001-stopped-inspect.stdout";stderr=audit/"10001-stopped-inspect.stderr"
        files[str(stdout)]=b"[]";files[str(stderr)]=b""
        path=audit/"10001-stopped-inspect.receipt.json"
        row=dict(argv=["/usr/bin/docker","inspect","a"*64],command="/usr/bin/docker",cwd=str(c.ROOT),
                 exit_code=0,error=None,automatic_retry=False,stdout=str(stdout),stderr=str(stderr),
                 stdout_sha256=c.digest(b"[]"),stderr_sha256=c.digest(b""))
        files[str(path)]=c.canonical(row)
        self.assertEqual(len(c.command_receipts(audit,"stopped-inspect",lambda p:files[p],
                                                lambda p:[str(path)])),1)

    def test_grouped_plugin_inventory_not_six_general(self):
        source=(BASE/"launch.py").read_text()
        self.assertIn('group="vllm.general_plugins"',source)
        self.assertIn('group="vllm.platform_plugins"',source)
        self.assertIn('"ascend" in platform',source)

    def test_mount_requires_actual_same_absolute_ro(self):
        e=dict(Mounts=[dict(Type="bind",Source=str(c.ROOT),Destination=str(c.ROOT),RW=False)])
        l.mount_binding(e,str(c.PROJECT/"tools/service/contract.py"))
        with self.assertRaises(ValueError):
            l.mount_binding(e,"/cache/cch/unmounted/report.json")
        e["Mounts"][0]["Source"]="/other/repo"
        with self.assertRaisesRegex(ValueError,"alias"):
            l.mount_binding(e,str(c.ROOT))
        e["Mounts"][0]["Source"]=str(c.ROOT);e["Mounts"][0]["RW"]=True
        with self.assertRaisesRegex(ValueError,"RO/RW"):
            l.mount_binding(e,str(c.ROOT))

    def test_no_legacy_gate_or_shim_rewrite(self):
        tree=ast.parse((BASE/"launch.py").read_text())
        attrs={x.attr for x in ast.walk(tree) if isinstance(x,ast.Attribute)}
        self.assertNotIn("validate_native_gate",attrs)
        self.assertIn("validate_identity",attrs)
        self.assertIn("execve",attrs)
        self.assertNotIn("runpy", (BASE/"launch.py").read_text())
        self.assertNotIn("SOURCE_BEFORE.json",(BASE/"consumer.py").read_text())

    def test_original_server_argv_unchanged(self):
        new=ast.parse((BASE/"launch.py").read_text())
        old=ast.parse((c.PROJECT/"tools/service/launch.py").read_text())
        def assignment(tree):
            values=[x for x in ast.walk(tree) if isinstance(x,ast.Assign) and
                    any(isinstance(t,ast.Name) and t.id=="argv" for t in x.targets)]
            self.assertEqual(len(values),1)
            return values[0]
        a=SimpleNamespace(model=Path("/models/Qwen3.6-27B"),port=8231,arm="candidate")
        fixed_budget=lambda arm:dict(native_bytes=8053063680)
        result=[]
        for tree in (old,new):
            env=dict(a=a,sys=SimpleNamespace(executable=FakeDispatch.PYTHON),
                     budget=fixed_budget,old=SimpleNamespace(budget=fixed_budget))
            exec(compile(ast.fix_missing_locations(ast.Module(body=[assignment(tree)],type_ignores=[])),
                         "<synthetic-source-argv>","exec"),env)
            result.append(env["argv"])
        self.assertEqual(*result)

    def test_exec_primary_survives_secondary_failure(self):
        tree=ast.parse((BASE/"launch.py").read_text())
        bodies=[x for x in ast.walk(tree) if isinstance(x,ast.Try) and
                any(isinstance(y,ast.Call) and isinstance(y.func,ast.Attribute) and
                    y.func.attr=="execve" for y in ast.walk(ast.Module(body=x.body,type_ignores=[])))]
        self.assertEqual(len(bodies),1)
        primary=RuntimeError("original exec failed")
        def bad_exec(*args):raise primary
        def bad_write(*args):raise OSError("evidence write failed")
        env=dict(os=SimpleNamespace(execve=bad_exec),c=SimpleNamespace(write_new=bad_write),
                 sys=__import__("sys"),traceback=__import__("traceback"),
                 root=Path("/synthetic/unwritable"),argv=["image-python"],env={})
        with self.assertRaises(RuntimeError) as caught:
            exec(compile(ast.fix_missing_locations(ast.Module(body=[bodies[0]],type_ignores=[])),
                         "<actual-draft-except-body>","exec"),env)
        self.assertIs(caught.exception,primary)

if __name__=="__main__":
    unittest.main()
