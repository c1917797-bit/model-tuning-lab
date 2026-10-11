"""Source-bound 3.9 AST representation, not source or algorithm substitution.
Only empty 3.12 type_params are omitted from digest copies. Execution trees
remain original. The frozen004 reader is compiled privately with one digest
expression adapted; all its actual whole/source/owner/resource checks remain.
"""
import ast,copy,hashlib,sys,types
from pathlib import Path

CONTROL={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/MAIN_HOST.py",
 "bytes":25396,"sha256":"05b1522a2ef0a9ccc7f203818378d064c910cb4fdab0f3c753fa44792cf962e4"}
READER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-capture014-offline-consumer-v1-004/consume_cpu_whole.py",
 "bytes":12501,"sha256":"e0c1fcca073bbbe52f2aeae51df8604752fe3627a2ec94b8833a6a991da2d2ca"}
CONTROL_39="ed8993c286547e4fd03ee8bcc0aeaeb707e569a36f3b118293628b19ab5320fb"
AUTHOR_BYTES=15928
AUTHOR_SHA="16f33eb9248605fca33fdf504ae93475ef6f768d9c58f6aa2661ce5b03f6c100"
AUTHOR_39="183b3406c04207247dda1aa5cc23caeffe59a52d5ccb92bb0bb6774eac71f070"

def need(value,message):
    if not value:raise ValueError(message)

def digest(node):
    return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()

def project(node):
    need(sys.version_info[:2] in ((3,9),(3,10),(3,11),(3,12)),"reviewed Python3.9..3.12 AST only")
    value=copy.deepcopy(node)
    for item in ast.walk(value):
        if "type_params" in item._fields:
            need(isinstance(item,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and
              type(item.type_params)is list and item.type_params==[],
              "only empty Python3.12 class/function type_params; nonempty/unknown rejected")
            item._fields=tuple(k for k in item._fields if k!="type_params")
    return value

def source_node(raw,size,sha,kind,name):
    need(type(raw)is bytes and len(raw)==size and hashlib.sha256(raw).hexdigest()==sha,
      "exact original immutable whole source bytes")
    tree=ast.parse(raw);nodes=[x for x in tree.body if isinstance(x,kind) and x.name==name]
    need(len(nodes)==1 and not nodes[0].decorator_list,"one undecorated source-bound original body")
    return nodes[0]

def control_proof(raw):
    node=source_node(raw,CONTROL["bytes"],CONTROL["sha256"],ast.ClassDef,"Control")
    legacy=digest(project(node));need(legacy==CONTROL_39,"unchanged Control3.9 body digest")
    return {"native_sha256":digest(node),"legacy_sha256":legacy,
      "empty_type_params":sum("type_params" in x._fields for x in ast.walk(node))}

def control_digest(raw):
    return control_proof(raw)["legacy_sha256"]

def author_digest(raw):
    node=source_node(raw,AUTHOR_BYTES,AUTHOR_SHA,ast.FunctionDef,"get_reorder_indices")
    legacy=digest(project(node));need(legacy==AUTHOR_39,"unchanged original author function3.9 body digest")
    return legacy

def controller_digest(Controller,raw=None):
    need(Controller.donor_source_ref==CONTROL,"exact original014 Control source, no alias or substituted class")
    raw=Path(CONTROL["path"]).read_bytes() if raw is None else raw
    proof=control_proof(raw)
    need(Controller.donor_class_ast_sha256==proof["native_sha256"],
      "original004 class native digest must match exact source on this interpreter")
    return proof["legacy_sha256"]

def adapt_reader_tree(raw):
    need(type(raw)is bytes and len(raw)==READER["bytes"] and hashlib.sha256(raw).hexdigest()==READER["sha256"],
      "exact frozen004 whole reader bytes")
    tree=ast.parse(raw,filename=READER["path"])
    hits=[x for x in ast.walk(tree) if isinstance(x,ast.Attribute) and
      isinstance(x.value,ast.Name) and x.value.id=="Controller" and x.attr=="donor_class_ast_sha256"]
    need(len(hits)==1,"one frozen004 Control digest expression, all other guards unchanged")
    target=hits[0]
    class Adapter(ast.NodeTransformer):
        def visit_Attribute(self,node):
            if node is target:
                return ast.copy_location(ast.Call(func=ast.Name(id="_strict_legacy_control_digest",ctx=ast.Load()),
                  args=[ast.Name(id="Controller",ctx=ast.Load())],keywords=[]),node)
            return self.generic_visit(node)
    return ast.fix_missing_locations(Adapter().visit(tree))

def derived_reader(row):
    need(row==READER,"one exact frozen004 consumer Ref")
    raw=Path(row["path"]).read_bytes();tree=adapt_reader_tree(raw)
    name="_skvq_cal011_private_derived004_whole"
    need(name not in sys.modules,"no ambient private reader reuse or replacement")
    module=types.ModuleType(name);module.__file__=row["path"]
    module.__dict__["_strict_legacy_control_digest"]=controller_digest
    exec(compile(tree,row["path"],"exec"),module.__dict__)
    return module
