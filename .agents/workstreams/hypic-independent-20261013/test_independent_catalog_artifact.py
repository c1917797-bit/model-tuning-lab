import hashlib,json,tempfile,unittest
from pathlib import Path
from independent_catalog_artifact import catalog_from_artifact,resolve_catalog_config

class CatalogArtifactTests(unittest.TestCase):
    def spec(self,path,segments):
        raw=json.dumps({"schema":"hypic-public-catalog/v1","public_segments":segments}).encode()
        path.write_bytes(raw)
        return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"segments":len(segments)}
    def test_load_distinct_segments_and_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec=self.spec(Path(tmp)/"catalog.json",[[1]*10,[2]*12])
            self.assertEqual(catalog_from_artifact(spec),((1,)*10,(2,)*12))
            original={"public_catalog_artifact":spec,"enable_mixed":True}
            resolved=resolve_catalog_config(original)
            self.assertIn("public_catalog_artifact",original)
            self.assertNotIn("public_catalog_artifact",resolved)
            self.assertEqual(len(resolved["public_segments"]),2)
    def test_drift_count_duplicate_and_invalid_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"catalog.json"
            spec=self.spec(p,[[1]*10])
            with self.assertRaises(ValueError):catalog_from_artifact(dict(spec,segments=2))
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaises(ValueError):catalog_from_artifact(spec)
            for segments in ([[1]*10,[1]*10],[[True]*10],[[1]*8]):
                with self.assertRaises(ValueError):catalog_from_artifact(self.spec(p,segments))
    def test_ambiguous_config_and_relative_path(self):
        with self.assertRaises(ValueError):
            resolve_catalog_config({"public_catalog_artifact":{},"public_tokens":[1]})
        with self.assertRaises(ValueError):
            catalog_from_artifact({"path":"relative.json","sha256":"x","segments":1})
if __name__=="__main__":unittest.main()
