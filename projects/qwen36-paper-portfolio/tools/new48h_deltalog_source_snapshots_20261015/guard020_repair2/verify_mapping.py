import hashlib,json,pathlib,sys
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from mapping_rules import restore
def undo_input_repair(n,text):
 if n=='host.py':
  newer=(P.parent/'deltalog-regression137-guard-new48h-20261015-020-physical4-repair1'/'host.py').read_text(encoding='utf8')
  prior_start="                        need(len(proof)==1 and dv['logical']==0"
  original=next(line for line in newer.splitlines(True)if line.startswith(prior_start))
  start=text.index("                        need(dv['logical']==0")
  end=text.index("                        cmd=proof[0]['argv']",start)
  text=text[:start]+original+text[end:]
  text=text.replace('MAIN-020-physical4-repair2','MAIN-020-physical4-repair1')
  old='MAIN-020-physical4-repair1';assert text.count(old)==1;text=text.replace(old,'MAIN-020-physical4')
 if n=='bind_source.py':
  addition=' from input_contract import require\n require(old,C.checked);require(m,C.checked)\n'
  assert text.count(addition)==1;text=text.replace(addition,'')
 if n=='io_contract.py':
  addition=" contract=load(m['files']['input_contract.py'],'_exact_regression_input_contract')\n contract.require(m,checked)\n"
  assert text.count(addition)==1;text=text.replace(addition,'')
 return text
def verify():
 b=(P/'ORIGINAL020_SOURCE.json').read_bytes();assert len(b)==57688 and hashlib.sha256(b).hexdigest()=='0278e763414c3740d031f67c4b59093fde78cd6607b61846396ded115fc89228';m=json.loads(b);rows=[]
 for n,r in m['files'].items():
  if not n.endswith('.py'):continue
  new=(P/n).read_bytes();assert b'\r'not in new;back=restore(n,undo_input_repair(n,new.decode())).encode();assert len(back)==r['bytes']and hashlib.sha256(back).hexdigest()==r['sha256'],n;rows.append(dict(file=n,unchanged=new==back,exact_inverse=True))
 assert "n['physical']==[5]"in(P/'io_contract.py').read_text(),'historical007 actual physical5 receipt must remain5'
 assert 'canary==[4.,5.]'in(P/'producer.py').read_text(),'canary arithmetic unchanged'
 return dict(schema='deltalog.physical4-resource-only-inverse/v1',base_source_sha256=hashlib.sha256(b).hexdigest(),rows=rows,physical=4,logical=0,NPU=False,math_changed=False)
if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
