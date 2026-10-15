import json,unittest
from pathlib import Path
from unittest.mock import patch
from audit_native_decode_terminal import audit_terminal
CONTRACT="NATIVE_DECODE_BATCH_CANARY_R1_CONTRACT.json"
REAL_READ=Path.read_text
class TerminalTests(unittest.TestCase):
    def test_offline_positive_does_not_claim_current_release(self):
        result=audit_terminal(CONTRACT)
        self.assertTrue(result["terminal_evidence_valid"])
        self.assertFalse(result["live_release_verified"])
        self.assertEqual(result["shadow_groups"],384)
    def test_terminal_negative_controls(self):
        for filename,field,value in [
            ("result.json","valid",False),("result.json","responses",15),
            ("release.json","port_free",False),("compiled-cache-unit.json","input_sha256","bad")]:
            def read(path,*args,**kwargs):
                text=REAL_READ(path,*args,**kwargs)
                if path.name==filename:
                    data=json.loads(text);data[field]=value;return json.dumps(data)
                return text
            with self.subTest(filename=filename,field=field),patch.object(Path,"read_text",read):
                with self.assertRaises(ValueError):audit_terminal(CONTRACT)
    def test_token_count_negative(self):
        def read(path,*args,**kwargs):
            text=REAL_READ(path,*args,**kwargs)
            if path.name=="compiled-cache-unit.json":
                data=json.loads(text);data["results"][0]["response"]["usage"]["completion_tokens"]=63
                return json.dumps(data)
            return text
        with patch.object(Path,"read_text",read),self.assertRaises(ValueError):audit_terminal(CONTRACT)
if __name__=="__main__":unittest.main()
