"""Compiler-order controls for the actual R27 failed/native service log formats."""
from pathlib import Path
import unittest
from host_audits.r29_graph_compile_order import parse_compile_order

WORKERS = {r: 58 + r for r in range(4)}


def start(rank, pid=None):
    return f'(Worker_TP{rank} pid={WORKERS[rank] if pid is None else pid}) DEBUG 10-25 09:20:00 [compilation/decorators.py:593] Start compiling function <code object installed at 0xaaab1234, file "/probe/graph_candidate/entry_router.py", line 190>'


def capture(rank, pid=None):
    return f'(Worker_TP{rank} pid={WORKERS[rank] if pid is None else pid}) DEBUG 10-25 09:22:00 [acl_graph.py:164] Capturing a aclgraph on (FULL,BatchDescriptor(num_tokens=32, num_reqs=32, uniform=True, has_lora=False, num_active_loras=0))'


FINISH = '(Worker_TP0 pid=58) INFO 10-25 09:21:00 [compilation/monitor.py:53] torch.compile took 89.35 s in total'


def log(lines):
    return ("\n".join(lines) + "\n").encode()


class CompileOrderTests(unittest.TestCase):
    def lines(self):
        return [*[start(r) for r in range(4)], FINISH, *[capture(r) for r in range(4)]]

    def test_local_first_monitor_is_sufficient(self):
        report = parse_compile_order(log(self.lines()), WORKERS)
        self.assertEqual(report["first_compile_before_own_capture_ranks"], list(range(4)))
        self.assertEqual(report["per_rank"][1]["compile_complete_lines"], [])

    def test_actual_failed_first_compile_in_capture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "within/after"):
            parse_compile_order(log([capture(0), *[start(r) for r in range(4)], FINISH,
                *[capture(r) for r in range(1, 4)]]), WORKERS)

    def test_missing_worker_compile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            parse_compile_order(log([x for x in self.lines() if x != start(3)]), WORKERS)

    def test_compile_completion_after_capture_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finish before"):
            parse_compile_order(log([*[start(r) for r in range(4)],
                                    *[capture(r) for r in range(4)], FINISH]), WORKERS)

    def test_foreign_pid_is_rejected(self):
        lines = self.lines()
        lines[0] = start(0, 999)
        with self.assertRaisesRegex(ValueError, "physical owner"):
            parse_compile_order(log(lines), WORKERS)

    def test_unrelated_forward_compile_cannot_stand_in_for_installed(self):
        lines = [x.replace("code object installed", "code object forward") for x in self.lines()]
        with self.assertRaisesRegex(ValueError, "missing"):
            parse_compile_order(log(lines), WORKERS)

    def test_no_cross_rank_completion_barrier_is_invented(self):
        # Rank1 may reach its capture after its own compile starts, before TP0's
        # info_once completion. Successful complete canary is checked separately.
        lines = [*[start(r) for r in range(4)], capture(1), FINISH,
                 capture(0), capture(2), capture(3)]
        parse_compile_order(log(lines), WORKERS)

    def test_original_service_bytes_required(self):
        with self.assertRaises(ValueError):
            parse_compile_order("not raw bytes", WORKERS)

    def test_ansi_source_prefix_is_supported(self):
        parse_compile_order(log(["\x1b[36m" + x + "\x1b[0m" for x in self.lines()]), WORKERS)


if __name__ == "__main__":
    unittest.main()
