"""Offline reflection regression only; no tensor runtime or device operation."""
import hashlib
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest

P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_reflection_timing',P.parent/'gdn_timing/time_gdn.py')
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)


def ref(p):
    b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


class Controls(unittest.TestCase):
    def test_unregistered_dynamic_class_source_and_negative_method(self):
        text='class AscendBackend:\n'+''.join(' def '+name+'(self):pass\n' for name in ('__init__','parse_options','pack_metadata','add_stages'))
        namespace={'__name__':'_unregistered_ascend_reflection_fixture'}
        exec(compile(text,str(__file__),'exec'),namespace)
        cls=namespace['AscendBackend'];backend=cls()
        with self.assertRaises(TypeError):inspect.getsourcefile(cls)
        H=SimpleNamespace(need=D.need);C=SimpleNamespace(ref=ref)
        manifest={'runtime_sources':{'ascend_compiler':ref(__file__)}}
        D.backend_source(H,C,manifest,backend)
        for method in ('__init__','parse_options','pack_metadata','add_stages'):
            original=getattr(cls,method)
            setattr(cls,method,lambda self:None)
            with self.assertRaises(ValueError):D.backend_source(H,C,manifest,backend)
            setattr(cls,method,original)
        with self.assertRaises(ValueError):D.backend_source(H,C,{'runtime_sources':{'ascend_compiler':ref(D.__file__)}},backend)
        with self.assertRaises(ValueError):D.backend_source(H,C,manifest,object())


if __name__=='__main__':unittest.main()
