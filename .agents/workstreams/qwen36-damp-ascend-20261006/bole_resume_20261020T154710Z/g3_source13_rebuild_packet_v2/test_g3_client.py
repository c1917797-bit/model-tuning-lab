"""Actual HTTP client protocol controls; no model/device execution."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g1_contract as G
import service_client as CLIENT

class ClientTests(unittest.TestCase):
 def fixture(self):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);root=Path(td.name)
  sr=C.write(root/'SOURCE.json',dict(prepared_only=False,service_experiment=G.SCOPE))
  return root,sr,NS(vocab_size=248320,encode=lambda *args,**kw:list(range(200)))
 def opener(self,requests,short=False):
  def call(request,timeout):
   body=json.loads(request.data);requests.append(body);count=body['max_tokens'];header=request.get_header('X-request-id')
   wire=json.dumps(dict(id='cmpl-'+header,choices=[dict(token_ids=list(range(count-(1 if short else 0))))],
    usage=dict(prompt_tokens=131,completion_tokens=count))).encode()
   class Response(io.BytesIO):status=200
   return Response(wire)
  return call
 def test_single_full1024_token_ID_response_then_native_one_token_barrier(self):
  root,sr,tok=self.fixture();requests=[];value=CLIENT.run(sr,root,tok,self.opener(requests))
  self.assertEqual([v['max_tokens']for v in requests],[1024,1]);self.assertEqual(len(value['rows']),2)
  self.assertEqual([v['label']for v in value['rows']],['tree-1','retirement-barrier'])
  self.assertTrue(all(v['ignore_eos']and v['return_token_ids']for v in requests));self.assertEqual(requests[0]['prompt'],list(range(131)))
 def test_truncated_fixed_output_preserves_failure_and_does_not_issue_barrier(self):
  root,sr,tok=self.fixture();requests=[]
  with self.assertRaises(ValueError):CLIENT.run(sr,root,tok,self.opener(requests,True))
  self.assertEqual(len(requests),1);self.assertTrue((root/'HTTP-FAILURE.json').is_file());self.assertFalse((root/'HTTP_RESULT.json').exists())
 def test_all_new_entrypoints_are_cold_default_OFF_and_help(self):
  for name in('prepare_g3.py','g2_consumer.py','g2_finalize.py','host_service.py','service_client.py','server090.py','service_entry.py'):
   for flags in([],['--help']):
    q=subprocess.run([sys.executable,'-I','-B',str(P/name),*flags],capture_output=True,text=True,timeout=10)
    self.assertEqual(q.returncode,0,name+q.stderr)
    if not flags:self.assertIs(json.loads(q.stdout)['enabled'],False)

if __name__=='__main__':unittest.main()
