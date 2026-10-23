"""Fixed representative2k workload contract; never inherits131 qualification."""
INPUT=2048
OUTPUT=1024
TOKENIZER='/models/Qwen3.6-27B'
CHECKPOINT='/cache/efim/Qwen3.6-27B'
TEXT='Explain how trees grow. '
REPEATS=1024
ADD_SPECIAL_TOKENS=False
MAX_MODEL_LEN=4096
CONCURRENCY=1
STAGE='source-only input/native-input-identity/strict-transport components'
def need(v,s):
 if not v:raise ValueError(s)
def validate_prompt(ids,vocab_size):
 need(type(vocab_size)is int and vocab_size>0 and type(ids)is list and len(ids)==INPUT and
      all(type(x)is int and 0<=x<vocab_size for x in ids),'exact actual2048 token IDs; never string length/padding/131 reuse')
 return ids
def required_geometry(output=OUTPUT):
 need(type(output)is int and output in (8,OUTPUT),'short8 size witness or explicit full1024 domain')
 before=INPUT+output-2
 return dict(prefix_tokens=INPUT,maximum_before=before,private_end_exclusive=before+3,
  prefix_kernel_pages=(INPUT+127)//128,maximum_private_kernel_pages=(before+3+127)//128,
  maximum_committed_path_kernel_pages=(before+2+127)//128,
  actual_allocated_table_proven=False,physical_allocation_growth_proven=False,
  joint_raw_budget_fit=False,numerical_qualified=False)
def require_model_qualification(*args,**kwargs):
 raise ValueError('2k independent native-prefill allocation/identity/full64 numeric+state, joint raw budget and current2k source/authority remain unbound;131 proof is not2k proof')
