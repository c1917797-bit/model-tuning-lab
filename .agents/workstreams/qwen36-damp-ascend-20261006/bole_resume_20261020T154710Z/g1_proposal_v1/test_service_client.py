"""Real HTTP client serialization against an in-process transport fixture."""
import json,tempfile,unittest
from pathlib import Path
import sourceio as C
import service_client as H
import g1_contract as G1

class Tests(unittest.TestCase):
 def run_client(self,*,include_tokens):
  class Tokenizer:
   vocab_size=1000
   def encode(self,text,add_special_tokens):return list(range(300))
  class Response:
   status=200
   def __init__(self,value):self.value=value
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,limit):return json.dumps(self.value).encode()
  calls=[]
  def transport(request,timeout):
   body=json.loads(request.data);calls.append(body)
   self.assertTrue(body['return_token_ids']);self.assertEqual(body['prompt'],list(range(131)))
   header={k.lower():v for k,v in request.header_items()}['x-request-id']
   choice=dict(text='transport fixture')
   if include_tokens:choice['token_ids']=list(range(body['max_tokens']))
   return Response(dict(id='cmpl-'+header,choices=[choice],usage=dict(prompt_tokens=131,completion_tokens=body['max_tokens'])))
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);sr=C.write(root/'SOURCE.json',dict(prepared_only=False,service_experiment=G1.SCOPE))
   result=H.run(sr,root,Tokenizer(),transport)
   self.assertEqual(result['schema'],G1.HTTP_SCHEMA)
   self.assertEqual([x['max_tokens']for x in calls],[2,2,1])
   self.assertEqual(C.obj(result['rows'][0]['response'])['choices'][0]['token_ids'],[0,1])
 def test_two_sequential_two_token_requests_and_native_retirement_barrier(self):
  self.run_client(include_tokens=True)
 def test_missing_actual_returned_token_ids_fails_closed(self):
  with self.assertRaisesRegex(ValueError,'actual returned generated token IDs'):
   self.run_client(include_tokens=False)

if __name__=='__main__':unittest.main()
