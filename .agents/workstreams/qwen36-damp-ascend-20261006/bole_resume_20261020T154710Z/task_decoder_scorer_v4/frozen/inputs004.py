"""Same-image CPU input producer and shared smoke/full input contract. OFF.

No model, network, Docker, NPU, evaluator execution or admission is performed.
Original GSM token lists are reused; HE uses original completion prompts;
MMLU formatting executes only the three pinned original author functions.
"""
import argparse,ast,gzip,hashlib,importlib.util,json,os,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CUT=1791922930
COUNTS={'GSM8K':1319,'HumanEval':164,'MMLU':14042}
SMOKE={'GSM8K':['gsm8k-test-0000','gsm8k-test-0001'],
       'HumanEval':['HumanEval/0','HumanEval/1'],
       'MMLU':['mmlu-abstract_algebra-0000','mmlu-abstract_algebra-0001']}
SERVICE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_adakv_current_prepare/R118/skvq-service-full-v1-008/SOURCE_MANIFEST.json',bytes=21508,sha256='948916a3cdb94c98e4af4bcb14d4168f733ade02387b15e65f4df3283617732e')
GSM_DATA_SHA='3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14'
GSM_PROMPTS_SHA='94cc27bb415cf5705f8b4f0220468762d9b705bd657f9a3c8a370a5777d6c1d5'
AUTHOR_SHA='8b7d84e5a2e9290df0d43d1c060aa68ecb638c4666415b3a58d709c18eace4ec'
TOKENIZER_SHA='d35d249ccc9f3cbd6fa9a289f70436e70deba7a0df38e7fc26ad0d2436b6999d'

def need(v,m):
    if not v:raise ValueError(m)

def ref(p):
    p=Path(p);need(p.is_absolute()and p.is_file()and not p.is_symlink()and not any(x.is_symlink()for x in p.parents),'ordinary actual source/input')
    a=p.stat();h=hashlib.sha256();n=0
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b);n+=len(b)
    z=p.stat();need((a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino),'stable source/input')
    return dict(path=str(p),bytes=n,sha256=h.hexdigest())

def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>=0,'Ref3')
    need(ref(r['path'])==r,'whole immutable bytes');return Path(r['path'])

def obj(r):return json.loads(checked(r).read_bytes())

def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def publish(p,x):
    p=Path(p);need(p.parent.is_dir()and not p.exists(),'new output only')
    with p.open('xb')as f:f.write(canonical(x))
    return ref(p)

def module(p,sha,name):
    p=Path(p);need(ref(p)['sha256']==sha,'exact imported original source')
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s)
    sys.modules[name]=m;s.loader.exec_module(m);return m

def original_mmlu(raw):
    need(hashlib.sha256(raw).hexdigest()==AUTHOR_SHA,'pinned author evaluate.py')
    tree=ast.parse(raw);names=('format_subject','format_example','gen_prompt')
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
    need([n.name for n in nodes]==list(names),'three actual original formatting bodies')
    ns={'choices':list('ABCD')};exec(compile(ast.Module(body=nodes,type_ignores=[]),'original-evaluate.py','exec'),ns)
    return ns

def official_inputs(index,root):
    root=Path(root);need(root.is_absolute(),'explicit official source root')
    rows={}
    for entry in index['files']:
        name=entry['relative'];p=root/Path(name)
        need(not Path(name).is_absolute()and '..'not in Path(name).parts and name not in rows,'bounded unique relocation')
        r=ref(p);need((r['bytes'],r['sha256'])==(entry['bytes'],entry['sha256']),'original official bytes after explicit relocation')
        rows[name]=r
    return rows

def ids_ok(ids):return type(ids)is list and 0<len(ids)<=38912 and all(type(x)is int and 0<=x<248320 for x in ids)

def gsm_rows(data,prompts):
    need(ref(data)['sha256']==GSM_DATA_SHA and ref(prompts)['sha256']==GSM_PROMPTS_SHA,'same actual original GSM dataset and token list')
    gold=[json.loads(l)for l in Path(data).read_text(encoding='utf-8').splitlines()if l.strip()]
    ps=json.loads(Path(prompts).read_bytes());need(len(gold)==len(ps)==1319,'full1319 official GSM')
    for i,(g,p)in enumerate(zip(gold,ps)):
        rid='gsm8k-test-%04d'%i
        need(p['id']==rid and ids_ok(p['prompt_token_ids'])and type(g['question'])is str and type(g['answer'])is str,'complete actual GSM order/schema')
        yield dict(id=rid,prompt_token_ids=p['prompt_token_ids'],gold_row=g,
                   prompt_policy='reuse-exact-original-Qwen-zero-shot-chat-token-list')

def he_rows(path,tok):
    with gzip.open(path,'rt',encoding='utf-8')as f:rows=[json.loads(l)for l in f if l.strip()]
    need(len(rows)==164 and [r['task_id']for r in rows]==['HumanEval/'+str(i)for i in range(164)],'full original HE order164')
    for p in rows:
        need(all(type(p[k])is str for k in('task_id','prompt','canonical_solution','test','entry_point')),'full official problem')
        ids=tok.encode(p['prompt'],add_special_tokens=False);need(ids_ok(ids),'HE prompt complete no crop')
        yield dict(id=p['task_id'],prompt_text=p['prompt'],prompt_token_ids=ids,
                   official_problem=p,prompt_policy='original-completion-prompt-no-chat-or-repair')

def mmlu_rows(rows,root,tok,pandas):
    author=original_mmlu(checked(rows['mmlu/evaluate.py']).read_bytes())
    subjects=sorted(Path(k).name[:-9]for k in rows if k.startswith('mmlu/data/test/')and k.endswith('_test.csv'))
    need(len(subjects)==57 and len(set(subjects))==57,'original57 subjects')
    count=0
    for subject in subjects:
        dev=pandas.read_csv(checked(rows['mmlu/data/dev/'+subject+'_dev.csv']),header=None)
        test=pandas.read_csv(checked(rows['mmlu/data/test/'+subject+'_test.csv']),header=None)
        need(dev.shape==(5,6)and test.shape[1]==6,'original5shot four-choice geometry')
        for i in range(test.shape[0]):
            text=author['gen_prompt'](dev,subject,5)+author['format_example'](test,i,include_answer=False)
            ids=tok.encode(text,add_special_tokens=True);need(ids_ok(ids),'MMLU full5shot fits; never silently reduce/crop')
            gold=test.iloc[i,5];need(gold in list('ABCD'),'author gold')
            count+=1
            yield dict(id='mmlu-%s-%04d'%(subject,i),subject=subject,index=i,ntrain=5,
                       prompt_text=text,prompt_token_ids=ids,gold=gold,prompt_policy='original-author-five-shot-next-token-likelihood')
    need(count==14042,'full14042 official MMLU')

def select(value,phase):
    need(value['schema']=='skvq.latest-three-task-inputs/v2'and value['service_ref']==SERVICE and value['cutoff_epoch']==CUT,'current008 protocol')
    need(phase in('smoke','full')and value['smoke_ids']==SMOKE and value['full_counts']==COUNTS,'frozen smoke2/full coverage')
    need(set(value['tasks'])==set(COUNTS),'exact three tasks')
    for task in COUNTS:
        rows=json.loads(checked(value['tasks'][task]['rows_ref']).read_bytes())
        need(len(rows)==COUNTS[task]and len({r['id']for r in rows})==len(rows),'whole unique official cohort')
        chosen=rows if phase=='full'else [r for r in rows if r['id']in SMOKE[task]]
        if phase=='smoke':need([r['id']for r in chosen]==SMOKE[task],'frozen ordered two smoke IDs')
        for row in chosen:
            need(ids_ok(row['prompt_token_ids']),'actual complete IDs');yield task,row

def main():
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-audit-only',action='store_true');p.add_argument('--source-sha256')
    for k in('official-root','model-tokenizer-root','gsm-dataset','gsm-prompts','output'):p.add_argument('--'+k,type=Path)
    a=p.parse_args()
    if not(a.execute or a.source_audit_only):print(json.dumps(dict(enabled=False,NPU=False,task_ready=False)));return
    need(not(a.execute and a.source_audit_only),'one explicit source or tokenizer stage')
    started=time.monotonic();need(time.time()+900<=CUT,'CPU input phase900 fits unchangedR118')
    mf=ref(HERE/'SOURCE_MANIFEST.json');need(mf['sha256']==a.source_sha256,'frozen preparation source')
    m=obj(mf)
    for r in m['files'].values():checked(r)
    checked(SERVICE)
    need(all((a.official_root,a.model_tokenizer_root,a.gsm_dataset,a.gsm_prompts)),'complete explicit inputs')
    if a.execute:need(a.output and not a.output.exists(),'new output')
    T=module(HERE/'original_tokenizer_preflight.py',TOKENIZER_SHA,'_latest_original_tokenizer004')
    if a.execute:need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','MAIN-owned Devices[] required');T.no_backend()
    assets=[]
    for name,(n,h)in T.ASSETS.items():
        r=ref(a.model_tokenizer_root/name);need((r['bytes'],r['sha256'])==(n,h),'same checkpoint tokenizer');assets.append(r)
    index=json.loads((HERE/'OFFICIAL_INDEX.json').read_bytes());rows=official_inputs(index,a.official_root)
    need(ref(a.gsm_dataset)['sha256']==GSM_DATA_SHA and ref(a.gsm_prompts)['sha256']==GSM_PROMPTS_SHA,'whole existing GSM originals')
    if a.source_audit_only:
        print(json.dumps(dict(source_ref=mf,service_ref=SERVICE,official_files=len(rows),tokenizer_assets=assets,gsm_sources=[ref(a.gsm_dataset),ref(a.gsm_prompts)],NPU=False,tokenized=False,task_ready=False),sort_keys=True));return
    for k,v in dict(USE_TORCH='0',USE_TF='0',USE_FLAX='0',TOKENIZERS_PARALLELISM='false',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1').items():os.environ[k]=v
    import transformers,tokenizers,pandas
    from transformers import AutoTokenizer
    T.no_backend();need((transformers.__version__,tokenizers.__version__)==('5.5.4','0.22.2'),'same660 tokenizer stack')
    tok=AutoTokenizer.from_pretrained(str(a.model_tokenizer_root),local_files_only=True,trust_remote_code=False)
    choices={k:tok.encode(k,add_special_tokens=False)for k in(' A',' B',' C',' D')}
    need(all(len(v)==1 and tok.decode(v,skip_special_tokens=False,clean_up_tokenization_spaces=False)==k for k,v in choices.items())and len({v[0]for v in choices.values()})==4,'MMLU actual four single-token keys; no invented option map')
    a.output.mkdir(mode=0o700)
    result=dict(schema='skvq.latest-three-task-inputs/v2',source_ref=mf,service_ref=SERVICE,cutoff_epoch=CUT,
        tasks={},smoke_ids=SMOKE,full_counts=COUNTS,thinking_enabled=False,task_ready=False,NPU=False,
        tokenizer_assets=assets,choice_token_ids=choices,library_refs=[ref(Path(x.__file__).resolve())for x in(transformers,tokenizers,pandas)],
        original_sources=list(rows.values()),gsm_sources=[ref(a.gsm_dataset),ref(a.gsm_prompts)],
        protocol=dict(GSM8K={'max_tokens':2048,'ignore_eos':False},HumanEval={'max_tokens':2048,'ignore_eos':False},MMLU={'max_tokens':1,'logprobs':100,'echo':True,'return_token_ids':False,'return_tokens_as_token_ids':False}),
        native_parser_checked=False,model_ready=False,score_ready=False)
    producers={'GSM8K':gsm_rows(a.gsm_dataset,a.gsm_prompts),'HumanEval':he_rows(checked(rows['human-eval/data/HumanEval.jsonl.gz']),tok),'MMLU':mmlu_rows(rows,a.official_root,tok,pandas)}
    for name,it in producers.items():
        values=[]
        for row in it:
            need(time.monotonic()-started<810 and time.time()+90<CUT,'CPU child810 plus reserved cleanup90');values.append(row)
        need(len(values)==COUNTS[name],'full task count before publish')
        result['tasks'][name]={'rows_ref':publish(a.output/(name+'.rows.json'),values)}
    he_package=dict(repository='openai/human-eval',commit='6d43fb980f9fee3c892a914eda09951f772ad10d',
        dataset_ref=rows['human-eval/data/HumanEval.jsonl.gz'],
        files=[r for n,r in rows.items()if n.startswith('human-eval/')and n!='human-eval/data/HumanEval.jsonl.gz'],
        explicit_relocation=True,original_index_ref=ref(HERE/'OFFICIAL_INDEX.json'),count=164,code_executed=False)
    result['human_eval_package_ref']=publish(a.output/'HUMANEVAL_PACKAGE.json',he_package)
    # Exact shared reader consumes this producer before INPUTS publication.
    need(len(list(select(result,'smoke')))==6 and sum(1 for _ in select(result,'full'))==15525,'shared client input contract')
    T.no_backend();result['elapsed_seconds']=time.monotonic()-started
    print(json.dumps(publish(a.output/'INPUTS.json',result),sort_keys=True))

if __name__=='__main__':main()
