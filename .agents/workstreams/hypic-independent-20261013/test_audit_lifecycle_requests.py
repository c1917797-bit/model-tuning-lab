import copy,unittest
from audit_lifecycle_requests import audit_lifecycle_requests
class Tests(unittest.TestCase):
    def fixture(self,stage="enabled"):
        payloads=[dict(model="qwen3.5",prompt=list(range(3+i)),temperature=0,seed=0,max_tokens=1 if i==0 else 64,ignore_eos=True)for i in range(3)]
        records=[dict(index=i,payload=copy.deepcopy(p),response=dict(id="r"+str(i),usage=dict(prompt_tokens=len(p["prompt"]),completion_tokens=p["max_tokens"]),choices=[dict(text="ok")]))for i,p in enumerate(payloads)]
        semantic=dict(event="lifecycle-semantic",stage=stage,payload={"model":"qwen3.5","messages":[{"role":"user","content":"Calculate 2 + 2. Reply with only the integer."}],"temperature":0,"seed":0,"max_tokens":32,"chat_template_kwargs":{"enable_thinking":False}},
            response=dict(id="semantic",choices=[dict(message=dict(content="4"))],usage=dict(completion_tokens=1)))
        journal=[dict(r,event="response")for r in copy.deepcopy(records)]+[copy.deepcopy(semantic)]
        return records,journal,semantic,stage,payloads
    def test_three_stages(self):
        for s in ("disabled","enabled","uninstalled"):self.assertTrue(audit_lifecycle_requests(*self.fixture(s))["lifecycle_requests_verified"])
    def reject(self,mutate):
        a=self.fixture();mutate(*a)
        with self.assertRaises(ValueError):audit_lifecycle_requests(*a)
    def test_payload_drift(self):self.reject(lambda r,j,s,stage,p:r[1]["payload"]["prompt"].append(99))
    def test_missing_response(self):self.reject(lambda r,j,s,stage,p:r.pop())
    def test_reordered(self):self.reject(lambda r,j,s,stage,p:r.reverse())
    def test_journal_drift(self):self.reject(lambda r,j,s,stage,p:j.pop(0))
    def test_duplicate_id(self):
        def mutate(r,j,s,stage,p):
            r[1]["response"]["id"]="r0";j[1]["response"]["id"]="r0"
        self.reject(mutate)
    def test_truncated_private(self):
        def mutate(r,j,s,stage,p):
            r[1]["response"]["usage"]["completion_tokens"]=63;j[1]["response"]["usage"]["completion_tokens"]=63
        self.reject(mutate)
    def test_prompt_accounting(self):
        def mutate(r,j,s,stage,p):
            r[0]["response"]["usage"]["prompt_tokens"]=2;j[0]["response"]["usage"]["prompt_tokens"]=2
        self.reject(mutate)
    def test_boolean_token_usage(self):
        def mutate(r,j,s,stage,p):
            r[0]["response"]["usage"]["completion_tokens"]=True;j[0]["response"]["usage"]["completion_tokens"]=True
        self.reject(mutate)
    def test_semantic_wrong(self):self.reject(lambda r,j,s,stage,p:s["response"]["choices"][0]["message"].update(content="5"))
    def test_semantic_stage_drift(self):self.reject(lambda r,j,s,stage,p:s.update(stage="disabled"))
    def test_semantic_thinking_drift(self):self.reject(lambda r,j,s,stage,p:s["payload"]["chat_template_kwargs"].update(enable_thinking=True))
    def test_semantic_id_collision(self):self.reject(lambda r,j,s,stage,p:s["response"].update(id="r0"))
    def test_semantic_journal_missing(self):self.reject(lambda r,j,s,stage,p:j.pop())
    def test_semantic_usage_overbound(self):self.reject(lambda r,j,s,stage,p:s["response"]["usage"].update(completion_tokens=33))
    def test_semantic_consistent_wrong_answer(self):
        a=self.fixture();a[2]["response"]["choices"][0]["message"]["content"]="5";a[1][-1]=copy.deepcopy(a[2])
        with self.assertRaisesRegex(ValueError,"semantic answer failed"):audit_lifecycle_requests(*a)
    def test_semantic_consistent_id_collision(self):
        a=self.fixture();a[2]["response"]["id"]="r0";a[1][-1]=copy.deepcopy(a[2])
        with self.assertRaisesRegex(ValueError,"distinct complete"):audit_lifecycle_requests(*a)
    def test_boolean_index(self):
        a=self.fixture();a[0][0]["index"]=False;a[1][0]["index"]=False
        with self.assertRaises(ValueError):audit_lifecycle_requests(*a)
if __name__=="__main__":unittest.main()
