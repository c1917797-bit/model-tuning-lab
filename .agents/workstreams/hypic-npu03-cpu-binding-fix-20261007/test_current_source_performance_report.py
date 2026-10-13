"""Negative controls for current report tables, commands and scope."""
import copy
import json
import unittest
from verify_current_source_performance_report import REPORT, AGGREGATE, review_text

class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=REPORT.read_text()
        cls.aggregate=json.loads(AGGREGATE.read_text())

    def test_retained_report(self):
        self.assertEqual(review_text(self.text,self.aggregate)["historical_commands"],6)

    def test_counterexamples(self):
        changes=[
            ("75.6181 | 58.3311","75.6181 | 58.9999"),
            ("75.0528 ± 0.4905","75.0528 ± 0.0000"),
            ("-22.0163% |","22.0163% |"),
            ("| no-cache/screen | 170","| no-cache/screen | 171"),
            ("--arm no-cache --phase screen --action run","--arm hypic-only --phase screen --action run"),
            ("Fixed output1024","Fixed output2048"),
            ("deployment_allowed=false","deployment_allowed=true"),
            ("No new profile","Matched profiles prove the cause"),
            ("not a confidence interval","a confidence interval"),
            ("All120 candidate scored requests","All121 candidate scored requests"),
        ]
        for old,new in changes:
            with self.subTest(old=old):
                self.assertIn(old,self.text)
                with self.assertRaises(RuntimeError):
                    review_text(self.text.replace(old,new),self.aggregate)

    def test_removed_phase(self):
        # The original report omitted these per-round metrics while retaining
        # their aggregate values. Preserve that real counterexample.
        header="| Round | G1 TPOT P95 ms | G2 TPOT P95 ms | G1 batch duration s | G2 batch duration s |"
        lines=self.text.splitlines();start=lines.index(header)
        without="\n".join(lines[:start]+lines[start+5:])
        with self.assertRaises(RuntimeError):review_text(without,self.aggregate)

    def test_missing_phase_in_aggregate(self):
        a=copy.deepcopy(self.aggregate);a["phases"].pop()
        with self.assertRaises(RuntimeError):review_text(self.text,a)

    def test_wrong_source(self):
        a=copy.deepcopy(self.aggregate);a["source_commit"]="wrong"
        with self.assertRaises(RuntimeError):review_text(self.text,a)

    def test_missing_disclosure(self):
        with self.assertRaises(RuntimeError):
            review_text(self.text.replace("unrecorded transport retries",""),self.aggregate)

    def test_placeholder(self):
        with self.assertRaises(RuntimeError):review_text(self.text+"\nTODO\n",self.aggregate)

if __name__=="__main__":unittest.main()
