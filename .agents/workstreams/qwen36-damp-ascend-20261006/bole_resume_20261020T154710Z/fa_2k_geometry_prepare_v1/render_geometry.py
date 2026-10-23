"""Narrow reversible geometry layer; not a whole2k source/authority producer."""
from pathlib import Path
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
NAMES=('g3_fia_contract.py','service_fia.py','cache_registry.py','live_owner.py','model_entry.py','fa_prefill131r10.py','service_runner.py')
PARENT_IDENTITIES={"adapter.py":{"bytes":8622,"sha256":"37369161fbadad74e0f727c62e769069277d6f2696f7a8b2d88d67e92d93dc59"},"cache_registry.py":{"bytes":6547,"sha256":"befb35dbc49a2aaf740a1cf771568b145c131a516b1549938422a73c62e3a14c"},"core112.py":{"bytes":1443,"sha256":"b7e3f3a91889e98c54195a0c5f5eb2a4c6cdf8fc9c667ece26d7250b3e6eebe7"},"fa_prefill131r10.py":{"bytes":6174,"sha256":"9e3ba453f232faf0f9a36ae0f8b7c962d700c3115c98ba574b3d89a3d3650550"},"g2_numeric.py":{"bytes":24956,"sha256":"e2b66454b354175e1b00708ebbb70cd562a707acce34e8678ea581d7b6c2da91"},"g3_fia_contract.py":{"bytes":1334,"sha256":"dba6a3d251b74277af4679502bc8242da63027ff379f2cb9cb0ea4f355e98400"},"independent_model.py":{"bytes":14336,"sha256":"cdffc7dcb59b744788c2b736a5607e7218a9e13595b0f6a7d10f450a4fb6ad72"},"live_owner.py":{"bytes":11777,"sha256":"589aedf227797f8f08d3d2efc8c5236e768bdc5a2712f9068e44834952d7f6a8"},"model_entry.py":{"bytes":32009,"sha256":"8684325946bfb2d5cf1ab972c10be98f86c8b95605f676c709668277b360d0b9"},"oracle112.py":{"bytes":774,"sha256":"6ba6709289ee37cf54c13faf0bff43f361f06276049774bc3b1cd58456aa3a70"},"service_fia.py":{"bytes":3764,"sha256":"61203de14e3bd0680aeada666372200d776dd05869055bae15947132cf559a24"},"service_runner.py":{"bytes":51175,"sha256":"730ff8d03824d5da0cbe960eb1f2e47dddabae22b282b610e2deee6fb8119d6a"},"tp_consensus.py":{"bytes":5982,"sha256":"39334eaae500d515985ae5c775bb9bed90f20648d89a3ec78f382a1d0fafe73e"},"transaction.py":{"bytes":7968,"sha256":"44f1438febd6c4de3a59f6a5a10ceae6e1849b2d63eac411fc80e40ef88bde6c"}}

def need(v,s):
    if not v:raise ValueError(s)

def one(text,old,new):
    need(text.count(old)==1,'exact geometry source operand '+repr(old[:100]))
    return text.replace(old,new,1)

def adapt(original):
    files=dict(original);delta={}
    for name in NAMES:need(name in files,'actual source geometry dependency '+name)
    files['fa_native_geometry.py']=(HERE/'fa_native_geometry.py').read_bytes()
    domain=files['g3_fia_contract.py'].decode()
    domain=one(domain,'def shape(length):','def _legacy_shape(length):')
    domain=one(domain,'def allocation(*,table,physical_blocks,ratio,physical_size,kernel_size,use_hybrid):',
               'def _legacy_allocation(*,table,physical_blocks,ratio,physical_size,kernel_size,use_hybrid):')
    domain+='\n\ndef shape(length,geometry=None):\n    if type(length)is int and PREFIX<=length<=MAX_BEFORE:return _legacy_shape(length)\n    import fa_native_geometry as NATIVE\n    return NATIVE.shape(length,geometry)\n\ndef allocation(*,table,physical_blocks,ratio,physical_size,kernel_size,use_hybrid,geometry=None):\n    operands=dict(table=table,physical_blocks=physical_blocks,ratio=ratio,physical_size=physical_size,kernel_size=kernel_size,use_hybrid=use_hybrid)\n    if geometry is None:return _legacy_allocation(**operands)\n    import fa_native_geometry as NATIVE\n    return NATIVE.require(geometry).allocation(**operands)\n'
    files['g3_fia_contract.py']=domain.encode()
    fia=files['service_fia.py'].decode()
    fia=one(fia,'geometry=DOMAIN.shape(length)',"geometry=DOMAIN.shape(length,trial.get('native_geometry'))")
    # Receipt retains the existing flags/fields; only its explicit domain label
    # distinguishes actual registered2k from the unchanged legacy131 path.
    fia=one(fia,"scope='explicit fixed1024 C1/131..1153/one physical1536 allocation; every frame independently consumed',",
        "scope=('actual native2k fixed-allocation/private3 view; every frame independently consumed' if length>=2048 else 'explicit fixed1024 C1/131..1153/one physical1536 allocation; every frame independently consumed'),")
    files['service_fia.py']=fia.encode()
    registry=files['cache_registry.py'].decode()
    registry=one(registry,'forward_context,get_attention_context,refs,length,request_epoch=1):',
                         'forward_context,get_attention_context,refs,length,request_epoch=1,native_geometry=None):')
    registry=one(registry,"need(type(length)is int and length==131, 'first real model smoke uses exactly131 prefix tokens')",
        "need(type(length)is int and length in(131,2048), 'explicit original131 or native-observed2k prefix')\n if length==2048:\n  import fa_native_geometry as NG\n  NG.require_registration(native_geometry,runner,request_id,request,length,request_epoch)\n else:need(native_geometry is None,'original131 registration unchanged')")
    registry=one(registry,' return rows,dict(request=request,request_id=request_id,metadata=metadata,',
        " if length==2048:native_geometry.attach(rows)\n return rows,dict(request=request,request_id=request_id,metadata=metadata,")
    files['cache_registry.py']=registry.encode()
    owner=files['live_owner.py'].decode()
    owner=one(owner,'initial_owner.length==131 and','initial_owner.length in(131,2048) and')
    owner=one(owner,'self.version=0;self.length=131;','self.version=0;self.length=initial_owner.length;')
    owner=one(owner,'and 131<=length<=131+self.output_budget-2,',
        'and self.initial.length<=length<=self.initial.length+self.output_budget-2,')
    owner=one(owner,'ratio=table.blocks_per_phys_block,physical_size=table.physical_block_size,kernel_size=table.block_size,use_hybrid=table.use_hybrid_blocks)',
        "ratio=table.blocks_per_phys_block,physical_size=table.physical_block_size,kernel_size=table.block_size,use_hybrid=table.use_hybrid_blocks,geometry=binding.get('native_geometry'))")
    owner=one(owner," def check_fa(self,binding):\n  self.check_request();",
        " def check_fa(self,binding):\n  if self.initial.length==2048:\n   import fa_native_geometry as NG\n   NG.require(binding.get('native_geometry')).check(self.length)\n  self.check_request();")
    files['live_owner.py']=owner.encode()
    model=files['model_entry.py'].decode()
    model=one(model,"  owner=self.A.Owner(o.request,o.generation,o.slot,o.length,o.version)\n",
        "  if o.length>=2048:\n   import fa_native_geometry as NG\n   NG.require(b.get('native_geometry')).check(o.length)\n  owner=self.A.Owner(o.request,o.generation,o.slot,o.length,o.version)\n")
    needle='   trial=self.A.prepare'
    # Real source uses two-space indentation here; require the full exact call.
    needle='  trial=self.A.prepare(t,owner,query.reshape(3,6,256),key.reshape(3,1,256),value.reshape(3,1,256),compact_k,compact_v,tuple(range(pages)))'
    model=one(model,needle,needle+"\n  if o.length>=2048:trial['native_geometry']=b['native_geometry']")
    files['model_entry.py']=model.encode()
    mapping=files['fa_prefill131r10.py'].decode()
    mapping=one(mapping,"need(type(length)is int and length==131 and context.attn_metadata is metadata,'same actual first-prefill context')",
        "need(type(length)is int and length in(131,2048)and context.attn_metadata is metadata,'same actual native-prefill context')\n if length==2048:need(os.environ.get('BOLE_NATIVE_2K_GEOMETRY_ENABLE')=='1','native2k metadata observer default OFF')")
    files['fa_prefill131r10.py']=mapping.encode()
    runner=files['service_runner.py'].decode()
    runner=one(runner,"        ids, positions = kw['input_ids'], kw['positions']\n",
        "        ids, positions = kw['input_ids'], kw['positions']\n        native_fa_geometry = None\n        if tuple(ids.shape) == (2048,):\n            import fa_native_geometry as NG\n            native_fa_geometry = NG.bind_all(torch, C, m, source_ref, worker, inner,\n                request_id=kw['request_id'], request=kw['request'], metadata=kw['metadata'],\n                context=kw['forward_context'], get_attention_context=get_attention_context,\n                input_ids=ids, positions=positions, generation=state.generation)\n")
    runner=one(runner,'get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation)',
        'get_attention_context=get_attention_context, refs=refs, length=131, request_epoch=state.generation,native_geometry=native_fa_geometry)')
    # Other native2k input/GDN/whole-source contracts remain explicit blockers;
    # this component does not silently relax their independent131 assertions.
    files['service_runner.py']=runner.encode()
    for name,raw in files.items():
        if name.endswith('.py'):compile(raw,name,'exec')
        if original.get(name)!=raw:delta[name]=dict(before=original.get(name),after=raw)
    return dict(files=files,inverse_delta=delta,prepared_only=True,whole_source_ready=False,NPU=False)

def inverse(bundle):
    files=dict(bundle['files'])
    for name,d in bundle['inverse_delta'].items():
        need(files[name]==d['after'],'exact source geometry inverse after')
        if d['before']is None:files.pop(name)
        else:files[name]=d['before']
    return files

def read_parent():
    out={}
    for name,expected in PARENT_IDENTITIES.items():
        p=PARENT/name
        need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'actual frozen ordinary geometry parent')
        raw=p.read_bytes()
        need(len(raw)==expected['bytes']and hashlib.sha256(raw).hexdigest()==expected['sha256'],
             'complete pinned geometry parent '+name)
        out[name]=raw
    return out

if __name__=='__main__':
    if not sys.argv[1:]:print(json.dumps(dict(enabled=False,whole_source_ready=False,NPU=False)))
    else:
        need(sys.argv[1:]==['--check'],'explicit source-only --check')
        parent=read_parent();b=adapt(parent);need(inverse(b)==parent,'complete inverse')
        print(json.dumps(dict(changed=sorted(b['inverse_delta']),whole_source_ready=False,NPU=False),sort_keys=True))
