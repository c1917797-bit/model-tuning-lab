import io
import json
import types
import unittest
from unittest.mock import patch
import r23_state_diagnostic as d

class RequestTests(unittest.TestCase):
    def setUp(self):
        self.q=types.SimpleNamespace(MODEL_NAME="m",BASE_URL="http://127.0.0.1:8223")
        self.item=dict(prompt="p",boundary=16,prompt_tokens=32)
        self.response=dict(id="chatcmpl-id",usage=dict(prompt_tokens=32,completion_tokens=2),
                           choices=[dict(message=dict(content="D"),finish_reason="stop")])
    def test_explicit_id_and_segment_protocol(self):
        def opened(req,timeout):
            body=json.loads(req.data)
            self.assertEqual(body["request_id"],"id")
            self.assertEqual(body["n"],1)
            self.assertEqual(body["vllm_xargs"]["hypic_segment_ends"],[16,32])
            self.assertFalse(body["ignore_eos"])
            self.assertFalse(body["chat_template_kwargs"]["enable_thinking"])
            self.assertEqual(body["max_tokens"],2048)
            self.assertNotIn("X-request-id",req.headers)
            return io.StringIO(json.dumps(self.response))
        with patch.object(d,"urlopen",side_effect=opened):
            self.assertEqual(d.request(self.q,self.item,"id",2048)["request_id"],"chatcmpl-id")
    def test_wrong_response_id_rejected(self):
        self.response["id"]="chatcmpl-other"
        with patch.object(d,"urlopen",return_value=io.StringIO(json.dumps(self.response))):
            with self.assertRaisesRegex(RuntimeError,"identity"):
                d.request(self.q,self.item,"id",2048)
    def test_wrong_usage_rejected(self):
        self.response["usage"]["completion_tokens"]=2049
        with patch.object(d,"urlopen",return_value=io.StringIO(json.dumps(self.response))):
            with self.assertRaisesRegex(RuntimeError,"accounting"):
                d.request(self.q,self.item,"id",2048)

if __name__=="__main__":
    unittest.main()
