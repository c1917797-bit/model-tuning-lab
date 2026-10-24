"""Emit exactly seven source-review operands, not authority."""
import argparse,importlib.util,json,os,resource
from pathlib import Path
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--output',required=True);a=p.parse_args()
 os.sched_setaffinity(0,{145});resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
 own=Path(__file__).parent;s=importlib.util.spec_from_file_location('_v12review',own/'runtime_lossless_imports.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
 b=R.render();R.inverse(b);m=b['manifest']
 V=R.module(b['files']['qualification_source_validate.py'],R.ROOT/'qualification_source_validate.py','_v12_review_scope')
 values=dict(scope=V.SCOPE,source_root=m['root'],output_root=m['output_root'],files=m['files'],parent_preparation_readset=m['qualification_parent_preparation_readset'],historical_short_source=m['qualification_historical_short_source'],short2k_helper_refs=m['short2k_helper_refs'])
 out=Path(a.output)
 with out.open('xb')as f:f.write((json.dumps(values,sort_keys=True)+'\n').encode())
 print(json.dumps(dict(files=len(b['files']),whole_inverse=True,not_authority=True,review=R.ref(out,out.read_bytes()))))
if __name__=='__main__':main()
