import unittest
from damp_integration.contract import (GDN_LAYERS, Ownership, Row, Unsupported, admit, byte_counts, typed_shapes)

class AdmissionTests(unittest.TestCase):
    def test_layers(self):
        self.assertEqual(len(GDN_LAYERS), 48)
        self.assertNotIn(3, GDN_LAYERS)

    def test_cache_payload(self):
        shapes = typed_shapes((3, 2560))
        self.assertEqual(len(shapes), 4)
        self.assertEqual(shapes[1:], ((12,128,16), (12,128,112), (12,4,112)))
        sizes = byte_counts((3,2560), 801792)
        self.assertEqual(sizes["typed_payload_bytes"], 258048)
        self.assertEqual(sizes["native_payload_bytes"], 801792)
        self.assertEqual(sizes["allocated_page_bytes"], 801792)  # no false memory win

    def test_initial_prefill_and_decode(self):
        pre = admit([Row("a", 2, 1024, 0, 1024)], 3)
        owner = Ownership()
        owner.check(pre)
        owner.publish(pre)
        step = admit([Row("a", 2, 1, 1024, 1024)], 3)
        owner.check(step)
        owner.publish(step)
        self.assertEqual(step.actual_seq_lengths, (0,1))
        owner.check(admit([Row("a", 2, 1, 1025, 1024)], 3))

    def test_recycled_and_skipped_rejected(self):
        owner = Ownership()
        owner.publish(admit([Row("a", 2, 1024, 0, 1024)], 3))
        for row in (Row("b",2,1,1024,1024), Row("a",2,1,1025,1024)):
            with self.assertRaises(Unsupported):
                owner.check(admit([row], 3))
        owner.publish(admit([Row("b",2,1024,0,1024)], 3))
        owner.check(admit([Row("b",2,1,1024,1024)], 3))

    def test_all_unsupported_scheduler_states(self):
        cases = [
            [Row("a",0,1,0,1)],  # first-token prefill
            [Row("a",0,512,0,1024)],  # chunked initial
            [Row("a",0,512,512,1024)],  # continuation
            [Row("a",0,0,1024,1024)],  # dummy padding
            [Row("a",-1,1,1024,1024)],
            [Row("a",0,1,1024,1024), Row("b",0,1,1024,1024)],
            [Row("a",0,1,1024,1024), Row("a",1,1,1024,1024)],
            [Row("a",0,1,1024,1024), Row("b",1,1024,0,1024)], # mixed
        ]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(Unsupported):
                admit(rows, 32, 16)

    def test_exact_b16_but_not_intermediate_batches(self):
        rows = [Row(str(i),i,1,1024,1024) for i in range(16)]
        self.assertEqual(admit(rows,20,16).actual_seq_lengths, (0,)+(1,)*16)
        for count in range(2,16):
            with self.assertRaises(Unsupported):
                admit(rows[:count],20,16)
        with self.assertRaises(Unsupported):
            admit(rows,20,1)

    def test_bad_geometry(self):
        for shape in ((3,1280),(4,2560)):
            with self.assertRaises(Unsupported):
                typed_shapes(shape)

if __name__ == "__main__":
    unittest.main()

