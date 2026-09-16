"""CPU-only launch-contract tests; no accelerator or Docker call."""
import unittest
from unittest.mock import patch

import run_v12r10_once as trial


class LaunchContractTests(unittest.TestCase):
    def test_pa_shapes_are_forwarded_as_common_additional_config(self):
        captured = []

        def fake_run(args, **kwargs):
            captured.append(args)
            return "container-id"

        with patch.object(trial.controller, "run", side_effect=fake_run):
            self.assertEqual(trial.controller.launch(), "container-id")

        command = captured[-1]
        index = command.index("--additional-config")
        self.assertEqual(
            command[index + 1],
            '{"pa_shape_list":[1,2,4,8,16]}',
        )
        self.assertEqual(command.count("--additional-config"), 1)


if __name__ == "__main__":
    unittest.main()
