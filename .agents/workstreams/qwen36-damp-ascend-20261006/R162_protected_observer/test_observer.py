"""Real /proc lifetime tests plus explicit negative fault-injection controls.
Synthetic SMI associations are observer software tests, never device evidence.
"""
import copy, importlib.util, os, subprocess, sys, time, unittest
from pathlib import Path
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("r162observer",P/"observer.py")
O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)

def missing(pid):
    return dict(pid=pid,observed_ns=0,reads={k:dict(status="missing",errno=2) for k in ("stat_before","stat_after","cgroup","cmdline")})
def live(pid,start=200):
    text=str(pid)+" (test) S "+" ".join(["0"]*18+[str(start)])
    return dict(pid=pid,observed_ns=0,reads=dict(stat_before=dict(status="ok",text=text),stat_after=dict(status="ok",text=text),
        cgroup=dict(status="ok",text="0::/external\n"),cmdline=dict(status="ok",hex=b"python\0".hex())))
class Controls(unittest.TestCase):
    def run_observer(self,seq,listed=(),owned=(),cids=()):
        logs=[];it=iter(seq)
        result=O.observe([(0,0,90001)],lambda pid:next(it),lambda:dict(exit_code=0,stdout="synthetic-smi"),lambda text:list(listed),
                         logs.append,owned_pids=owned,owned_cids=cids)
        return result,logs
    def test_live(self):
        rows,logs=self.run_observer([live(90001)])
        self.assertEqual(rows[0]["start_ticks"],200);self.assertEqual(logs,[])
    def test_departed_external_row_recorded(self):
        rows,logs=self.run_observer([missing(90001)]*3)
        self.assertEqual(rows,[]);self.assertFalse(logs[0]["events"][0]["initial_identity_known"])
        self.assertFalse(logs[0]["events"][0]["resource_authority"])
    def test_still_smi_fail(self):
        with self.assertRaises(O.ObservationError):self.run_observer([missing(90001)]*2,[(0,0,90001)])
    def test_reused_after_smi_fail(self):
        with self.assertRaises(O.ObservationError):self.run_observer([missing(90001),missing(90001),live(90001,400)])
    def test_live_partial_fail(self):
        a=live(90001);a["reads"]["cmdline"]=dict(status="missing",errno=2)
        with self.assertRaises(O.ObservationError):self.run_observer([a,live(90001)])
    def test_permission_fail(self):
        a=live(90001);a["reads"]["cgroup"]=dict(status="error",errno=13)
        with self.assertRaises(O.ObservationError):self.run_observer([a])
    def test_changed_identity_fail(self):
        a=live(90001);a["reads"]["stat_after"]=live(90001,300)["reads"]["stat_after"]
        with self.assertRaises(O.ObservationError):self.run_observer([a])
    def test_own_pid_fail(self):
        with self.assertRaises(O.ObservationError):self.run_observer([live(90001)],owned=(90001,))
    def test_own_cid_fail(self):
        with self.assertRaises(O.ObservationError):self.run_observer([live(90001)],cids=("external",))
    def test_out_of_scope_fail(self):
        with self.assertRaises(O.ObservationError):O.observe([(4,0,90001)],None,None,None,None)
    @unittest.skipUnless(sys.platform.startswith("linux"),"requires real Linux proc")
    def test_real_short_lived_departures_and_live_unreadable(self):
        seen=set()
        for attempt in range(16):
            p=subprocess.Popen([sys.executable,"-B","-c","import sys;sys.stdout.write('ready\\n');sys.stdout.flush();sys.stdin.readline()"],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertEqual(p.stdout.readline(),"ready\n")
                before=O.snapshot(p.pid);self.assertEqual(len(O.frames(before)),2)
                key=(p.pid,O.frames(before)[0]["start_ticks"]);self.assertNotIn(key,seen);seen.add(key)
                # Actual live PID with an explicit unreadability injection must reject.
                denied=copy.deepcopy(before);denied["reads"]["cmdline"]=dict(status="error",errno=13)
                with self.assertRaises(O.ObservationError):
                    O.observe([(0,0,p.pid)],lambda _:denied,None,None,lambda _:None)
                p.stdin.write("\n");p.stdin.flush();p.communicate(timeout=3)
                self.assertEqual(p.returncode,0)
                logs=[]
                rows=O.observe([(0,0,p.pid)],O.snapshot,lambda:dict(exit_code=0,stdout="synthetic absent SMI"),
                               lambda _:[],logs.append)
                self.assertEqual(rows,[]);self.assertEqual(len(logs[0]["events"]),1)
                self.assertFalse(Path("/proc",str(p.pid)).exists())
            finally:
                if p.poll() is None:p.terminate();p.communicate(timeout=3)
if __name__=="__main__":unittest.main(verbosity=2)

