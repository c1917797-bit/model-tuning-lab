"""Remove exact G3 lifecycle/domain delta before the unchanged G2→G1→V6 inverses."""
import hashlib,importlib.util
from pathlib import Path
import sourceio as C
P=Path(__file__).resolve().parent


def reverse(name,text):
 m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));prior=m['g3_predecessor'];parent=C.obj(prior['source'])
 current=m['files'][name]
 C.need(len(text.encode())==current['bytes']and hashlib.sha256(text.encode()).hexdigest()==current['sha256'],
    'exact actual G3 historical operand bytes')
 proof=C.obj(m['files']['G3_LONG_EDITS_V1.json']);C.need(proof['baseline']==prior['source'],'exact G3 inverse baseline')
 row=proof['files'].get(name)
 if row is not None:
  C.need(row['after']==current and row['before']==parent['files'][name]and len(row['edits'])==1 and row['edits'][0]['after']==text,'whole exact declared G3 inverse')
  text=row['edits'][0]['before']
 C.need(text==C.checked(parent['files'][name]).read_text(),'exact G2 bytes before its original inverse stack')
 spec=importlib.util.spec_from_file_location('_exact_G2_historical_inverse',C.checked(parent['files']['g1_inverse.py']))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module.reverse(name,text)


def previous_text(path):
 path=Path(path).resolve();C.need(path.parent==P,'only source-owned current historical file')
 return reverse(path.name,path.read_text())
