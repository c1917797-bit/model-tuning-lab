"""Typed actual closure and reuse of original unchanged sealed storage policy."""
import importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def load(ref,name,H):return H.load(ref,name)
def target_closure(sr):
 import host as H,bridge_io as C
 m=C.source(sr);H.need(m.get('bound')is True and m['producer_source']==m['original_source_ref'],'bound new consumer / original target split')
 H.need('recovery_refs'not in m,'no embedded readset array in manifest')
 R=H.load(m['files']['readset127.py'],'_127_streamed_readset')
 d=m['recovery_readset_index'];H.need(d['index_ref']['path']==str(P/'RECOVERY_READSET127.jsonl'),'same-source exact streamed index')
 refs=R.Readset([sr,m['prepared_template'],*m['files'].values(),d['index_ref']],d,H.validate_ref_streamed)
 for r in refs:H.validate_ref_streamed(r)
 return P,m,C,refs,Path(m['original_source_ref']['path']).parent
def original_policy(m):
 import host as H
 original=H.obj(m['original_source_ref']);root=Path(original['root']);sys.path.insert(0,str(root))
 h=H.load(original['files']['host.py'],'_127_original_policy_host')
 _,original,C,refs,_=h.target_closure(m['original_source_ref'])
 # Accounting provenance is the original immutable storage policy/template;
 # CPU execution provenance is separately and explicitly this new source.
 return H,original,C,refs
def storage(m):
 H,original,C,refs=original_policy(m)
 S=H.load(original['files']['storage061.py'],'_127_actual_storage')
 B=H.load(original['files']['storage_bridge088r6.py'],'_127_actual_storage_bridge')
 seal=B.install(C,original,S)
 return S,seal
