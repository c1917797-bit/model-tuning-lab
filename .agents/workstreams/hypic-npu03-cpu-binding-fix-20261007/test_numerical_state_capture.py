import types
import unittest
import torch
from numerical_state_capture import Collector


class CaptureTests(unittest.TestCase):
    def test_snapshot_owns_cpu_bytes(self):
        collector = Collector(lambda event: None, rank=0)
        tensor = torch.tensor([1., 2.])
        snapshot = collector.tensor(tensor, "fixture")
        tensor.add_(9)
        self.assertEqual(snapshot["values"], [1., 2.])

    def test_budget_fails_closed(self):
        collector = Collector(lambda event: None, rank=0, max_scalars=1)
        with self.assertRaisesRegex(RuntimeError, "budget"):
            collector.tensor(torch.ones(2), "fixture")

    def test_position_capture_is_not_hot_or_device_proof(self):
        events = []
        ctx = types.SimpleNamespace(
            req_ids=("x",), plans={"x": types.SimpleNamespace(physical_positions=(0, 9))},
            num_scheduled_tokens={"x": 2}, batch_plan=types.SimpleNamespace(step_id=3))
        Collector(events.append, rank=1)("positions_committed", "x", dict(
            ctx=ctx, runner=types.SimpleNamespace(positions=torch.tensor([0, 9]))))
        self.assertEqual(events[0]["actual_positions"]["values"], [0, 9])
        self.assertFalse(events[0]["physical_device_proven"])
        self.assertTrue(events[0]["hot_receipt_join_required"])


    def test_gdn_records_inputs_and_actual_destination_separately(self):
        events = []
        ctx = types.SimpleNamespace(req_ids=("x",), plans={"x": object()},
                                    batch_plan=types.SimpleNamespace(step_id=7))
        row = types.SimpleNamespace(start=0, end=2)
        frame = dict(ctx=ctx, layer_name="gdn0", structure=types.SimpleNamespace(
            stages_by_req=((("row", 0),),),
            conv_actions_by_req=((("row", row),),)),
            h_batch=torch.ones(1, 1, 2, 2),
            transitions=torch.eye(2).reshape(1, 1, 2, 2),
            zero_finals=torch.zeros(1, 1, 2, 2),
            conv_request_states=torch.zeros(1, 3, 2),
            dim_first=True, state_len=2, mixed_qkv=torch.ones(2, 3),
            ssm_state_indices=torch.tensor([0]), conv_state_indices=torch.tensor([0]),
            ssm_cache=torch.full((1, 1, 2, 2), 9.), conv_cache=torch.ones(1, 3, 2))
        collector = Collector(events.append, rank=0)
        collector("gdn_initial", "x", frame)
        collector("gdn_committed", "x", frame)
        self.assertEqual(events[0]["incoming_state"]["values"], [1.] * 4)
        self.assertEqual(events[1]["actual_state"]["values"], [9.] * 4)

    def test_kv_reads_destination_not_source_copy(self):
        events = []
        segment = types.SimpleNamespace(start=0, end=4)
        entry = types.SimpleNamespace(seg_hash=b"x")
        plan = types.SimpleNamespace(segments=(segment,), entries=(entry,),
                                     hit_seam={(0, 4): (0,)})
        ctx = types.SimpleNamespace(req_ids=("x",), plans={"x": plan},
                                    batch_plan=types.SimpleNamespace(step_id=7))
        material = types.SimpleNamespace(full_kv_by_layer={
            "attn0": (torch.ones(3, 1, 2), torch.ones(3, 1, 2)*2)})
        geometry = types.SimpleNamespace(is_neox_style=True, rotary_dim=2,
                                          cache=torch.tensor([[1., 0.]]))
        collector = Collector(events.append, rank=0,
            attention_module=types.SimpleNamespace(_ROPE_GEOMETRY=geometry))
        collector("kv_committed", "x", dict(ctx=ctx, layer_name="attn0",
            cache_layout="normal", block_size=4, materials={b"x": material},
            attn_metadata=types.SimpleNamespace(block_tables=torch.tensor([[1]])),
            key_cache=torch.full((2, 4, 1, 2), 9.),
            value_cache=torch.full((2, 4, 1, 2), 8.)))
        sample = events[0]["segments"][0]["samples"][0]
        self.assertEqual(sample["destination_slot"], 5)
        self.assertEqual(sample["canonical_key"]["values"], [1., 1.])
        self.assertEqual(sample["actual_key"]["values"], [9., 9.])

if __name__ == "__main__":
    unittest.main()
