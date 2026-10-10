"""Real stdlib aggregate/import/reference regressions; no compile/NPU claims."""
import ast,hashlib,json,math,os,subprocess,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
import layout as L
import reference as R
import contract as C
import kernel as K
import numeric as N
import reader_consume as I
from runtime_cache import Cache
from unittest.mock import patch
def layout():
    return dict(permutation=list(reversed(range(256))),starts=[0,1,64,129,256],smooth=[1.]*256,clip=.95)
def encode_fixture(length,bits,kind):
    """Independent fixture pack in ORIGINAL variable-group order, not candidate mapping."""
    l=layout();p=bytearray();s=[];z=[];n=8//bits
    for t in range(length):
        for g,(a,b)in enumerate(zip(l["starts"],l["starts"][1:])):
            width=(b-a+n-1)//n;codes=[(t+j+g)%((1<<bits))for j in range(b-a)]
            codes.extend([0]*(width*n-len(codes)))
            for x in range(width):p.append(sum(codes[x*n+j]<<(bits*(n-1-j))for j in range(n)))
            s.append(R.scalar(.125*(g+1),kind));z.append(R.scalar(-.25*(g+1),kind))
    original=R.bytes_a16([((t+c)%17-8)*.0625 for t in range(length)for c in range(256)],kind)
    return bytes(p),R.bytes_a16(s,kind),R.bytes_a16(z,kind),original,l
class ReaderTests(unittest.TestCase):
    def test01_complete_source_compile(self):
        for p in HERE.glob("*.py"):
            compile(p.read_bytes(),str(p),"exec");ast.parse(p.read_bytes())
    def test02_all_original_channel_addresses(self):
        l=layout()
        for bits in(2,4):
            rows,stride=L.addresses(l,bits);n=8//bits;offset=0
            for g,(a,b)in enumerate(zip(l["starts"],l["starts"][1:])):
                for j in range(b-a):self.assertEqual(rows[l["permutation"][a+j]],[offset+j//n,bits*(n-1-j%n),g])
                offset+=(b-a+n-1)//n
            self.assertEqual(offset,stride);self.assertEqual(len(rows),256)
    def test03_group_padding_is_not_fixed32(self):
        _,s=L.addresses(layout(),2);self.assertEqual(s,66)
        _,s=L.addresses(layout(),4);self.assertEqual(s,130)
    def test04_reject_arbitrary_permutation(self):
        x=layout();x["permutation"][0]=0
        with self.assertRaises(ValueError):L.addresses(x,2)
    def test05_reject_empty_group_or_smoothing(self):
        for key,value in(("starts",[0,0,64,129,256]),("smooth",[2.]*256),("clip",1.)):
            x=layout();x[key]=value
            with self.assertRaises(ValueError):L.addresses(x,2)
    def test06_real_window_boundaries(self):
        for n in(1,4,5,6,127,128,132,133,134,4096,32768,33792):
            a,b=L.interval(n);self.assertEqual((a,b),(min(5,n),max(min(5,n),n-128)))
            edges=[L.edge_index(t,n)for t in range(n)if not a<=t<b]
            self.assertEqual(edges,list(range(len(edges))));self.assertLessEqual(len(edges),133)
    def test07_reject_middle_edge_alias(self):
        with self.assertRaises(ValueError):L.edge_index(5,4096)
    def test08_complete_scalar_decode_inverse_and_edges(self):
        for kind in("float16","bfloat16"):
            for bits in(2,4):
                p,s,z,o,l=encode_fixture(134,bits,kind);result=R.decode_axis(p,s,z,o,l,bits,kind,134)
                self.assertEqual(result[:5], [R.values(o,kind)[t*256:(t+1)*256]for t in range(5)])
                self.assertEqual(result[6:], [R.values(o,kind)[t*256:(t+1)*256]for t in range(6,134)])
                n=8//bits;offset=5*sum((b-a+n-1)//n for a,b in zip(l["starts"],l["starts"][1:]))
                for g,(a,b)in enumerate(zip(l["starts"],l["starts"][1:])):
                    for j in range(b-a):
                        code=(p[offset+j//n]>>(bits*(n-1-j%n)))&((1<<bits)-1)
                        expect=R.scalar(R.scalar(code*R.values(s,kind)[20+g],kind)+R.values(z,kind)[20+g],kind)
                        self.assertEqual(result[5][l["permutation"][a+j]],expect)
                    offset+=(b-a+n-1)//n
    def test09_no_quant_short_rows(self):
        p,s,z,o,l=encode_fixture(5,2,"float16")
        self.assertEqual(R.decode_axis(p,s,z,o,l,2,"float16",5),[R.values(o,"float16")[i*256:(i+1)*256]for i in range(5)])
    def test10_plane_extent_rejected(self):
        p,s,z,o,l=encode_fixture(134,2,"bfloat16")
        with self.assertRaises(ValueError):R.decode_axis(p[:-1],s,z,o,l,2,"bfloat16",134)
    def test11_attention_all1536_reference(self):
        q=[[0.]*256 for _ in range(6)];k=[[1.]*256,[2.]*256];v=[[1.]*256,[3.]*256]
        actual=R.attention(q,k,v,"float16")
        self.assertEqual(R.values(actual["output"],"float16"),[2.]*1536)
        self.assertEqual(R.compare(actual["output"],actual["output"],"float16")["relative_rms"],0.)
    def test12_whole_output_nonfinite_and_threshold_reject(self):
        good=R.bytes_a16([1.]*1536,"float16");bad=R.bytes_a16([1.01]*1536,"float16")
        with self.assertRaises(ValueError):R.compare(bad,good,"float16")
        with self.assertRaises(ValueError):R.compare(bytes.fromhex("007c"),bytes.fromhex("003c"),"float16")
    def test13_default_off_does_not_call_qualifier(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):K.build(None,None,None,device_properties={},validate_nd=None,qualify=lambda:self.fail("OFF called qualifier"))
    def test14_actual_factory_global_binding_and_rebind_refusal(self):
        original=K.__dict__.get("tl");has="tl"in K.__dict__
        fake=types.SimpleNamespace(constexpr=object())
        jit=types.SimpleNamespace(jit=lambda fn:fn)
        with patch.dict(os.environ,{K.ENV:"1"}):
            if has:K.__dict__.pop("tl")
            try:
                cls=K.build(None,jit,fake,device_properties=dict(num_aicore=24,num_vectorcore=48),
                  validate_nd=lambda x:None,qualify=lambda:None)
                r=cls();self.assertIs(r.qk.__globals__["tl"],fake);self.assertEqual(r.av.__name__,"av")
                with self.assertRaises(ValueError):K.bind_jit_language(object())
            finally:
                K.__dict__.pop("tl",None)
                if has:K.__dict__["tl"]=original
    def test15_masked_signed_conversion_not_packed_word_cast(self):
        tree=ast.parse((HERE/"kernel.py").read_text());text=ast.unparse(tree)
        self.assertEqual(text.count("code.to(tl.int32).to(tl.float32)"),2)
        self.assertIn("word >> shift",text);self.assertIn("enable_fp_fusion=False",text)
        self.assertNotIn("32 // BITS",text);self.assertNotIn("KP +",text)
    def test16_independent_reference_has_no_candidate_math_import(self):
        tree=ast.parse((HERE/"reference.py").read_text())
        names=[n.names[0].name for n in ast.walk(tree)if isinstance(n,ast.Import)]
        self.assertEqual(names,["math"]);self.assertNotIn("import layout",ast.unparse(tree))
    def test17_actual_default_off_cli_clean_I(self):
        for name in("numeric.py","reader_consume.py","software_check.py","model_consume.py","reader_host.py","reader_whole.py","reader_cpu.py","reader_canary.py"):
            result=subprocess.run([sys.executable,"-I","-B",str(HERE/name)],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(json.loads(result.stdout)["model_ready"])
    def test18_metadata_ref_extra_and_bool_rejected(self):
        for x in({"path":"x","bytes":True,"sha256":"0"*64},{"path":"x","bytes":1,"sha256":"0"*64,"origin":"fake"}):
            with self.assertRaises(ValueError):C.read(x)
    def test19_true_owner_proof_wrong_card_rejects_before_any_module(self):
        value=dict(schema="skvq.compiled-reader.owned-proof/v1",source_ref={},writer_whole_ref={},image="wrong",physical_card=0)
        with self.assertRaises(ValueError):C.proof(value,{}, {})
    def test20_actual_old_writer_axis_not_sufficient_model_permission(self):
        value=dict(schema="skvq.actual-writer.whole/v1",status="source_only")
        with patch.object(C,"obj",return_value=value):
            with self.assertRaises(ValueError):C.writer_whole({})
    def test21_source_scalar_name_concatenation(self):
        needles=("__name__"+"for","__func__"+"is","__func__"+"and","__self__"+"is")
        for p in HERE.glob("*.py"):
            for needle in needles:self.assertNotIn(needle,p.read_text())
if __name__=="__main__":unittest.main()
