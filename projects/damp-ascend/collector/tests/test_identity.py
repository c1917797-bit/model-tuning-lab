"""Stdlib identity fixtures, not real-model capture or legacy acceptance."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from damp_capture.contract import token_digest,file_digest
from damp_capture.identity import (NATIVE_SOURCES,Observer,exact_pair,live_identity,
    recover_bindings,source_identity,legacy_source,audit_destination)
from damp_capture.contract import RESULT_ROOT

def fixture():
    rows = [dict(id=f"row-{i}",input_ids=[11+i,22+i],
                 input_ids_sha256=token_digest([11+i,22+i])) for i in range(2)]
    manifest = dict(rows=rows,generation=dict(max_tokens=2))
    clients = {r["id"]:dict(logical_id=r["id"],runtime_id=str(i),
        prompt_token_sha256=r["input_ids_sha256"],output_tokens=2,
        output_token_ids=[100+i,200+i],output_token_sha256=token_digest([100+i,200+i]))
        for i,r in enumerate(rows)}
    ranks = [[dict(event="request_bound",rank=rank,logical_id=r["id"],
        runtime_id=str(i)+"-"+["a8d5e777","92148c88"][i],
        prompt_token_sha256=r["input_ids_sha256"]) for i,r in enumerate(rows)] for rank in range(4)]
    return manifest,clients,copy.deepcopy(clients),ranks

class FakeEngine:
    def __init__(self):self.calls=[];self.last_result=None
    def add_request(self,request_id,prompt,params,priority=0):
        self.calls.append((request_id,prompt,params,priority))
        self.last_result=request_id+"-deadbeef"
        return self.last_result

class IdentityTests(unittest.TestCase):
    def test_observer_original_objects_return_and_external_output(self):
        m,_,_,_=fixture();engine=FakeEngine();events=[];observer=Observer(engine.add_request,m,events.append)
        for i,row in enumerate(m["rows"]):
            prompt=dict(type="token",prompt_token_ids=row["input_ids"]);params=SimpleNamespace(n=1)
            returned=observer(str(i),prompt,params,priority=7)
            self.assertIs(returned,engine.last_result)
            self.assertIs(engine.calls[-1][1],prompt);self.assertIs(engine.calls[-1][2],params)
            self.assertEqual(engine.calls[-1][3],7)
            identity=observer.output(str(i),row,row["input_ids"])
            self.assertEqual(identity["runtime_id"],str(i)+"-deadbeef")
            self.assertEqual(identity["external_request_id"],str(i))
        observer.complete();self.assertEqual(len(events),2)

    def test_replay_and_unknown_prompt_rejected_before_original(self):
        m,_,_,_=fixture();engine=FakeEngine();observer=Observer(engine.add_request,m,lambda x:None)
        prompt=dict(type="token",prompt_token_ids=m["rows"][0]["input_ids"]);p=SimpleNamespace(n=1)
        observer("0",prompt,p)
        for external,other in (("0",prompt),("1",prompt),("2",dict(type="token",prompt_token_ids=[99]))):
            with self.assertRaises(ValueError):observer(external,other,p)
        self.assertEqual(len(engine.calls),1)

    def test_non_token_and_multiple_candidates_rejected(self):
        m,_,_,_=fixture();engine=FakeEngine();observer=Observer(engine.add_request,m,lambda x:None)
        for prompt,p in ((dict(type="embeds",prompt_token_ids=[11,22]),SimpleNamespace(n=1)),
                         (dict(type="token",prompt_token_ids=[11,22]),SimpleNamespace(n=2))):
            with self.assertRaises(ValueError):observer("0",prompt,p)
        self.assertEqual(engine.calls,[])

    def test_wrong_output_identity_or_incomplete_coverage_rejected(self):
        m,_,_,_=fixture();observer=Observer(FakeEngine().add_request,m,lambda x:None)
        observer("0",dict(type="token",prompt_token_ids=[11,22]),SimpleNamespace(n=1))
        with self.assertRaises(ValueError):observer.output("0",m["rows"][1],[12,23])
        with self.assertRaises(ValueError):observer.output("missing",m["rows"][0],[11,22])
        with self.assertRaises(ValueError):observer.complete()

    def test_exact_known_external_not_suffix_stripping(self):
        exact_pair("real-id-with-hyphens","real-id-with-hyphens-aabbccdd")
        for external,internal in (("0","0"),("0","0-abcdefg1"),("0","0-ABCDEF12"),
                                  ("0","0-aabbccdd-extra"),("0","1-aabbccdd"),("0","00-aabbccdd"),
                                  ("0","0-aabbccdd00")):
            with self.assertRaises(ValueError):exact_pair(external,internal)

    def test_native_source_gate_and_disabled_randomization(self):
        with patch("damp_capture.identity.file_digest",side_effect=lambda path:NATIVE_SOURCES.get(str(path),"f"*64)), \
                patch.dict("os.environ",{"VLLM_DISABLE_REQUEST_ID_RANDOMIZATION":"0"}):
            self.assertEqual(source_identity()["native_sources"],NATIVE_SOURCES)
        with patch.dict("os.environ",{"VLLM_DISABLE_REQUEST_ID_RANDOMIZATION":"1"}):
            with self.assertRaises(ValueError):source_identity()
        with patch("damp_capture.identity.file_digest",return_value="0"*64), \
                patch.dict("os.environ",{"VLLM_DISABLE_REQUEST_ID_RANDOMIZATION":"0"}):
            with self.assertRaises(ValueError):source_identity()

    def test_legacy_strict_join_preserves_original_client(self):
        m,clients,oracles,ranks=fixture();original=copy.deepcopy(clients)
        recovered=recover_bindings(m,clients,oracles,ranks)
        self.assertEqual(recovered["row-0"]["runtime_id"],"0-a8d5e777")
        self.assertEqual(clients,original)

    def test_legacy_missing_rank_duplicate_or_disagreement_rejected(self):
        for case in range(4):
            m,clients,oracles,ranks=fixture()
            if case==0:ranks.pop()
            if case==1:ranks[0].append(copy.deepcopy(ranks[0][0]))
            if case==2:ranks[3][0]["runtime_id"]="0-00000000"
            if case==3:ranks[0][0]["rank"]=3
            with self.subTest(case=case),self.assertRaises(ValueError):
                recover_bindings(m,clients,oracles,ranks)

    def test_legacy_prompt_output_external_and_hex_mutations_rejected(self):
        for case in range(6):
            m,clients,oracles,ranks=fixture()
            if case==0:ranks[0][0]["prompt_token_sha256"]="0"*64
            if case==1:oracles["row-0"]["output_token_ids"][0]=99
            if case==2:clients["row-0"]["runtime_id"]="1"
            if case==3:ranks[0][0]["runtime_id"]="0-zzzzzzzz"
            if case==4:clients["row-0"]["output_token_sha256"]="0"*64
            if case==5:oracles["row-0"]["output_tokens"]=1
            with self.subTest(case=case),self.assertRaises(ValueError):
                recover_bindings(m,clients,oracles,ranks)

    def test_legacy_wrong_container_never_accepted(self):
        m,clients,oracles,ranks=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"synthetic-wrong-legacy-source.json"
            p.write_text(json.dumps(dict(schema="damp.legacy-v4-source/v1",container_name="not-original-v4")))
            with self.assertRaises(ValueError):legacy_source(p,Path(tmp),Path(tmp),m)

    def test_audit_never_writes_inside_original_evidence(self):
        on,off=RESULT_ROOT/"smoke-hook-v4-on",RESULT_ROOT/"smoke-hook-v4-off"
        for output in (RESULT_ROOT,on/"new-audit",off/"new-audit",Path("/tmp/elsewhere")):
            with self.assertRaises(ValueError):audit_destination(output,on,off)

    def test_live_client_matches_observed_ids_and_complete_source(self):
        m,clients,_,_=fixture();engine=FakeEngine();events=[];observer=Observer(engine.add_request,m,events.append)
        for i,row in enumerate(m["rows"]):
            observer(str(i),dict(type="token",prompt_token_ids=row["input_ids"]),SimpleNamespace(n=1))
            clients[row["id"]]["external_request_id"]=str(i)
            clients[row["id"]]["runtime_id"]=str(i)+"-deadbeef"
        import damp_capture.identity as module
        metadata=dict(schema="damp.request-identity/v1",native_sources=NATIVE_SOURCES,
            identity_helper_sha256=file_digest(module.__file__),mechanism="instance-add_request-return-observer")
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/"RUN.json").write_text(json.dumps(dict(request_identity=metadata)))
            (p/"request-identities.jsonl").write_text("\n".join(json.dumps(e) for e in events)+"\n")
            self.assertEqual(live_identity(p,m,clients)["native_sources"],NATIVE_SOURCES)
            clients["row-0"]["runtime_id"]="0-aabbccdd"
            with self.assertRaises(ValueError):live_identity(p,m,clients)

if __name__=="__main__":unittest.main()
