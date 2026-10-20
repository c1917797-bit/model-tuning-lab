"""Offline exact-installed-source launch-grid regression; no NPU timing."""
import ast
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import unittest


class Controls(unittest.TestCase):
    def test_compiled_runner_requires_explicit_three_dimensions(self):
        path=Path(os.environ.get('BOLE_TIMING_COMPILED_SOURCE_PATH',str(
            Path(__file__).resolve().parents[3]/'bole_service_reference/installed/triton_compiled.py')))
        data=path.read_bytes()
        self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),
            (18714,'4e432986cb567b94d282f9a2c2f9911a6c3718337289fa936f240282a6a5d54b'))
        tree=ast.parse(data)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='CompiledKernel')
        fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='__getitem__')
        launches=[]
        scope=dict(driver=SimpleNamespace(active=SimpleNamespace(
            get_current_device=lambda:0,get_current_stream=lambda device:123)),
            CompiledKernel=SimpleNamespace(launch_enter_hook=None,launch_exit_hook=None))
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path)+'#offline-grid-control','exec'),scope)
        instance=SimpleNamespace(_init_handles=lambda:None,
            launch_metadata=lambda *args:None,run=lambda *args:launches.append(args),
            function='known-offline-placeholder',packed_metadata='known-offline-placeholder')
        args=('q','k','v','beta','p','ratio','state','output','updates')
        scope['__getitem__'](instance,(12,4,1))(*args)
        self.assertEqual(launches[0][:4],(12,4,1,123))
        self.assertEqual(launches[0][-9:],args)
        with self.assertRaises(IndexError):scope['__getitem__'](instance,(12,4))(*args)
        self.assertEqual(len(launches),1)


if __name__=='__main__':unittest.main()
