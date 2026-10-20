"""Local stdlib/AST/control tests only; never import Torch or use a device."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace


def main():
    root = Path(__file__).resolve().parent
    modules = {}
    for name in ('time_gdn', 'timing_paths'):
        path = root / (name + '.py')
        ast.parse(path.read_text(), filename=str(path))
        spec = importlib.util.spec_from_file_location('stdlib_check_' + name, path)
        module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module
        spec.loader.exec_module(module); modules[name] = module
    D = modules['time_gdn']
    for args, expected in (([], 0), (['--help'], 0), (['--execute'], 2)):
        saved = sys.argv; sys.argv = ['time_gdn.py', *args]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                try:
                    code = D.main()
                except SystemExit as error:
                    code = error.code
            assert code == expected
            if not args:
                assert json.loads(out.getvalue())['enabled'] is False
        finally:
            sys.argv = saved
    for frame in range(384):
        orders = [D.order(frame, pair) for pair in range(20)]
        assert orders.count(('original', 'candidate')) == 10
        assert orders.count(('candidate', 'original')) == 10
    assert D.stats([40, 80, 120], 4) == dict(count=3, batch_iterations=4,
        mean_ns=20.0, median_ns=20.0, minimum_ns=10.0, maximum_ns=30.0, outliers_removed=0)
    # Explicitly a control-flow stub, never an actual NPU measurement.
    syncs = []; calls = []; clock = iter((100, 200)); old = D.time.perf_counter_ns
    D.time.perf_counter_ns = lambda: next(clock)
    try:
        elapsed, last = D.measure(SimpleNamespace(npu=SimpleNamespace(
            synchronize=lambda: syncs.append(1))), lambda: calls.append(1) or len(calls), 4)
    finally:
        D.time.perf_counter_ns = old
    assert elapsed == 100 and last == 4 and len(calls) == 4 and len(syncs) == 2
    path = root / 'README.md'; data = path.read_bytes()
    reference = dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    assert D.checked_bootstrap(reference)[1] == data
    try:
        D.checked_bootstrap(dict(reference, sha256='0' * 64))
    except ValueError:
        pass
    else:
        raise AssertionError('bad source hash accepted')
    for name in ('MANIFEST_TEMPLATE.json', 'ADMISSION_TEMPLATE.json'):
        json.loads((root / name).read_text())
    primary = {'triton_jit.py': (36630, '8f170a849331e9ce75b0d2d05e0bcd6ad2f9de838bfb277e823617982d672aad'),
               'triton_compiled.py': (18714, '4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b')}
    for name, (size, digest) in primary.items():
        data = (root.parents[1] / 'bole_service_reference/installed' / name).read_bytes()
        assert len(data) == size and hashlib.sha256(data).hexdigest() == digest
    for package, name in (('gdn_kernel', 'PROPOSAL_MANIFEST.json'), ('gdn_replay', 'ADVISORY_MANIFEST.json')):
        old = json.loads((root.parent / package / name).read_text())
        for reference in old.get('proposal_files', old.get('files', {})).values():
            D.checked_bootstrap(reference)
    assert not any(k == prefix or k.startswith(prefix + '.')
                   for k in sys.modules for prefix in ('torch', 'triton', 'vllm'))
    checks = dict(schema='bole.gdn3-timing-local-stdlib-checks/v1', AST=True, bytecode_compile=True,
        default_OFF_help=True, missing_execute_args_rejected=True, source_hash_negative=True,
        all384_frame_orders_balanced=True, descriptive_stats_pure_arithmetic=True,
        symmetric_clock_loop_control_flow_stub_only=True, exact_installed_primary_source_hashes=True,
        frozen_candidate_and_replay_sources_unchanged=True, tensor_runtime_imported=False,
        Torch_API_tested=False, NPU=False, actual_compile=False,
        actual_replay_success_unconfirmed=True, actual_timing=False, prepared_only=True,
        model_ready=False, formal_success=False)
    print(json.dumps(checks, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
