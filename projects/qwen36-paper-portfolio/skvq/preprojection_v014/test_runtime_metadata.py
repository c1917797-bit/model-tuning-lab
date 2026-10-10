"""Actual metadata/lock/mount methods on real temporary bytes; no package or NPU authority."""
import ast,copy,hashlib,json,os,subprocess,sys,tempfile,time,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import current_contract as C
import input_dependency as D
import test_input_dependency as old
def manifest():return json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
def original():
    r=manifest()["predecessor_source"];p=Path(r["path"])
    if not p.exists():p=HERE.parent/"skvq-preprojection-current72h-20261010-013/SOURCE_MANIFEST.json"
    raw=p.read_bytes()
    C.require(len(raw)==r["bytes"] and hashlib.sha256(raw).hexdigest()==r["sha256"],"actual frozen013 original full manifest bytes")
    return json.loads(raw)
def write(p,v):
    p.write_bytes(json.dumps(v,sort_keys=True,separators=(",",":")).encode()+b"\n");return C.reference(p)
def fixture(root):
    value=old.fixture(root/"site")
    tree=dict(schema="skvq.isolated.pyarrow-files/v1",root=value["root"],files=[
        dict(relative=Path(r["path"]).relative_to(value["root"]).as_posix(),bytes=r["bytes"],sha256=r["sha256"])for r in value["files"]])
    lr=write(root/"INPUT_DEPENDENCY_LOCK.json",value);ir=write(root/"ACTUAL_TREE.json",tree)
    cr=write(root/"CLOCK.json",{"fixture_not_authority":True})
    m=dict(schema="skvq.current72h.preprojection.sources/v1",root=str(root),default_enabled=False,
        files=[lr],dependencies=[ir,cr],clock=cr,portfolio_cutoff_epoch=C.CUT,own_file_count=1,source_count=3,
        cpu_input_dependency_root=value["root"],cpu_input_dependency_lock_ref=lr,cpu_input_dependency_inventory_ref=ir,
        original_envelope_regression_ref=cr,native_format_patch_chain={})
    for key in("runtime_configuration_sources","multiprocessing_runtime_sources","rpc_runtime_sources",
        "native_tp_runtime_sources","native_qkv_runtime_sources","native_text_input_runtime_sources"):m[key]=[]
    sr=write(root/"SOURCE_MANIFEST.json",m);return m,value,sr
class Metadata(unittest.TestCase):
    def test01_actual013_missing_old_lock_metadata_reproduced_before_file_access(self):
        m=original();r=m["cpu_input_dependency_lock_ref"]
        self.assertTrue(r["path"].endswith("skvq-preprojection-current72h-v1-011/INPUT_DEPENDENCY_LOCK.json"))
        self.assertNotIn(r,m["files"]+m["dependencies"])
        own=next(x for x in m["files"]if x["path"].endswith("/INPUT_DEPENDENCY_LOCK.json"))
        self.assertEqual((r["bytes"],r["sha256"]),(own["bytes"],own["sha256"]))
        with self.assertRaisesRegex(ValueError,"current own input lock"):C.runtime_metadata_refs(m)
    def test02_current_all_accessed_metadata_exact_closure_and_lock_unchanged(self):
        m=manifest();refs=C.runtime_metadata_refs(m);r,inventory=C.input_dependency_refs(m)
        self.assertEqual(r["path"],m["root"]+"/INPUT_DEPENDENCY_LOCK.json")
        raw=(HERE/"INPUT_DEPENDENCY_LOCK.json").read_bytes();oldref=original()["cpu_input_dependency_lock_ref"]
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(oldref["bytes"],oldref["sha256"]))
        self.assertTrue(all(x in m["files"]+m["dependencies"]for x in refs))
        self.assertIn(inventory,m["dependencies"])
    def test03_each_accessed_metadata_missing_from_closure_rejected_but_history_not_authority(self):
        m=manifest()
        for ref in C.runtime_metadata_refs(m):
            bad=copy.deepcopy(m);bad["files"]=[r for r in bad["files"]if r!=ref];bad["dependencies"]=[r for r in bad["dependencies"]if r!=ref]
            with self.assertRaises(ValueError):C.runtime_metadata_refs(bad)
        bad=copy.deepcopy(m);bad["predecessor_source"]={"historical_only":"not accessed by production"}
        self.assertEqual(C.runtime_metadata_refs(bad),C.runtime_metadata_refs(m))
    def test04_old_alias_extra_key_wrong_bytes_hash_and_inventory_identity_refused(self):
        m=manifest()
        for key in("cpu_input_dependency_lock_ref","cpu_input_dependency_inventory_ref"):
            for kind in("extra","bytes","hash","path"):
                bad=copy.deepcopy(m)
                if kind=="extra":bad[key]["origin"]="not accepted"
                elif kind=="bytes":bad[key]["bytes"]=True
                elif kind=="hash":bad[key]["sha256"]="0"*64
                else:bad[key]["path"]=original()["cpu_input_dependency_lock_ref"]["path"]
                with self.assertRaises(ValueError):C.runtime_metadata_refs(bad)
    def test05_canonical_disk_manifest_actual_lock_and_complete_tree_replay(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);m,value,sr=fixture(root)
            with patch.object(C,"source",return_value=sr):
                self.assertEqual(D.lock(),(value,m["cpu_input_dependency_lock_ref"],sr))
                bad=copy.deepcopy(m);bad["cpu_input_dependency_lock_ref"]=original()["cpu_input_dependency_lock_ref"]
                sr=write(root/"SOURCE_MANIFEST.json",bad)
                with patch.object(C,"source",return_value=sr):
                    with self.assertRaisesRegex(ValueError,"current own input lock"):D.lock()
    def test06_actual_Control_mounts_covers_lock_inventory_and_exact_two_package_trees(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);m,value,sr=fixture(root);base=root/"base";base.mkdir()
            pins=[]
            for i in range(8):
                p=root/("donor"+str(i)+".py");p.write_bytes(b"exact_pin=True\n");r=C.reference(p);pins.append(dict(snapshot=r["path"],sha256=r["sha256"]))
            write(base/"source_pins.json",{"sources":pins})
            tree=ast.parse((HERE/"MAIN_HOST.py").read_bytes())
            ctrl=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=="Control")
            ns=dict(time=time,os=os,json=json,Path=Path,TOTAL=7200,DEADLINE=C.CUT,CLEANUP=180,
                HERE=root,BASE=base,ORDER=root/"order",PROJECTION=root/"projection",MODEL=root/"model",LINEAR=root/"linear",
                TRAIN=root/"train",TRAIN_GUEST="/original/train",C=C,D=D,require=C.require,reference=C.reference)
            exec(compile(ast.Module(body=[ctrl],type_ignores=[]),"actual-Control-source","exec"),ns)
            ctl=ns["Control"](root/"out")
            with patch.object(C,"source",return_value=sr):mounts=ctl.mounts(False)
            self.assertTrue(C.runtime_metadata_mounts(m,mounts))
            self.assertEqual(mounts[str(root)],(str(root),False))
            self.assertNotIn(value["root"],mounts)
            self.assertTrue(all(mounts[str(Path(value["root"])/p)]==(str(Path(value["root"])/p),False)for p in value["packages"]))
            for bad_kind in("absent","writable","alias"):
                bad=copy.deepcopy(mounts)
                if bad_kind=="absent":del bad[str(root)]
                elif bad_kind=="writable":bad[str(root)]=(str(root),True)
                else:bad[str(root)]=(str(root/"different"),False)
                with self.assertRaisesRegex(ValueError,"same-path RO mount"):C.runtime_metadata_mounts(m,bad)
    def test07_actual_entire_source_method_rejects_metadata_miss_not_only_count(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);m,value,sr=fixture(root)
            with patch.object(C,"HERE",root),patch.object(C,"ROOT",root),patch.object(C,"CLOCK",m["clock"]):
                self.assertEqual(C.source(sr["sha256"]),sr)
                with patch.object(C,"EXPECTED",sr["sha256"]):
                    self.assertEqual(D.lock(),(value,m["cpu_input_dependency_lock_ref"],sr))
                bad=copy.deepcopy(m);bad["cpu_input_dependency_lock_ref"]=original()["cpu_input_dependency_lock_ref"]
                wrong=write(root/"SOURCE_MANIFEST.json",bad)
                with self.assertRaisesRegex(ValueError,"current own input lock"):C.source(wrong["sha256"])
    def test08_fresh_isolated_child_actual_lock_and_aggregate_entry_order(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);m,value,sr=fixture(root)
            code="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import current_contract as C,input_dependency as D;C.source=lambda:C.reference(sys.argv[2]);v,r,s=D.lock();print(json.dumps({'lock_ref':r,'fixture_only':True,'native_ready':False}))"
            argv=[sys.executable,"-I","-B","-c",code,str(HERE),sr["path"]]
            result=subprocess.run(argv,capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr);got=json.loads(result.stdout)
            self.assertEqual(got["lock_ref"],m["cpu_input_dependency_lock_ref"]);self.assertIs(got["native_ready"],False)
            bad=copy.deepcopy(m);bad["dependencies"]=[]
            write(root/"SOURCE_MANIFEST.json",bad)
            failed=subprocess.run(argv,capture_output=True,text=True,timeout=10)
            self.assertNotEqual(failed.returncode,0);self.assertIn("actual input inventory",failed.stderr)
        software=(HERE/"software_check.py").read_text()
        self.assertLess(software.index("C.configure("),software.index("test_runtime_metadata"))
        self.assertIn('runtime_metadata.main([])',software)
        host=(HERE/"MAIN_HOST.py").read_text()
        self.assertLess(host.index("C.runtime_metadata_mounts(manifest,m)"),host.index('m[str(self.out)]=(str(self.out),True)'))
def main(argv=None):
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Metadata))
    return 0 if result.wasSuccessful()else 1
if __name__=="__main__":sys.exit(main())
