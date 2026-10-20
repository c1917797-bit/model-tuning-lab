"""Actual same-image public tokenizer factory diagnostic. No full task pass.
Auto entry calls the unchanged frozen decoder. Public entry calls the installed
real TokenizersBackend.from_pretrained. The no-accelerator guard is unchanged.
"""
import argparse
import json
import os
from pathlib import Path
import sys
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_common as C
import cpu_import_guard as A


def run(x,T,out):
    mode=x['tokenizer_probe'];C.need(mode in{'auto','public-backend'}and x['diagnostic_only']is True,'explicit new diagnostic source profile')
    C.tokenizer_sources(x,host=False);T.cpu_runtime();m=T.source(x['task_source_unbound_ref'],allow_unbound_inputs=True)
    base=T.obj(m['rendered_inputs_ref']);D=T.load(m['files']['decoder.py'],'_cpu_actual_frozen_decoder_probe')
    for r in base['tokenizer_assets']:T.checked(r)
    trace=A.Trace(out,x['task_source_unbound_ref']);outcome=None;error=None;controls=None;identity=None;loaded=False
    try:
        if mode=='auto':
            tok,identity=D.create(m,base)
        else:
            # Reuse the same frozen asset/class/version checks; only the public
            # factory selection is under diagnostic comparison, not a task run.
            G=D.S.gsm_module(m['files']['frozen/gsm_scorer.py']);expected=G.BINDING['assets']
            C.need(len(base['tokenizer_assets'])==len(expected)==7,'same seven original checkpoint assets')
            roots=set()
            for r in base['tokenizer_assets']:
                path=T.checked(r);C.need(r['sha256']==expected[path.name]['sha256'],'exact original tokenizer asset');roots.add(path.parent)
            C.need(roots=={Path('/models/Qwen3.6-27B')},'same exact original tokenizer root')
            import transformers,tokenizers
            T.cpu_runtime();C.need((transformers.__version__,tokenizers.__version__)==('5.5.4','0.22.2'),'same actual tokenizer versions')
            original=T.obj(m['original_inputs_ref']);libraries=[]
            for module in(transformers,tokenizers):
                r=T.ref(Path(module.__file__).resolve());C.need(r in original['library_refs'],'same actual original library source');libraries.append(r)
            from transformers.tokenization_utils_tokenizers import TokenizersBackend
            T.cpu_runtime()
            tok=TokenizersBackend.from_pretrained('/models/Qwen3.6-27B',local_files_only=True,trust_remote_code=False)
            T.cpu_runtime();C.need(type(tok)is TokenizersBackend and tok.eos_token_id==248046 and tok.clean_up_tokenization_spaces is False,'actual same public TokenizersBackend/EOS/cleanup identity')
            identity=dict(versions=dict(transformers=transformers.__version__,tokenizers=tokenizers.__version__),
                tokenizer_class=type(tok).__module__+'.'+type(tok).__qualname__,eos_token_id=tok.eos_token_id,
                clean_up_tokenization_spaces=tok.clean_up_tokenization_spaces,assets=base['tokenizer_assets'],libraries=libraries,
                public_factory='TokenizersBackend.from_pretrained',decoder_semantic_equivalence_not_yet_qualified=True)
        trace.check();T.cpu_runtime();loaded=True;controls=D.controls(tok);trace.check();T.cpu_runtime()
        outcome='public-factory-and-original-tiny-controls-completed'
    except BaseException as e:
        error=repr(e)
        if trace.forbidden:
            T.cpu_runtime();outcome='forbidden-import-observed-and-denied-before-execution'
        else:raise
    finally:trace.close()
    C.tokenizer_sources(x,host=False);T.cpu_runtime()
    return dict(schema='bole.actual-tokenizer-public-factory-diagnostic/v1',entry=mode,outcome=outcome,error=error,
        import_audit_ref=C.ref(trace.path),forbidden_attempts=list(trace.forbidden),tokenizer_constructed=loaded,
        identity=identity,tiny_original_decoder_controls=controls,all15525_provenance_executed=False,
        environment={k:os.environ.get(k)for k in __import__('owner_namespace').TOKENIZER_ENV},
        diagnostic_only=True,software_qualification_accepted=False,task_score_produced=False,model_ready=False,NPU=False)


if __name__=='__main__':
    argparse.ArgumentParser(description='Default OFF; actual probe runs only through finite source-bound CPU owner.',allow_abbrev=False).parse_args()
    print('{"enabled":false,"NPU":false,"software_qualification_accepted":false}')
