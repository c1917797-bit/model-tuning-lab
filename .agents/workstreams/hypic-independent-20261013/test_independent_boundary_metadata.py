import unittest
from independent_boundary_metadata import boundary_builder_config

class BoundaryMetadataTests(unittest.TestCase):
    def test_actual_long_window_geometry(self):
        for length in (65,4104,7176,12288):
            b,starts=boundary_builder_config(length,32,4)
            self.assertEqual(starts.tolist(),[0,length])
            self.assertEqual(b.vllm_config.model_config.hf_text_config.linear_num_value_heads,32)
            self.assertEqual(b.vllm_config.parallel_config.tensor_parallel_size,4)
    def test_invalid_geometry_rejected(self):
        for args in ((0,32,4),(64,31,4),(True,32,4),(64,32,0)):
            with self.assertRaises(ValueError):boundary_builder_config(*args)

if __name__=='__main__':unittest.main()
