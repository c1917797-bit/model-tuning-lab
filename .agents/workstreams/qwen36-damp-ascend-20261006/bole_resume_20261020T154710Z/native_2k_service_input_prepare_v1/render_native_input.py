"""Reversible native2048 callback: explicit qualifiers8/160/1024; formal1024."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
GEOMETRY={'bytes':10907,'sha256':'3c7b6059320206757be8fbadcba70f701781579e84e975aa460bf1ffab6e7382'}
SNAPSHOT={'bytes':4765,'sha256':'1f4e0462a4e1b0fe6af9397e800e750738d88397cda7f02e74846a424be1e3eb'}
G2={'bytes':1746,'sha256':'f9e545876a0e922f22408d88c997195abd3ffb4f023b9b2954e168988f47de0a'}
def need(v,s):
 if not v:raise ValueError(s)
def once(text,old,new):
 need(text.count(old)==1,'exact native2048 callback operand '+repr(old[:100]))
 return text.replace(old,new,1)
DOMAIN="""        scope=m['performance_profile']['scope']
        E.need(type(scope.get('input_tokens'))is int and scope['input_tokens']==2048 and
            type(scope.get('output_tokens'))is int,
            'source-reviewed actual2048 callback and typed actual output budget')
        qualification=m.get('fastpath_numeric_qualification')
        if qualification is None:
            E.need(scope['output_tokens']==1024 and
                os.environ.get('BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE')in(None,'','0'),
                'formal performance remains fixed1024 and is not a numerical qualifier')
        else:
            E.need(type(qualification)is dict and scope['output_tokens']in(8,160,1024) and
                os.environ.get('BOLE_FASTPATH_NUMERIC_QUALIFICATION_ENABLE')=='1',
                'explicit diagnostic8/160/1024 qualification flag and budget')
            expected_qualification=dict(schema='bole.fastpath-numeric-qualification-profile/v1',
                enabled=True,input_tokens=2048,output_tokens=scope['output_tokens'],generations=2,
                logical_frame_cap=384*2**20,independent_reference=True,formal_performance=False)
            E.need(set(qualification)==set(expected_qualification)and all(
                type(qualification[k])is type(v)and qualification[k]==v
                for k,v in expected_qualification.items()),
                'same complete source-pinned qualification and actual performance profile budget')
        native_input=kw['native_input']
        E.need(type(native_input)is dict and native_input['actual_token_ids']is ids and
            native_input['request_id']==kw['request_id'] and
            native_input['sources']=={k:refs[k]for k in('runner','base_runner','qwen35','qwen_next')} and
            native_input['no_mm_features']is True and native_input['no_soft_prompt']is True and
            native_input['actual_input_mode']in('native-token-ids','native-text-embeddings'),
            'same source-proved actual native input object before target forward')
        E.need(native_input['actual_CPU_token_ids']==native_input['request_prompt_token_ids']==
            list(kw['request'].prompt_token_ids) and len(native_input['actual_CPU_token_ids'])==2048,
            'retained native CPU IDs and the same strong request full2048 prefix')
        native_fa_geometry = None
        if tuple(ids.shape) == (2048,):
            import fa_native_geometry as NG
            E.need(C.ref(NG.__file__)==m['files']['fa_native_geometry.py'],
                'actual source-reviewed live native geometry module')
"""
OLD_GEOMETRY="""        native_fa_geometry = None
        if tuple(ids.shape) == (2048,):
            import fa_native_geometry as NG
"""
def adapt(original):
 out=dict(original);need('service_runner.py'in out,'actual native callback source')
 text=out['service_runner.py'].decode()
 need("G2.capacity(owner.length,len(pages),geometry=b.get('native_geometry'))"in text,
  'fixed composition: actual geometry then snapshot capacity then native callback')
 text=once(text,OLD_GEOMETRY,DOMAIN)
 text=once(text,"        E.need(ids.dtype == torch.int32 and tuple(ids.shape) == (131,), 'actual native 131-token input')",
  "        E.need(isinstance(ids,torch.Tensor) and ids.device.type=='npu' and ids.dtype == torch.int32 and tuple(ids.shape) == (2048,), 'actual native source-proved 2048-token input')")
 text=once(text,"        expected = list(range(131)) if axes == 1 else [list(range(131))]*3",
  "        expected = list(range(2048)) if axes == 1 else [list(range(2048))]*3")
 text=once(text,"        E.need((axes == 1 or tuple(positions.shape) == (3, 131)) and",
  "        E.need(isinstance(positions,torch.Tensor) and positions.device.type=='npu' and positions.dtype==torch.int64 and\n            tuple(positions.shape)in((2048,),(3,2048)) and")
 text=once(text,'rank=group.rank_in_group, length=131, request_epoch=state.generation)',
  'rank=group.rank_in_group, length=2048, request_epoch=state.generation)')
 text=once(text,'get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation,native_geometry=native_fa_geometry)',
  'get_attention_context=get_attention_context, refs=refs, length=2048, request_epoch=state.generation,native_geometry=native_fa_geometry)')
 text=once(text,'        E.need(isinstance(root_hidden, torch.Tensor) and tuple(root_hidden.shape) == (131, 5120),',
  "        E.need(isinstance(root_hidden, torch.Tensor) and root_hidden.device.type=='npu' and\n            root_hidden.dtype==torch.bfloat16 and tuple(root_hidden.shape) == (2048, 5120),")
 text=once(text,"        owner = E.Owner(window['request_id'], state.generation, window['slot'], 131, 0)",
  "        owner = E.Owner(window['request_id'], state.generation, window['slot'], 2048, 0)")
 out['service_runner.py']=text.encode();compile(out['service_runner.py'],'service_runner.py','exec')
 return dict(files=out,inverse_delta={'service_runner.py':dict(before=original['service_runner.py'],after=out['service_runner.py'])},
  prepared_only=True,whole_source_ready=False,NPU=False)
def inverse(bundle):
 out=dict(bundle['files']);d=bundle['inverse_delta']['service_runner.py']
 need(out['service_runner.py']==d['after'],'exact native2048 callback inverse')
 out['service_runner.py']=d['before'];return out
def checked(path,identity):
 p=Path(path);need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary actual source')
 raw=p.read_bytes();need(len(raw)==identity['bytes']and hashlib.sha256(raw).hexdigest()==identity['sha256'],'pinned preparation source '+p.name)
 return raw
def private(path,identity):
 raw=checked(path,identity);n={'__file__':str(path),'__name__':'_native2k_private_renderer'}
 exec(compile(raw,str(path),'exec'),n);return n
def actual_chain():
 g=private(HERE.parent/'fa_2k_geometry_prepare_v1/render_geometry.py',GEOMETRY)
 s=private(HERE.parent/'snapshot_2k_capacity_prepare_v1/render_capacity.py',SNAPSHOT)
 original=g['read_parent']();original['g2_contract.py']=checked(PARENT/'g2_contract.py',G2)
 geometry=g['adapt'](original);snapshot=s['adapt'](geometry['files'])
 return original,geometry,snapshot,g,s
if __name__=='__main__':
 if not sys.argv[1:]:print(json.dumps(dict(enabled=False,whole_source_ready=False,NPU=False)))
 else:
  need(sys.argv[1:]==['--check'],'explicit source-only --check')
  p,g,s,G,S=actual_chain();b=adapt(s['files'])
  need(inverse(b)==s['files']and G['inverse'](dict(g,files=S['inverse'](dict(s,files=inverse(b)))))==p,'entire actual composition inverse')
  print(json.dumps(dict(changed=list(b['inverse_delta']),whole_source_ready=False,NPU=False)))
