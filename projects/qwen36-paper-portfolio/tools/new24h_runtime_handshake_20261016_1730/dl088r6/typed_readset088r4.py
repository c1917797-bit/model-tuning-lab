"""Read-set of actual119/093/069 validate calls, NOT provenance recursion.

Opaque receipt/source JSON remains whole-file byte-bound. Unchanged validators
check role fields, full retained trees, live inspect and proc proof separately.
Embedded guest identities, supersedes, inverses are not host dependencies.
"""
import json
from pathlib import Path

class Reader:
 def __init__(self,C):self.C=C;self.refs={};self.notes=[]
 def add(self,r,role):
  self.C.need(type(r)is dict and set(r)=={'path','bytes','sha256'},'typed '+role+' Ref3')
  self.C.need(type(r['path'])is str and Path(r['path']).is_absolute(),'typed absolute '+role)
  self.C.checked(r);self.refs[json.dumps(r,sort_keys=True)]=r;return r
 def obj(self,r,role,schema=None):
  self.add(r,role);v=self.C.obj(r)
  if schema is not None:self.C.need(type(v)is dict and v.get('schema')==schema,'typed '+role+' schema')
  self.notes.append(dict(container=r,role=role));return v
 def helper(self,r,name):self.add(r,'executable helper');return self.C.load(r,name)
 def phase(self,p,version):
  self.C.need(type(p)is dict,'typed phase')
  self.obj(p['owner_ref'],'owner receipt');self.obj(p['tree_ref'],'tree snapshot')
  if version==119:
   for q in p['receipts']:
    self.obj(q['create_ref'],'create receipt');self.obj(q['cleanup_ref'],'cleanup receipt')
  else:
   for key in ('cleanup_refs','container_state_refs'):
    self.C.need(type(p[key])is list,'typed '+key)
    for r in p[key]:self.obj(r,key)
   if version==93:
    for r in p['create_refs']:self.obj(r,'create receipt')
   else:
    # Exact path reads in069.verify_terminal, not arbitrary nested Ref3s.
    names=('numeric/create-receipt.json','native/create-receipt.json')if Path(p['leaf']).name=='run-numeric16-MAIN-20261016-NEW24H-001'else('native/create-receipt.json',)
    for name in names:self.obj(self.C.ref(Path(p['leaf'])/name),'069 create receipt')
   if p.get('operation_terminal_ref')is not None:self.obj(p['operation_terminal_ref'],'operation terminal','ascend.actual-operation-terminal-observation/v1')
   elif version==93:
    q=self.obj(p['quiescent_ref'],'quiescent closure','deltalog.actual-quiescent-closure/v093')
    self.obj(q['operation_unavailable_ref'],'actual unavailable operations');self.obj(q['second_tree_ref'],'second tree snapshot')
 def evidence(self,r,version):
  tag={69:'v069',93:'v093',119:'v119'}[version]
  e=self.obj(r,'storage evidence '+tag,'deltalog.closed-phase-storage-evidence/'+tag)
  self.C.need(type(e.get('phases'))is list and len(e['phases'])==3,'typed three phases')
  self.obj(e['baseline_ledger_ref'],'baseline ledger');self.add(e['authority_ref'],'storage authority')
  for p in e['phases']:self.phase(p,version)
  return e

def readset(C,m,SOURCE119,api):
 R=Reader(C);s=R.obj(SOURCE119,'119 source','deltalog.closed-storage-source/v119')
 for r in s['files'].values():R.add(r,'reviewed119 source file')
 S=api(C,m)
 p=R.obj(S.PRIOR,'093 source','deltalog.closed-storage-source/v093')
 P=R.helper(p['files']['sealed_storage093.py'],'_088R4_readset093')
 R.helper(P.OLD,'_088R4_readset069')
 b11=R.obj(S.BASE,'ledger11');b7=R.obj(P.BASE,'ledger7')
 e119=R.evidence(m['storage_seal_evidence_ref'],119)
 C.need(e119['source_manifest_ref']==SOURCE119 and e119['prior_source_ref']==S.PRIOR and e119['prior_evidence_ref']==b11['sealed_evidence_ref'],'119 exact prior edges')
 e93=R.evidence(b11['sealed_evidence_ref'],93)
 R.obj(e93['source_manifest_ref'],'093 evidence source','deltalog.closed-storage-source/v093')
 C.need(e93['baseline_ledger_ref']==P.BASE and e93['prior_evidence_ref']==b7['sealed_evidence_ref'],'093 exact prior edges')
 e69=R.evidence(b7['sealed_evidence_ref'],69)
 # Actual prefix_chain/119.prior/storage_bridge.chain physical ledger reads.
 low=int(Path(e69['baseline_ledger_ref']['path']).name.split('.')[1]);high=int(Path(m['storage_seal_generation_ref']['path']).name.split('.')[1])
 C.need(0<=low<=7 and high==12,'reviewed retained ledger range')
 for n in range(low,high+1):R.obj(C.ref(S.ROOT/('STORAGE_LEDGER061.%d.json'%n)),'actual ledger chain')
 R.add(m['storage_seal_generation_ref'],'bound ledger12')
 return list(R.refs.values()),R.notes

def main():
 import argparse,sys
 p=argparse.ArgumentParser();p.add_argument('--source-ref',required=True);a=p.parse_args();sr=json.loads(a.source_ref)
 sys.path.insert(0,str(Path(sr['path']).parent));import bridge_io as C,storage_bridge119 as B
 refs,notes=readset(C,C.obj(sr),B.SOURCE119,B.api)
 print(json.dumps(dict(schema='deltalog.typed119-readset-probe/v088',absolute_refs_checked=len(refs),containers=notes,readset_only=True,numeric_qualified=False,no_write=True)))
if __name__=='__main__':main()
