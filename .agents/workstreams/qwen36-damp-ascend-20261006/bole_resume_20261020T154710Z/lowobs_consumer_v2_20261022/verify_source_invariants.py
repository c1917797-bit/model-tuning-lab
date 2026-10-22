"""Inspect the exact source delta; never run a state or performance consumer."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BASELINES = {
    'read_short_results.py': (4204, 'ebcee4f6a9cc3cbb8cd6b47b3c6ce947ceb01dab83398eca8188ac68cd2102d0'),
    'consume_pair.py': (7899, '5c11717e03c958661411c102c407c8f8b773d599d45f42b245f8c257b44196d9'),
}


def need(value, message):
    if not value:
        raise ValueError(message)


def node_dump(value):
    return ast.dump(value, include_attributes=False)


def parse_file(path):
    data = path.read_bytes()
    text = data.decode('utf-8')
    return data, text, ast.parse(text, filename=str(path))


def functions(tree):
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def normalized_arm(node, key):
    node = copy.deepcopy(node)
    expected = ast.parse(
        "cleanup_obj(s[" + key + "],out/('dense'if " + key
        + "=='model_release'else'cpu-preflight')/'cleanup.json')", mode='eval').body
    replacement = ast.parse('obj(s[' + key + '])', mode='eval').body
    seen = []

    class ReplaceOnlyCleanupCall(ast.NodeTransformer):
        def visit_Call(self, call):
            if isinstance(call.func, ast.Name) and call.func.id == 'cleanup_obj':
                need(node_dump(call) == node_dump(expected), 'exact role-bound cleanup call')
                seen.append(call)
                return copy.deepcopy(replacement)
            return self.generic_visit(call)

    result = ReplaceOnlyCleanupCall().visit(node)
    need(len(seen) == 1, 'one cleanup adapter call site inside the original role loop')
    return result


def inspect_one(old_path, new_path, key):
    original, old_text, old_tree = parse_file(old_path)
    need((len(original), hashlib.sha256(original).hexdigest()) == BASELINES[old_path.name],
         'unchanged exact frozen baseline')
    current, new_text, new_tree = parse_file(new_path)
    old_functions, new_functions = functions(old_tree), functions(new_tree)
    need(set(new_functions) == set(old_functions) | {'cleanup_obj'}, 'only one new helper adapter function')
    need(node_dump(old_functions['arm']) == node_dump(normalized_arm(new_functions['arm'], key)),
         'all original arm predicates and logic preserved after the one declared read seam')
    unchanged = []
    for name, old in old_functions.items():
        if name in ('arm', 'main'):
            continue
        need(ast.get_source_segment(old_text, old) == ast.get_source_segment(new_text, new_functions[name]),
             'unchanged complete function source: ' + name)
        unchanged.append(name)
    if 'main' in old_functions:
        main = copy.deepcopy(new_functions['main'])
        renamed = 0
        for node in ast.walk(main):
            if isinstance(node, ast.Constant) and node.value == 'LOWOBS_SHORT_NPU_COMPARE_v2.json':
                node.value = 'LOWOBS_SHORT_NPU_COMPARE_v1.json'
                renamed += 1
        need(renamed == 1 and node_dump(main) == node_dump(old_functions['main']),
             'short main changes only the exclusive result filename')
        for label in ('ON', 'OFF'):
            old = next(n for n in old_tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == label for t in n.targets))
            new = next(n for n in new_tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == label for t in n.targets))
            need(node_dump(old) == node_dump(new), 'original exact bound source Ref ' + label)
    writes = [n for n in ast.walk(new_tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute) and n.func.attr == 'open'
              and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == 'xb']
    need(len(writes) == 1 and node_dump(writes[0].func.value) == node_dump(ast.Name(id='out', ctx=ast.Load())),
         'one exclusive output write only')
    output_name = ('LOWOBS_SHORT_NPU_COMPARE_v2.json' if key == 'k'
                   else 'LOWOBS_FIXED131_PAIR_SCREEN_v2.json')
    output = [n for n in ast.walk(new_tree) if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'out' for t in n.targets)
              and isinstance(n.value, ast.BinOp) and isinstance(n.value.right, ast.Constant)
              and n.value.right.value == output_name]
    need(len(output) == 1, 'new sibling result identity')
    return dict(baseline=str(old_path), candidate=str(new_path),
                baseline_sha256=hashlib.sha256(original).hexdigest(),
                candidate_sha256=hashlib.sha256(current).hexdigest(),
                unchanged_complete_function_sources=unchanged,
                original_arm_predicates_preserved=True, generic_Ref3_unchanged=True,
                qualification_flags_unchanged=True, role_paths_exact=True,
                exclusive_output_name=output_name)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--baseline-dir', type=Path, required=True)
    args = parser.parse_args()
    helper = (ROOT / 'cleanup_summary.py').read_bytes()
    need((len(helper), hashlib.sha256(helper).hexdigest()) ==
         (3957, '1c2e014303bec214cff2e19d8c428eee1a13d69c3f8b525308b3ae958faf9687'),
         'actual v4 helper copied byte-for-byte')
    rows = [inspect_one(args.baseline_dir / 'read_short_results.py', ROOT / 'read_short_results_v2.py', 'k'),
            inspect_one(args.baseline_dir / 'consume_pair.py', ROOT / 'consume_pair_v2.py', 'key')]
    print(json.dumps(dict(schema='bole.lowobs-consumer-source-invariants/v2', source_invariants_pass=True,
                         source_only=True, NPU_executed=False, paired_gate_pass=False,
                         performance_admitted=False, rows=rows), sort_keys=True))


if __name__ == '__main__':
    main()
