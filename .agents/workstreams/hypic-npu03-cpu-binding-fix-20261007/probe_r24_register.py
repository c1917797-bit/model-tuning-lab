import importlib,importlib.metadata,importlib.machinery,json,sys
import numerical_state_loader as old
import numerical_state_loader_v2 as new
assert importlib.machinery.PathFinder.find_spec(old.TARGET) is None
try:
 old.RegistrationFinder({}).find_spec(old.TARGET)
except ImportError:
 print("OLD_FINDER_FAIL_REPRODUCED",flush=True)
else:
 raise AssertionError("old failure did not reproduce")
config=dict(raw_root="/tmp/no-capture",request_id="probe",kv_layer="kv",gdn_layer="gdn",manifest_sha256="1"*64)
hook=new.RegistrationFinder(config)
sys.meta_path.insert(0,hook)
ep=next(x for x in importlib.metadata.entry_points(group="vllm.general_plugins") if x.name=="hypic_vllm_ascend")
func=ep.load()
assert hook.adapter is not None
assert func is hook.adapter.replacement
module=sys.modules[old.TARGET]
original=hook.adapter.original
func()
assert hook.adapter.observer is not None
print("REAL_REGISTER_AND_OBSERVER_INSTALLED",flush=True)
hook.uninstall()
assert module.register is original and hook not in sys.meta_path
print(json.dumps(dict(new_entrypoint_load=True,rollback=True,source=module.__file__,version=module.__version__,register_called=True,devices_used=False)),flush=True)
