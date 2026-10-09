"""Actual protocol positive/negative stdlib checks, not a fabricated service pass."""
import json,unittest
from bench import StreamState
class Protocol(unittest.TestCase):
 def event(self,ids,prompt=None,finish=None,usage=None,server="cmpl-real"):
  choice=dict(index=0,text="",token_ids=ids,finish_reason=finish)
  if prompt is not None:choice["prompt_token_ids"]=prompt
  return json.dumps(dict(id=server,choices=[choice],usage=usage)).encode()
 def test_original_token_ID_stream(self):
  s=StreamState([1,2],2);s.feed(self.event([3],[1,2]),1)
  s.feed(self.event([4],finish="length",usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4)),2)
  s.feed(b"[DONE]",3);s.finish_check();self.assertEqual(s.tokens,[3,4])
 def test_foreign_server_ID_rejected(self):
  s=StreamState([1],2);s.feed(self.event([3],[1]),1)
  with self.assertRaises(ValueError):s.feed(self.event([4],server="changed"),2)
 def test_actual_prompt_mismatch_rejected(self):
  s=StreamState([1],2)
  with self.assertRaises(ValueError):s.feed(self.event([3],[9]),1)
 def test_non_ID_or_post_done_stream_rejected(self):
  s=StreamState([1],2)
  with self.assertRaises(ValueError):s.feed(json.dumps(dict(id="real",choices=[dict(index=0,text="text",token_ids=None)])).encode(),1)
  s.feed(b"[DONE]",2)
  with self.assertRaises(ValueError):s.feed(self.event([3]),3)
if __name__=="__main__":unittest.main()
