"""Complete source/gold/template replay using existing IDs, never prompt encoding."""
import gzip
import hashlib
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import postprocess as S

INPUTS_SHA='0773169d441bfae70f8126a29f57a70c19c747cda37c4ee62b486c80a2b14c25'
CONTENT_SHA='7c97b4ef5350660866018726e69db0c2dca5cb275be80050d99fdc17e7969bde'


def whole_decode(tok,ids):
    C.need(type(ids)is list and ids and all(type(x)is int and 0<=x<248320 for x in ids),'whole frozen prompt IDs')
    return tok.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)


def official_sources(original,official_source):
    mapped={}
    for reference in original['original_sources']:
        path=C.checked(reference);parts=path.parts
        C.need(parts.count('official')==1,'one explicit historical official source root')
        name=str(Path(*parts[parts.index('official')+1:]))
        C.need(name not in mapped and not name.startswith('../'),'unique original official file')
        mapped[name]=reference
    C.need(len(mapped)==132,'whole original official source inventory')
    index=C.obj(official_source['official_index_ref'])
    C.need(len(index['files'])==132 and set(mapped)=={r['relative']for r in index['files']},
           'whole actual original official index, no substituted source inventory')
    for row in index['files']:
        actual=mapped[row['relative']]
        C.need((actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256']),
               'every actual official source matches original independent index')
    return mapped


def run(m,effective,tok):
    """Actual tokenizer-only operation. Reconstruct author text/gold from originals.

    No apply_chat_template or encode call occurs here. Complete already frozen
    IDs are decoded and compared with the exact fixed original template frame.
    """
    C.cpu_runtime();original=C.obj(m['original_inputs_ref'])
    official=official_sources(original,C.obj(m['official_source_ref']))
    G=S.gsm_module(m['files']['frozen/gsm_scorer.py'])
    for key in('source','license'):
        reference=G.BINDING['official_provenance'][key]
        C.need(C.ref(reference['path'])['sha256']==reference['sha256'],
               'actual original GSM author dataset source/license')
    O=C.load(m['files']['frozen/inputs004.py'],'_bole_original_inputs_functions')
    C.need(m['files']['frozen/inputs004.py']['sha256']==INPUTS_SHA,'unchanged original input functions')
    K=C.load(m['files']['frozen/content_contract.py'],'_bole_original_content_contract')
    C.need(m['files']['frozen/content_contract.py']['sha256']==CONTENT_SHA,'unchanged exact chat content contract')
    instruction=whole_decode(tok,C.INSTRUCTION_IDS)
    C.need(instruction.startswith('\n')and '#### <number>'in instruction and len(instruction)<256,
           'actual original fixed12-token numeric-format instruction text')
    # Use unchanged author-content contract to pin the full checkpoint template.
    K.validate('probe',K.PREFIX+'probe'+K.SUFFIX,tok.chat_template)
    counts={};chains={};maxima={};all_prompt_bytes=0
    for task in C.COUNTS:
        rows=C.obj(effective['tasks'][task]['rows_ref']);chain=hashlib.sha256()
        if task=='GSM8K':
            sources=original['gsm_sources'];C.need(len(sources)==2,'two whole original GSM data/prompt sources')
            golds=[__import__('json').loads(line)for line in C.checked(sources[0]).read_text().splitlines()if line.strip()]
            originals=list(O.gsm_rows(C.checked(sources[0]),C.checked(sources[1])))
            C.need(len(golds)==len(originals)==len(rows)==1319,'complete actual GSM source coverage')
            iterable=((row,gold['question'].strip()+instruction,dict(gold_row=gold,original=old))
                      for row,gold,old in zip(rows,golds,originals))
        elif task=='HumanEval':
            package=C.obj(m['human_eval_package_ref']);C.checked(package['dataset_ref'])
            with gzip.open(package['dataset_ref']['path'],'rt',encoding='utf8')as stream:
                problems=[__import__('json').loads(line)for line in stream if line.strip()]
            C.need(len(problems)==len(rows)==164,'whole official HE problem cohort')
            iterable=((row,p['prompt'],dict(official_problem=p))for row,p in zip(rows,problems))
        else:
            import pandas
            C.need(C.ref(Path(pandas.__file__).resolve())in original['library_refs'],'actual frozen pandas source')
            author=O.original_mmlu(C.checked(official['mmlu/evaluate.py']).read_bytes())
            subjects=sorted(Path(k).name[:-9]for k in official if k.startswith('mmlu/data/test/')and k.endswith('_test.csv'))
            C.need(len(subjects)==len(set(subjects))==57,'full official57 MMLU subjects')
            def mmlu_cases():
                cursor=0
                for subject in subjects:
                    dev=pandas.read_csv(C.checked(official['mmlu/data/dev/'+subject+'_dev.csv']),header=None)
                    test=pandas.read_csv(C.checked(official['mmlu/data/test/'+subject+'_test.csv']),header=None)
                    C.need(dev.shape==(5,6)and test.shape[1]==6,'unchanged official5shot geometry')
                    for i in range(test.shape[0]):
                        C.need(cursor<len(rows),'MMLU row overrun')
                        row=rows[cursor];cursor+=1
                        text=author['gen_prompt'](dev,subject,5)+author['format_example'](test,i,include_answer=False)
                        C.need(row['id']=='mmlu-%s-%04d'%(subject,i)and row['subject']==subject
                               and row['index']==i and row['ntrain']==5 and row['gold']==test.iloc[i,5]
                               and row['prompt_text']==text,'actual full official MMLU author formatter/gold/order')
                        yield row,text,dict(subject=subject,index=i,ntrain=5,gold=test.iloc[i,5])
                C.need(cursor==len(rows)==14042,'whole MMLU official coverage')
            iterable=mmlu_cases()
        n=0;maximum=0
        for row,content,gold in iterable:
            if task=='GSM8K':
                C.need(row['id']==gold['original']['id']and row['gold_row']==gold['gold_row']
                       and row['prompt_token_ids']==gold['original']['prompt_token_ids'],
                       'same actual official GSM gold and original complete token list')
            elif task=='HumanEval':
                C.need(row['id']==gold['official_problem']['task_id']and row['official_problem']==gold['official_problem']
                       and row['prompt_text']==content,'same exact official HE problem/prompt/test/entrypoint')
            actual=whole_decode(tok,row['prompt_token_ids'])
            # GSM format instruction is now part of the declared author content.
            K.validate(content,actual,tok.chat_template)
            if task!='GSM8K':
                C.need(S.text_hash(actual)==row['rendered_text_sha256']
                       and S.text_hash(content)==row['author_content_sha256'],'all preserved011 text/template receipts')
            maximum=max(maximum,len(row['prompt_token_ids']));n+=1;all_prompt_bytes+=len(actual.encode())
            chain.update(bytes.fromhex(C.digest(dict(id=row['id'],row_sha256=C.digest(row),
                actual_decoded_prompt_sha256=S.text_hash(actual),official_gold_sha256=C.digest(gold),
                author_content_sha256=S.text_hash(content)))))
        C.need(n==C.COUNTS[task],'measured full source/decoded-template cohort')
        counts[task]=n;chains[task]=chain.hexdigest();maxima[task]=maximum
    C.cpu_runtime();C.current_authority(m['authority_ref'])
    return dict(schema='bole.actual-full-decoder-input-provenance/v012',counts=counts,
        ordered_verified_row_chains=chains,max_prompt_tokens=maxima,total_decoded_prompt_bytes=all_prompt_bytes,
        GSM_instruction_token_ids=C.INSTRUCTION_IDS,GSM_instruction_actual_decoded_text=instruction,
        GSM_instruction_decoded_sha256=S.text_hash(instruction),official_source_files=len(official),
        complete_official_source_gold_and_template_coverage=True,prompt_tokenization_repeated=False,
        prompt_chat_rendering_repeated=False,model_output_consumed=False,task_score_produced=False,NPU=False)
