"""Typed predecessor join; consumes a real completed device ABI, never invents it."""
def join(C,*,template,device_owner_ref,consumer_owner_ref):
 owner=C.obj(device_owner_ref);sr=owner['source'];source=C.obj(sr)
 C.need(source['prepared_template']==template and source['prepared_only']is False,'reviewed actual ABI-only source')
 C.need(owner['schema']=='bole.tree-owned/v118a'and owner['primary']is None and owner['secondary']==[]and owner['stopped_retained']is True and owner['physical']==[4]and owner['logical']==0,'actual released singleton ABI owner')
 outer=C.obj(owner['result']);C.need(outer['schema']=='bole.tree-stage/v118a'and outer['source']==sr and outer['primary']is None and outer['NPU']is True,'same-source original device stage')
 abi_ref=outer['result'];abi=C.obj(abi_ref)
 C.need(abi['schema']=='bole.actual-device-conv-ABI/v118'and abi['source']==sr and abi['plan']==outer['plan']and abi['NPUallocated']is True and abi['operator_executed']is False and abi['qualified']is False and abi['calibration_pending']is True and abi['actual_MAIN_ARM']is True,'actual device allocated schema receipt, not conv numeric')
 co=C.obj(consumer_owner_ref);C.need(co['schema']=='bole.tree-owned-CPU/v118a'and co['source']==sr and co['primary']is None and co['secondary']==[]and co['resource_release_verified']is True and co['numeric_owner']==device_owner_ref and co['stage_ref']==owner['result'],'actual released independent ABI consumer')
 result=C.obj(co['stage_result']);C.need(result['schema']=='bole.conv-ABI-independent/v118a'and result['source']==sr and result['actual_device_conv_abi_ref']==abi_ref and result['pass_gate']is True and result['schema_capture_complete']is True and result['qualified']is False,'actual schema consumption completeness only')
 return abi_ref,abi
def overload(torch,abi):
 family=torch.ops._C_ascend.npu_causal_conv1d_custom._schemas
 C={k:dict(schema=str(v),name=v.name,argument_names=[a.name for a in v.arguments],is_mutable=v.is_mutable)for k,v in family.items()}
 if C!=abi['actual_schema_family']or ''not in C:raise ValueError('actual full overload family differs; review required')
 names=C['']['argument_names']
 if len(names)!=12 or names[3:]!=['conv_state','bias_opt','query_start_loc_opt','cache_indices_opt','initial_state_mode_opt','num_accepted_tokens_opt','activation_mode','pad_slot_id','run_mode']:raise ValueError('native positional/keyword ABI differs from actual GDN call')
 return torch.ops._C_ascend.npu_causal_conv1d_custom.default
