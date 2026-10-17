"""No-model local HTTP transport check using actual client and original helper."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import client
def main():
 ap=argparse.ArgumentParser(allow_abbrev=False);ap.add_argument('--url',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if not a.url.startswith('http://127.0.0.1:'):raise ValueError('local transport check only')
 p=P/'fixtures/native_capture_overlay.py';b=p.read_bytes()
 if(len(b),hashlib.sha256(b).hexdigest())!=(6707,'848e180ac7612a69996a901ae68e3858825bf0878bbb0653708d55c37e4a234f'):raise ValueError('exact actual003 overlay')
 spec=importlib.util.spec_from_file_location('_101R10_actual003_overlay',p);o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
 C=client.http_module((P/'fixtures/native_capture_client.py').read_bytes(),o,o.need,P/'fixtures/native_capture_client.py')
 # Explicit SOFTWARE architecture/vocab fixture only. Actual main retains the
 # exact real checkpoint SHA check and normal source/model launch prerequisites.
 body=client.payload2048(dict(model_type='qwen3_5',text_config=dict(vocab_size=248320)),o.need)
 result=C.request_once(a.url,body,a.output,'SOFTWARE101R10-decode')
 print(json.dumps(dict(schema='deltalog.local-client-wire-control/v101R10',isolated=bool(sys.flags.isolated),actual_request_helper=True,result=result,NPU=False,model_qualified=False)))
if __name__=='__main__':main()
