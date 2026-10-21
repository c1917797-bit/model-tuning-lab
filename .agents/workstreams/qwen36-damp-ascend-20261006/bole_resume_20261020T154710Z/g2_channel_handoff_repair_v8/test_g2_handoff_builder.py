"""Exact inherited source inverse and retained actual failure provenance."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_g2_v8_preparation_controls',P/'prepare_g2_handoff_v8.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)


def oldfiles():
    review=P.parent.parent/'g2_review_v7';stream=P.parent/'g2_long_output/test_g2_stream.py'
    if review.is_dir():
        m=json.loads((review/'source/SOURCE_BOUND.json').read_text());paths={n:review/'source'/n for n in B.CHANGED};paths['test_g2_stream.py']=stream
        for n,p in paths.items():
            data=p.read_bytes();assert(len(data),hashlib.sha256(data).hexdigest())==(m['files'][n]['bytes'],m['files'][n]['sha256'])
        return m,paths
    current=B.obj(B.ref(P/'SOURCE_BOUND.json'));m=B.obj(current['g2_metadata_handoff_v8']['failed_source']);return m,{n:B.checked(m['files'][n])for n in B.CHANGED}


class BuilderControls(unittest.TestCase):
 def test_all_exact_inverse_edits_and_15_original_negative_assertions_preserved(self):
    m,paths=oldfiles()
    for n,p in paths.items():self.assertEqual(B.inverse(n,(P/n).read_text()),p.read_text(),n)
    B.fixture_assertions(paths['test_g2_stream.py'].read_text(),(P/'test_g2_stream.py').read_text())
    owner=(P/'g2_stream_owner.py').read_bytes();self.assertEqual((len(owner),hashlib.sha256(owner).hexdigest()),(5917,'3d7d61e06e2de7e0680f4503530267bbb0cd87402b287d037cf89dd1562db8af'))
 def test_undeclared_source_or_test_assertion_edits_remain_rejected(self):
    m,paths=oldfiles();changed=(P/'test_g2_stream.py').read_text().replace("self.assertFalse(list(root.glob('ACK-*')))","self.assertTrue(list(root.glob('ACK-*')))")
    with self.assertRaises(ValueError):B.fixture_assertions(paths['test_g2_stream.py'].read_text(),changed)
    for n in B.CHANGED:
        bad=(P/n).read_text()+'\n# undeclared source delta\n';self.assertNotEqual(B.inverse(n,bad),paths[n].read_text())
 def test_new_preparer_audit_and_cold_entry_are_default_OFF_and_help_only(self):
    for n in('prepare_g2_handoff_v8.py','audit_source_v8.py','g2_handoff_cold.py'):
        for args in([],['--help']):
            q=subprocess.run([sys.executable,'-I','-B',str(P/n),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr)
            if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))


if __name__=='__main__':unittest.main()
