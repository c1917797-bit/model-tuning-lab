"""CPU-only tests for fail-closed physical-device ownership parsing."""

import unittest
from unittest.mock import patch

import run_v12r6_once as controller
from run_v12r6_once import (
    container_claims_from_inspect,
    npu_process_rows,
    runtime_resource_blockers,
)


def inspected(*, privileged=False, devices=None, env=None):
    return {
        "HostConfig": {
            "Privileged": privileged,
            "Devices": devices or [],
        },
        "Config": {"Env": env or []},
    }


class ContainerClaimTests(unittest.TestCase):
    def test_explicit_host_mapping_is_physical_authority(self):
        item = inspected(
            devices=[
                {
                    "PathOnHost": "/dev/davinci4",
                    "PathInContainer": "/dev/davinci0",
                }
            ],
            env=["ASCEND_RT_VISIBLE_DEVICES=0"],
        )
        self.assertEqual(container_claims_from_inspect(item), [4])

    def test_privileged_visible_devices_are_host_claims(self):
        item = inspected(
            privileged=True,
            env=["ASCEND_RT_VISIBLE_DEVICES=4,5,6,7"],
        )
        self.assertEqual(container_claims_from_inspect(item), [4, 5, 6, 7])

    def test_nonprivileged_environment_without_mapping_is_not_access(self):
        item = inspected(env=["ASCEND_RT_VISIBLE_DEVICES=4,5,6,7"])
        self.assertEqual(container_claims_from_inspect(item), [])

    def test_unrelated_privileged_lane_does_not_block_target(self):
        item = inspected(
            privileged=True,
            env=["ASCEND_RT_VISIBLE_DEVICES=0,1,2,3"],
        )
        self.assertEqual(container_claims_from_inspect(item), [])

    def test_privileged_claim_unions_mapping_and_visible_devices(self):
        item = inspected(
            privileged=True,
            devices=[
                {
                    "PathOnHost": "/dev/davinci4",
                    "PathInContainer": "/dev/davinci4",
                }
            ],
            env=["ASCEND_RT_VISIBLE_DEVICES=5,6,7"],
        )
        self.assertEqual(container_claims_from_inspect(item), [4, 5, 6, 7])


class ResourcePolicyTests(unittest.TestCase):
    def setUp(self):
        self.hbm = {device: 2868 for device in range(8)}
        self.claims = {"foreign": [4, 5, 6, 7]}

    @patch.object(controller, "port_available", return_value=True)
    def test_default_policy_blocks_idle_claim(self, _port):
        blockers = runtime_resource_blockers(self.hbm, set(), self.claims)
        self.assertIn("running container device claims", blockers[0])

    @patch.object(controller, "port_available", return_value=True)
    def test_authorized_policy_records_idle_claim_without_blocking(self, _port):
        with patch.object(controller, "BLOCK_ON_IDLE_CONTAINER_CLAIMS", False):
            self.assertEqual(
                runtime_resource_blockers(self.hbm, set(), self.claims),
                [],
            )

    @patch.object(controller, "port_available", return_value=True)
    def test_authorized_policy_still_blocks_real_process(self, _port):
        with patch.object(controller, "BLOCK_ON_IDLE_CONTAINER_CLAIMS", False):
            blockers = runtime_resource_blockers(self.hbm, {4}, self.claims)
        self.assertTrue(any("active NPU process" in value for value in blockers))

    @patch.object(controller, "port_available", return_value=True)
    def test_authorized_policy_still_blocks_high_hbm(self, _port):
        hbm = dict(self.hbm)
        hbm[7] = controller.IDLE_HBM_LIMIT_MIB + 1
        with patch.object(controller, "BLOCK_ON_IDLE_CONTAINER_CLAIMS", False):
            blockers = runtime_resource_blockers(hbm, set(), self.claims)
        self.assertTrue(any("HBM" in value for value in blockers))


class PostReadinessOwnershipTests(unittest.TestCase):
    def test_npu_process_rows_returns_host_pids_per_physical_device(self):
        raw = """
| NPU     Chip              | Process id    | Process name             |
| 4       0                 | 4104          | VLLMWorker_TP            |
| 5       0                 | 4105          | VLLMWorker_TP            |
| 6       0                 | 4106          | VLLMWorker_TP            |
| 7       0                 | 4107          | VLLMWorker_TP            |
"""
        self.assertEqual(
            npu_process_rows(raw),
            {4: {4104}, 5: {4105}, 6: {4106}, 7: {4107}},
        )

    def test_post_readiness_gate_accepts_only_owned_tp_workers(self):
        raw = """
| NPU     Chip              | Process id    | Process name             |
| 4       0                 | 4104          | VLLMWorker_TP            |
| 5       0                 | 4105          | VLLMWorker_TP            |
| 6       0                 | 4106          | VLLMWorker_TP            |
| 7       0                 | 4107          | VLLMWorker_TP            |
"""
        with (
            patch.object(controller, "run", return_value=raw),
            patch.object(
                controller,
                "container_host_pids",
                return_value={4104, 4105, 4106, 4107, 4200},
            ),
            patch.object(controller, "atomic_json") as write_json,
        ):
            controller.validate_post_readiness_ownership()
        self.assertTrue(write_json.call_args.args[1]["ok"])

    def test_post_readiness_gate_rejects_foreign_target_pid(self):
        raw = """
| NPU     Chip              | Process id    | Process name             |
| 4       0                 | 4104          | VLLMWorker_TP            |
| 5       0                 | 4105          | VLLMWorker_TP            |
| 6       0                 | 4999          | VLLMWorker_TP            |
| 7       0                 | 4107          | VLLMWorker_TP            |
"""
        with (
            patch.object(controller, "run", return_value=raw),
            patch.object(
                controller,
                "container_host_pids",
                return_value={4104, 4105, 4107},
            ),
            patch.object(controller, "atomic_json"),
        ):
            with self.assertRaisesRegex(RuntimeError, "foreign_pids"):
                controller.validate_post_readiness_ownership()

if __name__ == "__main__":
    unittest.main()
