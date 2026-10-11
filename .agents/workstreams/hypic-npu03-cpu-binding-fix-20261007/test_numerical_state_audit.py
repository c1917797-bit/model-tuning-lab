"""Synthetic fault controls: not NPU evidence or HYPIC quality validation."""
import copy
import unittest
import torch
from numerical_state_audit import audit, join_request_hot_receipts, tensor, gdn


def snap(values, dtype="torch.float32"):
    value = torch.tensor(values)
    return dict(shape=list(value.shape), values=value.reshape(-1).tolist(), dtype=dtype)


def fixture():
    events, receipts = [], []
    bindings = {}
    for rank in range(4):
        base = dict(schema="hypic-state-capture/v1", request_id="selected",
                    rank=rank, pid=100+rank, step=7)
        bindings[rank] = base["pid"]
        events += [
            dict(base, stage="positions_committed", layer=None,
                 expected_positions=[3, 4], actual_positions=snap([3, 4], "torch.int64")),
            dict(base, stage="kv_committed", layer="attention",
                 rope=dict(rotary_dim=2, neox=True, rows={"3": snap([0., 1.])}),
                 segments=[dict(segment_hash="ab", anchor=3, seam=1, samples=[
                     dict(material_row=0, logical_position=4, destination_slot=99,
                          canonical_key=snap([2., 3.]), actual_key=snap([-3., 2.]),
                          canonical_value=snap([5., 7.]), actual_value=snap([5., 7.]))])]),
            dict(base, stage="gdn_initial", layer="gdn",
                 incoming_state=snap([[1., 2.], [3., 4.]]),
                 stages=[
                     dict(kind="row", transition=snap([[2., 1.], [0., 3.]]),
                          zero_state=snap([[1., 1.], [1., 1.]])),
                     dict(kind="cache", transition=snap([[0., 1.], [1., 0.]]),
                          zero_state=snap([[1., 0.], [0., 1.]]))],
                 conv_dim_first=False, state_len=2, conv_initial=snap([[1., 2.], [3., 4.]]),
                 conv_actions=[
                     dict(kind="cache", value=snap([[5., 6.], [7., 8.]])),
                     dict(kind="row", original_tokens=1, value=snap([[9., 10.]]))]),
            dict(base, stage="gdn_committed", layer="gdn",
                 actual_state=snap([[11., 6.], [13., 10.]]),
                 actual_conv=snap([[7., 8.], [9., 10.]])),
        ]
        receipts.append(dict(event="worker_hot_request_verified", request_id="selected",
                             pid=100+rank, complete_hybrid_repair_validated=True,
                             skipped_prefix_tokens=10, expected_full_layers=2,
                             expected_gdn_layers=6))
    return events, receipts, bindings


def run(events):
    return audit(events, request_id="selected", kv_layer="attention", gdn_layer="gdn")


class AuditTests(unittest.TestCase):
    def test_hand_calculated_reconstruction(self):
        events, receipts, bindings = fixture()
        result = run(events)
        for rank in result["ranks"]:
            for value in [rank["positions"], rank["kv"][0]["key"], rank["kv"][0]["value"],
                          rank["gdn"]["state"], rank["gdn"]["conv"]]:
                self.assertEqual(value["max_abs"], 0)
                self.assertEqual(value["numerical_acceptance"], "not-decided")
        joined = join_request_hot_receipts(result, receipts, bindings)
        self.assertTrue(joined["request_level_hot_receipts_joined"])
        self.assertFalse(joined["step_level_hot_proven"])
        self.assertFalse(result["physical_device_proven"])
        self.assertFalse(result["producer_generation_proven"])

    def test_fault_localization(self):
        mutations = [
            (1, lambda e: e["segments"][0]["samples"][0]["actual_key"]["values"].__setitem__(0, 99), "key"),
            (1, lambda e: e["segments"][0]["samples"][0]["actual_value"]["values"].__setitem__(0, 99), "value"),
            (3, lambda e: e["actual_state"]["values"].__setitem__(0, 99), "state"),
            (3, lambda e: e["actual_conv"]["values"].__setitem__(0, 99), "conv"),
            (0, lambda e: e["actual_positions"]["values"].__setitem__(0, 99), "positions"),
        ]
        for index, change, component in mutations:
            with self.subTest(component=component):
                events, _, _ = fixture()
                change(events[index])
                result = run(events)["ranks"][0]
                metrics = dict(positions=result["positions"], **result["kv"][0], **result["gdn"])
                for key in ("key", "value", "state", "conv", "positions"):
                    self.assertEqual(metrics[key]["max_abs"] > 0, key == component)

    def test_conv_dimension_first(self):
        events, _, _ = fixture()
        initial, final = copy.deepcopy(events[2:4])
        initial["conv_dim_first"] = True
        for item in (initial["conv_initial"], initial["conv_actions"][0]["value"], final["actual_conv"]):
            value = tensor(item).T
            item["values"] = value.reshape(-1).tolist()
        self.assertEqual(gdn(initial, final)["conv"]["max_abs"], 0)

    def test_missing_duplicate_stage(self):
        events, _, _ = fixture()
        for broken in (events[:-1], events+events[:1], events[:12]):
            with self.assertRaises(ValueError):
                run(broken)

    def test_identity_mismatch(self):
        for key, value in (("step", 8), ("pid", 999), ("layer", "other"),
                           ("request_id", "foreign"), ("rank", 4)):
            events, _, _ = fixture()
            events[3][key] = value
            with self.assertRaises(ValueError):
                run(events)

    def test_reject_bad_numeric_records(self):
        for bad in (dict(shape=[2], dtype="torch.float32", values=[0, float("nan")]),
                    dict(shape=[2], dtype="torch.float32", values=[1]),
                    dict(shape=[1], dtype="torch.int64", values=[1.5]),
                    dict(shape=[-1], dtype="torch.float32", values=[])):
            with self.assertRaises(ValueError):
                tensor(bad)

    def test_shape_and_geometry_rejected(self):
        events, _, _ = fixture()
        events[1]["rope"]["rotary_dim"] = 3
        with self.assertRaises(ValueError):
            run(events)
        events, _, _ = fixture()
        events[2]["stages"][0]["transition"] = snap([[1.]])
        with self.assertRaises(ValueError):
            run(events)

    def test_hot_join_missing_foreign_duplicate_false(self):
        events, receipts, bindings = fixture()
        result = run(events)
        foreign = copy.deepcopy(receipts)
        foreign[0]["pid"] = 888
        cold = copy.deepcopy(receipts)
        cold[0]["complete_hybrid_repair_validated"] = False
        for broken in (receipts[:-1], receipts+receipts[:1], foreign, cold):
            with self.assertRaises(ValueError):
                join_request_hot_receipts(result, broken, bindings)
        bindings[0] = 999
        with self.assertRaises(ValueError):
            join_request_hot_receipts(result, receipts, bindings)

    def test_canonical_input_change_detected(self):
        events, _, _ = fixture()
        events[1]["segments"][0]["samples"][0]["canonical_key"]["values"][0] += 1
        self.assertGreater(run(events)["ranks"][0]["kv"][0]["key"]["max_abs"], 0)
        events, _, _ = fixture()
        events[2]["stages"][0]["transition"]["values"][0] += 1
        self.assertGreater(run(events)["ranks"][0]["gdn"]["state"]["max_abs"], 0)


if __name__ == "__main__":
    unittest.main()
