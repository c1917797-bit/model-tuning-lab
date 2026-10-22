"""Explicit opt-in, source-bound native projection callsite observer.

Imports only stdlib. No model/operator execution, tracing, hooks or I/O at import.
The factory only constructs; the parent must call install() and own uninstall().
Code hashes and full logical tensor hashes are producer-runtime witnesses.
"""
import ast
import hashlib
import inspect
import json
import marshal
import os
import sys
import types

FLAG = 'BOLE_NATIVE_PROJECTION_PROBE_ENABLE'
SCHEMA = 'bole.native-projection-internal/v1'
STAGES = ('projection_input', 'quant_return', 'pre_reduce', 'post_reduce', 'projection_return')
EVENT = 'PROJECTION-INTERNAL'
ENVELOPE_CAP = 8192
GENERATION_READ_CAP = 8 * 2**20
TOTAL_READ_CAP = 16 * 2**20
SINGLE_READ_CAP = 2 * 2**20
DECLARATION = dict(schema=SCHEMA, enabled=True, arm='ON', generations=2,
    input_tokens=131, stages=list(STAGES), envelope_bytes_cap=ENVELOPE_CAP,
    extra_read_bytes_per_generation=GENERATION_READ_CAP,
    extra_read_bytes_total=TOTAL_READ_CAP, raw_bytes=4 * 131 * 5120 * 2,
    full_weight_bytes_hashed=False, source_bound_python_callsites_only=True,
    numerical_qualified=False, formal_performance=False)

EXPECTED_RUNTIME_REFS = {
    '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py': dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py', bytes=21354, sha256='3f14a92019a6612158ba41a26c358c8f164cbda66b743c518a5e4019694b5dc3'),
    '/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py': dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py', bytes=30813, sha256='0333d3229dbfed3010413510b76395a9ad89138dfd1d578caab057573b6cd0fb'),
    '/vllm-workspace/vllm-ascend/vllm_ascend/utils.py': dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/utils.py', bytes=67646, sha256='575b45d684eabdb7ac3195d33de48bd5f3233081f78886c08be92a4a2fd2fc02'),
    '/vllm-workspace/vllm/vllm/model_executor/custom_op.py': dict(path='/vllm-workspace/vllm/vllm/model_executor/custom_op.py', bytes=13924, sha256='4b4ba01623005d6a93698eaec007a934dd512bf9ec7241090927de819621de2e'),
    '/vllm-workspace/vllm/vllm/model_executor/layers/linear.py': dict(path='/vllm-workspace/vllm/vllm/model_executor/layers/linear.py', bytes=63273, sha256='a5e099997f868a5ce670aa2afe94da90222fceace36aef4e1275f3830ee257ab'),
}

REDUCERS = {'tensor_model_parallel_all_reduce', 'tensor_model_parallel_reduce_scatter',
            'reduce_scatter', 'npu_mm_all_reduce_base', 'npu_mm_reduce_scatter_base'}
FUSED = {'npu_mm_all_reduce_base', 'npu_mm_reduce_scatter_base'}
_MISSING = object()


def need(value, why):
    if not value:
        raise ValueError(why)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode()


def text(value, limit=192):
    need(type(value) is str and len(value) <= limit, 'bounded literal metadata string')
    return value


def class_name(value):
    return text(type(value).__module__ + '.' + type(value).__qualname__)


def code_sha(code):
    return hashlib.sha256(marshal.dumps(code)).hexdigest()


def select(environ, declaration):
    value = environ.get(FLAG)
    if value in (None, '', '0'):
        need(declaration is None, 'declared projection observer requires explicit flag')
        return None
    need(value == '1' and type(declaration) is dict and
         canonical(declaration) == canonical(DECLARATION),
         'exact typed projection declaration and explicit opt-in')
    return declaration


def _function_node(tree, qualname):
    found = []
    def visit(node, parents=()):
        for child in getattr(node, 'body', ()):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                path = parents + (child.name,)
                if '.'.join(path) == qualname:
                    found.append(child)
                visit(child, path)
    visit(tree)
    need(len(found) == 1 and isinstance(found[0], ast.FunctionDef), 'one exact source function AST')
    return found[0]


def source_code(C, method, refs, cache):
    """Compile the complete module; never execute the retrieved module."""
    need(inspect.ismethod(method), 'actual Python bound method')
    function = method.__func__
    module = inspect.getmodule(function)
    path = inspect.getsourcefile(function)
    need(module is not None and function.__globals__ is module.__dict__ and
         not hasattr(function, '__wrapped__'), 'unwrapped actual module globals')
    need(path in refs and C.ref(path) == refs[path], 'exact installed-source Ref3')
    if path not in cache:
        body = C.checked(refs[path]).read_bytes()
        cache[path] = (compile(body, path, 'exec', dont_inherit=True), ast.parse(body, filename=path))
    compiled, tree = cache[path]
    codes = []
    def visit(code, parts=()):
        parts = parts + (() if code.co_name == '<module>' else (code.co_name,))
        if getattr(code, 'co_qualname', '.'.join(parts)) == function.__qualname__:
            codes.append(code)
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                visit(value, parts)
    visit(compiled)
    need(len(codes) == 1 and codes[0] == function.__code__, 'complete-source exact native method code')
    return function.__code__, path, _function_node(tree, function.__qualname__)


def _target(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _target(node.value)
        return None if parent is None else parent + '.' + node.attr
    return None


def reduction_sites(function_node):
    """Only direct native assignment/return callsites; skip nested definitions."""
    sites = []
    def visit(node, root=False):
        if not root and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        expression = None
        destination = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            expression, destination = node.value, node.targets[0].id
        elif isinstance(node, ast.Return):
            expression, destination = node.value, 'return'
        if isinstance(expression, ast.Call):
            target = _target(expression.func)
            kind = None if target is None else target.rsplit('.', 1)[-1]
            if kind in REDUCERS:
                need(destination in ('output', 'return'), 'supported exact native reduction destination')
                fused = kind in FUSED
                need(fused or expression.args and isinstance(expression.args[0], ast.Name) and
                     expression.args[0].id == 'output_parallel', 'actual nonfused output_parallel operand')
                sites.append(dict(line=node.lineno, end_line=node.end_lineno, target=target,
                                  kind=kind, destination=destination, fused=fused))
        for child in ast.iter_child_nodes(node):
            visit(child)
    visit(function_node, root=True)
    return sites


def create(owner, environ):
    """Default OFF has no source reads, wrapper, trace, files or tensor operation."""
    if environ.get(FLAG) in (None, '', '0'):
        return None
    if select(environ, owner.manifest.get('projection_probe_profile')) is None:
        return None
    return Observer(owner)


class Observer:
    def __init__(self, owner):
        self.owner = owner
        owner._identity()
        C, manifest = owner.C, owner.manifest
        need(C.ref(__file__) == manifest['files']['projection_probe_v1.py'] and
             C.obj(owner.source) == manifest, 'source-owned projection helper and exact owner source')
        refs = manifest.get('projection_runtime_refs')
        need(type(refs) is dict and canonical(refs) == canonical(EXPECTED_RUNTIME_REFS),
             'exact original five installed runtime Ref3s')
        self.refs = dict(refs)
        self.ref_list = [refs[path] for path in sorted(refs)]
        for ref in self.ref_list:
            C.checked(ref)
        self.gdn = owner.model.layers[0].linear_attn
        self.layer = self.gdn.out_proj
        self.original = self.layer.forward
        need(inspect.ismethod(self.original) and self.original.__self__ is self.layer,
             'actual target layer0 bound projection forward')
        self.original_instance = self.layer.__dict__.get('forward', _MISSING)
        self.quant = self.layer.quant_method
        self.custom = getattr(self.layer, 'custom_op', None)
        targets = [('projection.forward', self.original), ('quant.apply', self.quant.apply)]
        for base in type(self.layer).__mro__[1:]:
            function = base.__dict__.get('forward')
            if base.__name__ == 'RowParallelLinear' and inspect.isfunction(function) and function is not self.original.__func__:
                targets.append(('projection.generic_forward', types.MethodType(function, self.layer)))
        if self.custom is not None:
            need(self.custom.layer is self.layer, 'actual custom operation owns target projection')
            targets += [('custom.apply', self.custom.apply), ('custom.apply_impl', self.custom.apply_impl)]
            if hasattr(self.custom, 'matmul_and_reduce'):
                targets.append(('custom.matmul_and_reduce', self.custom.matmul_and_reduce))
        need(len(targets) <= 6, 'bounded actual method role set')
        self.methods, self.roles = {}, []
        cache = {}
        for role, method in targets:
            code, path, node = source_code(C, method, refs, cache)
            need(code not in self.methods, 'distinct exact native role code objects')
            function = method.__func__
            row = dict(role=role, source_index=sorted(refs).index(path),
                       qualname=text(function.__qualname__), receiver=id(method.__self__),
                       code_sha256=code_sha(code), first_line=code.co_firstlineno)
            self.roles.append(row)
            self.methods[code] = (role, method.__self__, function, reduction_sites(node))
        self.failed = False
        self.installed = False
        self.install_attempted = False
        self.wrapper = None
        self.trace = self._trace  # Retain one exact bound callable for ownership checks.
        self.current = None
        self.completed = {}
        self.retired = []
        self.extra_read_bytes = 0
        import projection_raw_v1 as PR
        self.raw_writer = PR.Writer(owner)

    def _fail(self):
        self.failed = True
        self.owner.failed = True

    def install(self):
        need(not self.failed and not self.install_attempted and self.current is None,
             'single explicit projection observer installation')
        self.install_attempted = True
        original = self.original
        observer = self
        def forward(layer, *args, **kwargs):
            need(layer is observer.layer, 'same actual projection wrapper receiver')
            if not observer.owner.scope:
                need(not observer.failed, 'sticky projection observer failure')
                return original(*args, **kwargs)
            return observer._invoke(args, kwargs)
        self.wrapper = types.MethodType(forward, self.layer)
        try:
            need(self.layer.__dict__.get('forward', _MISSING) is self.original_instance,
                 'unchanged original instance forward slot before install')
            self.layer.forward = self.wrapper
            need(self.layer.__dict__.get('forward') is self.wrapper, 'own exact instance wrapper installed')
            self.installed = True
            return self
        except BaseException as primary:
            self._fail()
            try:
                self.uninstall()
            except BaseException as secondary:
                primary.add_note('projection partial installation rollback: ' + repr(secondary))
            raise

    def _scope(self):
        owner = self.owner
        owner._identity()
        need(not self.failed and self.installed and owner.scope is True and
             owner.generation in (1, 2) and owner.generation == len(owner.retirements) + 1 and
             owner.active is not None and owner.pending is None and tuple(owner.native) == (0,) and
             owner.native[0][0] is self.gdn and owner.native[0][3] is owner.active[1] and
             owner.native[0][1].num_actual_tokens == 131 and
             owner.model.layers[0].linear_attn is self.gdn and self.gdn.out_proj is self.layer and
             self.layer.__dict__.get('forward') is self.wrapper and
             self.layer.quant_method is self.quant and getattr(self.layer, 'custom_op', None) is self.custom,
             'real native G1/G2 after GDN0 return, before layer1, same request and actual operands')
        need('layer0_gated_norm' in owner.raw_seen and 'layer0_out_projection' not in owner.raw_seen,
             'after original gated-norm witness and before original projection output witness')
        return owner.generation, owner.active[0], owner.active[1]

    def _tensor_metadata(self, tensor):
        need(isinstance(tensor, self.owner.t.Tensor), 'actual tensor metadata only')
        geometry = self.owner._geometry(tensor)
        try:
            version = tensor._version
            need(type(version) is int and 0 <= version < 2**64, 'bounded actual tensor version')
        except RuntimeError:
            version = None
        return dict(geometry=geometry, version=version, bytes_hashed=False,
                    format_observed=False, format=None)

    def _active_metadata(self):
        layer = self.layer
        need(type(layer.tp_rank) is int and type(layer.tp_size) is int and
             1 <= layer.tp_size <= 4 and 0 <= layer.tp_rank < layer.tp_size and
             all(type(getattr(layer, key)) is bool for key in
                 ('input_is_parallel', 'reduce_results', 'return_bias')),
             'actual bounded TP flags and group rank, no inferred defaults')
        return dict(layer_class=class_name(layer), layer_object=id(layer),
            gdn_object=id(self.gdn), prefix=text(layer.prefix, 128),
            tp_rank=layer.tp_rank, tp_size=layer.tp_size,
            input_is_parallel=layer.input_is_parallel, reduce_results=layer.reduce_results,
            return_bias=layer.return_bias,
            quant_class=class_name(self.quant), quant_object=id(self.quant),
            custom_class=None if self.custom is None else class_name(self.custom),
            custom_object=None if self.custom is None else id(self.custom),
            weight=self._tensor_metadata(layer.weight),
            bias=None if layer.bias is None else self._tensor_metadata(layer.bias))

    def _hash(self, stage, tensor, role, line):
        generation, request, native_request = self._scope()
        current = self.current
        need(current is not None and current['generation'] == generation and
             current['request'] == request and current['request_object'] == id(native_request) and
             stage not in current['stages'], 'one fresh hash stage in exact active generation')
        geometry = self.owner._geometry(tensor)
        count = geometry['logical_bytes']
        need(0 < count <= SINGLE_READ_CAP and
             current['read_bytes'] + count <= GENERATION_READ_CAP and
             self.extra_read_bytes + count <= TOTAL_READ_CAP,
             'original owner plus bounded extra 2MiB/8MiB/16MiB reads')
        if current['stages']:
            previous = list(current['stages'])[-1]
            need(STAGES.index(previous) < STAGES.index(stage), 'monotonic actual projection hash stages')
        before = self.owner.read_bytes
        cpu, raw, captured_geometry = self.owner._read(tensor)
        need(self.owner.read_bytes == before + count and len(raw) == count and
             captured_geometry == geometry, 'owner accounting charges this complete logical read once')
        current['read_bytes'] += count
        self.extra_read_bytes += count
        self.owner._finite(cpu)
        current['stages'][stage] = dict(observed=True, read_ordinal=len(current['stages']) + 1,
            source_role=role, line=line, sha256=hashlib.sha256(raw).hexdigest(), bytes=count,
            dtype=geometry['dtype'], shape=geometry['shape'], geometry=geometry, finite=True,
            full_actual_tensor=True, numerical_qualified=False)
        if stage in ('pre_reduce', 'post_reduce'):
            current['stages'][stage]['raw'] = self.raw_writer.put(generation, stage, raw, geometry)

    def _runtime_execution(self):
        enabled = self.owner.t.are_deterministic_algorithms_enabled()
        warn_only = self.owner.t.is_deterministic_algorithms_warn_only_enabled()
        need(type(enabled) is bool and type(warn_only) is bool,
             'actual worker torch deterministic flags')
        environment = {key: os.environ.get(key) for key in
                       ('HCCL_DETERMINISTIC', 'HCCL_ALGO', 'ASCEND_LAUNCH_BLOCKING')}
        need(all(value is None or type(value) is str and len(value) <= 128
                 for value in environment.values()), 'three bounded literal execution flags only')
        return dict(torch_deterministic_enabled=enabled,
                    torch_deterministic_warn_only=warn_only, environment=environment)

    def _projection_tensor(self, value):
        if self.layer.return_bias:
            need(type(value) is tuple and len(value) == 2, 'actual original projection tuple return')
            need(value[1] is None or isinstance(value[1], self.owner.t.Tensor), 'original output bias value')
            return value[0]
        need(isinstance(value, self.owner.t.Tensor), 'actual original projection tensor return')
        return value

    def _ancestor(self, frame):
        parent = frame.f_back
        while parent is not None:
            row = self.current['frames'].get(id(parent))
            if row is not None:
                need(row['frame'] is parent, 'same strongly retained native ancestor frame')
                return row
            parent = parent.f_back
        return None

    def _alias(self, frame, target):
        parts = target.split('.')
        value = frame.f_locals.get(parts[0], frame.f_globals.get(parts[0], _MISSING))
        for part in parts[1:]:
            if isinstance(value, types.ModuleType):
                value = value.__dict__.get(part, _MISSING)
            else:
                # Never invoke properties or manufacture a communication group.
                value = inspect.getattr_static(value, part, _MISSING) if value is not _MISSING else _MISSING
                if isinstance(value, (property, staticmethod, classmethod)):
                    value = value.__func__ if isinstance(value, (staticmethod, classmethod)) else _MISSING
        if value is _MISSING:
            return dict(observed=False, reason='descriptor_or_dynamic_receiver_not_evaluated')
        return dict(observed=True, object=id(value), type=class_name(value),
            module=text(getattr(value, '__module__', ''), 192),
            qualname=text(getattr(value, '__qualname__', getattr(value, '__name__', '')), 192),
            code_sha256=code_sha(value.__code__) if hasattr(value, '__code__') else None,
            source_pinned=False)

    def _start_reduce(self, frame, row, site):
        current = self.current
        need(not current['reductions'], 'one actual selected reduction callsite per projection')
        item = dict(site, role=row['role'], callsite_only=True, callee_source_pinned=False,
                    transport_kernel_observed=False, alias=self._alias(frame, site['target']))
        current['reductions'].append(item)
        row['pending_reduce'] = item
        if not site['fused']:
            need('output_parallel' in frame.f_locals, 'actual local output exists immediately before reduction')
            self._hash('pre_reduce', frame.f_locals['output_parallel'], row['role'], frame.f_lineno)

    def _trace(self, frame, event, arg):
        try:
            current = self.current
            need(current is not None, 'trace belongs to one active wrapper invocation')
            if event == 'call':
                match = self.methods.get(frame.f_code)
                if match is None:
                    return None
                role, receiver, function, sites = match
                parent = self._ancestor(frame)
                if role == 'projection.forward':
                    need(parent is None and frame.f_back is current['invocation_frame'] and
                         frame.f_locals.get('self') is self.layer and not current['root_seen'],
                         'one direct original projection invocation, no recursive substitute')
                    current['root_seen'] = True
                else:
                    if parent is None:
                        return None
                self._scope()
                need(frame.f_locals.get('self') is receiver and frame.f_globals is function.__globals__,
                     'actual native code, bound receiver and exact module globals')
                if role == 'quant.apply':
                    need(frame.f_locals.get('layer') is self.layer, 'quant method consumes this exact projection layer')
                    need(sum(call == [role, 'call'] for call in current['calls']) == 0,
                         'one actual selected quant call')
                need(len(current['calls']) < 24, 'bounded actual call metadata')
                current['calls'].append([role, 'call'])
                current['frames'][id(frame)] = dict(frame=frame, role=role, sites=sites,
                                                   pending_reduce=None, site_started=set())
                return self.trace
            row = current['frames'].get(id(frame))
            if row is None:
                return None
            need(row['frame'] is frame, 'same current native frame')
            role = row['role']
            if event == 'exception':
                need(len(current['exceptions']) < 4, 'bounded observed Python exception events')
                current['exceptions'].append(dict(role=role, line=frame.f_lineno,
                    type=text(arg[0].__module__ + '.' + arg[0].__qualname__)))
                return self.trace
            if event == 'line':
                pending = row['pending_reduce']
                if pending is not None and pending['destination'] == 'output' and frame.f_lineno > pending['end_line']:
                    need('output' in frame.f_locals, 'actual source-assigned reduction output')
                    self._hash('post_reduce', frame.f_locals['output'], role, frame.f_lineno)
                    row['pending_reduce'] = None
                for site in row['sites']:
                    if site['line'] <= frame.f_lineno <= site['end_line'] and site['line'] not in row['site_started']:
                        row['site_started'].add(site['line'])
                        self._start_reduce(frame, row, site)
                return self.trace
            if event == 'return':
                pending = row['pending_reduce']
                if arg is not None:
                    if pending is not None:
                        need(pending['destination'] == 'return', 'source assignment reduction output observed before return')
                        self._hash('post_reduce', arg, role, frame.f_lineno)
                        row['pending_reduce'] = None
                    if role == 'quant.apply':
                        self._hash('quant_return', arg, role, frame.f_lineno)
                    if role == 'projection.forward':
                        self._hash('projection_return', self._projection_tensor(arg), role, frame.f_lineno)
                current['calls'].append([role, 'return'])
                del current['frames'][id(frame)]
                return None
            return self.trace
        except BaseException:
            self._fail()
            raise

    def _invoke(self, args, kwargs):
        result = _MISSING
        try:
            generation, request, native_request = self._scope()
            need(self.current is None and generation not in self.completed and
                 generation == len(self.completed) + 1 and self.retired == list(range(1, generation)),
                 'one observed projection in each actual retired generation sequence')
            need(sys.gettrace() is None and sys.getprofile() is None, 'no existing trace/profile instrumentation')
            bound = inspect.signature(self.original).bind(*args, **kwargs)
            need('input_' in bound.arguments, 'actual original projection input argument')
            self.current = dict(generation=generation, request=text(request, 128),
                request_object=id(native_request), frames={}, calls=[], exceptions=[],
                stages={}, reductions=[], root_seen=False, read_bytes=0,
                invocation_frame=sys._getframe(), active=self._active_metadata())
            self._hash('projection_input', bound.arguments['input_'], 'projection.wrapper_entry', 0)
            need(sys.gettrace() is None and sys.getprofile() is None, 'trace/profile still unclaimed before native call')
            sys.settrace(self.trace)
            try:
                result = self.original(*args, **kwargs)  # Exactly one original bound call.
            finally:
                current_trace = sys.gettrace()
                if current_trace is self.trace:
                    sys.settrace(None)
                else:
                    need(current_trace is None and self.failed,
                         'trace ownership changed; never overwrite another installed trace')
            need(sys.getprofile() is None and not self.failed and not self.current['frames'],
                 'original call returned and own trace fully released')
            self._scope()
            current = self.current
            need(current['calls'].count(['projection.forward', 'call']) == 1 and
                 current['calls'].count(['projection.forward', 'return']) == 1 and
                 'projection_input' in current['stages'] and 'projection_return' in current['stages'],
                 'exact original input/return and one native call')
            fused = any(row['fused'] for row in current['reductions'])
            if fused:
                need('quant_return' not in current['stages'] and 'pre_reduce' not in current['stages'] and
                     'post_reduce' in current['stages'], 'fused local partial is truly absent')
            else:
                need('quant_return' in current['stages'], 'actual nonfused quant return observed')
            if current['reductions']:
                need('post_reduce' in current['stages'] and (fused or 'pre_reduce' in current['stages']),
                     'actual callsite before/after witnesses complete')
            else:
                need('pre_reduce' not in current['stages'] and 'post_reduce' not in current['stages'],
                     'no reduction claimed without an executed source callsite')
            stages = dict(current['stages'])
            for stage in STAGES:
                if stage not in stages:
                    stages[stage] = dict(observed=False, reason='fused_no_python_local_result' if fused else 'no_reduce_callsite_executed')
            record = dict(schema=SCHEMA, generation=generation, request=request,
                request_object=id(native_request), active=current['active'],
                runtime_refs=self.ref_list, roles=self.roles, calls=current['calls'],
                exceptions=current['exceptions'], stages={stage: stages[stage] for stage in STAGES},
                reductions=current['reductions'], read_bytes_generation=current['read_bytes'],
                read_bytes_total=self.extra_read_bytes,
                code_hash_algorithm='sha256(marshal.dumps(code)); producer-runtime witness',
                outer_records=dict(norm='G%d-RAW-layer0_gated_norm.json' % generation,
                                   projection='G%d-RAW-layer0_out_projection.json' % generation),
                trace_restored=True, original_bound_calls=1, new_raw_bytes=self.raw_writer.bytes,
                weight_bytes_hashed=False, source_bound_python_callsites_only=True,
                collective_implementation_pinned=False, runtime_execution=self._runtime_execution(), numerical_qualified=False,
                formal_performance=False, diagnostic_only=True)
            envelope = dict(schema=self.owner.manifest['boundary_probe_profile']['schema'],
                source_sha256=self.owner.source['sha256'], rank=self.owner.rank, pid=os.getpid(),
                generation=generation, event=EVENT, record=record,
                numerical_qualified=False, formal_performance=False)
            data = canonical(envelope)
            need(len(data) <= ENVELOPE_CAP, 'entire projection envelope within8192 bytes; no truncation')
            reference = self.owner.writer.put('G%d-%s.json' % (generation, EVENT), data)
            self.completed[generation] = dict(reference=reference, request=request,
                                             read_bytes=current['read_bytes'])
            self.current = None
            return result
        except BaseException:
            self._fail()
            raise
        finally:
            # Do not retain Python frames after an exception. Original return/args are untouched.
            if self.current is not None:
                self.current['frames'].clear()
                self.current = None

    def before_retire(self, generation):
        """Called after original native-removal proof, before parent's RETIRE write."""
        try:
            need(not self.failed and self.current is None and generation in (1, 2) and
                 self.owner.generation == generation and self.owner.active is not None and
                 self.retired == list(range(1, generation)) and generation in self.completed and
                 self.completed[generation]['request'] == self.owner.active[0] and
                 sys.gettrace() is not self.trace, 'one completed observer record before genuine retirement')
            self.retired.append(generation)
            if generation == 2:
                need(set(self.completed) == {1, 2}, 'exact two complete projection records')
                self.raw_writer.complete()
                self.uninstall()
        except BaseException:
            self._fail()
            raise

    def uninstall(self):
        """Idempotent restoration; never overwrite a foreign replacement."""
        need(self.current is None, 'no live native call during observer restoration')
        current = self.layer.__dict__.get('forward', _MISSING)
        if self.wrapper is not None and current is self.wrapper:
            if self.original_instance is _MISSING:
                del self.layer.forward
            else:
                self.layer.forward = self.original_instance
            need(self.layer.__dict__.get('forward', _MISSING) is self.original_instance,
                 'exact original instance attribute presence/value restored')
        elif self.install_attempted:
            need(current is self.original_instance, 'foreign forward replacement retained; not overwritten')
        self.installed = False
