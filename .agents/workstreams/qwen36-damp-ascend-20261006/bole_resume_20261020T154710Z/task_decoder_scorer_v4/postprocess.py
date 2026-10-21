"""Prospective rules accepted and frozen before any task model output.

GSM remains the exact original scorer. MMLU is explicitly generative, not the
old likelihood protocol. HE performs only declared transport/prompt de-duplication.
"""
import hashlib
import re
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C

PROTOCOL='bole.three-task-postprocess/prospective-v1'
GSM_SHA='a6abc4d1172517b0572919ab67cc49a0751f28f41dbcfb1a6a7e13f7a8120948'
MMLU_LEADING=re.compile(r'^(?:Answer:\s*)?([ABCD])(?=$|[\s.)])')
HE_OUTER_FENCE=re.compile(r'\A[ \t\r\n]*```(?:python)?\r?\n(?P<body>[\s\S]*?)\r?\n```[ \t\r\n]*\Z')


def text_hash(text):return hashlib.sha256(text.encode('utf8')).hexdigest()


def gsm_module(reference=None):
    reference=C.ref(P/'frozen/gsm_scorer.py')if reference is None else reference
    C.need(reference['sha256']==GSM_SHA,'unchanged entire original GSM scorer source')
    return C.load(reference,'_bole_original_GSM_scorer')


def gsm_grade(text,gold_row,reference=None):
    G=gsm_module(reference)
    C.need(type(text)is str and type(gold_row)is dict and type(gold_row['answer'])is str,
           'actual decoded string and original official GSM gold row')
    C.need(G.extract_answer(gold_row['answer'])!=G.INVALID_ANS,'official GSM gold has original exact answer marker')
    return dict(answer=G.extract_answer(text),gold=G.extract_answer(gold_row['answer']),
                correct=bool(G.is_correct(text,gold_row)),decoded_sha256=text_hash(text),
                scorer_sha256=GSM_SHA,rule='original first #### numeric-string extraction; comma removal only')


def mmlu_grade(text,gold):
    C.need(type(text)is str and gold in('A','B','C','D'),'actual generated text and unchanged official MMLU gold')
    first=next((line.strip()for line in text.splitlines()if line.strip()),'')
    match=MMLU_LEADING.match(first)
    prediction=None if match is None else match.group(1)
    return dict(prediction=prediction,gold=gold,correct=prediction==gold,
                first_nonempty_line_sha256=text_hash(first),decoded_sha256=text_hash(text),
                postprocess_protocol=PROTOCOL,
                rule='first nonempty line, anchored uppercase A-D; optional literal Answer: prefix; no body search',
                likelihood_used=False)


def human_eval_completion(text,official_prompt):
    C.need(type(text)is str and type(official_prompt)is str and official_prompt,
           'actual decoded completion and exact original official prompt')
    match=HE_OUTER_FENCE.fullmatch(text)
    body=text if match is None else match.group('body')
    if match is not None and '```'in body:
        # Multiple/nested fences are outside the declared single-envelope rule.
        match=None;body=text
    removed=body.startswith(official_prompt)
    completion=body[len(official_prompt):]if removed else body
    return dict(completion=completion,raw_decoded_sha256=text_hash(text),
        after_fence_sha256=text_hash(body),completion_sha256=text_hash(completion),
        outer_single_fence_removed=match is not None,exact_original_prompt_prefix_removed=removed,
        official_prompt_sha256=text_hash(official_prompt),postprocess_protocol=PROTOCOL,
        fuzzy_repair_performed=False,indentation_rewritten=False,AST_rewritten=False)
