"""Pure call-count/semantic closure regressions, no Docker/Torch/NPU."""
import collections,hashlib,importlib.util,json
from pathlib import Path
import unittest
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('coverage_v2',P/'coverage_v2.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
SOURCE=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole2k_runtime_complete_prepare_v3/prepared-source-short8-qualifier/SOURCE_BOUND.json')
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
class Counter:
    """Counting fixture only: actual full-SHA invocation is a separate check."""
    def __init__(self):self.calls=collections.Counter()
    def checked(self,r):self.calls[r['path']]+=1;return Path(r['path'])
    def obj(self,r):return json.loads(self.checked(r).read_bytes())
class Tests(unittest.TestCase):
    def test_entire_original_inverse(self):
        self.assertEqual(M.inverse(),Path(M.ORIGINAL_REF['path']).read_bytes())
    def test_actual_semantic_increment_exact17_and_checked_once(self):
        c=Counter();sr=ref(SOURCE);old=M._required_original(c,sr)
        baseline=sum(c.calls.values());c=Counter();new=M.required(c,sr)
        prior={r['path']:r for r in old};added={r['path']:r for r in new if r['path']not in prior}
        self.assertEqual(added,{r['path']:r for r in M.AUDIT17})
        self.assertTrue(all(n==1 for n in c.calls.values()))
        self.assertEqual(sum(c.calls.values()),len(new))
        self.assertGreater(baseline,len(old))
        print(json.dumps(dict(old_checked_calls=baseline,old_unique=len(old),
                              new_checked_calls=sum(c.calls.values()),new_unique=len(new))))
    def test_readset_dedup_checked_once(self):
        c=Counter();r=ref(SOURCE);M.readset_coverage(c,[r],[r,r,r])
        self.assertEqual(c.calls[r['path']],1)
    def test_conflict_before_readset_hash(self):
        c=Counter();r=ref(SOURCE);bad=dict(r,sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'conflicting'):
            M.readset_coverage(c,[r],[r,bad])
        self.assertFalse(c.calls)
        call=M._Invocation(c,[r]);call.obj(r)
        with self.assertRaisesRegex(ValueError,'conflicting'):
            call.obj(bad)
        self.assertEqual(c.calls[r['path']],1)
    def test_actual17_missing_readset_and_mount_refused(self):
        c=Counter();sr=ref(SOURCE);old=M._required_original(c,sr);new=M.required(c,sr)
        with self.assertRaisesRegex(ValueError,'missing independently'):
            M.readset_coverage(c,new,old)
        mounts={r['path']:(r['path'],False)for r in old}
        with self.assertRaisesRegex(ValueError,'missing exact RO'):
            M.mount_coverage(c,new,mounts,SOURCE.parent)
        for r in M.AUDIT17:mounts[r['path']]=(r['path'],False)
        self.assertEqual(M.mount_coverage(c,new,mounts,SOURCE.parent)['required'],len(new))
    def test_helper_list_drift_refused(self):
        old=M.Q_HELPERS
        try:
            M.Q_HELPERS={k:v for k,v in old.items()if k!='qualification_smoke_join.py'}
            with self.assertRaisesRegex(ValueError,'complete HELPERS'):
                M.required(Counter(),ref(SOURCE))
        finally:M.Q_HELPERS=old
    def test_no_broad_mount_exemption(self):
        c=Counter();r=M.AUDIT17[0]
        with self.assertRaisesRegex(ValueError,'missing exact RO'):
            M.mount_coverage(c,[r],{'/opt':('/opt',False)},SOURCE.parent)
    def test_audit_original_seventeen_pinned(self):
        b=Path(M.AUDIT_EVIDENCE_REF['path']).read_bytes()
        self.assertEqual(len(b),M.AUDIT_EVIDENCE_REF['bytes'])
        self.assertEqual(hashlib.sha256(b).hexdigest(),M.AUDIT_EVIDENCE_REF['sha256'])
        v=json.loads(b)['actualAudit']['structuredContent']['operation']['result']['record']
        rows=[json.loads(x)for x in v['stdout'].splitlines()if x][1]
        self.assertTrue(rows['actual_validation_succeeded'])
        self.assertEqual(rows['opened_unique'],5961)
        self.assertEqual([{k:z for k,z in x.items()if k!='reads'}for x in rows['uncovered']],M.AUDIT17)
if __name__=='__main__':unittest.main()
