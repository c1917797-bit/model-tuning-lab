"""CPU-only tests for fail-closed physical-device ownership parsing."""

import unittest

from run_v12r6_once import container_claims_from_inspect


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


if __name__ == "__main__":
    unittest.main()
