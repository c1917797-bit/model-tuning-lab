"""Real file/Ref/API checks for the new reader; no fake NPU receipt."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import fast_consume
from test_fast_oracle import OLD, encode, fixture


class ReaderTests(unittest.TestCase):
    def test_actual_consumer_and_failure_boundaries(self):
        for bits, dtype in ((2, "float16"), (4, "bfloat16")):
            with self.subTest(bits=bits, dtype=dtype), tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                def put(name, data):
                    path = root / name
                    path.write_bytes(data)
                    return {"path": str(path), "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()}
                pool, row, query = fixture(129, bits, dtype)
                old = OLD.attention(pool, row, query, bits, dtype)
                answer = [v for h in old["scalar_a16_boundary_output"] for v in h]
                identity = put("identity.json", b"{}")
                row.update(request_id="software-fixture-not-NPU", epoch=1, generation=1,
                           identity_refs={k: identity for k in fast_consume.IDENTITIES},
                           query_ref=put("q.raw", encode([x for h in query for x in h], dtype)),
                           output_ref=put("out.raw", encode(answer, dtype)))
                frame = dict(schema="kivi.actual-packed-qkav-frame/v1",
                             kernel_source_sha256="a" * 64, bits=bits, dtype=dtype,
                             pool_geometry=[3, 67, 2], rows=[row],
                             pool_fields={k: put(k + ".raw", v) for k, v in pool.items()})
                ref = put("frame.json", json.dumps(frame).encode())
                got = fast_consume.consume(ref, kernel_sha="a" * 64)
                self.assertEqual(got["rows"][0]["named_ascend_boundary_measure"]["max_abs"], 0)
                self.assertEqual(got["rows"][0]["full_output_elements"], 1536)
                self.assertFalse(got["model_ready"])
                self.assertEqual(len(got["reference_source_sha256"]), 64)
                with self.assertRaises(ValueError):
                    fast_consume.consume(ref, kernel_sha="b" * 64)
                with self.assertRaises(ValueError):
                    fast_consume.consume(dict(ref, sha256="0" * 64), kernel_sha="a" * 64)
                row["output_ref"] = put("bad-output.raw", encode([10.0] * 1536, dtype))
                bad = put("bad-frame.json", json.dumps(frame).encode())
                with self.assertRaisesRegex(ValueError, "RMS"):
                    fast_consume.consume(bad, kernel_sha="a" * 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
