import unittest
from dataclasses import make_dataclass
import torch
from independent_c2_cache_binding import BoundQueryWindow
from independent_c2_metadata import window_metadata


def metadata():
    values=dict(causal=True,num_decodes=0,num_decode_tokens=0,prefill=None,
        decode_meta=None,kvcomp_metadata=None,attn_state='native',
        num_actual_tokens_pcp_padded=12,num_actual_tokens=12,num_prefills=2,
        seq_lens=torch.tensor([6,6],dtype=torch.int32),
        seq_lens_cpu=torch.tensor([6,6],dtype=torch.int32),
        seq_lens_list=[6,6],actual_seq_lengths_q=[6,12],
        query_start_loc=torch.tensor([0,6,12],dtype=torch.int32),max_query_len=6,
        block_tables=torch.tensor([[4,5],[9,3]],dtype=torch.int32),
        slot_mapping=torch.arange(12,dtype=torch.int64),attn_mask=None)
    cls=make_dataclass('MetadataFixture',[(k,object) for k in values])
    return cls(**values)


class MetadataTests(unittest.TestCase):
    def test_window_preserves_other_request_and_native_object(self):
        native=metadata()
        window=BoundQueryWindow(0,2,(3,4),(39,12),5,(9,3))
        result=window_metadata(native,window,request_row=1,cache_hit_state='paged')
        self.assertEqual(result.actual_seq_lengths_q,[2])
        self.assertEqual(result.seq_lens_list,[5])
        self.assertEqual(result.slot_mapping.tolist(),[39,12])
        self.assertEqual(result.block_tables.tolist(),[[9,3]])
        result.block_tables[0,0]=100
        result.seq_lens_list[0]=100
        self.assertEqual(native.block_tables.tolist(),[[4,5],[9,3]])
        self.assertEqual(native.seq_lens_list,[6,6])
        self.assertEqual(native.attn_state,'native')

    def test_live_table_drift_and_mixed_batch_rejected(self):
        native=metadata()
        window=BoundQueryWindow(0,2,(3,4),(39,12),5,(9,3))
        native.block_tables[1,0]=8
        with self.assertRaises(ValueError):
            window_metadata(native,window,request_row=1,cache_hit_state='paged')
        native=metadata();native.num_decodes=1
        with self.assertRaises(ValueError):
            window_metadata(native,window,request_row=1,cache_hit_state='paged')


if __name__=='__main__':unittest.main()
