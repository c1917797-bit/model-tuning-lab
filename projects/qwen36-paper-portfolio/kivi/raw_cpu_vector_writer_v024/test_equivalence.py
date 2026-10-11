"""Exact-byte reference equivalence, local CPU only; never consumes actual018 raw."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
SCALAR_SHA = "45ccb0c2fff417e518cb591aaf5ba201645551a1aeafc9d8bdc3c97ce6a8fd49"
CHECKED = 0
S = V = NP = None
ACTUAL_TILES = None


def load(path, name, sha=None):
    data = path.read_bytes()
    if sha is not None:
        assert hashlib.sha256(data).hexdigest() == sha
    assert name not in sys.modules, "no ambient test module substitution"
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def scalar(raw, axis, bits, dtype):
    values = S.scalars(raw, dtype)
    return S.pack((values[t*256:(t+1)*256] for t in range(128)), axis, bits, dtype)


def equivalent(raw, axis, bits, dtype):
    global CHECKED
    try:
        expected = scalar(raw, axis, bits, dtype)
    except (ValueError, OverflowError) as exc:
        with unittest.TestCase().assertRaises(type(exc)):
            V.pack_tile(raw, axis, bits, dtype, NP)
        CHECKED += 1
        return
    actual = V.pack_tile(raw, axis, bits, dtype, NP)
    for name in ("axis", "tokens", "dim", "bits", "dtype", "payload", "scales", "minima"):
        unittest.TestCase().assertEqual(actual[name], getattr(expected, name), name)
    CHECKED += 1


def tile_values(kind, dtype):
    if kind == "ramp":
        values = [((i*17)%257-128)/16.0 for i in range(128*256)]
    elif kind == "random":
        values = NP.random.default_rng(1988).normal(size=128*256).tolist()
    elif kind == "constant":
        values = [-3.25]*(128*256)
    elif kind == "zeros":
        values = [-0.0 if i%5 in (0,1) else 0.0 for i in range(128*256)]
    elif kind == "signed_subnormal":
        unit = 2**(-24 if dtype == "float16" else -133)
        values = [(-1 if i%3 else 1)*(i%32)*unit for i in range(128*256)]
    elif kind == "underflow":
        unit = 2**(-24 if dtype == "float16" else -133)
        values = [(i%2)*unit for i in range(128*256)]
    elif kind == "wide":
        size = 60000.0 if dtype == "float16" else 3e38
        values = [-size if i%2 else size for i in range(128*256)]
    elif kind == "tie":
        values = [(0.0, 0.5, 1.5, 2.5, 3.0)[i%5] for i in range(128*256)]
    else:
        raise AssertionError(kind)
    return S.scalar_bytes(values, dtype)


class Equivalence(unittest.TestCase):
    def test01_full_tile_matrix(self):
        for dtype in ("float16", "bfloat16"):
            for kind in ("ramp", "random", "constant", "zeros", "signed_subnormal",
                         "underflow", "wide", "tie"):
                blob = tile_values(kind, dtype)
                for bits in (2, 4):
                    for axis in ("K", "V"):
                        with self.subTest(dtype=dtype, kind=kind, bits=bits, axis=axis):
                            equivalent(blob, axis, bits, dtype)

    def test02_all_finite_a16_identity(self):
        for dtype in ("float16", "bfloat16"):
            raw = b"".join(struct.pack("<H", word) for word in range(65536))
            decoded = V._decode(raw, dtype, NP)
            finite = decoded[NP.isfinite(decoded)]
            expected = S.scalar_bytes(finite.tolist(), dtype)
            self.assertEqual(V._encode(finite, dtype, NP), expected)

    def test03_float16_rounding_halfway(self):
        a = NP.arange(0, 0x7bff, dtype="<u2").view("<f2").astype(NP.float64)
        b = NP.arange(1, 0x7c00, dtype="<u2").view("<f2").astype(NP.float64)
        for midpoint in ((a+b)/2, -(a+b)/2):
            self.assertEqual(V._encode(midpoint, "float16", NP),
                             S.scalar_bytes(midpoint.tolist(), "float16"))

    def test04_bfloat16_rounding_halfway(self):
        a = V._decode(NP.arange(0, 0x7f7f, dtype="<u2").tobytes(), "bfloat16", NP)
        b = V._decode(NP.arange(1, 0x7f80, dtype="<u2").tobytes(), "bfloat16", NP)
        for midpoint in ((a+b)/2, -(a+b)/2):
            self.assertEqual(V._encode(midpoint, "bfloat16", NP),
                             S.scalar_bytes(midpoint.tolist(), "bfloat16"))

    def test05_halfway_nextafter_both_sides(self):
        for dtype in ("float16", "bfloat16"):
            mid = NP.asarray([0.5,1.5,2.5,3.5,7.5,14.5], dtype=NP.float64)
            values = NP.concatenate([NP.nextafter(mid,-NP.inf),mid,NP.nextafter(mid,NP.inf)])
            for sign in (-1,1):
                self.assertEqual(V._encode(values*sign,dtype,NP),
                                 S.scalar_bytes((values*sign).tolist(),dtype))

    def test06_signed_zero_minima_first_operand(self):
        for dtype in ("float16", "bfloat16"):
            for first in (-0.0, 0.0):
                group = [first]+[-first]*31
                codes, scale, low = V._groups(NP.asarray([group]),2,dtype,NP)
                original = S.group(group,2,dtype)
                self.assertEqual(codes.tolist()[0],list(original[0]))
                self.assertEqual(V._encode(low,dtype,NP),S.scalar_bytes([original[2]],dtype))
                self.assertEqual(V._encode(scale,dtype,NP),S.scalar_bytes([original[1]],dtype))

    def test07_nonfinite_rejected(self):
        for dtype in ("float16","bfloat16"):
            for value in (float("nan"),float("inf"),-float("inf")):
                with self.assertRaises(ValueError):S.cast(value,dtype)
                with self.assertRaises(ValueError):V._round_a16([value],dtype,NP)

    def test08_float_overflow_exception(self):
        for dtype, value in (("float16",65520.0),("bfloat16",3.5e38)):
            for sign in (-1,1):
                with self.assertRaises(OverflowError):S.cast(sign*value,dtype)
                with self.assertRaises(OverflowError):V._round_a16([sign*value],dtype,NP)

    def test09_bfloat_round_to_infinity_not_clamped(self):
        values=[3.4028234663852886e38,-3.4028234663852886e38]
        actual=V._round_a16(values,"bfloat16",NP)
        self.assertEqual(actual.tolist(),[S.cast(x,"bfloat16")for x in values])
        for x in actual:
            with self.assertRaises(ValueError):S.cast(float(x),"bfloat16")
        with self.assertRaises(ValueError):V._round_a16(actual,"bfloat16",NP)

    def test10_packing_order_known_codes(self):
        group = [0,1,2,3]*8
        for dtype in ("float16","bfloat16"):
            # V: each row has eight identical channel groups.
            raw=S.scalar_bytes(group*8*128,dtype)
            actual=V.pack_tile(raw,"V",2,dtype,NP)
            self.assertEqual(actual["payload"],bytes.fromhex("e4e4e4e4")*(128*16))
            equivalent(raw,"V",2,dtype)
            # K: tokens cycle0,1,2,3; words vary only by token group.
            raw=S.scalar_bytes([float(t%4)for t in range(128)for d in range(256)],dtype)
            actual=V.pack_tile(raw,"K",2,dtype,NP)
            self.assertEqual(actual["payload"],bytes.fromhex("e4e4e4e4")*(8*256))
            equivalent(raw,"K",2,dtype)

    def test11_one_byte_mutation_is_visible(self):
        raw=tile_values("ramp","bfloat16")
        expected=scalar(raw,"K",2,"bfloat16")
        actual=V.pack_tile(raw,"K",2,"bfloat16",NP)
        bad=bytearray(actual["payload"]);bad[13]^=1
        self.assertNotEqual(bytes(bad),expected.payload)
        self.assertEqual(actual["payload"],expected.payload)

    def test12_bounds_are_not_partial_coverage(self):
        raw=bytes(65536)
        for data in (b"",raw[:-2],raw+b"00",bytearray(raw)):
            with self.assertRaises(ValueError):V.pack_tile(data,"K",2,"bfloat16",NP)
        for bits in (0,1,3,8,True,2.0):
            with self.assertRaises(ValueError):V.pack_tile(raw,"K",bits,"bfloat16",NP)
        with self.assertRaises(ValueError):V.pack_tile(raw,"wrong",2,"bfloat16",NP)
        with self.assertRaises(ValueError):V.pack_tile(raw,"K",2,"float32",NP)

    def test13_byte_input_nan_and_infinity(self):
        for dtype,words in (("float16",(0x7c00,0xfc00,0x7e00)),("bfloat16",(0x7f80,0xff80,0x7fc0))):
            for word in words:
                raw=struct.pack("<H",word)+bytes(65534)
                for axis in ("K","V"):
                    equivalent(raw,axis,2,dtype)

    def test14_no_candidate_or_torch_import(self):
        self.assertFalse(any(name in sys.modules for name in ("torch","torch_npu","triton")))
        imports=[]
        import ast
        for node in ast.walk(ast.parse((HERE/"independent_vector_writer.py").read_text())):
            if isinstance(node,ast.Import):imports.extend(alias.name for alias in node.names)
            if isinstance(node,ast.ImportFrom):imports.append(node.module)
        self.assertEqual(imports,["math"])

    def test15_retained018_actual_two_tiles(self):
        import base64
        expected = ("d48f1de42eb47c79a0b80a89ada3508526b296bd6adeda7562c082b1e93d48eb",
                    "e1dc65b8d1cab8d7fe18533ef198be6154cebb91be473db8dda8ecf31e12274f")
        if ACTUAL_TILES is not None:
            archive = ACTUAL_TILES.read_bytes()
            self.assertEqual(hashlib.sha256(archive).hexdigest(),
                             "b4e97fc2dcf718ff6ede0f6d29f43c0f44944f6afa597075a557a19bc294fe3a")
            rows = json.loads(archive)["entries"]
        else:
            # Same-image source-only suite reads the exact retained original input mount.
            original = Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/packed-raw")
            rows = []
            for axis, sha in zip(("K", "V"), expected):
                path = original / ("r0-language_model-model-layers-11-self_attn-attn-e000001-s00-PREFILL-ORIGINAL-"+axis+"-00000.bin")
                blob = path.read_bytes()
                rows.append(dict(path=str(path), bytes=len(blob), sha256=sha, base64=base64.b64encode(blob).decode()))
        self.assertEqual(len(rows), 2)
        for row, axis, sha in zip(rows, ("K", "V"), expected):
            blob = base64.b64decode(row["base64"], validate=True)
            self.assertEqual(len(blob), 65536)
            self.assertEqual(row["bytes"], len(blob)); self.assertEqual(row["sha256"], sha)
            self.assertEqual(hashlib.sha256(blob).hexdigest(), sha)
            self.assertTrue(row["path"].endswith("PREFILL-ORIGINAL-"+axis+"-00000.bin"))
            equivalent(blob, axis, 2, "bfloat16")


def benchmark():
    tile=tile_values("ramp","bfloat16")
    start=time.perf_counter();cpu=time.process_time();h=hashlib.sha256()
    for index in range(256):
        for axis in ("K","V")if index<255 else ("K",):
            value=V.pack_tile(tile,axis,2,"bfloat16",NP)
            for name in ("payload","scales","minima"):h.update(value[name])
    elapsed=time.perf_counter()-start
    assert h.hexdigest()=="d77783ff6806cfdd7323993e6ddef4aaa4076087f3b01924f5d7f0288d16ec37"
    return dict(original_prompt_tokens=32768,K_tiles=256,V_tiles=255,
                measured_FA_count=1,all64_measured=False,actual018_input=False,
                output_digest=h.hexdigest(),wall_seconds=elapsed,cpu_seconds=time.process_time()-cpu,
                local64_writer_extrapolation_seconds=64*elapsed,numeric_pass=False,NPU=False)


def main():
    global S,V,NP,ACTUAL_TILES
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scalar-source",type=Path,required=True)
    parser.add_argument("--benchmark",action="store_true")
    parser.add_argument("--actual-tiles",type=Path)
    args=parser.parse_args()
    ACTUAL_TILES=args.actual_tiles
    import numpy as np
    NP=np
    S=load(args.scalar_source,"_local_kivi_scalar_equivalence",SCALAR_SHA)
    V=load(HERE/"independent_vector_writer.py","_local_kivi_vector_equivalence")
    start=time.perf_counter()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Equivalence))
    report=dict(schema="kivi.vector-reference-local-equivalence/v1",tests=result.testsRun,
                failures=len(result.failures),errors=len(result.errors),comparisons=CHECKED,
                elapsed=time.perf_counter()-start,python=sys.version,numpy=np.__version__,
                scalar_sha256=SCALAR_SHA,
                vector_sha256=hashlib.sha256((HERE/"independent_vector_writer.py").read_bytes()).hexdigest(),
                actual018_raw=False,NPU=False,model_pass=False,consumer_integration=False)
    if result.wasSuccessful()and args.benchmark:report["full_one_FA_benchmark"]=benchmark()
    print(json.dumps(report,sort_keys=True),flush=True)
    return 0 if result.wasSuccessful()else 1


if __name__=="__main__":
    raise SystemExit(main())
