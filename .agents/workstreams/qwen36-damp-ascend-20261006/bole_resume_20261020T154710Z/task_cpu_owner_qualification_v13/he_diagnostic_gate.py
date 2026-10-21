"""Exact actual HEv3 facts, source/retirement/readback; never a qualification."""
from pathlib import Path
import owner_common as C


def readset(owner_ref,independent_ref):
    refs={}
    def add(r):
        a=C.ref(C.checked(r));refs[a['path']]=a;return a
    def obj(r):add(r);return C.obj(r)
    er=add(C.ref(Path(__file__).resolve().parent/'HE_DIAGNOSTIC_EXPECTED.json'))
    C.need(er['sha256']==C.HE_DIAGNOSTIC_EXPECTED_SHA,'frozen actual HEv3 diagnostic/source inventory')
    e=obj(er);a=e['actual_refs'];C.need(add(owner_ref)==a['owner/RESULT.json']and add(independent_ref)==a['HE_RUNTIME_DIAGNOSTIC_V3_READBACK.json'],
        'exact complete actual source-owned diagnostic3 and original independent readback')
    for r in a.values():add(r)
    owner=obj(owner_ref);ind=obj(independent_ref);x=obj(owner['inputs_ref'])
    C.need(owner['schema']=='bole.actual-HE-runtime-diagnostic-owner/v3'and owner['diagnostic_observation_complete']is True
        and owner['primary']is None and owner['secondary']==[]and owner['source_input_before']
        and owner['source_input_before']==owner['source_input_after']and owner['private_namespace_restored_by_identity']is True
        and owner['full_software_qualification_accepted']is False and x['diagnostic_revision']==3 and x['image_id']==C.IMAGE,
        'actual retained/source-equal complete diagnostic, never full qualification')
    C.need(set(x['files'])==set(e['source_files']),'whole actual15-source diagnostic closure')
    for name,r in x['files'].items():
        row=add(r);want=e['source_files'][name]
        C.need((row['bytes'],row['sha256'])==(want['bytes'],want['sha256'])
            and owner['source_input_before'].get(row['path'])==row['sha256'],'actual byteexact diagnostic source '+name)
    s=owner['summary'];ob=obj(s['observation_ref']);namespace=obj(s['net_namespace_ref']);release=obj(s['release_ref'])
    C.need(ind['schema']=='bole.independent-HE-runtime-isolation-diagnostic/v3'and add(ind['owner_ref'])==add(owner_ref)
        and ind['actual_diagnostic_evidence_joined']is True and ind['actual_host_guest_netns_evidence_joined']is True
        and ind['inherited_owner_lock_evidence_joined']is True and ind['observation']==ob
        and ind['network_safety_accepted']is False and ind['full_software_qualification_accepted']is False
        and ob['original_runtime_guard']['called']is True and ob['original_runtime_guard']['passed']is False
        and ob['conditions']==dict(ASCEND_VISIBLE_DEVICES_empty=True,HOME_tmp=True,sys_class_interfaces_loopback_only=False)
        and namespace['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False)
        and release['stopped']is True and release['retained']is True and release['errors']==[],
        'original actual failed name-only guard and actual private guest facts/retirement, no posthoc score')
    copy=obj(a['uapi/COPY.json']);C.need(copy['schema']=='bole.actual-same-image-linux-uapi-copy/v1'
        and copy['stopped_readonly_source']is True and copy['container']==obj(s['owned_ref'])['cid']and obj(s['owned_ref'])['image']==C.IMAGE,
        'actual copied public UAPI from the stopped same-image qualified diagnostic container')
    return list(refs.values())
