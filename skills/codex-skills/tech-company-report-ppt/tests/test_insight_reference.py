import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prepare_design_jobs import insight_reference


class InsightReferenceTests(unittest.TestCase):
    def test_reference_library_is_complete_and_traceable(self):
        library = ROOT / 'assets/insight-reference'
        data = json.loads((library / 'catalog.json').read_text())
        self.assertEqual(len(data['slides']), 24)
        self.assertEqual(len({x['source_file'] for x in data['slides']}), 4)
        self.assertEqual(len({x['reference_id'] for x in data['slides']}), 24)
        for item in data['slides']:
            self.assertTrue((library / item['preview']).is_file())
            self.assertEqual(len(item['source_sha256']), 64)
            self.assertGreater(item['source_pdf_page'], 0)
            self.assertFalse(item['editable'])
        with zipfile.ZipFile(library / '优秀洞察报告精选参考.pptx') as z:
            slides = [n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
            self.assertEqual(len(slides), 24)
            self.assertIsNone(z.testzip())

    def test_explicit_reference_overrides_role_and_invalid_id_fails(self):
        selected = insight_reference({'page_role': 'table', 'insight_reference_id': 'R24'})
        self.assertEqual(selected['source_pdf_page'], 37)
        self.assertTrue(Path(selected['preview']).is_file())
        self.assertEqual(insight_reference({'page_role': 'table'})['reference_id'], 'R05')
        self.assertIsNone(insight_reference({'page_role': 'cover'}))
        with self.assertRaises(SystemExit):
            insight_reference({'insight_reference_id': 'R99'})
