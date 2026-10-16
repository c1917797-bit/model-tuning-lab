"""Model and worker share exactly the same source-bound052 receipt reader."""
import importlib.util
import owner_overlay as C
MODE='actual052-split-scale-diagnostic-only'
def api(m):
 r=m.get('split_qualification_api_ref')
 C.need(type(r)is dict,'reviewed052 shared qualification API pending')
 plugin=C.obj(m['plugin_source'])
 C.need(plugin['files']['qwen36_deltalog_service/split_qualification.py']==r,'same exact model/worker reader')
 p=C.obj_file(r);s=importlib.util.spec_from_file_location('_actual053_052_qualification',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def consume(m):
 C.need(m.get('admission_mode')==MODE and m.get('prepared_only')is False,'actual052 explicit optin binding')
 return api(m).admit(C,m)
def closure(m):
 refs=[m['split_qualification_api_ref'],m['bridge024_source_ref'],m['bridge024_owner_ref'],m['reviewed_domain_template_ref'],m['component_cpu_owner_ref'],m['production_build_ref'],m['split_kernel_source_ref'],m['library_ref'],m['debug_library']]
 owner=C.obj(m['bridge024_owner_ref']);prod=C.obj(owner['result']);pair=C.obj(owner['independent_consumer']);cpu=C.obj(m['component_cpu_owner_ref'])
 refs.extend([owner['result'],owner['independent_consumer'],prod['plan'],cpu['result'],pair['original_strict_consumer'],pair['domain_consumer']])
 refs.extend(pair['initial_anchor_refs'].values())
 refs.extend(C.obj(m['bridge024_source_ref'])['files'].values())
 return refs
