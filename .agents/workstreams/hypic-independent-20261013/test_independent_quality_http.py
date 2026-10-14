import json,threading,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from independent_quality_client import http_quality,quality_payload,validate_response
class QualityHttpTests(unittest.TestCase):
    def test_loopback_transport_preserves_ruler_and_end(self):
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                payload=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append((self.path,payload))
                data=json.dumps({"id":"real-http-fixture","choices":[{"text":"A","finish_reason":"stop"}],
                    "usage":{"prompt_tokens":16,"completion_tokens":1}}).encode()
                self.send_response(200);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever);thread.start()
        try:
            row={"token_ids":[1]*16};guards=[]
            response=http_quality(server.server_port,quality_payload(row),guard=lambda:guards.append(True),timeout=5)
            self.assertEqual(validate_response(response,row),("real-http-fixture","A","stop",1))
            self.assertEqual(seen[0][0],"/v1/completions")
            self.assertFalse(seen[0][1]["ignore_eos"])
            self.assertEqual(seen[0][1]["max_tokens"],1024)
            self.assertGreaterEqual(len(guards),3)
        finally:server.shutdown();thread.join();server.server_close()
    def test_port_and_output_identity_rejected(self):
        with self.assertRaises(ValueError):http_quality(0,{},guard=lambda:None)
        with self.assertRaises(ValueError):
            validate_response({"id":"r","choices":[{"text":"A","finish_reason":"stop"}],
                "usage":{"prompt_tokens":16,"completion_tokens":2048}},{"token_ids":[1]*16})
if __name__=="__main__":unittest.main()
