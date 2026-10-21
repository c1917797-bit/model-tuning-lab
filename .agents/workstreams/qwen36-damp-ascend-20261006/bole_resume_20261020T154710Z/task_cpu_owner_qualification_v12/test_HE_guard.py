"""Offline projection and rejection controls; no host/network/evaluator execution."""
import ast
import copy
import json
from pathlib import Path
import sys
import unittest
P=Path(__file__).resolve().parent
PACKET=P/'task_packet'if(P/'task_packet').is_dir()else P.parent/'task_decoder_scorer_v3'
sys.path.insert(0,str(P));sys.path.insert(0,str(PACKET))
import he_network_guard as G
import he_admission as H


def facts():return copy.deepcopy(json.loads((P/'HE_V3_FACTS_FIXTURE.json').read_bytes())['facts'])
def down(v):return next(r for r in v['sys_entries']if r['attributes']['flags']['text']=='0x1002\n')
def acknowledge(v):
    host=dict(pid=90,start_ticks=91,link='net:[999]',file_identity=dict(device=v['net_namespace']['device'],inode=999))
    init=dict(host,pid=1)
    ready=dict(schema='bole.actual-HE-network-ready/v1',nonce='a'*64,root_source_sha256='b'*64,capsule_sha256='c'*64,facts=v,predicate=G.validate(v))
    ack=dict(schema='bole.actual-HE-host-network-admission-ack/v1',nonce=ready['nonce'],root_source_sha256=ready['root_source_sha256'],
        capsule_sha256=ready['capsule_sha256'],container_id='d'*64,owned_host_pid=501,owned_start_ticks=v['guest']['start_ticks'],
        guest=v['guest'],guest_net_namespace=v['net_namespace'],host_namespaces=dict(owner=host,host_init=init))
    return ready,ack


class Network(unittest.TestCase):
    def test_actual_v3_projection_is_supported_without_runtime_qualification(self):
        fixture=json.loads((P/'HE_V3_FACTS_FIXTURE.json').read_bytes());r=G.validate(fixture['facts'])
        self.assertIs(fixture['projection_only'],True);self.assertIs(fixture['qualified'],False)
        self.assertIs(r['standalone_network_safety_accepted'],False);self.assertEqual(r['unusable_ipv6_reject_rows'],2)
    def test_no_interface_name_whitelist(self):
        v=facts();mapping={r['name']:'renamed'+str(i)for i,r in enumerate(v['sys_entries'])}
        for r in v['sys_entries']:
            old=r['name'];r['name']=mapping[old]
            if r['symlink_target']:r['symlink_target']='../../devices/virtual/net/'+r['name']
        v['sys_entries'].sort(key=lambda r:r['name'])
        for k in('dev','ipv6_route'):
            for old,new in mapping.items():v['proc_files'][k]=v['proc_files'][k].replace(old,new)
        self.assertTrue(G.validate(v)['local_predicate_passed'])
    def test_all_active_nonloopback_flag_bits_rejected(self):
        for bit in(1,64,65536,131072):
            v=facts();down(v)['attributes']['flags']['text']=hex(0x1002|bit)+'\n'
            with self.assertRaises(ValueError):G.validate(v)
    def test_operstate_up_unknown_or_dormant_rejected(self):
        for state in('up\n','unknown\n','dormant\n'):
            v=facts();down(v)['attributes']['operstate']['text']=state
            with self.assertRaises(ValueError):G.validate(v)
    def test_carrier_up_and_unknown_errors_rejected(self):
        for value in(dict(ok=True,text='1\n',error=None),dict(ok=False,text=None,error=dict(type='PermissionError',errno=13))):
            v=facts();down(v)['attributes']['carrier']=value
            with self.assertRaises(ValueError):G.validate(v)
    def test_nonloopback_peer_or_physical_device_rejected(self):
        for mode in('peer','physical'):
            v=facts();r=down(v)
            if mode=='peer':r['attributes']['iflink']['text']='8\n'
            else:r['symlink_target']='../../devices/pci0000/net/'+r['name']
            with self.assertRaises(ValueError):G.validate(v)
    def test_regular_file_cannot_masquerade_as_interface(self):
        v=facts();v['sys_entries'][0]['is_dir']=True
        with self.assertRaises(ValueError):G.validate(v)
    def test_missing_or_unknown_interface_inventory_rejected(self):
        v=facts();v['sys_entries'].pop()
        with self.assertRaises(ValueError):G.validate(v)
    def test_fake_loopback_hardware_rejected(self):
        v=facts();down(v)['attributes']['flags']['text']='0x9\n'
        with self.assertRaises(ValueError):G.validate(v)
    def test_any_ipv4_main_route_rejected(self):
        v=facts();v['proc_files']['route']+='dummy 00000000 00000000 0001 0 0 0 00000000 0 0 0\n'
        with self.assertRaises(ValueError):G.validate(v)
    def test_any_ipv6_address_rejected(self):
        v=facts();v['proc_files']['if_inet6']='00000000000000000000000000000001 01 80 10 80 lo\n'
        with self.assertRaises(ValueError):G.validate(v)
    def test_ipv6_up_unknown_or_gateway_route_rejected(self):
        for mode in('up','unknown','gateway'):
            v=facts();line=v['proc_files']['ipv6_route'].splitlines()[0].split()
            if mode=='up':line[8]='00200201'
            elif mode=='unknown':line[8]='00200000'
            else:line[4]='1'*32
            v['proc_files']['ipv6_route']=' '.join(line)+'\n'
            with self.assertRaises(ValueError):G.validate(v)
    def test_malformed_raw_route_or_counter_rejected(self):
        for key in('route','ipv6_route','dev'):
            v=facts();v['proc_files'][key]='malformed'
            with self.assertRaises(ValueError):G.validate(v)
    def test_nonloopback_prior_traffic_rejected(self):
        v=facts();name=down(v)['name'];lines=v['proc_files']['dev'].splitlines()
        for i,line in enumerate(lines):
            if line.strip().startswith(name+':'):
                a,b=line.split(':',1);values=b.split();values[0]='1';lines[i]=a+': '+' '.join(values)
        v['proc_files']['dev']='\n'.join(lines)+'\n'
        with self.assertRaises(ValueError):G.validate(v)
    def test_capabilities_privileges_or_uid_rejected(self):
        for key,value in(('CapEff','0000000000001000'),('CapBnd','0000000000001000'),('NoNewPrivs','0'),('Uid','0 0 0 0')):
            v=facts();v['privilege'][key]=value
            with self.assertRaises(ValueError):G.validate(v)
    def test_ack_exact_nonce_source_capsule_pid_and_namespace(self):
        r,a=acknowledge(facts());self.assertEqual(G.validate_ack(a,r),a)
        for key,value in(('nonce','e'*64),('root_source_sha256','e'*64),('capsule_sha256','e'*64),('owned_start_ticks',1)):
            bad=copy.deepcopy(a);bad[key]=value
            with self.assertRaises(ValueError):G.validate_ack(bad,r)
    def test_ack_cannot_accept_host_network_namespace(self):
        r,a=acknowledge(facts())
        for row in a['host_namespaces'].values():row['file_identity']=dict(device=r['facts']['net_namespace']['device'],inode=r['facts']['net_namespace']['inode'])
        with self.assertRaises(ValueError):G.validate_ack(a,r)
    def test_ready_must_join_actual_host_pid_start_and_private_namespace(self):
        r,a=acknowledge(facts());v=r['facts'];binding=dict(container_id=a['container_id'],host_pid=501,guest_pid=v['guest']['pid'],start_ticks=v['guest']['start_ticks'])
        ns=dict(container_id=a['container_id'],bound_guest_host_pid=501,bound_guest_start_ticks=binding['start_ticks'],
            namespaces=dict(guest=dict(link=v['net_namespace']['link'],file_identity={k:v['net_namespace'][k]for k in('device','inode')})),
            comparisons=dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False))
        text=G.READY_MARKER+json.dumps(r);H.ready(text,G,'b'*64,'c'*64,binding,ns)
        binding['host_pid']+=1
        with self.assertRaises(ValueError):H.ready(text,G,'b'*64,'c'*64,binding,ns)
    def test_original_official_eval_call_and_resource_constraints_preserved(self):
        old=ast.parse((PACKET/'frozen/he_worker_v2.py').read_bytes());new=ast.parse((PACKET/'he_worker.py').read_bytes())
        def calls(tree):return [ast.dump(n,include_attributes=False)for n in ast.walk(tree)if isinstance(n,ast.Call)
            and isinstance(n.func,ast.Attribute)and n.func.attr=='evaluate_functional_correctness']
        self.assertEqual(calls(old),calls(new));self.assertEqual(len(calls(new)),1)
        def functions(tree):return {n.name:ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,ast.FunctionDef)}
        a,b=functions(old),functions(new)
        for name in('local_hash','rows','main'):self.assertEqual(a[name],b[name])
        old_runtime=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='runtime')
        new_runtime=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='runtime')
        self.assertEqual([ast.dump(n)for n in old_runtime.body[:2]],[ast.dump(n)for n in new_runtime.body[:2]])
        self.assertEqual([ast.dump(n)for n in old_runtime.body[3:]],[ast.dump(n)for n in new_runtime.body[3:-3]])
    def test_guard_no_active_network_and_host_ACK_uses_exclusive_atomic_publish(self):
        tree=ast.parse((PACKET/'he_network_guard.py').read_bytes())
        calls={n.func.attr if isinstance(n.func,ast.Attribute)else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call)and isinstance(n.func,(ast.Attribute,ast.Name))}
        self.assertFalse({'socket','ioctl','setns','unshare','connect','send','sendto','recv'}&calls)
        source=(P/'he_admission.py').read_text()
        for value in('os.O_NOFOLLOW','os.O_EXCL','os.link(','dir_fd=tmpfd','os.fsync(fd)','F.namespace_id(proc)==before'):
            self.assertIn(value,source)


if __name__=='__main__':unittest.main()
