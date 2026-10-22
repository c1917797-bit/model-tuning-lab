"""Actual prepared test-source imports in an explicit virtual source fixture. No binding or NPU."""
import argparse
import hashlib
import importlib.abc
import importlib.util
import json
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);mode=p.add_mutually_exclusive_group()
    mode.add_argument('--check',action='store_true');mode.add_argument('--reconstruct-only',action='store_true');a=p.parse_args()
    if not(a.check or a.reconstruct_only):
        print(json.dumps(dict(enabled=False,NPU=False,same_image=False)));return
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import qualification_short_prepare as Q
    b=Q.render();Q.inverse(b)
    root=Path(b['manifest']['root']);virtual={str(root/n):raw for n,raw in b['files'].items()}
    # This is a synthetic software fixture, NOT a physical SOURCE_BOUND,
    # authority or approval. prepared_only remains True.
    virtual[str(root/'SOURCE_BOUND.json')]=(json.dumps(b['manifest'],sort_keys=True)+'\n').encode()
    original_read=Path.read_bytes;original_text=Path.read_text
    original_open=Path.open
    original_stat=Path.stat;original_isfile=Path.is_file;original_exists=Path.exists
    def read(path,*args,**kw):
        key=str(path)
        return virtual[key]if key in virtual else original_read(path,*args,**kw)
    def text(path,encoding=None,errors=None):
        if str(path)in virtual:return virtual[str(path)].decode(encoding or'utf8',errors or'strict')
        return original_text(path,encoding=encoding,errors=errors)
    def opened(path,mode='r',*args,**kw):
        if str(path)not in virtual:return original_open(path,mode,*args,**kw)
        if any(x in mode for x in 'wax+'):raise ValueError('virtual source fixture is read-only')
        raw=virtual[str(path)]
        return io.BytesIO(raw)if'b'in mode else io.StringIO(raw.decode(kw.get('encoding')or'utf8'))
    def stat(path,*args,**kw):
        if str(path)not in virtual:return original_stat(path,*args,**kw)
        return types.SimpleNamespace(st_dev=999,st_ino=sorted(virtual).index(str(path))+1,
            st_size=len(virtual[str(path)]),st_mtime_ns=0,st_ctime_ns=0,
            st_mode=0o100600,st_mtime=0,st_ctime=0,st_atime=0)
    names={n[:-3]for n in b['files']if n.endswith('.py')and'/'not in n}
    class Loader(importlib.abc.MetaPathFinder,importlib.abc.Loader):
        def find_spec(self,fullname,path=None,target=None):
            if fullname in names:return importlib.util.spec_from_loader(fullname,self,origin=str(root/(fullname+'.py')))
        def create_module(self,spec):return None
        def exec_module(self,module):
            name=module.__name__+'.py';module.__file__=str(root/name)
            exec(compile(b['files'][name],module.__file__,'exec'),module.__dict__)
    saved={n:sys.modules[n]for n in names if n in sys.modules}
    for n in saved:sys.modules.pop(n)
    loader=Loader();sys.meta_path.insert(0,loader)
    try:
        with patch.object(Path,'read_bytes',read),patch.object(Path,'read_text',text),patch.object(Path,'open',opened),\
             patch.object(Path,'stat',stat),\
             patch.object(Path,'is_file',lambda s:True if str(s)in virtual else original_isfile(s)),\
             patch.object(Path,'exists',lambda s:True if str(s)in virtual else original_exists(s)):
            import qualification_source_validate as V
            cases=V.enumerate_tests(b['manifest'])
            suite=unittest.TestSuite()
            for file in V.TEST_FILES:suite.addTests(unittest.defaultTestLoader.loadTestsFromName(file[:-3]))
            if suite.countTestCases()!=V.TEST_COUNT:raise ValueError('exact actual imported test count')
            result=unittest.TextTestRunner(verbosity=2).run(suite)if a.check else unittest.TestResult()
            # Authority missing and prepared state MUST still fail admission.
            rejected=False
            try:V.require_fastpath_admission(b['manifest'])
            except ValueError:rejected=True
            if not rejected:raise ValueError('virtual source must never receive runtime admission')
            # Exercise the deployed, source-owned renderer import path, not
            # just the preparation-side Q object. Parent namespace must be
            # isolated and restored, including the actual FAST policy object.
            import qualification_short_prepare as LOADED
            import validated_performance_policy as POLICY
            before={n:sys.modules.get(n)for n in names}
            rebuilt=LOADED.render(base_root=Path(b['manifest']['qualification_preparation_root']),
                permit_materialized=True,
                parent_pair_preparation_root=Path(b['manifest']['qualification_parent_pair_preparation_root']),
                historical_short_source_ref=b['manifest']['qualification_historical_short_source'],
                authority_ref=None,parent_preparation_readset=b['manifest']['qualification_parent_preparation_readset'])
            if rebuilt['manifest']!=b['manifest']or rebuilt['files']!=b['files']:
                raise ValueError('actual source-owned renderer must reconstruct every prepared source byte')
            if any(sys.modules.get(n)is not module for n,module in before.items()):
                raise ValueError('parent renderer polluted source-owned worker namespace')
            if sys.modules['validated_performance_policy']is not POLICY:
                raise ValueError('actual source-owned FAST worker policy was replaced')
            print(json.dumps(dict(schema='bole.prepared-qualification-source-import-controls/v1',
                tests=result.testsRun,skipped=len(result.skipped),all_tests_passed=result.wasSuccessful()if a.check else None,
                actual_test_source_bytes=True,synthetic_source_fixture_only=True,prepared_only=True,
                physical_SOURCE_BOUND_created=False,authority_created=False,same_image=False,
                NPU=False,numerical_qualified=False,performance_admitted=False,
                runtime_admission_rejected=rejected,source_owned_reconstruction_passed=True,
                parent_namespace_restored=True,cases=cases),sort_keys=True))
            if not result.wasSuccessful()or result.skipped:raise SystemExit(1)
    finally:
        sys.meta_path.remove(loader)
        for n in names:sys.modules.pop(n,None)
        sys.modules.update(saved)

if __name__=='__main__':main()
