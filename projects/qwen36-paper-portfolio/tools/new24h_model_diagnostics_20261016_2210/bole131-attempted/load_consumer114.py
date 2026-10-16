"""Independent load observation check, not BOLE/numeric qualification."""
def need(v,s):
 if not v:raise ValueError(s)
def expected_loaded(name):
 need(name.startswith('mtp.'),'actual MTP index name');name='model.'+name[4:]
 for old,new in(('.q_proj.','.qkv_proj.'),('.k_proj.','.qkv_proj.'),('.v_proj.','.qkv_proj.'),('.gate_proj.','.gate_up_proj.'),('.up_proj.','.gate_up_proj.')):name=name.replace(old,new)
 return name
def consume(rows,expected_names,source,observer):
 need(type(expected_names)is list and len(expected_names)==15 and len(set(expected_names))==15,'actual checkpoint exact15 MTP names')
 need(len(rows)==4 and all(type(r['pid'])is int and r['pid']>0 for r in rows)and len({r['pid']for r in rows})==4,'actual four native MTP loader processes')
 expected=set(expected_names);loaded={expected_loaded(n)for n in expected}
 for r in rows:
  need(r['schema']=='bole.native-MTP-load-observation/v111'and r['actual_original_source']==source and r['observer_source']==observer and r['actual_class']=='vllm.model_executor.models.qwen3_5_mtp.Qwen3_5MTP'and r['BOLE']is False and r['forward_modified']is False,'actual source-bound load-only receipt')
  actual=r['input_mtp_weights'];need(len(actual)==15 and {x['name']for x in actual}==expected,'all exact checkpoint MTP input keys, not only15 arbitrary names')
  need(all(type(x['numel'])is int and x['numel']>0 and type(x['shape'])is list and all(type(s)is int and s>0 for s in x['shape'])for x in actual),'actual nonempty weight geometries')
  need(loaded<=set(r['loaded_names']),'all source-defined packed MTP names actually returned loaded')
 return dict(schema='bole.native-MTP-load-consumption/v114',actual_workers=4,actual_input_mtp_names=sorted(expected),actual_packed_loaded_names=sorted(loaded),loaded_MTP_observed=True,BOLE=False,model_numerical_qualified=False)
