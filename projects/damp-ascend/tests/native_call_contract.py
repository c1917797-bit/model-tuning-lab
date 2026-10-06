"""Pure-stdlib native torch schema/call-signature guards; no device execution."""
import ast
from pathlib import Path
from types import SimpleNamespace

NATIVE_NAMES = ('query', 'key', 'value', 'state', 'beta', 'scale',
                'actual_seq_lengths', 'ssm_state_indices',
                'num_accepted_tokens', 'g', 'gk')
KEYWORD_NAMES = NATIVE_NAMES[4:]


def validate_native_schema(schema):
    names = [argument.name for argument in schema.arguments]
    keyword_only = [getattr(argument, 'kwarg_only', None) for argument in schema.arguments]
    if names != list(NATIVE_NAMES) or keyword_only != [False]*4+[True]*7:
        raise RuntimeError('native names/keyword-only contract differs: '+str(schema))
    if len(schema.returns) != 1:
        raise RuntimeError('native must return exactly one Tensor: '+str(schema))
    return {'argument_names': names, 'keyword_only': keyword_only,
            'positional_count': 4, 'keyword_count': 7}


def cpu_signature_checks(directory):
    """AST plus strict Python binder; deliberately does not import torch/helper."""
    path = Path(directory)/'native_compressed_golden.py'
    tree = ast.parse(path.read_text(), filename=str(path))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
             isinstance(node.func, ast.Name) and node.func.id == 'native_op']
    if len(calls) != 1:
        raise AssertionError('helper must have exactly one explicit native_op call')
    call = calls[0]
    if len(call.args) != 4 or any(isinstance(arg, ast.Starred) for arg in call.args):
        raise AssertionError('native accepts exactly four explicit positional args')
    if [keyword.arg for keyword in call.keywords] != list(KEYWORD_NAMES):
        raise AssertionError('all seven native keyword-only args must be explicit and ordered')
    sentinels = {name: object() for name in ('qe', 'ke', 'vb', 'state', 'beta',
                                          'lengths', 'nids', 'g', 'device')}
    captured = {}
    def strict_native(query, key, value, state, *, beta=None, scale=None,
                      actual_seq_lengths=None, ssm_state_indices=None,
                      num_accepted_tokens=None, g=None, gk=None):
        captured.update(query=query, key=key, value=value, state=state,
            beta=beta, scale=scale, actual_seq_lengths=actual_seq_lengths,
            ssm_state_indices=ssm_state_indices, num_accepted_tokens=num_accepted_tokens,
            g=g, gk=gk)
        return 'strict-binder-result'
    expression = ast.fix_missing_locations(ast.Expression(body=call))
    environment = {**sentinels, 'native_op': strict_native, '_nd': lambda x, device: x}
    result = eval(compile(expression, str(path), 'eval'), {'__builtins__': {}}, environment)
    if result != 'strict-binder-result': raise AssertionError('native binder did not run')
    for parameter, variable in (('query', 'qe'), ('key', 'ke'), ('value', 'vb'),
            ('state', 'state'), ('beta', 'beta'), ('actual_seq_lengths', 'lengths'),
            ('ssm_state_indices', 'nids'), ('g', 'g')):
        if captured[parameter] is not sentinels[variable]:
            raise AssertionError('native argument semantic mapping differs: '+parameter)
    if captured['scale'] != 128**-0.5 or captured['num_accepted_tokens'] is not None or captured['gk'] is not None:
        raise AssertionError('native scale/optional argument values differ')
    # The exact old 11-positional call must reject before any body executes.
    try:
        strict_native(*[object() for _ in range(11)])
    except TypeError:
        old_positional_rejected = True
    else:
        raise AssertionError('strict binder unexpectedly admitted legacy 11-positional call')
    fake = SimpleNamespace(arguments=[SimpleNamespace(name=name, kwarg_only=i >= 4)
                         for i, name in enumerate(NATIVE_NAMES)], returns=[object()])
    good = validate_native_schema(fake)
    rejected = []
    for kind in ('keyword_only', 'name', 'argument_count', 'return_count'):
        bad = SimpleNamespace(arguments=[SimpleNamespace(name=a.name, kwarg_only=a.kwarg_only)
                             for a in fake.arguments], returns=list(fake.returns))
        if kind == 'keyword_only': bad.arguments[4].kwarg_only = False
        elif kind == 'name': bad.arguments[8].name = 'wrong_accepted_tokens'
        elif kind == 'argument_count': bad.arguments.pop()
        else: bad.returns.clear()
        try: validate_native_schema(bad)
        except RuntimeError: rejected.append(kind)
        else: raise AssertionError('schema guard accepted malformed '+kind)
    return {'ast_call_positional_count': 4, 'explicit_keywords': list(KEYWORD_NAMES),
            'strict_binder_mapping_pass': True, 'legacy_11_positional_rejected': old_positional_rejected,
            'schema_guard_positive': good, 'schema_guard_negative_rejected': rejected,
            'scope': 'stdlib call-signature guard only; no actual Torch schema, NPU or numeric result'}
