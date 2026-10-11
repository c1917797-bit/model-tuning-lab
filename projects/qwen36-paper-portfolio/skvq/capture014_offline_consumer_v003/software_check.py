"""Actual full small-metadata/entry aggregate; not full raw/NPU/calibration."""
import argparse,hashlib,json,sys,time,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import offline_contract as D
def run(a):
    before=D.ref(HERE/'SOURCE_MANIFEST.json');D.need(before['sha256']==a.source_manifest_sha256,'one new full manifest SHA')
    manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_bytes())
    installed=a.mirror_root is None
    if installed:D.source(a.source_manifest_sha256)
    else:
        D.need(a.capture_source and a.native_source and a.linear_source,'explicit Windows readonly review mirrors')
        for r in manifest['files']:
            p=HERE/Path(r['path']).name
            raw=p.read_bytes();D.need(len(raw)==r['bytes']and hashlib.sha256(raw).hexdigest()==r['sha256'],'all current own exact bytes')
            compile(raw,str(p),'exec')
    import test_identity as I
    I.prepare(a)
    import test_entry as E
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(I.ActualIdentity),
      unittest.defaultTestLoader.loadTestsFromTestCase(E.Entry)])
    start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(suite)
    D.need(result.wasSuccessful()and result.testsRun==31,'entire actual20+11 aggregate, not partial PASS')
    D.need(D.ref(HERE/'SOURCE_MANIFEST.json')==before,'immutable current source manifest through actual software')
    value=dict(schema='skvq.capture014.offline.software/v1',status='SOURCE_SMALL_METADATA_SOFTWARE_ONLY',
      source_manifest_sha256=before['sha256'],tests=31,actual_all4_identity_counterexample_used=True,
      full_installed_closure_checked=installed,local_readonly_mirror_transport_used=not installed,
      actual_all256_raw_consumed=False,original_failed_whole_preserved=True,
      elapsed_seconds=time.monotonic()-start,no_Torch=True,no_NPU=True,model_ready=False,native_ready=False)
    if a.output:D.publish(a.output,value)
    print(json.dumps(value,sort_keys=True));return 0
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-manifest-sha256')
    p.add_argument('--output');p.add_argument('--mirror-root',type=Path)
    p.add_argument('--capture-source',type=Path,default=Path(D.CAPTURE['path']).parent)
    p.add_argument('--native-source',type=Path);p.add_argument('--linear-source',type=Path);a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,model_ready=False,no_NPU=True)));return
    sys.exit(run(a))
if __name__=='__main__':main()
