import ast,json,os,tempfile,unittest
from unittest import mock
from pathlib import Path
import fault_receipt as F


class Tests(unittest.TestCase):
    def persist(self,root,*args):
        if os.name!='nt':return F.persist(root,*args)
        # Windows cannot open directories as fds; exercise the exact call/order,
        # not Linux directory durability. Real Linux fsync remains required.
        original=os.open;calls=[]
        def directory(path,flags):
            self.assertEqual((str(path),flags),(str(root),os.O_RDONLY));calls.append(str(path))
            return original(str(Path(root)/'HOST-FIRST-FAULT.json'),os.O_RDWR)
        with mock.patch.object(F.os,'open',side_effect=directory):result=F.persist(root,*args)
        self.assertEqual(calls,[str(root)]);return result
    def test_exact_missing_executable_before_cleanup(self):
        with tempfile.TemporaryDirectory()as name:
            events=[]
            try:raise FileNotFoundError(2,'missing executable','/exact/missing-tool')
            except BaseException as error:
                events.append('fault');self.persist(name,{'path':'/exact/source'},error,{'phase':'dense-startup','step':'health-run','ordinal':7})
                events.append('cleanup')
            value=json.loads((Path(name)/'HOST-FIRST-FAULT.json').read_bytes())
            self.assertEqual(events,['fault','cleanup']);self.assertEqual(value['errno'],2)
            self.assertEqual(value['filename'],'/exact/missing-tool');self.assertIn('test_exact_missing_executable_before_cleanup',value['traceback'])
            self.assertEqual(value['phase']['step'],'health-run');self.assertTrue(value['fail_closed'])
            with self.assertRaises(FileExistsError):F.persist(name,{},FileNotFoundError(2,'other','/other'),{})
    def test_both_paths_and_full_traceback(self):
        with tempfile.TemporaryDirectory()as name:
            error=OSError(2,'rename missing','/from',None,'/to')
            self.persist(name,{},error,{'phase':'receipt','step':'write'})
            value=json.loads((Path(name)/'HOST-FIRST-FAULT.json').read_bytes())
            self.assertEqual((value['filename'],value['filename2']),('/from','/to'))
            self.assertFalse(value['recovery_attempted']);self.assertTrue(value['cleanup_not_started'])
    def test_real_host_except_persists_before_original_finally(self):
        text=(Path(__file__).parent/'host090.py').read_text(encoding='utf8');tree=ast.parse(text)
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        block=next(n for n in main.body if isinstance(n,ast.Try))
        handler=block.handlers[0]
        calls=[n for n in ast.walk(handler)if isinstance(n,ast.Call)and ast.unparse(n.func)=='fault_receipt.persist']
        self.assertEqual(len(calls),1);self.assertLess(calls[0].lineno,block.finalbody[0].lineno)
        self.assertIn('primary = repr(e)',ast.unparse(handler));self.assertIn('first-fault-persistence',text)

if __name__=='__main__':unittest.main()
