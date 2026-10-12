import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import numerical_state_loader as frozen
import numerical_state_loader_v2 as loader
import r24_state_diagnostic as controller


class R24Tests(unittest.TestCase):
    def test_registration_error_not_swallowed_as_exception(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"plugin.py"
            src="def register():\n    raise ValueError('registration-failed')\n"
            path.write_text(src)
            module=types.ModuleType("fixture")
            module.__file__=str(path)
            exec(compile(src,str(path),"exec"),module.__dict__)
            original=module.register
            with patch.object(frozen,"PLUGIN_SHA",hashlib.sha256(src.encode()).hexdigest()):
                adapter=loader.RuntimeAdapter(module,{})
                with patch("sys.stderr",new=io.StringIO()), self.assertRaises(SystemExit) as caught:
                    module.register()
                self.assertEqual(caught.exception.code,78)
                adapter.uninstall()
                self.assertIs(module.register,original)

    def test_registration_requires_each_actual_worker(self):
        with tempfile.TemporaryDirectory() as root:
            base=Path(root)
            (base/controller.ARM).mkdir()
            (base/controller.ARM/"worker-namespace-map.json").write_text(json.dumps(
                {"physical_npu_to_namespace_pid":dict(zip("0123",[11,12,13,14]))}))
            records=[dict(schema="hypic-state-observer-installed/v2",pid=p,
                manifest_sha256="hash",request_id="chatcmpl-"+controller.BODY_ID,
                kv_layer=controller.KV,gdn_layer=controller.GDN,
                plugin_sha256=frozen.PLUGIN_SHA) for p in (11,12,13,14)]
            q=types.SimpleNamespace(QROOT=base,name_for=lambda arm:"owned",
                write_json=lambda *args:None)
            with patch.object(controller,"digest",return_value="hash"):
                q.run=lambda *args:types.SimpleNamespace(stdout="\n".join(map(json.dumps,records)),stderr="")
                controller.registered_workers(q,"enabled")
                records.pop()
                with self.assertRaisesRegex(RuntimeError,"four worker"):
                    controller.registered_workers(q,"enabled")
                records.append(dict(records[0],pid=99))
                with self.assertRaisesRegex(RuntimeError,"four worker"):
                    controller.registered_workers(q,"enabled")

    def test_disabled_successor_does_not_import_support(self):
        import subprocess
        package=Path(__file__).resolve().parent/"state-observer-package-v2"
        env=dict(os.environ,PYTHONPATH=str(package),PYTHONDONTWRITEBYTECODE="1",
                 HYPIC_STATE_OBSERVER_ENABLE="0")
        code="import sys;import sitecustomize;assert 'numerical_state_loader_v2' not in sys.modules;assert 'hypic_vllm_ascend' not in sys.modules"
        r=subprocess.run([__import__("sys").executable,"-B","-c",code],env=env,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)


if __name__=="__main__":
    unittest.main()
