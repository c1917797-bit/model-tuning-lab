import hashlib,json,tempfile,unittest
from pathlib import Path
from independent_public_token_artifact import public_tokens_from_artifact

class TokenArtifactTests(unittest.TestCase):
    def test_verified_external_tokens_and_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"tokens.json"
            raw=json.dumps({"public_segment":[2]*16384}).encode();p.write_bytes(raw)
            spec={"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"length":16384}
            self.assertEqual(public_tokens_from_artifact(spec),(2,)*16384)
            p.write_bytes(raw+b" ")
            with self.assertRaises(ValueError):public_tokens_from_artifact(spec)
    def test_relative_path_rejected(self):
        with self.assertRaises(ValueError):
            public_tokens_from_artifact({"path":"tokens.json","sha256":"x","length":16384})

if __name__=="__main__":unittest.main()
