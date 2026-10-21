from pathlib import Path
P=Path(__file__).resolve().parent;OLD=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11')
s=(OLD/'prepare_g2_phases_v11.py').read_text();a=s.index('def need(');b=s.index('def inverse_host',a)
head='''"""New immutable lossless ACK wire/source12; default OFF, no resource action."""
import argparse,ast,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from g2_ack_proof import SOURCE
ROOT=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v12');OUT=ROOT.with_name('run-'+ROOT.name)
CHANGED=('g2_channel.py','g2_consumer.py','g2_finalize.py','g2_software_stages.py','g2_exact_controls.py','contract090.py','G2_STREAM_EDITS_V1.json')
'''
target=P/'prepare_g2_ack_v12.py'
assert not target.exists()
target.write_text(head+s[a:b]+(P/'PREPARE_V12_BODY.txt').read_text())
compile(target.read_bytes(),str(target),'exec',dont_inherit=True)
print('new preparer AST pass with exact original stdlib helpers and explicit private bootstrap')
