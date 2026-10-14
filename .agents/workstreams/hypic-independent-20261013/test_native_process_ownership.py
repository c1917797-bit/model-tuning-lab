import unittest
from native_tp4_smoke import classify_process_owner

class ProcessOwnershipTests(unittest.TestCase):
    def test_exact_container_and_namespace_proofs(self):
        self.assertEqual(classify_process_owner('1:x:/docker/abc','abc'),'owned-cgroup')
        self.assertEqual(classify_process_owner('1:x:/','abc',same_pid_namespace=True),
                         'owned-pid-namespace')
    def test_unresolved_is_not_claimed_foreign_or_owned(self):
        for group in ('1:x:/','owner_unverified',''):
            self.assertEqual(classify_process_owner(group,'abc'),'ownership-unresolved')
        self.assertEqual(classify_process_owner('1:x:/docker/other','abc'),'foreign-cgroup')
        self.assertEqual(classify_process_owner('1:x:/',None,same_pid_namespace=True),
                         'ownership-unresolved')

if __name__=='__main__':unittest.main()
