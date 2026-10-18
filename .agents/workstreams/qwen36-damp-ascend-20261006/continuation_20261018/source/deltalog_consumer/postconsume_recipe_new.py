"""One serial geometry-accounting CPU consumer on original R36 Owned machinery."""
import json
import os
import resource
import time
import traceback
from pathlib import Path


def cap(now, started, wall, cutoff):
    import phase_budget_r21 as budget
    value = min(900.0, budget.work_remaining(now, started, wall, cutoff))
    if value <= 0:
        raise ValueError('no positive consumer budget after cleanup270/postverify900/margin90')
    return value


def run(h, model_ref, component_owner, started, input_ref, consumer_ref, geometry_ref):
    source = h._CONSUMER_MANIFEST
    model_source = h._CONSUMER_MODEL
    h.need(source['model_source'] == model_ref and h._CONSUMER_SOURCE == consumer_ref, 'distinct actual consumer/model identities')
    h.need(Path(__file__).resolve().as_posix() == source['files']['postconsume_recipe_new.py']['path'], 'actual independent recipe source path')
    h._CONSUMER_ABSENCE()
    c, S, Owned, state = h.safety(model_ref, h.POLICY, started)
    import postwork_verify
    postwork_verify.protect(Owned, state, started, h.CUTOFF)
    lease = h._SNAPSHOT
    ctl = None
    primary = None
    detail = None
    result = {}
    secondary = h._CONSUMER_SECONDARY
    payload_ref = source['payload_source']
    try:
        _, hard = resource.getrlimit(resource.RLIMIT_AS)
        h.need(hard == resource.RLIM_INFINITY, 'original host AS ABI remains unlimited-hard')
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, hard))
        h.need(Path(h.OUT).as_posix() == source['output_root'], 'sole new source-owned output')
        lease.extra_opt = h.OUT
        lease.open(existing=True)
        lease.wrap_writer(c)
        inputs = c.obj(input_ref)
        h.need(set(inputs) == {'schema', 'model_source', 'payload_source', 'owner_ref', 'inspect_ref', 'loaded_ref', 'reports_ref'}, 'original exact seven-key actual INPUT')
        h.need(inputs['schema'] == 'deltalog.firstdecode-postconsumer-input/v1' and inputs['model_source'] == model_ref and inputs['payload_source'] == payload_ref, 'same original model/payload actual input')
        h.need(model_source['firstdecode_contract']['payload_source'] == payload_ref, 'unchanged payload relation')
        h._CONSUMER_ABSENCE()
        result['consumer_context'] = c.write(h.OUT / 'CONSUMER_CONTEXT.json', dict(
            schema='deltalog.geometry-consumer-context/v1', consumer_source=consumer_ref,
            model_source=model_ref, payload_source=payload_ref, input_ref=input_ref,
            geometry_refs_ref=geometry_ref, host_entry=source['files']['host_consumer.py'],
            original_owned_controller=model_source['host017_ref'],
            original_model_host=model_source['files']['host_ticket.py'],
            model_snapshot_journal=lease.journal, old_postconsumer_output=model_source['postconsumer_output_root'],
            old_postconsumer_absent=True, combined_opt_roots=[model_source['output_root'], source['output_root']],
            combined_opt_cap_bytes=2 * 2**30, terminal_reserve_bytes=64 * 2**20,
            whole_seconds=3600, cleanup_seconds=270, postverify_seconds=900, margin_seconds=90,
            child_max_seconds=900, cutoff_epoch=h.CUTOFF, runtime_identity=source['runtime_identity'],
            Devices=[], NPU=False, qualified=False,
        ))
        root = h.OUT / 'cpu-consumer'
        root.mkdir(mode=0o700)
        ctl = Owned(root)
        original_observe = ctl.observe

        def observe(*args, **kwargs):
            h._CONSUMER_ABSENCE(terminal=lease.terminal)
            value = original_observe(*args, **kwargs)
            h._CONSUMER_ABSENCE(terminal=lease.terminal)
            return value

        ctl.observe = observe
        ctl.observe('geometry-consumer-serial-Devices-empty-admission', initial=True)
        host = S.H.cpu_view(os.getpid())
        os.sched_setaffinity(0, {min(host['effective_cpus'])})
        _, hard = resource.getrlimit(resource.RLIMIT_AS)
        h.need(hard == resource.RLIM_INFINITY, 'same actual host AS ABI')
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, hard))
        original_inspect = c.obj(inputs['inspect_ref'])
        if type(original_inspect) is list:
            h.need(len(original_inspect) == 1, 'one exact original parent CID')
            original_inspect = original_inspect[0]
        parent_cid = original_inspect['Id']

        def parent_stopped(label):
            h._CONSUMER_ABSENCE()
            observed, _ = ctl.call(label, [S.DOCKER, 'inspect', parent_cid])
            h.need(observed['exit_code'] == 0, 'fresh original parent inspect')
            rows = json.loads(observed['stdout'])
            h.need(len(rows) == 1, 'one fresh original parent inspect row')
            value = rows[0]
            h.need(value['Id'] == parent_cid and value['Image'] == original_inspect['Image'] and value['State']['Running'] is False and value['State']['Pid'] == 0 and not value['State']['OOMKilled'] and not value.get('ExecIDs'), 'same original parent remains stopped/noExec/noOOM')
            h._CONSUMER_ABSENCE()
            return c.write(root / (label + '.json'), rows)

        fresh_inspect = parent_stopped('MODEL-PARENT-BEFORE')
        child_cap = cap(time.monotonic(), started, time.time(), h.CUTOFF)
        model = c.model(c.MODEL_REF)
        ctl.create_native(model, True)
        inspected, _ = ctl.inspect()
        host_config = inspected['HostConfig']
        h.need(not host_config.get('Devices') and not host_config.get('DeviceRequests') and host_config['Memory'] == 8 * 2**30 and len(ctl.expected['guest_cpus']) == 1, 'actual exact inspected Devices[],8GiB,1CPU')
        rw = [mount for mount in inspected['Mounts'] if mount['RW']]
        h.need(rw and {mount['Source'] for mount in rw} == {str(root)} and any(mount['Destination'] == '/adakv-results' for mount in rw), 'all original RW aliases name only the new CPU leaf')
        result['actual_CPU_inspect'] = c.write(root / 'CPU-INSPECT.json', inspected)
        entry = source['files']['postconsume_entry_new.py']
        command = [entry['path'], '--execute', '--consumer-source-ref', json.dumps(consumer_ref), '--model-source-ref', json.dumps(model_ref), '--payload-source-ref', json.dumps(payload_ref)]
        for name, value in zip(('owner', 'inspect', 'loaded', 'reports'), (inputs['owner_ref'], fresh_inspect, inputs['loaded_ref'], inputs['reports_ref'])):
            command += ['--' + name + '-ref', json.dumps(value)]
        command += ['--geometry-refs-ref', json.dumps(geometry_ref), '--output', '/adakv-results/FIRST-DECODE-INDEPENDENT.json']
        child_cap = min(child_cap, cap(time.monotonic(), started, time.time(), h.CUTOFF))
        h._CONSUMER_ABSENCE()
        h.child(ctl, c, 'geometry-firstdecode-independent-all4', command, child_cap, observe=False)
        h._CONSUMER_ABSENCE()
        output = root / 'FIRST-DECODE-INDEPENDENT.json'
        value = c.obj(c.ref(output))
        h.need(value['schema'] == 'deltalog.independent-all4-firstdecode/v1' and value['source'] == payload_ref and value['model_source'] == model_ref and value['consumer_source'] == consumer_ref and value['geometry_refs_ref'] == geometry_ref and value['repair_scope'] == 'geometry-control-accounting-only', 'actual independent consumer and unchanged original model/payload identities')
        h.need(value['diagnostic_complete'] is True and value['full_model_qualified'] is value['performance_qualified'] is value['task_qualified'] is False, 'all independent numerical gates remain diagnostic only')
        result.update(independent_ref=c.ref(output), child_cap_seconds=child_cap, parent_before=fresh_inspect, parent_after=parent_stopped('MODEL-PARENT-AFTER'))
    except BaseException as error:
        primary = error
        detail = dict(type=type(error).__name__, traceback=''.join(traceback.format_exception(type(error), error, error.__traceback__)))
    finally:
        cleanup_started = time.monotonic()
        cleanup_before = state['cleanup_spent']
        lease.terminal = True
        h._CONSUMER_ABSENCE(terminal=True)
        if ctl is not None and ctl.cid:
            try:
                result['cleanup'] = h.close_owned(ctl, c, primary)
            except BaseException as error:
                secondary.append('cleanup ' + repr(error))
            secondary.extend(ctl.secondary)
        state['cleanup_spent'] = max(state['cleanup_spent'], cleanup_before + time.monotonic() - cleanup_started)
        if time.monotonic() > state['end'] or state['cleanup_spent'] > h.CLEANUP_TOTAL or time.time() >= h.CUTOFF:
            secondary.append('original whole/cleanup/cut exhausted')
        released = False
        if result.get('cleanup'):
            try:
                note = c.obj(result['cleanup'])
                released = note['stopped'] is note['retained'] is True and not note['errors']
            except BaseException as error:
                secondary.append('cleanup receipt ' + repr(error))
        try:
            if lease.fd is not None:
                result['post_work_verification'] = postwork_verify.run(h, lease, model_ref, state, started, released, lambda: postwork_verify.fresh_owned(h, S, [ctl] if ctl else []))
        except BaseException as error:
            secondary.append('post-work-verification ' + repr(error))
        h._CONSUMER_ABSENCE(terminal=True)
        result.update(
            schema='deltalog.geometry-consumer-owned/v1', source=consumer_ref,
            consumer_source=consumer_ref, model_source=model_ref, payload_source=payload_ref,
            input_ref=input_ref, geometry_refs_ref=geometry_ref,
            repair_scope='geometry-control-accounting-only', original_model_failure_preserved=True,
            primary=repr(primary) if primary else None, primary_detail=detail, secondary=secondary,
            elapsed=time.monotonic() - started, cleanup_seconds=state['cleanup_spent'],
            cid=ctl.cid if ctl else None, resource_release_verified=released, stopped_retained=released,
            registered_child_max_seconds=900, Devices=[], NPU=False,
            model_qualified=False, performance_qualified=False, task_qualified=False,
        )
        try:
            c.write(h.OUT / 'RESULT.json', result)
        finally:
            lease.release()
    if primary:
        raise primary
    h.need(not secondary and released and time.monotonic() <= state['end'] and time.time() < h.CUTOFF, 'independent CPU source/release/absence/time final gates')
    return 0


if __name__ == '__main__':
    raise SystemExit('Not a standalone owner. Use the source-bound host_consumer.py entry.')
