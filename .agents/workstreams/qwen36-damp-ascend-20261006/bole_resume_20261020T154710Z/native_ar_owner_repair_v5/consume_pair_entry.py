"""Devices[] metadata-only adapter over the frozen pair run/math/identity reader.

The only function replacement is image_and_common, in this private source-bound
module instance, with identity-checked restoration. Initial environment evidence
is never promoted to current os.environ or matched common plugin effects.
"""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys


def declared_plugins(C,reference):
    tree=ast.parse(C.checked(reference).read_bytes());values=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='update':
            for keyword in node.keywords:
                if keyword.arg=='VLLM_PLUGINS':values.append(ast.literal_eval(keyword.value))
    C.need(len(values)==1 and type(values[0])is str,'one exact source-declared in-process plugin update')
    return values[0].split(',')


def initial_profile(C,reference,bundle,variant):
    p=C.obj(reference);guest=bundle['frontend_binding']['guest'];host=bundle['frontend_binding']['host']
    allowed=[guest,{k:host[k]for k in('pid','start_ticks','cgroup')}]
    C.need(p['schema']==('bole.actual-host-launch-profile-observation/v1'if variant=='BOLE'else'bole.actual-pair-launch-profile/v1')and p['variant']==variant and
           p['identity']in allowed and type(p['common_environment'])is dict and
           p['credential_values_retained']is False and p['plugin_effect_classification_performed']is False,
           'actual owned initial-only frontend environment, not current environment')
    if variant=='BOLE':
        C.need((reference['bytes'],reference['sha256'])==(3344,'519e2f3879acfcb6ee5c4802e47fff2d7f1925dfb1022e1026cd986275b77a78')and
               p['source_before']==p['source_after']==p['source']==bundle['source']and
               p['owned_cid']==bundle['frontend_binding']['owned_cid']and
               p['NSpid']==bundle['frontend_binding']['NSpid'], 'exact actual historical ON initial observation/source/host lifetime')
        C.checked(p['collector']);inspect=C.obj(p['container_inspection'])
        C.need(type(inspect)is list and len(inspect)==1 and inspect[0]['Id']==p['owned_cid'], 'actual initial observation inspected CID')
    return p


def metadata_join(C,x,pair,ar,on,m):
    # Repeat the frozen common-image/argv/runtime/model checks explicitly; no
    # mathematical or lifecycle guard is replaced by this metadata adapter.
    inspections=[C.obj(b['docker_inspect_ref'])for b in(ar,on)]
    C.need(all(type(v)is list and len(v)==1 and v[0]['Image']==m['expected_image_id']==C.IMAGE for v in inspections),
           'actual unmodified same-image inspect arrays')
    for b,v in zip((ar,on),inspections):
        C.need(v[0]['Id']==b['frontend_binding']['owned_cid'],'actual variant inspect/frontend CID')
    commands=[C.obj(b['server_command_ref'])for b in(ar,on)]
    P=C.load(m['files']['pair_contract.py'],'_ar_metadata_pair_contract')
    C.need(commands[0]['source']==pair['source']and commands[1]['source']==m['BOLE_source_ref']and
           commands[0]['argv']==P.native_argv(commands[1]['argv'])==m['native_server_argv'],
           'actual same argv except exactly declared native MTP delta')
    donor=C.obj(m['BOLE_source_ref'])
    common,observer_only=C.runtime_partition(m,donor)
    for r in m['runtime_sources'].values():C.checked(r)
    C.need(ar['model_manifest_ref']==on['model_manifest_ref']==m['model_manifest_ref'],'same shared model/tokenizer manifest')
    shared=C.obj(m['model_manifest_ref'])
    C.need(shared['schema']=='bole.actual-model-tokenizer-file-manifest/v1'and
           shared['model_root']==str(C.GUEST_MODEL)and len(shared['files'])==29,'same complete actual guest model')
    for r in shared['files']:C.checked(r)
    profiles=[initial_profile(C,b['launch_profile_ref'],b,v)for b,v in zip((ar,on),('native_AR','BOLE'))]
    C.need(profiles[0]['source']==pair['source']and profiles[0]['collector']==m['files']['launch_profile.py'],
           'actual exact AR initial collector; historical ON collector remains its genuine separate source')
    C.need(profiles[0]['common_environment']==profiles[1]['common_environment'],
           'same actually recorded exec-initial framework environment')
    ar_plugins=declared_plugins(C,m['files']['native_ar_server.py'])
    on_plugins=declared_plugins(C,donor['files']['server090.py'])
    C.need(ar_plugins==['ascend','bole_native_ar_pair']and on_plugins==['ascend','dense_opportunity090',
        'bole_mtp_load_receipt111','bole_three_node131'],'exact separately declared source plugin updates')
    # BOLE full independent pass + actual load receipts are a separate execution
    # join, not proof that omitted plugin effects are equal.
    _,owner,bundle,report=C.g1_pass(m['BOLE_source_ref'],x['G1_owner'],x['G1_bundle'],x['G1_independent'])
    C.need(on['ranks']==bundle['ranks']and on['snapshots']==bundle['snapshots'],'same qualified actual BOLE executions')
    load_refs=owner['summary']['MTP_load_receipts'];C.need(len(load_refs)==4,'four actual ON MTP load receipts')
    for r in load_refs:C.obj(r)
    C.obj(owner['summary']['MTP_load'])
    C.need(len(ar['snapshot_refs'])==4,'four actual AR plugin callback load snapshots')
    for rank,r in enumerate(ar['snapshot_refs']):
        snapshot=C.obj(r)
        C.need(snapshot in ar['snapshots']and snapshot['source_ref']==pair['source']and snapshot['rank']==rank and
               snapshot['actual_allow_hf32']is False and snapshot['registry']['counts']==dict(gdn=48,fa=16)and
               snapshot['registry']['worker_source']==m['runtime_sources']['worker'],
               'actual native plugin callback/after-load source join')
    return dict(schema='bole.initial-environment-plus-source-plugin-join/v1',
        actual_image_id=C.IMAGE,installed_runtime_sources_equal=False,
        common_installed_runtime_sources_equal=True,common_runtime_key_count=len(common),
        observer_only_runtime_sources=observer_only,observer_only_runtime_sources_checked_separately=True,
        runtime_source_map_relation='unchanged actual ON common map plus explicit observer-only dependency',
        common_argv_equal_after_declared_delta=True,
        actual_exec_initial_framework_environment_equal=True,actual_current_os_environ_observed=False,
        environment_semantics='Linux /proc/PID/environ initial exec environment only; excludes in-process updates',
        initial_environment_refs=[b['launch_profile_ref']for b in(ar,on)],
        initial_observed_plugins=[p['plugins']for p in profiles],
        source_declared_in_process_plugins=[ar_plugins,on_plugins],
        source_plugin_declarations=[m['files']['native_ar_server.py'],donor['files']['server090.py']],
        actual_plugin_execution_join=dict(native_AR_snapshots=ar['snapshot_refs'],BOLE_independent=x['G1_independent'],
            BOLE_MTP_loads=load_refs,source_declared_update_is_current_environment_read=False),
        common_plugin_effects_independently_reviewed=False,matched_common_plugin_effects_gate_pending=True,
        declared_algorithm_delta=dict(native_AR=dict(BOLE=False,speculative_config=None),
            BOLE=dict(BOLE=True,speculative_config=dict(method='mtp',num_speculative_tokens=8))),same_kernel_route_assumed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--owner-inputs-ref');p.add_argument('--pair-inputs-ref');p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"model_ready":false}');return 0
    if not all((a.owner_inputs_ref,a.pair_inputs_ref,a.output)):p.error('exact source-bound owner/pair inputs and output required')
    root=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('_native_ar_consumer_common',str(root/'ar_owner_common.py'))
    C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    ir=json.loads(a.owner_inputs_ref);x=C.obj(ir)
    C.need(C.ref(__file__)==x['files']['consume_pair_entry.py']and C.ref(C.__file__)==x['files']['ar_owner_common.py'],
           'exact reviewed metadata-only adapter source')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'
        and not list(Path('/dev').glob('davinci[0-9]*')),'actual independent Devices[] consumer')
    m,on,_=C.readset(x,installed=True)
    sys.path.insert(0,m['root']);C.load(m['files']['pair_contract.py'],'pair_contract')
    frozen=C.load(m['files']['consume_pair.py'],'_ar_frozen_complete_pair_consumer')
    original=frozen.image_and_common
    def bound(pair,ar,on,m):return metadata_join(C,x,pair,ar,on,m)
    C.need(frozen.run.__globals__ is vars(frozen)and original.__globals__ is vars(frozen),
           'private complete frozen reader instance, no foreign namespace')
    frozen.image_and_common=bound
    try:
        import torch
        result=frozen.run(torch,x['AR_source'],json.loads(a.pair_inputs_ref),a.output)
        C.need(result['bounded_pair_pass']is False and result['matched_common_plugin_effects_gate_pending']is True,
               'metadata adaptation cannot promote common effects qualification')
    finally:
        C.need(frozen.image_and_common is bound,'no foreign reader function replacement')
        frozen.image_and_common=original
        C.need(frozen.image_and_common is original,'exact function object inverse')
    return 0


if __name__=='__main__':raise SystemExit(main())
