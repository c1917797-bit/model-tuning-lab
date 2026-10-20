"""Pure source/freeze helpers. No model, network, container or device operations."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

P=Path(__file__).resolve().parent
COUNTS={'GSM8K':1319,'HumanEval':164,'MMLU':14042}
SMOKE={'GSM8K':['gsm8k-test-0000','gsm8k-test-0001'],
       'HumanEval':['HumanEval/0','HumanEval/1'],
       'MMLU':['mmlu-abstract_algebra-0000','mmlu-abstract_algebra-0001']}
CONSTRUCTOR_PROTOCOL='transformers-public-TokenizersBackend.from_pretrained/v2'
CONSTRUCTOR_SHA='a815923db0c762c89ac433905ee6f359ebb76720424fa9c961fd8379146ebe2b'
BASE_PROTOCOL='three-task-chat-no-thinking-generative2048-boundary-trim/v011'
PROTOCOL='three-task-chat-no-thinking-generative2048-GSM-original-format-restored/v012'
GSM_PROTOCOL='original-Qwen-zero-shot-chat-token-list-format-restored/v012'
TASK_PROTOCOLS={'GSM8K':GSM_PROTOCOL,'HumanEval':BASE_PROTOCOL,'MMLU':BASE_PROTOCOL}
INSTRUCTION_IDS=[198,5423,279,1534,4087,303,279,3443,25435,361,3946,13867]
ASSISTANT_SUFFIX=[198,248045,74455,198,248068,271,248069,271]
FROZEN={
 'rendered_inputs_ref':(3512,'8a2b30b77fb1716172fb533e3875cd1038cb986e1f0da61f95a4a5ab7b31a429'),
 'original_inputs_ref':(37759,'8bfeb36c5d639420ed6806ee99b263d91caa9adb8de91cafce423137a495b6e7'),
 'renderer_ref':(7839,'9cf0c890921aa8f52dcfb0b81ae72864de817fa3fcf96490c55c1a9d51513212'),
 'official_source_ref':(6351,'ab7bab6a2d88a5bd4629cafacc0e6412f1e915da0d72ab25984ff1c74550de97'),
 'human_eval_package_ref':(2582,'c8a7921ec36e62633b741414a7c6f94021b3681ea0c86313c8734914b352e81d')}
OLD_AUTHORITIES={'cd1ec8cf2f12e551a5b49e95b66ef053064ac634aef1e4524430d46ce333f300',
                 '71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'}


def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()


def ref(path):
    p=Path(path)
    need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),
         'ordinary absolute exact evidence file')
    before=p.stat();h=hashlib.sha256();size=0
    with p.open('rb')as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block);size+=len(block)
    after=p.stat()
    need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)
         and size==after.st_size,'stable whole evidence bytes')
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())


def checked(reference):
    need(type(reference)is dict and set(reference)=={'path','bytes','sha256'}
         and type(reference['bytes'])is int and reference['bytes']>=0
         and ref(reference['path'])==reference,'exact Ref3 bytes')
    return Path(reference['path'])


def obj(reference):return json.loads(checked(reference).read_bytes())


def write(path,value):
    p=Path(path)
    need(p.is_absolute()and p.parent.is_dir()and not any(x.is_symlink()for x in(p.parent,*p.parents)),
         'ordinary precreated output parent')
    with p.open('xb')as stream:stream.write(canonical(value)+b'\n');stream.flush();os.fsync(stream.fileno())
    return ref(p)


def load(reference,name):
    spec=importlib.util.spec_from_file_location(name,checked(reference))
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result)
    return result


def current_authority(reference,seconds=0,now=None):
    need(reference['sha256']not in OLD_AUTHORITIES,'a new authority is required; old cutoffs remain unchanged')
    value=obj(reference);now=time.time()if now is None else now
    need(type(seconds)in(int,float)and seconds>=0 and value['start_epoch']<=now
         and now+seconds<value['cutoff_epoch'],'current new-source CPU admission window including budget')
    return value


def source(source_ref,*,seconds=0,allow_unbound_inputs=False):
    m=obj(source_ref)
    need(m['schema']=='bole.three-task-decoder-scorer/source/v2'and m['root']==str(P)
         and m['prepared_only']is True and m['default_enabled']is False
         and m['tasks']==COUNTS and m['smoke_ids']==SMOKE and m['protocol']==PROTOCOL
         and m['task_protocols']==TASK_PROTOCOLS
         and canonical(m['generation'])==canonical(dict(max_tokens=2048,ignore_eos=False,thinking_enabled=False,
                                  temperature=0,seed=0))
         and m['minimum_model_context_tokens']==5199,'exact new bounded three-task protocol source')
    need(m['decoder_constructor_protocol']==CONSTRUCTOR_PROTOCOL and m['files']['DECODER_CONSTRUCTOR.json']['sha256']==CONSTRUCTOR_SHA,'explicit prospective constructor source lineage')
    constructor=obj(m['files']['DECODER_CONSTRUCTOR.json'])
    need(constructor['constructor']=='transformers.tokenization_utils_tokenizers.TokenizersBackend.from_pretrained'and constructor['kwargs']==dict(local_files_only=True,trust_remote_code=False)and m['files']['frozen/decoder_v1.py']['sha256']==constructor['original_decoder_sha256'],'real public factory only; preserved unchanged historical decoder')
    required={'DECODER_CONSTRUCTOR.json','frozen/original_packet_manifest.json','frozen/decoder_v1.py','task_contract.py','prepare_packet.py','decoder.py','provenance.py','postprocess.py',
        'score_tokens.py','request_plan.py','compare_components.py','consume_results.py','he_policy.py','he_worker.py','stage_he.py',
        'restore_GSM_inputs.py','frozen/gsm_scorer.py','frozen/inputs004.py',
        'frozen/content_contract.py','PROTOCOL.json'}
    need(required<=set(m['files']),'whole executable and prospective protocol closure')
    image=m['image_id']
    need(type(image)is str and image.startswith('sha256:')and len(image)==71
         and all(c in'0123456789abcdef'for c in image[7:]),'one actual declared immutable image ID')
    for name,reference in m['files'].items():
        relative=Path(name)
        need(not relative.is_absolute()and '..'not in relative.parts
             and checked(reference)==P/relative,'exact current complete own-source paths')
    need(ref(__file__)==m['files']['task_contract.py'],'exact source-bound helper')
    need(m['files']['frozen/original_packet_manifest.json']['sha256']==constructor['original_package_manifest_sha256'],
         'whole immutable original packet lineage')
    prior=obj(m['files']['frozen/original_packet_manifest.json'])
    for name,row in prior['files'].items():
        if name.endswith('.py')and name not in{'decoder.py','prepare_packet.py','task_contract.py'}:
            need((m['files'][name]['bytes'],m['files'][name]['sha256'])==(row['bytes'],row['sha256']),
                 'unchanged original input/scorer/sandbox/reader source '+name)
    for key,(size,sha)in FROZEN.items():
        need((m[key]['bytes'],m[key]['sha256'])==(size,sha),'unchanged frozen artifact '+key)
        checked(m[key])
    current_authority(m['authority_ref'],seconds)
    if not allow_unbound_inputs:need(m['effective_inputs_ref']is not None,'new actual v012 effective inputs must be bound')
    return m


def cpu_runtime():
    need(os.name=='posix'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''
         and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'
         and not list(Path('/dev').glob('davinci*'))
         and not any(Path(p).exists()for p in('/dev/devmm_svm','/dev/hisi_hdc')),
         'actual Devices[] CPU namespace')
    for p in Path('/proc/self/fd').iterdir():
        try:target=os.readlink(p)
        except FileNotFoundError:continue
        need(not target.startswith(('/dev/davinci','/dev/devmm','/dev/hisi_hdc')),'no actual device FD')
    need(not any(k.split('.')[0]in{'torch_npu','vllm','vllm_ascend','triton'}for k in sys.modules),
         'no accelerator/inference backend import')


def verify_base_inputs(m):
    renderer=load(m['renderer_ref'],'_bole_unchanged_actual_render011')
    value=renderer.verify(m['rendered_inputs_ref'])  # verification only: never renderer.main/render_one
    original=obj(m['original_inputs_ref'])
    need(value['original_inputs_ref']==m['original_inputs_ref']
         and value['producer_ref']==m['renderer_ref']and value['smoke_ids']==SMOKE
         and original['human_eval_package_ref']==m['human_eval_package_ref']
         and original['full_counts']==COUNTS and value['thinking_enabled']is False,
         'same complete actual rendered IDs and original gold cohort')
    need({k:v['count']for k,v in value['tasks'].items()}==COUNTS
         and {k:v['max_prompt_tokens']for k,v in value['tasks'].items()}
         =={'GSM8K':200,'HumanEval':417,'MMLU':3151},'frozen complete cohort and prompt maxima')
    return value


def restored_gsm_row(original,old):
    need(original['id']==old['id']and original['gold_row']==old['gold_row'],
         'same exact official GSM ID/question/gold before restoration')
    before=old['prompt_token_ids'];after=original['prompt_token_ids']
    need(before.count(248046)==1 and before[:3]==[248045,846,198]
         and before[-8:]==ASSISTANT_SUFFIX,'complete original single-user/thinkOFF chat frame')
    position=before.index(248046)
    need(after==before[:position]+INSTRUCTION_IDS+before[position:],
         'every GSM row changes only by the same exact12-token original format instruction insertion')
    return dict(id=original['id'],gold_row=original['gold_row'],prompt_token_ids=after,
        prompt_policy='restore-exact-original-Qwen-zero-shot-chat-token-list-with-format-instruction',
        render_protocol=GSM_PROTOCOL,original_token_ids_reused=True,thinking_enabled=False,
        base_render011_row_sha256=digest(old),original_GSM_row_sha256=digest(original),
        official_question_sha256=hashlib.sha256(original['gold_row']['question'].encode()).hexdigest(),
        format_instruction_token_ids=INSTRUCTION_IDS,prompt_token_ids_sha256=digest(after))


def verify_inputs(m):
    base=verify_base_inputs(m);effective=obj(m['effective_inputs_ref'])
    preparation=obj(m['input_preparation_source_ref'])
    expected=dict(m,effective_inputs_ref=None,input_preparation_source_ref=None)
    need(preparation==expected and effective['source']==m['input_preparation_source_ref']
         and effective['authority_ref']==m['authority_ref'],
         'immutable original preparation source and new bound source share whole exact code/authority')
    need(effective['schema']=='bole.three-task-effective-inputs/v012'
         and effective['protocol']==PROTOCOL and effective['task_protocols']==TASK_PROTOCOLS
         and effective['base_rendered_inputs_ref']==m['rendered_inputs_ref']
         and effective['original_inputs_ref']==m['original_inputs_ref']
         and effective['smoke_ids']==SMOKE and effective['tokenizer_assets']==base['tokenizer_assets']
         and effective['GSM_format_instruction_token_ids']==INSTRUCTION_IDS
         and effective['HE_MMLU_rerendered']is False
         and effective['GSM_original_token_ids_reused']is True
         and effective['GSM_tokenization_repeated']is False
         and effective['thinking_enabled']is False,'explicit new composite, no hidden input replacement')
    original=obj(m['original_inputs_ref'])
    a=obj(original['tasks']['GSM8K']['rows_ref']);b=obj(base['tasks']['GSM8K']['rows_ref'])
    actual=obj(effective['tasks']['GSM8K']['rows_ref'])
    need(len(a)==len(b)==len(actual)==1319,'all1319 actual GSM rows, never smoke-only substitution')
    chain=hashlib.sha256()
    for original_row,old,row in zip(a,b,actual):
        need(row==restored_gsm_row(original_row,old),'independent complete exact GSM restoration replay')
        chain.update(bytes.fromhex(digest(row)))
    meta=effective['tasks']['GSM8K']
    need(meta['count']==1319 and meta['ordered_row_hash_chain']==chain.hexdigest()
         and meta['max_prompt_tokens']==max(len(r['prompt_token_ids'])for r in actual),
         'measured complete restored GSM row-chain and geometry')
    for task in('HumanEval','MMLU'):
        need(effective['tasks'][task]==base['tasks'][task], 'HE/MMLU exact old011 metadata and row refs reused')
    need(effective['minimum_model_context_tokens']==max(v['max_prompt_tokens']for v in effective['tasks'].values())+2048==5199,
         'actual complete mixed-cohort prompt maximum plus normal-EOS cap')
    return effective


def select(rendered,phase):
    need(phase in('smoke','full')and set(rendered['tasks'])==set(COUNTS),'explicit complete phase')
    for task,count in COUNTS.items():
        rows=obj(rendered['tasks'][task]['rows_ref'])
        need(len(rows)==count and len({r['id']for r in rows})==count,'whole unique frozen cohort before selection')
        chosen=rows if phase=='full'else[r for r in rows if r['id']in SMOKE[task]]
        if phase=='smoke':need([r['id']for r in chosen]==SMOKE[task],'exact ordered frozen smoke IDs')
        for row in chosen:
            ids=row['prompt_token_ids']
            need(type(ids)is list and 0<len(ids)<=3151 and all(type(x)is int and 0<=x<248320 for x in ids)
                 and row['render_protocol']==TASK_PROTOCOLS[task],'actual complete uncropped frozen token IDs')
            if task=='MMLU':need(row['ntrain']==5,'same original five-shot prompt')
            yield task,row


def exact_order(records,cases):
    need([(r['task'],r['id'])for r in records]==[(t,r['id'])for t,r in cases],
         'complete ordered selected cohort; no omission, duplication, replacement or resume')
