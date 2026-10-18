"""Pure local transport/byte-copy controls; no model or historical raw data."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def module(name):
    path = HERE / name
    spec = importlib.util.spec_from_loader(name, loader=None)
    value = importlib.util.module_from_spec(spec)
    value.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), value.__dict__)
    return value


B = module('bulk_copy_unchanged_r38.py')
G = module('prepare_r38.py')


class CopyControls(unittest.TestCase):
    def fixture(self, temp):
        base = Path(temp)
        aliases = {a: str(base / ('new_' + a)) for a in ('model', 'early')}
        originals = {a: str(base / ('old_' + a)) for a in aliases}
        entries = {}
        for alias, root in originals.items():
            Path(root).mkdir()
            raw = b'\x00\xff\nraw-bytes-' + alias.encode()
            name = 'sub/payload.bin'
            path = Path(root) / name
            path.parent.mkdir()
            path.write_bytes(raw)
            old = B.ref(path, raw)
            new = B.ref(aliases[alias] + '/' + name, raw)
            entries[alias] = [dict(relative_name=name, ref=new,
                                   unchanged_original_ref=old, transfer='copy-exact-original')]
        return aliases, originals, entries

    def test_exact_non_utf8_copy_and_final_refs(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            copies, pending = B.select_copies(aliases, entries, originals)
            self.assertEqual(pending, {'model': [], 'early': []})
            B.copy_exact(aliases, copies)
            for alias in aliases:
                e = copies[alias][0]
                self.assertEqual(Path(e['ref']['path']).read_bytes(),
                                 Path(e['original_ref']['path']).read_bytes())
                B.inventory_check(Path(aliases[alias]), copies[alias])

    def test_existing_either_root_refuses_before_other_root_created(self):
        for existing in ('early', 'model'):
            with tempfile.TemporaryDirectory() as temp:
                aliases, originals, entries = self.fixture(temp)
                Path(aliases[existing]).mkdir()
                copies, _ = B.select_copies(aliases, entries, originals)
                with self.assertRaisesRegex(ValueError, 'wholly absent'):
                    B.copy_exact(aliases, copies)
                self.assertFalse(Path(aliases['model' if existing == 'early' else 'early']).exists())

    def test_tampered_original_refuses_before_any_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            copies, _ = B.select_copies(aliases, entries, originals)
            Path(copies['model'][0]['original_ref']['path']).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError, 'exact file bytes'):
                B.copy_exact(aliases, copies)
            self.assertTrue(all(not Path(r).exists() for r in aliases.values()))

    def test_symlink_original_refuses_before_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            copies, _ = B.select_copies(aliases, entries, originals)
            path = Path(copies['model'][0]['original_ref']['path'])
            ordinary = path.with_name('real.bin')
            path.rename(ordinary)
            path.symlink_to(ordinary)
            with self.assertRaisesRegex(ValueError, 'regular source'):
                B.copy_exact(aliases, copies)
            self.assertTrue(all(not Path(r).exists() for r in aliases.values()))

    def test_exclusive_file_open_never_overwrites_existing_leaf(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'already.bin'
            target.write_bytes(b'keep exact evidence')
            with B.directory(temp) as fd:
                with self.assertRaises(FileExistsError):
                    with B.destination(fd, target.name):
                        self.fail('must never open existing target')
            self.assertEqual(target.read_bytes(), b'keep exact evidence')

    def test_templates_bound_and_commands_are_never_copied(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            blocked = ('SOURCE_TEMPLATE.json', 'SOURCE_MANIFEST.json', 'SOURCE_BOUND.json',
                       'COMMANDS.json', 'plugin/SOURCE_TEMPLATE.json')
            for name in blocked:
                raw = b'{}\n'
                entries['model'].append(dict(relative_name=name,
                    ref=B.ref(aliases['model'] + '/' + name, raw),
                    unchanged_original_ref=B.ref(originals['model'] + '/' + name, raw),
                    transfer='copy-exact-original'))
            copies, pending = B.select_copies(aliases, entries, originals)
            self.assertEqual(len(copies['model']), 1)
            self.assertEqual(pending['model'], list(blocked))

    def test_wrong_source_duplicate_and_wrong_digest_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            for mode in ('wrong-source', 'duplicate', 'wrong-digest'):
                bad = copy.deepcopy(entries)
                if mode == 'wrong-source':
                    bad['model'][0]['unchanged_original_ref']['path'] = '/other/sub/payload.bin'
                elif mode == 'duplicate':
                    bad['model'].append(copy.deepcopy(bad['model'][0]))
                else:
                    bad['model'][0]['ref']['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    B.select_copies(aliases, bad, originals)

    def test_extra_file_final_inventory_rejected_without_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            aliases, originals, entries = self.fixture(temp)
            copies, _ = B.select_copies(aliases, entries, originals)
            B.copy_exact(aliases, copies)
            extra = Path(aliases['model']) / 'extra'
            extra.write_bytes(b'preserve this too')
            with self.assertRaisesRegex(ValueError, 'exact copied inventory'):
                B.inventory_check(Path(aliases['model']), copies['model'])
            self.assertTrue(extra.exists())

    def test_default_off_and_frozen_transport_pin(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(HERE / 'bulk_copy_unchanged_r38.py')],
                                text=True, capture_output=True, check=True)
        value = json.loads(result.stdout)
        self.assertIs(value['enabled'], False)
        self.assertIs(value['read_only'], True)
        raw = (HERE / 'transport_emit_r38.py').read_bytes()
        tr = B.ref(HERE / 'transport_emit_r38.py', raw)
        transport = B.load_transport(tr)
        self.assertEqual(transport.GENERATOR_SHA256,
                         hashlib.sha256((HERE / 'prepare_r38.py').read_bytes()).hexdigest())


class ActiveFixtureControls(unittest.TestCase):
    def fixture(self):
        snapshots = HERE.parent.parent / 'resume_packets'
        old_owner = (snapshots / 'deltalog_early/owner.py').read_bytes()
        old_early = (snapshots / 'deltalog36/early_scan_template.json').read_bytes()
        original = (snapshots / 'deltalog36/test_firstdecode_owner.py').read_bytes()
        new_owner = G.identity_text(old_owner.decode()).encode()
        new_early = b'{"new-exact-template": true}\n'
        tree = {'software_dependencies/early_scan_owner.py': old_owner,
                'software_dependencies/early_scan_template.json': old_early,
                'test_firstdecode_owner.py': original,
                'software_dependencies/early_scan_owner_R31.py.txt': b'unchanged historical bytes'}
        return tree, old_owner, new_owner, old_early, new_early

    def test_pair_updated_and_only_two_test_string_literals_differ(self):
        tree, *args = self.fixture()
        before = copy.deepcopy(tree)
        G.refresh_active_fixtures(tree, *args)
        self.assertEqual(tree['software_dependencies/early_scan_owner.py'], args[1])
        self.assertEqual(tree['software_dependencies/early_scan_template.json'], args[3])
        self.assertEqual(tree['software_dependencies/early_scan_owner_R31.py.txt'],
                         before['software_dependencies/early_scan_owner_R31.py.txt'])
        original = ast.parse(before['test_firstdecode_owner.py'])
        changed = ast.parse(tree['test_firstdecode_owner.py'])
        count = 0
        for node in ast.walk(changed):
            if isinstance(node, ast.Constant) and type(node.value) is str and G.P_NEW in node.value:
                count += 1
                node.value = node.value.replace(G.P_NEW, G.P_OLD)
        self.assertEqual(count, 2)
        self.assertEqual(ast.dump(original), ast.dump(changed))

    def test_mismatched_original_owner_or_template_refuses(self):
        for name in ('software_dependencies/early_scan_owner.py',
                     'software_dependencies/early_scan_template.json'):
            tree, *args = self.fixture()
            tree[name] += b'changed'
            with self.assertRaisesRegex(ValueError, 'original active early'):
                G.refresh_active_fixtures(tree, *args)

    def test_missing_extra_or_prechanged_path_refuses(self):
        for mode in ('missing', 'extra', 'prechanged'):
            tree, *args = self.fixture()
            value = tree['test_firstdecode_owner.py']
            if mode == 'missing':
                value = value.replace(G.P_OLD.encode(), b'wrong', 1)
            elif mode == 'extra':
                value += b'\n# ' + G.P_OLD.encode()
            else:
                value += b'\n# ' + G.P_NEW.encode()
            tree['test_firstdecode_owner.py'] = value
            with self.assertRaisesRegex(ValueError, 'exact two original'):
                G.refresh_active_fixtures(tree, *args)


if __name__ == '__main__':
    unittest.main()
