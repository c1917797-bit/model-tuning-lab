import unittest
from independent_compact_activation import install_owned_chain,activate_compact_hypic


class ActivationTests(unittest.TestCase):
    def test_late_install_failure_unwinds_only_owned_hooks_in_reverse_order(self):
        events=[]
        def installer(name):
            def install():
                events.append('install '+name)
                return lambda:events.append('stop '+name)
            return install
        def fail():raise RuntimeError('source drift')
        with self.assertRaises(RuntimeError):install_owned_chain((installer('runner'),installer('gdn'),fail))
        self.assertEqual(events,['install runner','install gdn','stop gdn','stop runner'])
    def test_successful_uninstall_reverse_order_and_idempotence(self):
        events=[]
        stop=install_owned_chain((lambda:lambda:events.append('runner'),lambda:lambda:events.append('model')))
        stop();stop();self.assertEqual(events,['model','runner'])
    def test_disabled_activation_has_no_runtime_imports(self):
        activate_compact_hypic(None,enabled=False)()


if __name__=='__main__':unittest.main()
