"""Default-off in-memory official scheduler seam. No framework file writes."""
import ast
import copy
import hashlib
import inspect
import textwrap
from pathlib import Path

def transform_schedule_source(source):
    tree=ast.parse(textwrap.dedent(source))
    funcs=[x for x in tree.body if isinstance(x,ast.FunctionDef)]
    if len(funcs)!=1 or funcs[0].name!="schedule" or funcs[0].decorator_list:
        raise ValueError("exact undecorated schedule method required")
    fn=funcs[0];running=0;waiting=0
    def visit_list(nodes):
        nonlocal running,waiting
        out=[]
        for node in nodes:
            if isinstance(node,ast.If) and ast.dump(node.test,include_attributes=False)==ast.dump(ast.parse("num_new_tokens == 0",mode="eval").body,include_attributes=False):
                if any(isinstance(x,ast.AugAssign) and isinstance(x.target,ast.Name) and x.target.id=="req_index" for x in node.body):
                    running+=1
                    out.extend(ast.parse("num_new_tokens = _independent_pic_cap(self, request, request.num_computed_tokens, num_new_tokens)").body)
            if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="limit_lookahead_tokens" for x in node.targets):
                waiting+=1
                out.extend(ast.parse("if not load_kv_async:\n    num_new_tokens = _independent_pic_cap(self, request, num_computed_tokens, num_new_tokens)\n    if num_new_tokens == 0:\n        break").body)
            for field,value in ast.iter_fields(node):
                if isinstance(value,list) and value and all(isinstance(x,ast.stmt) for x in value):
                    setattr(node,field,visit_list(value))
            out.append(node)
        return out
    fn.body=visit_list(fn.body)
    if (running,waiting)!=(1,1):
        raise ValueError("official pre-allocation scheduler anchors drifted")
    ast.fix_missing_locations(tree)
    return tree

def install_pic_scheduler(cls, *, enabled=False, expected_source_sha256=None, cap=None):
    if not enabled:return lambda:None
    if not callable(cap) or not expected_source_sha256:
        raise ValueError("source-bound readiness/admission callback required")
    original=cls.schedule
    if getattr(original,"_independent_pic_scheduler_owned",False) or original.__closure__:
        raise ValueError("already owned or unsupported scheduler closure")
    path=Path(inspect.getsourcefile(original))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_source_sha256:
        raise ValueError("official scheduler file identity drift")
    tree=transform_schedule_source(inspect.getsource(original))
    env=dict(original.__globals__)
    if "_independent_pic_cap" in env:raise ValueError("scheduler helper collision")
    def checked(self,request,computed,proposed):
        value=cap(self,request,computed,proposed)
        if type(value) is not int or not 0<=value<=proposed:
            raise ValueError("PIC admission may only cap native scheduled work")
        return value
    env["_independent_pic_cap"]=checked
    exec(compile(tree,str(path)+"<independent-pic>", "exec"),env)
    wrapped=env["schedule"];wrapped._independent_pic_scheduler_owned=True
    inherited="schedule" not in cls.__dict__
    cls.schedule=wrapped
    def stop():
        if cls.schedule is not wrapped:raise RuntimeError("scheduler hook ownership drift")
        if inherited:delattr(cls,"schedule")
        else:cls.schedule=original
    return stop
