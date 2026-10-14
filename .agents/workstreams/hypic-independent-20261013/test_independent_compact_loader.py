import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from independent_compact_loader import enable


class LoaderTests(unittest.TestCase):
    def test_disabled_does_not_require_any_config(self):
        with patch.dict(os.environ,{'INDEPENDENT_COMPACT_HYPIC':'0'}):enable()
    def test_source_drift_rejected_before_import_hook_or_file_creation(self):
        import sys
        before=tuple(sys.meta_path)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'source.py').write_text('value=1\n')
            manifest=root/'manifest.json'
            manifest.write_text(json.dumps({'source_sha256':{'source.py':'0'*64},'config':'config.json'}))
            with patch.dict(os.environ,{'INDEPENDENT_COMPACT_HYPIC':'1','INDEPENDENT_COMPACT_MANIFEST':str(manifest)}):
                with self.assertRaises(ValueError):enable()
            self.assertEqual(tuple(sys.meta_path),before)


if __name__=='__main__':unittest.main()
