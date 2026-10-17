"""Actual cold frozen-tiny imports, not mocked critical imports or runtime PASS."""
import json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent

class Controls(unittest.TestCase):
    def run_cold(self,body):
        prefix='''import sys,json,importlib.util,types
from pathlib import Path
P=Path(PAYLOAD_PATH);sys.path.insert(0,str(P))
import firstdecode_gate as Q
tiny={'files':{n:Q.ref(P/'software_fixtures/tiny'/n)for n in('reader.py','io_api.py','byteaudit.py')}}
payload={'files':{'byteaudit.py':Q.ref(P/'byteaudit.py')}}
def actual_reader():
 p=Q.checked(tiny['files']['reader.py']);s=importlib.util.spec_from_file_location('_cold_actual_frozen_tiny_reader',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
'''.replace('PAYLOAD_PATH',repr(str(P)))
        z=subprocess.run([sys.executable,'-I','-B','-c',prefix+body],capture_output=True,text=True)
        self.assertEqual(z.returncode,0,z.stderr+z.stdout)
    def test_real_tiny_import_and_backend_then_restore_exact_namespace(self):
        self.run_cold('''before=list(sys.path);assert 'byteaudit' not in sys.modules and 'io_api' not in sys.modules
with Q.tiny_namespace(tiny,payload):
 actual_reader()
 import byteaudit
 assert Path(byteaudit.__file__)==P/'software_fixtures/tiny/byteaudit.py'
assert sys.path==before and 'byteaudit' not in sys.modules and 'io_api' not in sys.modules
own=Q.payload_byteaudit(payload)
import firstdecode_capture
assert firstdecode_capture.Store is own.Store and Path(own.__file__)==P/'byteaudit.py'
from firstdecode_cli import numerical_modules
orig=P/'software_fixtures';assert str(orig) not in sys.path
mp=dict(original_tensor_consumer=Q.ref(orig/'tensor_consumer.py'),original_numeric_oracle=Q.ref(orig/'dependencies/numeric_oracle.py'),original_integer_round=Q.ref(orig/'dependencies/direct_round013.py'),original_precast=Q.ref(orig/'precast.py'),original_direct_round=Q.ref(orig/'direct_round.py'))
T,R=numerical_modules(mp)
assert R.STATE_LIMIT==7.92e-7 and R.OUTPUT_LIMIT==.00303
assert Path(sys.modules['precast'].__file__)==orig/'precast.py' and Path(sys.modules['direct_round'].__file__)==orig/'direct_round.py'
assert str(orig) not in sys.path and 'torch' not in sys.modules
''')
    def test_actual_import_exception_restores_prior_payload_and_path(self):
        self.run_cold('''own=Q.payload_byteaudit(payload);before=list(sys.path)
try:
 with Q.tiny_namespace(tiny,payload):
  actual_reader()
  raise RuntimeError('actual body failure')
except RuntimeError as e:assert str(e)=='actual body failure'
else:raise AssertionError('exception swallowed')
assert sys.path==before and sys.modules['byteaudit'] is own and 'io_api' not in sys.modules
assert Q.payload_byteaudit(payload).Store is own.Store
''')
    def test_foreign_alias_and_wrong_tiny_hash_refuse_without_mutating(self):
        self.run_cold('''before=list(sys.path);foreign=types.ModuleType('io_api');foreign.__file__=str(P/'firstdecode.py');sys.modules['io_api']=foreign
try:
 with Q.tiny_namespace(tiny,payload):raise AssertionError('must not enter')
except ValueError:pass
else:raise AssertionError('foreign accepted')
assert sys.path==before and sys.modules['io_api'] is foreign
del sys.modules['io_api'] # remove only this test-created fixture, not a framework module
tiny['files']['io_api.py']['sha256']='0'*64
try:
 with Q.tiny_namespace(tiny,payload):raise AssertionError('must not enter')
except ValueError:pass
else:raise AssertionError('wrong source accepted')
assert sys.path==before and 'io_api' not in sys.modules and 'byteaudit' not in sys.modules
''')

if __name__=='__main__':unittest.main(verbosity=2)
