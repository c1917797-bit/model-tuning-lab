"""Reopen actual component chains; never a whole-model certificate."""
PAGED_SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-paged-tree-owned-new24h-v1-118t-repair1/SOURCE_MANIFEST.json',bytes=25737,sha256='fdafbb8872ad9da1ff8150ddafa1e66acae3a80e05aa2b62bb04202da6e33faa')
GDN_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-tree-gdn-new24h-v1-112-repair4/SOURCE_TEMPLATE.json',bytes=8034,sha256='d65e72d203bee43d3f2457373e4376f757fdcfa7bc9cdbebb92ec2fb57a20075')
def same_body(a,b):return (a['bytes'],a['sha256'])==(b['bytes'],b['sha256'])
def consume(C,refs,*,gdn_math,paged_math):
 C.need(type(refs)is dict and set(refs)=={'gdn','paged'},'actual112full and actual118tR1 receipts required')
 result={}
 for kind,version,schema,count,math,leaf in(('gdn','v112','bole.tree-gdn-source/v112',72,gdn_math,'core112.py'),('paged','v118t','bole.tree-fa-owned-source/v118t',8,paged_math,'adapter.py')):
  p=refs[kind];C.need(set(p)=={'source','numeric_owner','consumer_owner'},'exact typed component Ref set')
  if kind=='paged':C.need(p['source']==PAGED_SOURCE,'exact actual supported pagedD256 source')
  source=C.obj(p['source']);C.need(source['schema']==schema and source['prepared_only']is False,'actual bound component source')
  if kind=='gdn':
   C.need(source['prepared_template']==GDN_TEMPLATE,'exact reviewed112R4 full template, not arbitrary same-math consumer')
   prepared=C.obj(GDN_TEMPLATE)
   C.need(source['files']==prepared['files']and source['root']==prepared['root'],'reviewed complete GDN producer/independent consumer readset')
  C.need(same_body(source['files'][leaf],math),'unchanged actual qualified math body')
  for ref in source['files'].values():C.checked(ref)
  no=C.obj(p['numeric_owner']);co=C.obj(p['consumer_owner'])
  C.need(no['schema']=='bole.tree-owned/'+version and no['source']==p['source']and no['primary']is None and no['secondary']==[]and no['stopped_retained']is True and no['physical']==[4]and no['logical']==0,'released actual singleton numeric owner')
  C.need(co['schema']=='bole.tree-owned-CPU/'+version and co['source']==p['source']and co['primary']is None and co['secondary']==[]and co['stopped_retained']is True and co['resource_release_verified']is True and co['numeric_owner']==p['numeric_owner']and co['stage_ref']==no['result'],'released same-source independent consumer owner')
  stage=C.obj(no['result']);v=C.obj(co['stage_result'])
  C.need(stage['schema']=='bole.tree-stage/'+version and stage['source']==p['source']and stage['primary']is None and stage['NPU']is True,'actual successful component producer')
  expected='bole.tree-independent/v112'if kind=='gdn'else'bole.paged-tree-independent/v118t'
  C.need(v['schema']==expected and v['source']==p['source']and v['pass_gate']is True and v['qualified']is False and v['model_ready']is False and len(v['rows'])==count,'actual independently consumed complete component matrix')
  if kind=='gdn':
   C.need(source['profile']=='full'and v['failures']==[]and all(r['passed']is True for r in v['rows']),'actual72 full GDN, not smoke6')
   C.need([r['raw']for r in v['rows']]==[r['raw']for r in stage['result']['rows']],'all72 actual producer/raw independent rows one-to-one')
  else:
   C.need(v['actual_capture']==stage['result']and v['component_pass']is True and all(r['metrics']['component_pass']is True for r in v['rows']),'actual8 paged oracle and commit checks')
  result[kind]=dict(source=p['source'],consumer=co['stage_result'])
  if kind=='paged':
   abi=C.obj(stage['actual_abi_ref']);capture=C.obj(stage['result'])
   C.need(abi['source']==p['source']and abi['schema']=='bole.actual-FIA-installed-ABI/v115'and
          abi['operator_executed']is False and capture['actual_abi_ref']==stage['actual_abi_ref'],
          'actual paged stage used exactly its source-bound installed ABI')
   result[kind]['actual_fia_abi']=stage['actual_abi_ref']
 return dict(schema='bole.actual-component-prerequisites/model-entry-v1',components=result,model_ready=False)
