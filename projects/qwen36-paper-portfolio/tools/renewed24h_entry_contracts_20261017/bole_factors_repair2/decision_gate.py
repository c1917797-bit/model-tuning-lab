"""An actual successful saved-input diagnostic is mandatory, never template bool.

This gate only authorizes a bounded attribution question. It does not turn the
original recovered attention or whole-model numeric FAIL into a PASS.
"""
from pathlib import Path
ORIGINAL_SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-three-node-entry-new24h-v1-131-repair17/SOURCE_BOUND.json',bytes=59418,sha256='1a6a1e1b6be6afa5ca91bd2909bcdc5fe3a821b4968b5cf04f9e2b2752977552')
TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-r17-fa-input-diagnostic-owned-renew24h-v1-001/SOURCE_TEMPLATE.json',bytes=8698,sha256='66861d83a5c5329ec8a295c41d8e59d0e4244e28eb2cf86c42818776ee8885e6')
ACTUAL_SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-r17-fa-input-diagnostic-owned-renew24h-v1-001/SOURCE_BOUND.json',bytes=8318,sha256='0f32a5fef0f24e4e7fa116f72dd304a6d569cc998e11c918bd664a9a3d3609cb')
ACTUAL_OWNER=dict(path='/opt/host/vnf/austinov/run-bole-r17-fa-input-diagnostic-MAIN-RENEW24H_001/fa/consumer/RESULT.json',bytes=866,sha256='2d1859d31ede464e58331359535fef3937e9c8ac29926e8e3600bc64b22266b8')
ACTUAL_ATTR=dict(path='/opt/host/vnf/austinov/run-bole-r17-fa-input-diagnostic-MAIN-RENEW24H_001/fa/consumer/ATTRIBUTION.json',bytes=2307,sha256='aa4a9b99ad5c5daf6295581db4c12f4bf9312c02aa0e4539b28e72b52f22709f')
def consume(C,source_ref,owner_ref):
 C.need(source_ref==ACTUAL_SOURCE and owner_ref==ACTUAL_OWNER,'exact actual12c4 saved-input CPU attribution, not a synthetic or future PASS')
 m=C.obj(source_ref);prepared=C.obj(TEMPLATE)
 C.need(m['schema']=='bole.r17-fa-input-diagnostic-source/v1'and m['prepared_only']is False and
        m['prepared_template']==TEMPLATE and m['root']==prepared['root']and m['files']==prepared['files'],
        'actual exact reviewed CPU diagnostic source, not future placeholder')
 refs=[source_ref,TEMPLATE,ORIGINAL_SOURCE,*m['files'].values(),m['recovery_plan_ref']]
 owner=C.obj(owner_ref);refs.append(owner_ref)
 C.need(owner['schema']=='bole.r17-FA-input-diagnostic-owned/v1'and owner['source']==source_ref and
        owner['primary']is None and owner['secondary']==[]and owner['resource_release_verified']is True and
        owner['stopped_retained']is True and owner['Devices']==[]and owner['NPU']is False,
        'successful released original diagnostic CPU owner only')
 result=C.obj(owner['stage_result']);refs.append(owner['stage_result'])
 C.need(owner['stage_result']==ACTUAL_ATTR,'exact independently completed CPU diagnostic attribution')
 ir=C.ref(Path(owner_ref['path']).parent/'FINAL_INSPECT.json');inspected=C.obj(ir);refs.append(ir)
 C.need(inspected['Id']==owner['cid']and inspected['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and
        inspected['State']['Running']is False and inspected['State']['Pid']==0 and inspected['State']['ExitCode']==0 and
        not inspected.get('ExecIDs')and not inspected['State'].get('OOMKilled')and
        not inspected['HostConfig'].get('Devices')and not inspected['HostConfig'].get('DeviceRequests')and
        inspected['HostConfig']['ReadonlyRootfs']is True,'actual terminal readonly Devices[] released diagnostic CID')
 C.need(result['schema']=='bole.r17-independent-FA-input-attribution/v1'and result['source']==source_ref and
        result['original_source']==ORIGINAL_SOURCE and result['diagnostic_complete']is True and result['ranks_completed']==4 and
        result['qualified']is False and result['original_numeric_failures_unchanged']is True,'actual four-rank diagnostic complete, never numerical promotion')
 ranks=[]
 for rank,rr in enumerate(result['rank_reports']):
  report=C.obj(rr);refs.append(rr)
  C.need(report['schema']=='bole.r17.saved-FA-input-attribution/v1'and report['source']==source_ref and
         report['original_source']==ORIGINAL_SOURCE and report['rank']==rank and report['qualified']is False,
         'same-source actual diagnostic rank, ordered all four')
  C.need([r['layer']for r in report['rows']]==list(range(3,64,4)),'complete all16 actual FA layers')
  for row in report['rows']:
   C.need(set(row['input_bit_joins'])=={'q','kv_prefix_and_nodes','full_ancestor_padding_mask','scratch_to_actual','block_table'}and
          all(value is True for value in row['input_bit_joins'].values())and
          row['saved_native_inputs_vs_canonical_CPU64']['peak_abs']==0,
          'saved-input structure exact: any layout/mask/anchor defect must be fixed, not sent to NPU matrix')
  producer=C.obj(report['producer']);refs.extend([report['producer'],report['original_raw']])
  C.need(producer['source']==ORIGINAL_SOURCE and producer['rank']==rank and producer['primary']is None and producer['raw']==report['original_raw'],
         'original source-bound raw producer and immutable raw join')
  ranks.append(dict(rank=rank,raw=report['original_raw'],producer=report['producer'],diagnostic=rr))
 C.need(len(ranks)==4,'exact four-rank structural proof')
 unique={}
 for ref in refs:
  C.checked(ref)
  if ref['path']in unique:C.need(unique[ref['path']]==ref,'no conflicting exact readset')
  unique[ref['path']]=ref
 return dict(schema='bole.actual-saved-FA-factor-prerequisite/v1',diagnostic_source=source_ref,
   diagnostic_owner=owner_ref,ranks=ranks,readset=list(unique.values()),original_source=ORIGINAL_SOURCE,
   original_numeric_failures_unchanged=True,qualified=False)

def abi_provenance(C):
 """Reopen original model's exact qualified paged ABI route, no model PASS."""
 m=C.obj(ORIGINAL_SOURCE);p=m['component_refs']['paged'];s=C.obj(p['source'])
 C.need(p['source']==dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-paged-tree-owned-new24h-v1-118t-repair1/SOURCE_MANIFEST.json',bytes=25737,sha256='fdafbb8872ad9da1ff8150ddafa1e66acae3a80e05aa2b62bb04202da6e33faa'),'exact actual paged component route used by original R17')
 n=C.obj(p['numeric_owner']);stage=C.obj(n['result']);abi_ref=stage['actual_abi_ref'];abi=C.obj(abi_ref)
 C.need(n['source']==p['source']and n['primary']is None and n['secondary']==[]and n['stopped_retained']is True and
        stage['source']==p['source']and stage['primary']is None and stage['NPU']is True and
        abi['schema']=='bole.actual-FIA-installed-ABI/v115'and abi['source']==p['source']and abi['NPU']is False and abi['operator_executed']is False,
        'original completed actual paged stage used this installed no-op ABI; not model qualification')
 return dict(abi=abi_ref,header=abi['header_ref'],family=abi['schema_family'],
   readset=[ORIGINAL_SOURCE,p['source'],p['numeric_owner'],n['result'],abi_ref],qualified=False)
