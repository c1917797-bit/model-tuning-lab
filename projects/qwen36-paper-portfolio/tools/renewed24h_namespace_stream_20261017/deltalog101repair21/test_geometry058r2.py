import ast,importlib.util,json,pathlib,sys,types,unittest
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));import client,consume
class Geometry(unittest.TestCase):
 def test_actual_client_request_matrix(self):
  tree=ast.parse((P/'client.py').read_bytes());loops=[n for n in ast.walk(tree)if isinstance(n,ast.For)and isinstance(n.iter,ast.Tuple)]
  values=[ast.literal_eval(x.iter)for x in loops if all(isinstance(a,ast.Tuple)for a in x.iter.elts)]
  self.assertEqual(values,[(('native-postprepare',2048),)])
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='C'and n.func.attr=='request_once']
  self.assertEqual(len(calls),1)
  stop=[n for n in main.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Attribute)and n.value.func.attr=='need'and n.value.args and isinstance(n.value.args[0],ast.Constant)and n.value.args[0].value is False]
  self.assertEqual(len(stop),1);self.assertGreater(stop[0].lineno,calls[0].lineno)
  self.assertEqual(len([n for n in ast.walk(main)if isinstance(n,ast.For)]),1)
 def test_actual_response_exact_input_usage(self):
  req=dict(request_id='x',payload=dict(n=1,max_tokens=10,min_tokens=10,ignore_eos=True,echo=False,return_token_ids=True,temperature=0,seed=0,prompt=[17]*2048))
  def wire(n):return ('data: '+json.dumps(dict(id='cmpl-x',choices=[dict(index=0,token_ids=list(range(10)),finish_reason='length')]))+'\n\ndata: '+json.dumps(dict(id='cmpl-x',choices=[],usage=dict(prompt_tokens=n,completion_tokens=10)))+'\n\ndata: [DONE]\n\n').encode()
  self.assertEqual(consume.response(req,wire(2048))['prompt_tokens'],2048)
  with self.assertRaises(ValueError):consume.response(req,wire(129))
 def test_predecessor_exact_actual139_refs(self):
  import packet_predecessor as B
  self.assertEqual(B.TEMPLATE_REF['bytes'],70479);self.assertEqual(B.TEMPLATE_REF['sha256'],'ea0d4d756025ac203f12f1c0265e5bc679eb652f04508c000cd16b47aa404b89');self.assertTrue(B.FILES);self.assertIn('consumer088.py',B.FILES)
if __name__=='__main__':unittest.main()
