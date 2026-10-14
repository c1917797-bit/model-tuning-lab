"""Local fake HTTP service controls; never real model/performance evidence."""
import json,threading,unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from independent_formal_client import http_measure

class FormalHTTPTests(unittest.TestCase):
    def run_server(self,usage_tokens=1024):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                captured.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200);self.send_header("Content-Type","text/event-stream")
                self.end_headers()
                packets=[
                    {"id":"cmpl-test","choices":[{"index":0,"text":"","finish_reason":None}]},
                    {"id":"cmpl-test","choices":[{"index":0,"text":"mock","finish_reason":"length"}]},
                    {"id":"cmpl-test","choices":[],"usage":{"prompt_tokens":32768,"completion_tokens":usage_tokens}}]
                for packet in packets:
                    self.wfile.write(("data: "+json.dumps(packet)+"\n\n").encode());self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n");self.wfile.flush()
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        return server,thread,captured
    def test_real_transport_mock_service_preserves_identity_and_usage(self):
        server,thread,captured=self.run_server()
        guards=[]
        try:
            r=http_measure(server.server_port,{"prompt":[1],"stream":True},
                           guard=lambda:guards.append(True),timeout=5)
            self.assertEqual(r["request_id"],"cmpl-test")
            self.assertEqual(r["completion_tokens"],1024)
            self.assertGreaterEqual(r["duration_ms"],r["ttft_ms"])
            self.assertEqual(len(captured),1);self.assertGreater(len(guards),2)
        finally:server.shutdown();server.server_close();thread.join()
    def test_wrong_real_usage_boundary_rejected(self):
        server,thread,captured=self.run_server(1000)
        try:
            with self.assertRaises(ValueError):
                http_measure(server.server_port,{},guard=lambda:None,timeout=5)
        finally:server.shutdown();server.server_close();thread.join()

if __name__=="__main__":unittest.main()
