"""Selective compiler bypass with an owned native-decode authorization.

The source-owned outer entry runs in Python before the compiler. It authorizes
only the pinned FULL uniform one-token decode route. The compiled model/layer
adapters consult this plain gate before any HYPIC ContextVars. No mode or
do_not_compile flag is rewritten. Native G1 does not use these adapters.
"""
from functools import wraps
from threading import Lock, get_ident


class SelectiveEntryRouter:
    """A component, not a service loader or an accepted runtime package.

    Production bindings must come from capture_native_bundle(), and the HYPIC
    prefill adapter must retain its selected-forward snapshot/lease/math checks.
    A source-verified original decorator __call__ remains the compiler owner.
    """
    def __init__(self, *, model_class, native_call, native_forward,
                 compilation_mode, graph_mode, forward_context_class,
                 batch_descriptor_class, get_context, is_compiling,
                 assert_ownership, prefill_forward):
        self.model_class = model_class
        self.native_call = native_call
        self.native_forward = native_forward
        self.compilation_mode = compilation_mode
        self.graph_mode = graph_mode
        self.forward_context_class = forward_context_class
        self.batch_descriptor_class = batch_descriptor_class
        self.get_context = get_context
        self.is_compiling = is_compiling
        self.assert_ownership = assert_ownership
        self.prefill_forward = prefill_forward
        self._lock = Lock()
        self._entry_model = None
        self._entry_thread = None
        self._native_decode = False
        self._installed = False
        self._owned = []

    def _profile(self, model, context):
        if type(model) is not self.model_class:
            raise ValueError("exact source-owned model instance required")
        if type(context) is not self.forward_context_class:
            raise ValueError("actual native ForwardContext required")
        config = getattr(model, "compilation_config", None)
        vllm = getattr(model, "vllm_config", None)
        if (config is None or getattr(vllm, "compilation_config", None) is not config
                or type(config.mode) is not self.compilation_mode
                or config.mode is not self.compilation_mode.VLLM_COMPILE
                or type(config.cudagraph_mode) is not self.graph_mode
                or config.cudagraph_mode is not self.graph_mode.FULL_DECODE_ONLY
                or getattr(model, "do_not_compile", None) is not False
                or getattr(getattr(vllm, "model_config", None), "enforce_eager", None) is not False):
            raise ValueError("actual VLLM_COMPILE/FULL_DECODE_ONLY profile required")
        parallel = getattr(vllm, "parallel_config", None)
        if (getattr(parallel, "tensor_parallel_size", None) != 4
                or getattr(parallel, "pipeline_parallel_size", None) != 1
                or getattr(parallel, "data_parallel_size", None) != 1
                or getattr(vllm, "speculative_config", None) is not None
                or getattr(vllm, "lora_config", None) is not None):
            raise ValueError("frozen TP4/PP1/DP1 non-speculative no-LoRA profile required")
        if context.ubatch_slices is not None or type(context.skip_compiled) is not bool:
            raise ValueError("ordinary unsliced native forward context required")
        mode = context.cudagraph_runtime_mode
        if type(mode) is not self.graph_mode:
            raise ValueError("actual native runtime graph mode required")
        if mode is self.graph_mode.NONE:
            return False
        if mode is not self.graph_mode.FULL:
            raise ValueError("PIECEWISE or mixed FULL graph is outside this candidate")
        metadata = getattr(context, "attn_metadata", None)
        if (type(metadata) is not dict or not metadata
                or any(type(getattr(item, "num_prefills", None)) is not int
                       or item.num_prefills != 0 for item in metadata.values())):
            raise ValueError("FULL route requires actual zero-prefill native metadata")
        descriptor = context.batch_descriptor
        if (type(descriptor) is not self.batch_descriptor_class
                or descriptor.uniform is not True
                or type(descriptor.num_tokens) is not int
                or type(descriptor.num_reqs) is not int
                or descriptor.num_tokens <= 0
                or descriptor.num_tokens != descriptor.num_reqs
                or descriptor.has_lora is not False
                or descriptor.num_active_loras != 0
                or context.skip_compiled is not False):
            raise ValueError("source-owned FULL pure one-token decode descriptor required")
        return True

    def _call(self, model, *args, **kwargs):
        # This outer function must never itself be traced or called concurrently.
        if self.is_compiling():
            raise RuntimeError("unowned compiled outer entry")
        if not self._lock.acquire(blocking=False):
            raise RuntimeError("concurrent or reentrant model entry")
        prior_skip = None
        context = None
        try:
            self.assert_ownership()
            context = self.get_context()
            native_decode = self._profile(model, context)
            prior_skip = context.skip_compiled
            self._entry_model = model
            self._entry_thread = get_ident()
            self._native_decode = native_decode
            if not native_decode:
                # Official decorator supports this field. Only this exact call
                # is bypassed; the actual compilation config stays unchanged.
                context.skip_compiled = True
            return self.native_call(model, *args, **kwargs)
        finally:
            self._native_decode = False
            self._entry_model = None
            self._entry_thread = None
            if context is not None and prior_skip is not None:
                context.skip_compiled = prior_skip
            self._lock.release()

    def model_forward(self, model, *args, **kwargs):
        # Keep authorization first: an authorized native decode trace must never
        # reach ContextVars, source inspection, locks or PIC branch selection.
        if self._native_decode and self._entry_model is model:
            if not self.is_compiling() and get_ident() != self._entry_thread:
                raise RuntimeError("decode outside owning native entry thread")
            return self.native_forward(model, *args, **kwargs)
        if self.is_compiling():
            raise RuntimeError("compiling prefill/PIC or unowned model entry")
        if self._entry_model is not model or get_ident() != self._entry_thread:
            raise RuntimeError("model forward bypassed owned outer entry")
        return self.prefill_forward(model, *args, **kwargs)

    def layer_forward(self, native, hypic):
        @wraps(native)
        def routed(layer, *args, **kwargs):
            if self._native_decode and self._entry_model is not None:
                if not self.is_compiling() and get_ident() != self._entry_thread:
                    raise RuntimeError("decode outside owning native entry thread")
                return native(layer, *args, **kwargs)
            if self.is_compiling():
                raise RuntimeError("compiling prefill/PIC or unowned layer entry")
            if self._entry_model is None or get_ident() != self._entry_thread:
                raise RuntimeError("layer forward bypassed owned outer entry")
            return hypic(layer, *args, **kwargs)
        routed._independent_graph_native_decode_route = True
        return routed

    def install(self, *, enabled=False, layers=()):
        """Install only when the caller has built a complete verified adapter.

        layers are (class, method name, exact native, exact HYPIC callable).
        This method neither finds nor unwraps unknown callables.
        """
        if not enabled:
            return lambda: None
        if self._installed:
            raise RuntimeError("graph entry already installed")
        self.assert_ownership()
        owned = []
        try:
            for cls, name, native, hypic in layers:
                if vars(cls).get(name) is not hypic:
                    raise ValueError("owned HYPIC layer slot changed")
                routed = self.layer_forward(native, hypic)
                setattr(cls, name, routed)
                owned.append((cls, name, hypic, routed, True))
            cls = self.model_class
            router = self
            for name, wrapper in (("forward", self.model_forward), ("__call__", self._call)):
                existed = name in vars(cls)
                original = vars(cls).get(name) if existed else None
                # Functions, rather than bound router methods, preserve Python
                # descriptor binding on model instances.
                if name == "forward":
                    # Official _mark_dynamic_inputs binds these exact names.
                    # Bytecode hooks also require the real model in local self.
                    @wraps(self.native_forward)
                    def installed(self, input_ids, positions,
                                  intermediate_tensors=None, inputs_embeds=None):
                        return router.model_forward(self, input_ids, positions,
                            intermediate_tensors, inputs_embeds)
                else:
                    @wraps(self.native_call)
                    def installed(self, *args, **kwargs):
                        return router._call(self, *args, **kwargs)
                setattr(cls, name, installed)
                owned.append((cls, name, original, installed, existed))
            self._owned = owned
            self._installed = True
        except BaseException:
            for cls, name, original, wrapper, existed in reversed(owned):
                if vars(cls).get(name) is wrapper:
                    if existed:
                        setattr(cls, name, original)
                    else:
                        delattr(cls, name)
            raise

        def stop():
            if self._entry_model is not None or self._native_decode:
                raise RuntimeError("cannot uninstall during model execution")
            if not self._installed:
                raise RuntimeError("graph entry is not installed")
            for cls, name, original, wrapper, existed in reversed(self._owned):
                if vars(cls).get(name) is not wrapper:
                    raise RuntimeError("graph adapter ownership changed")
            for cls, name, original, wrapper, existed in reversed(self._owned):
                if existed:
                    setattr(cls, name, original)
                else:
                    delattr(cls, name)
            self._installed = False
            self._owned = []
        return stop
