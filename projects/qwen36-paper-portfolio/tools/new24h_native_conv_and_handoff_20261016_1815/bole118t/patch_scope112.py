"""Compose exact112 physical4 with the unchanged069 safety transform."""
import ast,hashlib,inspect
from pathlib import Path
ADAPTER_SHA='a9f510a683a3cad1b22161107c2d5e6beaeab6f6df50612fbc92b939e5a64cc2'
ORIGINAL_SHA='432f5cc1613ef5faf43aca11e68c17c3957919d45978cdff04003b82598a5157'
PATCH_SHA='932d1c97ec8123aab4dff43b339d886a47e4f5e9e1676f65be9ec94341e0d9cc'
PAIRS=(('if physical!=5:','if physical!=4:'),('physical5','physical4'),('return (5,)','return (4,)'),("+1]!='5'","+1]!='4'"))
def original(raw):
 assert hashlib.sha256(raw).hexdigest()==ADAPTER_SHA,'exact reviewed112 physical4 adapter'
 result=raw
 for a,b in reversed(PAIRS):result=result.replace(b.encode(),a.encode())
 assert hashlib.sha256(result).hexdigest()==ORIGINAL_SHA,'whole physical4-to5 inverse equals actual069 source'
 return result
def install(adapter,helper,old_patch):
 raw=Path(adapter.__file__).read_bytes();base=original(raw)
 assert hashlib.sha256(Path(old_patch.__file__).read_bytes()).hexdigest()==PATCH_SHA and old_patch.OLD_SHA==ORIGINAL_SHA,'exact original safety patch; no OLD_SHA override'
 changed=old_patch.transform(base) # retains original SHA, anchor, inverse, AST
 for a,b in PAIRS:changed=changed.replace(a,b)
 inverse=changed
 for a,b in reversed(PAIRS):inverse=inverse.replace(b,a)
 assert inverse==old_patch.transform(base),'combined whole-source reversible safety+physical mapping'
 tree=ast.parse(changed);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='protected_observation')
 ns=dict(adapter.__dict__,_adapter_top_guard=helper);code=ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[]));exec(compile(code,str(adapter.__file__)+':registered-top-child028-physical4','exec'),ns);adapter.protected_observation=ns['protected_observation']
 return dict(original_sha256=ORIGINAL_SHA,actual_adapter_sha256=ADAPTER_SHA,original_patch_sha256=PATCH_SHA,mechanical_inverse=True,protected_observer002_unchanged=True)
