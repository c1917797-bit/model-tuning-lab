#!/usr/bin/env python3
"""Single authorized runtime release on chicaihong01. OFF unless --execute.
Only node0 1GiB pool; never service/config/mount/process mutation.
Receipts are new-only; rollback is one bounded restore attempt, not guaranteed.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import unittest

POOL = Path("/sys/devices/system/node/node0/hugepages/hugepages-1048576kB/nr_hugepages")
GLOBAL = Path("/sys/kernel/mm/hugepages/hugepages-1048576kB")
GIB_KIB = 1048576
EXPECTED = {"node0": 471, "node1": 485, "node2": 486, "node3": 474}
OVS_PID = 27118
SOCKET = "/var/run/openvswitch/ovs-vswitchd.27118.ctl"
OUTPUT_PARENT = Path("/cache/cch/qwen36-paper-preparation-20261007")

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def run(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=12)
    record = {"argv": argv, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    if p.returncode:
        raise RuntimeError(json.dumps(record))
    return record

def proc_identity(pid):
    p = Path("/proc") / str(pid)
    stat = (p / "stat").read_text()
    return {"pid": pid, "start_ticks": int(stat[stat.rindex(")") + 2:].split()[19]),
            "cgroup": (p / "cgroup").read_text(),
            "cmdline_sha256": hashlib.sha256((p / "cmdline").read_bytes()).hexdigest()}

def parse_mem():
    return {k: int(v.split()[0]) for k, v in
            (line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())}

def snapshot():
    s = {"utc": utc(), "memory_kib": parse_mem(), "nodes": {}, "global": {},
         "huge_consumers": [], "checks": {}}
    for p in sorted(Path("/sys/devices/system/node").glob("node*/hugepages/hugepages-1048576kB")):
        s["nodes"][p.parent.parent.name] = {
            n: int((p / n).read_text()) for n in ["nr_hugepages", "free_hugepages", "surplus_hugepages"]}
    s["global"] = {n: int((GLOBAL / n).read_text()) for n in
                   ["nr_hugepages", "free_hugepages", "resv_hugepages", "surplus_hugepages"]}
    for p in sorted(Path("/proc").iterdir()):
        if not p.name.isdigit():
            continue
        try:
            status = dict(line.split(":", 1) for line in (p / "status").read_text().splitlines() if ":" in line)
            size = int(status.get("HugetlbPages", "0 kB").split()[0])
            if size:
                c = proc_identity(int(p.name))
                c.update(name=status["Name"].strip(), hugetlb_kib=size,
                         maps=[line for line in (p / "numa_maps").read_text().splitlines()
                               if "kernelpagesize_kB=1048576" in line])
                s["huge_consumers"].append(c)
        except FileNotFoundError:
            continue
    for unit in ["ovs-vswitchd@1.service", "ovsdb-server.service"]:
        q = run(["/usr/bin/systemctl", "show", unit, "--property=MainPID",
                 "--property=ActiveState", "--property=SubState"])
        props = dict(line.split("=", 1) for line in q["stdout"].splitlines())
        if props["ActiveState"] != "active" or props["SubState"] != "running":
            raise RuntimeError("OVS unit not active/running: " + unit)
        props["identity"] = proc_identity(int(props["MainPID"]))
        s["checks"][unit] = props
    s["checks"]["version"] = run(["/usr/bin/ovs-appctl", "-t", SOCKET, "version"])["stdout"]
    s["checks"]["dpdk_raw"] = run(["/usr/bin/ovs-appctl", "-t", SOCKET, "dpif-dpdk/dump-dpdk-mem"])["stdout"]
    heaps = re.findall(r"----NUMA\[(\d+)\]----.*?heap_totalsz_bytes:\s*(\d+)",
                       s["checks"]["dpdk_raw"], re.S)
    s["checks"]["dpdk_heaps"] = [[int(n), int(b)] for n, b in heaps]
    s["checks"]["ovs_config"] = json.loads(run(["/usr/bin/ovs-vsctl", "--timeout=8", "--format=json",
                                              "--columns=other_config", "list", "Open_vSwitch"])["stdout"])
    interfaces = json.loads(run(["/usr/bin/ovs-vsctl", "--timeout=8", "--format=json",
                                 "--columns=name,type,admin_state,link_state,error", "list", "Interface"])["stdout"])
    s["checks"]["interfaces"] = sorted(interfaces["data"], key=lambda row: row[0])
    if any(row[2:4] != ["up", "up"] or row[4] != ["set", []] for row in interfaces["data"]):
        raise RuntimeError("OVS interface down/error")
    if {row[0] for row in interfaces["data"]} != {"bond1", "fst-ovs", "br-evs-bond1"}:
        raise RuntimeError("OVS interface identity drift")
    s["checks"]["default_route"] = run(["/usr/sbin/ip", "route", "show", "default"])["stdout"]
    if s["checks"]["default_route"].strip() != "default via 9.15.154.1 dev fst-mng":
        raise RuntimeError("management route drift")
    s["checks"]["gateway_ping"] = run(["/usr/bin/ping", "-n", "-c", "2", "-W", "2", "9.15.154.1"])
    paths = ["/proc/cmdline", "/etc/default/grub", "/usr/lib/systemd/system/ovs-vswitchd@.service",
             "/etc/sysconfig/openvswitch"]
    s["config_hashes"] = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
    return s

def guard(s, count=471):
    if set(s["nodes"]) != set(EXPECTED):
        raise ValueError("NUMA identity drift")
    if {n: d["nr_hugepages"] for n, d in s["nodes"].items()} != dict(EXPECTED, node0=count):
        raise ValueError("unexpected pool count")
    if any(d["surplus_hugepages"] for d in s["nodes"].values()):
        raise ValueError("surplus pages")
    if s["nodes"]["node0"]["free_hugepages"] != count:
        raise ValueError("node0 not wholly free")
    if s["global"]["resv_hugepages"] or s["global"]["surplus_hugepages"]:
        raise ValueError("reserved/surplus pages")
    if s["global"]["nr_hugepages"] != sum(d["nr_hugepages"] for d in s["nodes"].values()):
        raise ValueError("global/node count mismatch")
    if s["global"]["free_hugepages"] != sum(d["free_hugepages"] for d in s["nodes"].values()):
        raise ValueError("global/node free mismatch")
    if s["nodes"]["node3"]["free_hugepages"] != 450:
        raise ValueError("OVS used pages drift")
    c = s["huge_consumers"]
    if len(c) != 1 or c[0]["pid"] != OVS_PID or c[0]["name"] != "ovs-vswitchd" or c[0]["hugetlb_kib"] != 24 * GIB_KIB:
        raise ValueError("hugepage consumer drift")
    if len(c[0]["maps"]) != 24 or any("N3=1 " not in line for line in c[0]["maps"]):
        raise ValueError("OVS NUMA placement drift")
    if s["checks"]["ovs-vswitchd@1.service"]["identity"]["pid"] != OVS_PID:
        raise ValueError("OVS PID drift")
    if s["checks"]["dpdk_heaps"] != [[3, 24 * 1073741824]]:
        raise ValueError("DPDK capacity drift")

def stable(a, b):
    for key in ["huge_consumers", "config_hashes"]:
        if a[key] != b[key]:
            raise ValueError(key + " changed")
    for key in ["ovs-vswitchd@1.service", "ovsdb-server.service", "version", "interfaces",
                "default_route", "ovs_config", "dpdk_heaps"]:
        if a["checks"][key] != b["checks"][key]:
            raise ValueError("OVS/network identity changed: " + key)

def save(out, name, value):
    with (out / name).open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

def execute(out, pages):
    if not 1 <= pages <= 32:
        raise ValueError("authorized cap is 32 GiB")
    if out.parent.resolve() != OUTPUT_PARENT.resolve() or out.exists():
        raise ValueError("output must be a new direct child of the authorized artifact root")
    out.mkdir()
    receipt = {"schema": "hugepage.runtime-release32/v1", "started_utc": utc(),
               "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "target": str(POOL), "authorized_max_gib": 32, "requested_gib": pages,
               "permanent_config_changed": False, "service_stop_attempted": False,
               "write_attempted": False, "rollback": None}
    before = None
    try:
        before = snapshot()
        save(out, "before.json", before)
        guard(before)
        prewrite = snapshot()
        save(out, "prewrite.json", prewrite)
        guard(prewrite)
        stable(before, prewrite)
        if POOL.resolve() != POOL or int(POOL.read_text()) != 471:
            raise ValueError("exact sysfs path/count drift")
        save(out, "write-intent.json", {"old": 471, "new": 471-pages, "path": str(POOL), "utc": utc(),
              "rollback_target": 471, "rollback_guaranteed": False})
        receipt["write_attempted"] = True
        with POOL.open("w") as f:
            f.write(str(471-pages) + "\n")
        after = snapshot()
        save(out, "after.json", after)
        guard(after, 471-pages)
        stable(before, after)
        released = before["global"]["nr_hugepages"] - after["global"]["nr_hugepages"]
        if released != pages or before["memory_kib"]["Hugetlb"]-after["memory_kib"]["Hugetlb"] != pages * GIB_KIB:
            raise ValueError("actual release mismatch")
        receipt.update(status="completed", released_gib=released,
                       ordinary_available_before_gib=before["memory_kib"]["MemAvailable"]/GIB_KIB,
                       ordinary_available_after_gib=after["memory_kib"]["MemAvailable"]/GIB_KIB,
                       ovs_health_preserved=True, ovs_huge_gib_preserved=24,
                       node3_pool_preserved_gib=474)
        code = 0
    except BaseException as e:
        receipt.update(status="failed", primary_error=repr(e))
        if receipt["write_attempted"]:
            try:
                current = int(POOL.read_text())
                if current != 471-pages:
                    raise ValueError("unexpected current pool; do not overwrite external change")
                with POOL.open("w") as f:
                    f.write("471\n")
                restored = snapshot()
                save(out, "rollback.json", restored)
                guard(restored)
                stable(before, restored)
                receipt["rollback"] = {"attempted": True, "restored": True}
            except BaseException as re:
                receipt["rollback"] = {"attempted": True, "restored": False, "error": repr(re)}
        code = 1
    receipt["finished_utc"] = utc()
    save(out, "RESULT.json", receipt)
    print(json.dumps(receipt))
    return code

class Tests(unittest.TestCase):
    def base(self):
        return {"nodes": {n: {"nr_hugepages": k, "free_hugepages": k-(24 if n=="node3" else 0),
                              "surplus_hugepages": 0} for n,k in EXPECTED.items()},
                "global": {"nr_hugepages": 1916, "free_hugepages": 1892,
                           "resv_hugepages": 0, "surplus_hugepages": 0},
                "huge_consumers": [{"pid": OVS_PID, "name": "ovs-vswitchd", "hugetlb_kib": 24*GIB_KIB,
                                    "maps": ["x N3=1 kernelpagesize_kB=1048576"]*24}],
                "checks": {"ovs-vswitchd@1.service": {"identity": {"pid": OVS_PID}},
                           "dpdk_heaps": [[3,24*1073741824]]}}
    def test_approved(self):
        guard(self.base())
    def test_after(self):
        s=self.base()
        s["nodes"]["node0"]["nr_hugepages"]=439
        s["nodes"]["node0"]["free_hugepages"]=439
        s["global"]["nr_hugepages"]-=32
        s["global"]["free_hugepages"]-=32
        guard(s,439)
    def test_reserved(self):
        s=self.base();s["global"]["resv_hugepages"]=1
        with self.assertRaises(ValueError):guard(s)
    def test_used_target(self):
        s=self.base();s["nodes"]["node0"]["free_hugepages"]-=1
        with self.assertRaises(ValueError):guard(s)
    def test_foreign_consumer(self):
        s=self.base();s["huge_consumers"].append(dict(s["huge_consumers"][0],pid=999))
        with self.assertRaises(ValueError):guard(s)
    def test_ovs_node_changed(self):
        s=self.base();s["huge_consumers"][0]["maps"][0]="x N0=1 "
        with self.assertRaises(ValueError):guard(s)
    def test_surplus(self):
        s=self.base();s["nodes"]["node0"]["surplus_hugepages"]=1
        with self.assertRaises(ValueError):guard(s)
    def test_ovs_size_changed(self):
        s=self.base();s["huge_consumers"][0]["hugetlb_kib"]-=GIB_KIB
        with self.assertRaises(ValueError):guard(s)
    def test_node_counts_changed(self):
        s=self.base();s["nodes"]["node1"]["nr_hugepages"]-=1
        with self.assertRaises(ValueError):guard(s)
    def test_dpdk_changed(self):
        s=self.base();s["checks"]["dpdk_heaps"]=[[0,24*1073741824]]
        with self.assertRaises(ValueError):guard(s)

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--output-dir",type=Path)
    p.add_argument("--pages",type=int,default=32)
    a=p.parse_args()
    if a.self_test:
        if a.execute:
            p.error("tests cannot execute")
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        sys.exit(0 if result.wasSuccessful() else 1)
    if not a.execute:
        print(json.dumps({"status":"default-off","mutation_performed":False}))
        sys.exit(0)
    if not a.output_dir:
        p.error("--output-dir required")
    signal.signal(signal.SIGTERM,lambda signum,frame: (_ for _ in ()).throw(RuntimeError("SIGTERM")))
    sys.exit(execute(a.output_dir,a.pages))
