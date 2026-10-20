"""Pure software prerequisites for freezing a G1 source packet."""
import copy
import unittest
from unittest.mock import patch
import prepare_g1 as P


class Tests(unittest.TestCase):
    def fixture(self):
        sr, rr, qr = {'parent': 1}, {'owner': 1}, {'independent': 1}
        parent = dict(files={'actual.py': dict(path='/actual.py', sha256='frozen')})
        owner = dict(schema='bole.actual-three-node-model-owned/v131', source=sr,
            primary=None, secondary=[], cpu_only=False, source_before={'/actual.py': 'frozen'},
            source_after={'/actual.py': 'frozen'}, summary={'independent': qr},
            model_ready=False, candidate_qualification=False, performance_gain_measured=False,
            formal_performance=False, task_accuracy=False)
        qualification = dict(schema='bole.actual-c1-continuous-service-independent/v1', source=sr,
            service_complete=True, service_experiment_pass=True, component_checks_pass=True,
            scheduler_committed_independently=True, actual_all4_retirement=True,
            actual_HTTP_output_token_ID_join=True, actual_scheduler_flow_observed=True,
            model_ready=False, task_ready=False, performance_ready=False, formal_success=False,
            whole_numerical_qualified=False, native_AR_greedy_comparison_performed=False)
        return sr, parent, rr, qr, owner, qualification

    def test_both_actual_same_source_success_reports_are_required(self):
        sr, parent, rr, qr, owner, qualification = self.fixture()
        with patch.object(P, 'obj', side_effect=lambda r: owner if r == rr else qualification):
            P.validate_parent_qualification(sr, parent, rr, qr)

    def test_owner_failure_wrong_report_link_or_changed_source_reject_before_freeze(self):
        for change in ('primary','secondary','source','source_before','source_after','report','cpu_only'):
            with self.subTest(change=change):
                sr, parent, rr, qr, owner, qualification = self.fixture()
                if change == 'report':
                    owner['summary']['independent'] = {'foreign': 1}
                elif change == 'primary':
                    owner[change] = 'actual failure'
                elif change == 'secondary':
                    owner[change] = ['actual failure']
                elif change == 'source':
                    owner[change] = {'foreign': 1}
                elif change == 'cpu_only':
                    owner[change] = True
                else:
                    owner[change] = {'/actual.py': 'changed'}
                with patch.object(P, 'obj', side_effect=lambda r: owner if r == rr else qualification):
                    with self.assertRaises(ValueError):
                        P.validate_parent_qualification(sr, parent, rr, qr)

    def test_missing_component_retirement_HTTP_or_scheduler_success_reject(self):
        for field in ('service_complete','service_experiment_pass','component_checks_pass',
                      'scheduler_committed_independently','actual_all4_retirement',
                      'actual_HTTP_output_token_ID_join','actual_scheduler_flow_observed'):
            with self.subTest(field=field):
                sr, parent, rr, qr, owner, qualification = self.fixture()
                qualification[field] = False
                with patch.object(P, 'obj', side_effect=lambda r: owner if r == rr else qualification):
                    with self.assertRaises(ValueError):
                        P.validate_parent_qualification(sr, parent, rr, qr)

    def test_parent_model_formal_or_performance_claim_is_not_a_bounded_v6_prerequisite(self):
        for target, field in (('qualification','formal_success'),('qualification','model_ready'),
                              ('qualification','native_AR_greedy_comparison_performed'),
                              ('owner','performance_gain_measured')):
            with self.subTest(target=target, field=field):
                sr, parent, rr, qr, owner, qualification = self.fixture()
                (owner if target == 'owner' else qualification)[field] = True
                with patch.object(P, 'obj', side_effect=lambda r: owner if r == rr else qualification):
                    with self.assertRaises(ValueError):
                        P.validate_parent_qualification(sr, parent, rr, qr)


if __name__ == '__main__':
    unittest.main()
