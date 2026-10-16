import copy,unittest
from audit_c1_async_material import audit_transfer_rows

def fixture():
    events=[];workers={r:100+r for r in range(4)};private=['http0','http1']
    for rank,pid in workers.items():
        for layer in range(48):
            common={'rank':rank,'pid':pid,'manifest_sha256':'source','layer':str(layer),'generation':1}
            events.append(dict(common,event='compact_public_state_published',
                tokens_sha256='a'*64,transition_shape=[12,128,128],zero_state_shape=[12,128,128]))
            metrics=[{'tensor':k,'shape':s,'dtype':'torch.float32','bytes':n*4,'all_bytes_equal':True}
                for k,s,n in [('transition',[12,128,128],12*128*128),
                    ('zero_state',[12,128,128],12*128*128),('conv_tail',[3,2560],3*2560)]]
            events.append(dict(common,event='c1_private_material_transfer_verified',step=2,
                request_ids=['http0-0','http1-0'],tokens_sha256='a'*64,metrics=metrics,
                full_transfer_bytes_compared=True,actual_slot_commit='not_started'))
            for req in private:
                events.append(dict(common,event='compact_gdn_body_composed',step=2,request_id=req+'-0'))
    return events,workers,private

class TransferReceiptTests(unittest.TestCase):
    def test_complete_384_hot_receipts_join_192_private_leases(self):
        e,w,p=fixture();r=audit_transfer_rows(e,w,'source',p)
        self.assertEqual(r['matched_hot_receipts'],384);self.assertEqual(r['copy_leases'],192)
    def test_wrong_step_source_pid_generation_or_request_fails(self):
        for field,value in [('step',3),('manifest_sha256','wrong'),('pid',999),('generation',2),
                ('request_ids',['foreign']),('full_transfer_bytes_compared',False),
                ('actual_slot_commit','already_committed')]:
            e,w,p=fixture();row=next(x for x in e if x['event']=='c1_private_material_transfer_verified')
            row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):audit_transfer_rows(e,w,'source',p)
    def test_sampled_bytes_and_wrong_shape_or_missing_tensor_fail(self):
        for mutation in ('bytes','shape','missing','equal'):
            e,w,p=fixture();row=next(x for x in e if x['event']=='c1_private_material_transfer_verified')
            if mutation=='bytes':row['metrics'][0]['bytes']=4
            elif mutation=='shape':row['metrics'][0]['shape']=[1]
            elif mutation=='missing':row['metrics'].pop()
            else:row['metrics'][0]['all_bytes_equal']=False
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):audit_transfer_rows(e,w,'source',p)
    def test_missing_publication_lease_or_rank_fails(self):
        for name in ('compact_public_state_published','c1_private_material_transfer_verified','rank'):
            e,w,p=fixture()
            if name=='rank':e=[x for x in e if x['rank']!=3]
            else:e.pop(next(i for i,x in enumerate(e)if x['event']==name))
            with self.subTest(name=name),self.assertRaises(ValueError):audit_transfer_rows(e,w,'source',p)
    def test_duplicate_receipt_fails(self):
        e,w,p=fixture();e.append(copy.deepcopy(next(x for x in e if x['event']=='c1_private_material_transfer_verified')))
        with self.assertRaises(ValueError):audit_transfer_rows(e,w,'source',p)

if __name__=='__main__':unittest.main()
