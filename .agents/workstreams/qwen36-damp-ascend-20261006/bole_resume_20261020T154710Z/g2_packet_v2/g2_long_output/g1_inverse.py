"""Exact G2 lifecycle layer before the original G1-v2 historical inverse."""
import hashlib
import importlib.util
from pathlib import Path
import sourceio as C
P=Path(__file__).resolve().parent


def reverse(name,text):
    m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));prior=m['g2_predecessor'];parent=C.obj(prior['source'])
    current=m['files'][name]
    C.need(dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest())==
        {k:current[k]for k in('bytes','sha256')},'exact actual G2 historical operand bytes')
    proof=C.obj(m['files']['G2_STREAM_EDITS_V1.json'])
    C.need(proof['baseline']==prior['source'],'exact G2 inverse baseline')
    row=proof['files'].get(name)
    if row is not None:
        C.need(row['after']==current and row['before']==parent['files'][name]and
            len(row['edits'])==1 and row['edits'][0]['after']==text,'whole exact G2 inverse delta')
        text=row['edits'][0]['before']
    C.need(text==C.checked(parent['files'][name]).read_text(),'exact G1-v2 bytes before historical inverse')
    reference=parent['files']['g1_inverse.py'];path=C.checked(reference)
    spec=importlib.util.spec_from_file_location('_exact_parent_g1_historical_inverse',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.reverse(name,text)


def previous_text(path):
    path=Path(path).resolve();C.need(path.parent==P,'only current source-owned top-level inverse input')
    return reverse(path.name,path.read_text())
