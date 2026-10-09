"""Source-bound ANN successor contracts. Import/default OFF uses stdlib only."""
import hashlib,json,math,os,uuid
from pathlib import Path
COMMIT="554ea6db219405becbdc0a126984a19f181bdc69"
TREE="0f453a6880fb84f03035752be5d18d7c3ef777b6"
ROOT=Path(__file__).resolve().parent
BASE=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6")
BASE_MANIFEST_SHA="0fcc51ecf998110110d2ebba7b83a7a4bffae71b28f41b9a70e120d360f969d9"
BASE_CORE_SHA="c5ef88f12828597469f7f3ce32a78ca4b4bb31d66c38beba102420d11bb21393"
ANN={"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-ann-source-20261008-1040-001/ann_attention.py","sha256":"2b07afe06ff1dd6627f1a255be585c82a632f7bbdb7bf606f4ff2f8b260b6b74","bytes":14750,"git_blob":"eff11cd4fe50b864c2ec98daca876a12e1cf5f74"}
CAUSAL={"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-causal-source-20261008-1045-001/sparse_attention.py","sha256":"dc24fa18ca67b58dc0b28e8a18deb4728c7d7fdac020a61dd1238d24b5c0e4b1","bytes":11331,"git_blob":"ada6d8f3a179aaf81425eb99c42d827c98ce9a2a"}
IDENTITIES=[
 {"path":str(Path(ANN["path"]).parent/"SOURCE_RESULT.json"),"sha256":"347852be4a9ef13bb928bc3882ab04d12c5ac7cd78587ee084f4d8f04e17e331"},
 {"path":str(Path(CAUSAL["path"]).parent/"SOURCE_RESULT.json"),"sha256":"512ef331444a9cc561861edc08c7b9c169c8085d7369a223798e31651b14af27"}]
PROTOCOL="sparq.author-ann-original-dtype-selector/v4-FP32-compensation-fixed-capacity-per-request-SUM"
LIMITS={"relative_rms":.005,"cosine":.99998}
def require(ok,message):
 if not ok:raise ValueError(message)
def sha(path):
 p=Path(path);require(p.is_absolute() and p.is_file() and not p.is_symlink(),"absolute ordinary source")
 h=hashlib.sha256()
 with p.open("rb") as stream:
  for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def read_ref(r):
 require(sha(r["path"])==r["sha256"],"actual source byte SHA")
 p=Path(r["path"]);raw=p.read_bytes()
 if "bytes" in r:require(len(raw)==r["bytes"],"actual byte size")
 return raw
def source_pins():
 for r in (ANN,CAUSAL):read_ref(r)
 for i,r in enumerate(IDENTITIES):
  s=json.loads(read_ref(r));require(s["commit"]==COMMIT and s["tree"]==TREE and s["source"]=={k:(ANN,CAUSAL)[i][k] for k in ("path","sha256","bytes")} and
    s["git_blob_sha1"]==(ANN,CAUSAL)[i]["git_blob"] and s["algorithm_pass"] is False and s["npu_executed"] is False,
    "actual official commit/tree/blob identity; source freeze is not algorithm PASS")
 canonical=ROOT.resolve()==BASE.resolve()
 manifest=BASE/"SOURCE_MANIFEST.json"
 actual_sha=sha(manifest)
 if canonical:
  from receipt import execution_clock,validate_cutoff_fields
  m=json.loads(manifest.read_bytes());validate_cutoff_fields(m);execution_clock()
  require(m["schema"]=="sparq.token-preparation/v9-author-ann-FP32-compensation" and m["source_count"]==42 and len(m["files"])==31 and
   m["files"]["sparq_token_v4/core.py"]==BASE_CORE_SHA and m["files"]["contract.py"]==sha(Path(__file__).resolve()) and
   m["registered_author_successor"]["protocol"]==PROTOCOL,"actual current canonical42 source identity, no obsolete41/self-manifest recursion")
  require(m["author_sources"]=={"ann":ANN,"causal":CAUSAL,"identities":IDENTITIES,"commit":COMMIT,"tree":TREE},
   "actual current canonical author identities exactly frozen")
 else:
  require(actual_sha==BASE_MANIFEST_SHA,"private review binds exact original0fcc41-source substrate; no inherited gate permission")
  m=json.loads(manifest.read_bytes())
  require(m["source_count"]==41 and len(m["files"])==31 and m["files"]["sparq_token_v4/core.py"]==BASE_CORE_SHA,
   "frozen41 substrate closure only, original BF16 gate FAILED")
  review=json.loads((ROOT/"SOURCE_REVIEW_MANIFEST.json").read_bytes())
  require(review["schema"]=="sparq.FP32-compensation-private-source/v1" and review["ready"] is False and
   review["native_substrate"]=={"path":str(manifest),"sha256":BASE_MANIFEST_SHA} and
   review["protocol"]==PROTOCOL,"exact NEW private source context, no native PASS inheritance")
  for filename,digest in review["files"].items():
   require(Path(filename).name==filename and sha(ROOT/filename)==digest,"every proposed private source byte")
 for f,d in m["files"].items():read_ref({"path":str(BASE/f),"sha256":d})
 for path,d in m["dependencies"].items():read_ref({"path":path,"sha256":d})
 for pair in [m["native_device_operator"]]+list(m["model_sources"].values()):read_ref(pair["captured_source_ref"])
 return {"author_commit":COMMIT,"author_tree":TREE,"ann":ANN,"causal":CAUSAL,"actual_manifest_sha256":actual_sha,
  "context":"current-canonical42" if canonical else "private-frozen41-BF16-substrate","base_original011_status":"FAILED","ready":False}

def topk_legal(scores,selected,k,valid=None,forced=()):
 """Exact-score top-k legality, arbitrary exact ties, no epsilon or ID policy.
 +Inf is legal only for forced/local author sentinel. Never used for outputs.
 """
 n=len(scores);valid=list(range(n)) if valid is None else list(valid)
 require(type(k) is int and 0<k<=len(valid) and len(selected)==k and len(set(selected))==k and
   set(selected)<=set(valid) and set(forced)<=set(selected),"exact top-k membership/count/local")
 require(all(type(scores[i]) in (int,float) and not math.isnan(scores[i]) and
   (math.isfinite(scores[i]) or scores[i]==float("inf") and i in forced) for i in valid),
   "actual finite valid score except forced +Inf ranking sentinel")
 chosen=set(selected);outside=[scores[i] for i in valid if i not in chosen]
 require(not outside or min(scores[i] for i in selected)>=max(outside),"non-tie support discrepancy; no ULP tolerance")
 require(all(scores[a]>=scores[b] for a,b in zip(selected,selected[1:])),"author sorted top-k order except arbitrary exact ties")
 cutoff=min(scores[i] for i in selected)
 return {"selected_count":k,"exact_cutoff":cutoff if math.isfinite(cutoff) else "forced-positive-infinity",
  "tied_selected":[i for i in selected if scores[i]==cutoff],
  "tied_excluded":[i for i in valid if i not in chosen and scores[i]==cutoff],
  "epsilon":0,"stable_token_ID_required":False}
def write_new(path,value):
 """Atomic exclusive publication, same-directory tmp remains on failure."""
 p=Path(path);require(p.is_absolute() and p.parent.is_dir(),"owned existing output parent")
 raw=(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
 tmp=p.parent/("."+p.name+"."+uuid.uuid4().hex+".tmp")
 with tmp.open("xb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 os.link(str(tmp),str(p))
 fd=os.open(str(p.parent),os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
 return {"path":str(p),"sha256":sha(p),"publication_tmp_retained":str(tmp)}
