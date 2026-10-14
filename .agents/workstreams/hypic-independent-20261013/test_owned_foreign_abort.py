import unittest
from native_tp4_smoke import stop_owned_on_foreign,TASK


class OwnedAbortTests(unittest.TestCase):
    def meta(self,cid):
        return {'Id':cid,'Image':'frozen','Config':{'Labels':{'model-tuning-lab.task':TASK}},
            'HostConfig':{'Devices':[{'PathOnHost':'/dev/davinci'+str(i)} for i in range(4)]},
            'State':{'Running':True}}
    def test_stops_exact_owned_cid_without_deleting_evidence(self):
        cid='a'*64;calls=[]
        stop_owned_on_foreign(cid,image='frozen',inspect_fn=self.meta,
            command_fn=lambda args,**kwargs:calls.append(args))
        self.assertEqual(calls,[['docker','stop','-t','3',cid]])
    def test_foreign_label_or_device_drift_cannot_be_stopped(self):
        cid='a'*64
        for mode in ('label','devices'):
            meta=self.meta(cid)
            if mode=='label':meta['Config']['Labels']['model-tuning-lab.task']='foreign'
            else:meta['HostConfig']['Devices']=[{'PathOnHost':'/dev/davinci4'}]
            with self.assertRaises(ValueError):
                stop_owned_on_foreign(cid,image='frozen',inspect_fn=lambda c:meta,
                    command_fn=lambda *args,**kwargs:self.fail('foreign action'))
    def test_short_id_rejected_before_inspect(self):
        with self.assertRaises(ValueError):
            stop_owned_on_foreign('a'*12,image='frozen',inspect_fn=lambda c:self.fail())


if __name__=='__main__':unittest.main()
