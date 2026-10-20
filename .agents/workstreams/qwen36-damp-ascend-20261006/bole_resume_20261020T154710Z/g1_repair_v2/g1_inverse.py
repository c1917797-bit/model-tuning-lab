"""Reverse only the exact declared G1 lifecycle delta to passed V6 bytes.

Historical mathematical/ownership assertions run after this extra layer, then
use their existing inverse ledgers unchanged. Unknown current bytes fail first.
"""
import hashlib
import json
from pathlib import Path
import sourceio as C

P=Path(__file__).resolve().parent


def digest(text):
    data=text.encode('utf8')
    return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def reverse(name,text):
    m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'))
    reference=m['files']['G1_LIFECYCLE_EDITS_V1.json']
    proof=C.obj(reference)
    C.need(proof['schema']=='bole.exact-G1-lifecycle-inverse-to-passed-V6/v1' and
           proof['baseline_v6']==m['g1_inverse']['baseline_v6'] and
           proof['failed_g1_v1']==m['g1_inverse']['failed_g1_v1'],
           'exact source-bound G1 inverse layer lineage')
    parent=C.obj(proof['baseline_v6'])
    C.need(name in parent['files'] and name in m['files'],
           'only exact existing V6 files have a historical G1 inverse')
    current=m['files'][name]
    C.need(digest(text)=={k:current[k]for k in('bytes','sha256')},
           'current source differs from declared G1 lifecycle bytes')
    row=proof['files'].get(name)
    if row is not None:
        C.need(row['after']==current and row['before']==parent['files'][name] and
               len(row['edits'])==1 and text==row['edits'][0]['after'],
               'exact complete G1 before/after source join')
        text=row['edits'][0]['before']
    expected=parent['files'][name]
    C.need(digest(text)=={k:expected[k]for k in('bytes','sha256')},
           'exact passed V6 bytes restored before historical inverse checks')
    return text


def previous_text(path):
    path=Path(path).resolve()
    C.need(path.parent==P,'only source-owned top-level historical file')
    return reverse(path.name,path.read_text())
