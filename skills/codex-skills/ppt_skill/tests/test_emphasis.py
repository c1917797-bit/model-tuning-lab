import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_designs import review_slide, REQUIRED_SEMANTIC_CHECKS

class EmphasisTests(unittest.TestCase):
    def review(self, observed, emphasis=None):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); Image.new('RGB',(1280,720),'white').save(root/'draft.png')
            slide={'slide_number':1,'title':'Three paths','core_judgment':'Compare preparation timing'}
            if emphasis is not None: slide['emphasis']=emphasis
            return review_slide(root,slide,{'design_path':'draft.png'}, {'checks':dict.fromkeys(REQUIRED_SEMANTIC_CHECKS,True),'observed_emphasis_targets':observed})
    def test_unrequested_red_route_is_blocked(self):
        self.assertFalse(self.review(['route-2'])['passed'])
    def test_neutral_slide_passes(self):
        self.assertTrue(self.review([])['passed'])
    def test_explicit_targets_must_match_exactly(self):
        contract={'targets':['route-2-preparation','route-3-preparation'],'reason':'Compare where preparation occurs','meaning':'difference'}
        self.assertTrue(self.review(contract['targets'],contract)['passed'])
        self.assertFalse(self.review(['route-2-preparation'],contract)['passed'])
    def test_missing_inventory_blocks_boolean_only_review(self):
        self.assertFalse(self.review(None)['passed'])

class ColorPropagationTests(unittest.TestCase):
    def test_structural_palette_survives_empty_emphasis(self):
        import json
        from prepare_design_jobs import prepare
        from workflow_common import DEFAULT_CATALOG
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            palette = {'structural_palette': ['#356A8A', '#438478'],
                       'role_colors': {'device': '#356A8A', 'cloud': '#438478'}}
            spec = {'color_system': palette, 'slides': [
                {'slide_number': n, 'title': 'Device and cloud',
                 'core_judgment': 'Distinct processing locations',
                 'page_role': 'architecture', 'layout_type': 'architecture'}
                for n in [1, 2]]}
            (root / 'deck_spec.json').write_text(json.dumps(spec))
            prepare(root, DEFAULT_CATALOG)
            for n in [1, 2]:
                prompt = json.loads((root / 'design-prompts' / ('slide-%02d.json' % n)).read_text())
                self.assertEqual(prompt['emphasis']['targets'], [])
                self.assertEqual(prompt['color_system'], palette)
            del spec['color_system']
            (root / 'deck_spec.json').write_text(json.dumps(spec))
            prepare(root, DEFAULT_CATALOG)
            prompt = json.loads((root / 'design-prompts/slide-01.json').read_text())
            self.assertEqual(len(prompt['color_system']['structural_palette']), 3)
