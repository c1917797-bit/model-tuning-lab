"""Call ONLY after actual singleton set_device/canary/MAIN_ARM. No conv execution."""
import importlib,json,sys
def record(t,C,m,*,arm_verified):
 C.need(arm_verified is True,'actual original owner ARM required before HAL-dependent import')
 expected=m['conv_gdn_ref'];C.checked(expected)
 gdn=importlib.import_module('vllm_ascend.ops.gdn')
 C.need(C.ref(gdn.__file__)==expected,'normal installed GDN source, no fake architecture/module')
 family=t.ops._C_ascend.npu_causal_conv1d_custom._schemas
 C.need(isinstance(family,dict)and bool(family),'actual nonempty native conv overload family')
 rows={name:dict(schema=str(schema),name=schema.name,argument_names=[a.name for a in schema.arguments],is_mutable=schema.is_mutable)for name,schema in family.items()}
 return dict(schema='bole.actual-device-conv-ABI/v118',source=m['_actual_source'],plan=m['_plan_ref'],gdn_ref=expected,actual_schema_family=rows,torch_python_ref=C.ref(t.__file__),torch_npu_python_ref=C.ref(sys.modules['torch_npu'].__file__),NPUallocated=True,NPU=True,logical=0,physical=4,actual_MAIN_ARM=True,operator_executed=False,qualified=False,model_ready=False,calibration_pending=True)

def validate(v,sr):
 if not(v['schema']=='bole.actual-device-conv-ABI/v118'and v['source']==sr and v['NPUallocated']is True and v['NPU']is True and v['actual_MAIN_ARM']is True and v['logical']==0 and v['physical']==4 and v['operator_executed']is False and v['qualified']is False and v['calibration_pending']is True):raise ValueError('only actual admitted device schema capture, not native conv proof')
 if not isinstance(v['actual_schema_family'],dict)or not v['actual_schema_family']:raise ValueError('actual overload family required')
 return v
