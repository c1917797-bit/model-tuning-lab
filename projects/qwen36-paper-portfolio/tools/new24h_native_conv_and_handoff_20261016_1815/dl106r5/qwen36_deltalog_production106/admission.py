"""Production actual evidence adapter; no oldPF qualification alias."""
from pathlib import Path
import qualification106 as Q
need=Q.need;ref=Q.ref;obj=Q.obj;obj_file=Q.checked
def consume(sr,qref):
 q=Q.qualify(qref,sr);m=Q.source(sr)
 return dict(qualification_ref=qref,component_source=q['component_source'],model_source=q['model_source'],execution_admitted=True),m
