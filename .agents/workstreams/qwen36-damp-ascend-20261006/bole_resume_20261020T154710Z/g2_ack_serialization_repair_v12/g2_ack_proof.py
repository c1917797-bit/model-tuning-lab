import ast,hashlib
from pathlib import Path
SOURCE=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11/SOURCE_BOUND.json',bytes=824421,sha256='0cb8a78ee572778434b7b64f494fa42de46cdf4561c235effce3440a8b294f01')
ORIGINALS={'g2_consumer.py':(7521,'0ee132b1acecf59306d8d023ce83f39eebe9dafcbf283ac0ab91f995c95c6549'),'g2_channel.py':(10001,'30fc3445edda52940d398db81fa480ba55d30739953ea831d5060c0c3fe31387'),'g2_finalize.py':(17502,'4fc550421e3403e40243c33a048887be9e262b51be208e5338c3c92b9b855f88')}
OLD_LENGTH="len((json.dumps(ack,sort_keys=True)+'\\n').encode())<=3072"
NEW_LENGTH='len(CH.ack_bytes(ack))<=3072'
OLD_WRITE="    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\\n').encode()"
NEW_WRITE="    data=ack_bytes(value)if type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'else(json.dumps(value,sort_keys=True,allow_nan=False)+'\\n').encode()"
OLD_LOAD='def load(reference):\n    return json.loads(checked(reference).read_bytes())'
NEW_LOAD="""def load(reference):
    data=checked(reference).read_bytes();value=json.loads(data)
    need(not(type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'),
         'this source requires explicit canonical v3 ACK wire; no legacy size-cap bypass')
    return decode_ack(data)if type(value)is dict and value.get('schema')==ACK_WIRE_SCHEMA else value"""
OLD_FINAL="manifest=C.obj(event['manifest']);ack=C.obj(event['ack']);release=C.obj(event['release'])"
NEW_FINAL="manifest=C.obj(event['manifest']);ack=CH.load(event['ack']);release=C.obj(event['release'])"
CODEC_SHA256='75f7d6c38eed78f13a9f91c81ec7bc8c9b9e020142637d964d48ecabfb1ae92d'
def need(v,s):
 if not v:raise ValueError(s)
def inverse(name,raw):
 text=raw.decode()
 if name=='g2_consumer.py':
  need(text.count(NEW_LENGTH)==1,'sole consumer length expression');return text.replace(NEW_LENGTH,OLD_LENGTH,1).encode()
 if name=='g2_finalize.py':
  need(text.count(NEW_FINAL)==1,'sole finalizer ACK decode operand');return text.replace(NEW_FINAL,OLD_FINAL,1).encode()
 need(name=='g2_channel.py','only declared ACK actors')
 start=text.index('ACK_WIRE_SCHEMA=');end=text.index('def load(reference):',start)
 need(hashlib.sha256(text[start:end].encode()).hexdigest()==CODEC_SHA256 and text.count(NEW_WRITE)==1 and text.count(NEW_LOAD)==1,'exact reviewed codec and load/write dispatch')
 return(text[:start]+text[end:]).replace(NEW_WRITE,OLD_WRITE,1).replace(NEW_LOAD,OLD_LOAD,1).encode()
def check_pair(name,current,original):
 need((len(original),hashlib.sha256(original).hexdigest())==ORIGINALS[name],'whole actual v11 pin '+name)
 need(inverse(name,current)==original,'whole ACK-only exact inverse '+name)
 return dict(before_bytes=len(original),before_sha256=hashlib.sha256(original).hexdigest(),after_bytes=len(current),after_sha256=hashlib.sha256(current).hexdigest(),whole_inverse=True)
def original_assignment(raw):
 tree=ast.parse(raw);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 nodes=[n for n in ast.walk(main)if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='ack']
 need(len(nodes)==1,'one actual complete ACK constructor');return nodes[0]
def reconstruct(original,scope):
 need((len(original),hashlib.sha256(original).hexdigest())==ORIGINALS['g2_consumer.py'],'complete source-owned original before extraction')
 node=original_assignment(original);env=dict(scope);env['__builtins__']={'dict':dict}
 exec(compile(ast.Module(body=[node],type_ignores=[]),SOURCE['path']+'#original-ACK-constructor','exec'),env)
 return env['ack']
def preserved_functions(current,original):
 def functions(raw):
  out={}
  def walk(body,prefix=''):
   for n in body:
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
     out[prefix+n.name]=ast.dump(n,include_attributes=False);walk(n.body,prefix+n.name+'.')
  walk(ast.parse(raw).body);return out
 a=functions(original);b=functions(current)
 need(all(a[k]==b[k]for k in a if k not in('load','write')),'all original contract/validator/full Sender AST unchanged')
 return[k for k in a if k not in('load','write')]
def fixture(path):
 import base64,json
 value=json.loads(Path(path).read_bytes());need(value['schema']=='bole.actual-v11-ACK-serialization-failure-fixture/v1'and value['source_ref']==SOURCE and value['numerical_model_qualification']is False,'actual failure fixture, never qualification')
 records={}
 for name,row in value['records'].items():
  data=base64.b64decode(row['base64'],validate=True);r=row['actual_ref'];need((len(data),hashlib.sha256(data).hexdigest())==(r['bytes'],r['sha256']),'whole actual diagnostic copy '+name);records[name]=data
 return value,records
def actual_step(fixture_value,records):
 import json
 old=records['SOURCE/g2_consumer.py'];tree=ast.parse(old)
 node=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='STEP_GATES'for t in n.targets))
 env={'dict':dict};exec(compile(ast.Module(body=[node],type_ignores=[]),SOURCE['path']+'#actual-STEP-GATES','exec'),env)
 f=json.loads(records['STREAM/FRAME-RANK-0-000001.json']);ch=json.loads(records['STREAM/CHANNEL.json'])
 rr=fixture_value['records']['STREAM/REPORT-RANK-0-000001.json']['actual_ref'];ref=lambda n:fixture_value['records'][n]['actual_ref']
 cs=dict(path=str(Path(SOURCE['path']).parent/'g2_consumer.py'),bytes=ORIGINALS['g2_consumer.py'][0],sha256=ORIGINALS['g2_consumer.py'][1])
 ack=reconstruct(old,dict(sr=SOURCE,m=dict(stream_consumer_source=cs),cr=ref('STREAM/CHANNEL.json'),channel=ch,rank=0,sequence=1,kind='step',v=f,previous=[ref('STREAM/ACK-RANK-%d-000000.json'%i)for i in range(4)],error=None,STEP_GATES=env['STEP_GATES'],digest=rr['sha256'],report_ref=rr))
 return ack,f,json.loads(records['STREAM/REPORT-RANK-0-000001.json'])
