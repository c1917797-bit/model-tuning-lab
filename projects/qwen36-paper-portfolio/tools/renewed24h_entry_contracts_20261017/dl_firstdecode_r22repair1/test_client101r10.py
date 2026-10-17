import ast,hashlib,importlib.util,json,subprocess,sys,tempfile,threading,unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
P=Path(__file__).resolve().parent
import client
class ClientWire(unittest.TestCase):
 def test_fresh_I_real_request_until_HTTP(self):
  received=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_POST(self):
    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));received.append((body,self.headers['X-Request-Id'],self.path));wire=('data: '+json.dumps(dict(usage=dict(prompt_tokens=len(body['prompt']),completion_tokens=10)))+'\n\ndata: [DONE]\n\n').encode();self.send_response(200);self.end_headers();self.wfile.write(wire)
  server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'wire';v=subprocess.run([sys.executable,'-I','-B',str(P/'transport_probe101r10.py'),'--url','http://127.0.0.1:%d/v1/completions'%server.server_port,'--output',str(p)],capture_output=True,text=True,timeout=15);self.assertEqual(v.returncode,0,v.stderr);self.assertTrue(json.loads(v.stdout)['isolated']);self.assertTrue(p.with_suffix('.response.bin').is_file())
  finally:server.shutdown();server.server_close();thread.join(2)
  self.assertEqual(len(received),1);body,rid,path=received[0];self.assertEqual(body['prompt'],[1000+j%257 for j in range(2048)]);self.assertEqual((body['temperature'],body['seed'],body['max_tokens'],body['min_tokens'],body['ignore_eos'],body['echo']),(0,0,10,10,True,False));self.assertEqual((rid,path),('SOFTWARE101R10-decode','/v1/completions'))
 def test_bad_vocabulary_rejected(self):
  def need(v,m):
   if not v:raise ValueError(m)
  with self.assertRaises(ValueError):client.payload2048(dict(model_type='qwen3_5',text_config=dict(vocab_size=1000)),need)
  p=P/'fixtures/native_capture_overlay.py';spec=importlib.util.spec_from_file_location('_R10_original_length_fault',p);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  with self.assertRaisesRegex(ValueError,'only bounded new diagnostic input lengths'):old.prompt_ids(dict(model_type='qwen3_5',text_config=dict(vocab_size=248320)),2048)
 def test_actual_main_uses_same_payload_and_original_request(self):
  s=(P/'client.py').read_text();self.assertIn('body=payload2048(cfg,E.need)',s);self.assertNotIn('body=C.payload(cfg,n)',s);self.assertIn('C.request_once(',s);self.assertIn("rid=a.run_id+'-'+name",s);self.assertIn('o.sha(a.model_config)==o.MODEL_CONFIG_SHA',s)
