"""Independent long-native-domain stage reference. Stdlib/OFF at import.
Own BF16 per-head Q/K; registered FP32 requestwise SUM(0), own full padding.
No candidate modules/score/support used as reference. Whole complete original
q/K/V FP64 output remains the independently pinned numerical program.
Geometry is initialized stock metadata, not a hand-written 324-page mapping.
"""
import allocation_contract as a
require=a.require
PROTOCOL="sparq.long-native-per-request-FP32-SUM0/v1"
MAX_MODEL_LEN=40960
PERFORMANCE_PROMPT=32768
PERFORMANCE_OUTPUT=1024
def domain(pages,geometry,n):
 require(type(n) is int and 0<n<=MAX_MODEL_LEN,
  "actual nonempty full live context <= registered40960, no dropped short domain")
 require(type(geometry) is dict and geometry.get("max_model_len")==MAX_MODEL_LEN,
  "actual initialized stock geometry required, not toy18pages")
 a.geometry_pages(pages,geometry)
 capacity=pages*a.BLOCK
 require(capacity>=MAX_MODEL_LEN and n<=capacity and
  PERFORMANCE_PROMPT+PERFORMANCE_OUTPUT==33792<=MAX_MODEL_LEN,
  "actual physical-rounded table capacity covers logical40960; fixed1024 total33792")
 return dict(protocol=PROTOCOL,pages=pages,capacity=capacity,live_length=n,
  current_sentinel=n-1,logical_model_max=MAX_MODEL_LEN,
  performance_prompt_tokens=PERFORMANCE_PROMPT,performance_output_tokens=PERFORMANCE_OUTPUT,
  performance_total_tokens=33792,geometry=geometry,
  own_inputs=True,candidate_rank_or_score_used=False,
  cropped_reduction_diagnostic_only=True)
def geometry(q,key,pages,proof):
 n=key.shape[0]
 require(q.shape==(6,256) and key.shape==(n,256),"own full original long q/K geometry")
 return domain(pages,proof,n)
def native_stage(torch,q,key,dims,pages,proof):
 # No candidate import or intermediates: per-head original BF16 arithmetic.
 d=geometry(q,key,pages,proof);n=d["live_length"];capacity=d["capacity"]
 importance=q.abs().sum(0);projected_key=key.index_select(-1,dims)
 logits=[]
 for query in q:
  projected=query.index_select(0,dims)
  scale=projected.abs().sum(-1)
  scale.div_(query.abs().sum(-1));scale.mul_(query.shape[-1]);scale.pow_(.5)
  logits.append((projected.div(scale) @ projected_key.T).float())
 score=torch.stack(logits)
 padded=torch.full((6,capacity),float("-inf"),dtype=torch.float32,device=score.device)
 padded[:,:n].copy_(score);padded[:,n-1]=torch.finfo(torch.float32).max
 ranking=padded.sum(0)[:n]
 return importance,score,ranking,d
def source_legality(torch,q,key,dims,selected,witness_score,witness_ranking,pages,proof,topk_legal):
 d=geometry(q,key,pages,proof);n=d["live_length"];capacity=d["capacity"]
 require(callable(topk_legal),"source-bound independent author exact-topK contract")
 dims=dims.detach();selected=selected[:min(n,128)].detach()
 require(witness_score.shape==(6,capacity) and witness_ranking.shape==(capacity,) and
  witness_score.dtype==witness_ranking.dtype==torch.float32,
  "actual captured complete long score/rank, not cropped or reconstructed witness")
 importance,score,ranking,d=native_stage(torch,q,key,dims,pages,proof)
 channels=topk_legal(importance.detach().cpu().float().tolist(),dims.cpu().tolist(),32)
 require(torch.equal(score,witness_score[:,:n]),
  "independent original BF16 per-head long score; no backend ULP relaxation")
 require(torch.equal(ranking,witness_ranking[:n]),
  "independent fixed-capacity requestwise FP32 long GQA SUM and current +Inf sentinel")
 if n<capacity:
  require(bool(torch.isneginf(witness_score[:,n:]).all().detach().cpu()) and
   bool(torch.isneginf(witness_ranking[n:]).all().detach().cpu()),
   "all actual inactive long rank/score tails negative infinity")
 cropped=score.clone();cropped[:,-1]=torch.finfo(torch.float32).max
 cropped=cropped.sum(0)
 d["cropped_vs_registered_difference_tokens"]=(cropped!=ranking).nonzero().flatten().detach().cpu().tolist()
 support=topk_legal(ranking.detach().cpu().tolist(),selected.cpu().tolist(),min(n,128),forced=(n-1,))
 return dict(channel_contract=channels,support_contract=support,
  reference="independent original-dtype per-head NPU operators",
  nonzero_score_tolerance=False,CPU32_stable_ID_spec=False,
  rank_sentinel_final_finiteness_exempt_only=True,rank_layout=d)
def consume_domain(layout,n):
 expected=domain(layout["pages"],layout["geometry"],n)
 require(all(layout.get(k)==v for k,v in expected.items()),
  "whole actual long-native domain serializer -> independent consumer")
 differences=layout["cropped_vs_registered_difference_tokens"]
 require(type(differences) is list and len(differences)==len(set(differences)) and
  all(type(x) is int and 0<=x<n for x in differences),
  "complete cropped-reduction diagnostic only, no accepted nonzero tolerance")
 return expected
