import unittest
from independent_runner_context import install_runner_context,CURRENT_REQUEST_SLICES
class RunnerContextTests(unittest.TestCase):
    def make_runner(self):
        class Runner:
            def _prepare_inputs(self,x):return x
            def execute_model(self,x):
                self._prepare_inputs(x)
                if x=='fail':raise RuntimeError('failure')
                return CURRENT_REQUEST_SLICES.get()
        return Runner
    def test_disabled_does_not_install(self):
        cls=self.make_runner();before=cls._prepare_inputs
        install_runner_context(cls,None)()
        self.assertIs(cls._prepare_inputs,before)
    def test_request_context_clears_on_success_and_error_and_uninstalls(self):
        cls=self.make_runner();original=cls._prepare_inputs;checks=[]
        stop=install_runner_context(cls,lambda r,a,k:tuple(a),enabled=True,verify_source=lambda c:checks.append(c))
        self.assertEqual(cls().execute_model('a'),('a',))
        self.assertIsNone(CURRENT_REQUEST_SLICES.get())
        with self.assertRaises(RuntimeError):cls().execute_model('fail')
        self.assertIsNone(CURRENT_REQUEST_SLICES.get());stop()
        self.assertIs(cls._prepare_inputs,original);self.assertEqual(checks,[cls])
    def test_enabled_requires_verification(self):
        with self.assertRaises(ValueError):install_runner_context(self.make_runner(),None,enabled=True)
    def test_observer_after_native_prepare_and_failure_cleanup(self):
        cls=self.make_runner();events=[]
        def observe(r,s):
            events.append((s,CURRENT_REQUEST_SLICES.get()))
            if s==('bad',):raise ValueError('slot mismatch')
        stop=install_runner_context(cls,lambda r,a,k:tuple(a),enabled=True,
                                    verify_source=lambda c:None,after_prepare=observe)
        self.assertEqual(cls().execute_model('ok'),('ok',))
        self.assertEqual(events,[(('ok',),('ok',))])
        with self.assertRaises(ValueError):cls().execute_model('bad')
        self.assertIsNone(CURRENT_REQUEST_SLICES.get())
        stop()
    def test_duplicate_install_and_foreign_overwrite_fail_closed(self):
        cls=self.make_runner()
        stop=install_runner_context(cls,lambda r,a,k:tuple(a),enabled=True,verify_source=lambda c:None)
        with self.assertRaises(RuntimeError):install_runner_context(cls,None,enabled=True,verify_source=lambda c:None)
        foreign=lambda *a,**k:None
        cls.execute_model=foreign
        with self.assertRaises(RuntimeError):stop()
        self.assertIs(cls.execute_model,foreign)
if __name__=='__main__':unittest.main()
