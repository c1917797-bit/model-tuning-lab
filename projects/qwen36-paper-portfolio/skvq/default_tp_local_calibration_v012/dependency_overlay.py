"""DEFAULT-OFF three-package RO supply precheck; no install, download or controller.

The caller must source-bind a real manifest. No version is selected here. Static
wheel/tree validation is not ABI success. The optional same-image import/fit
smoke has synthetic 256x2 input and grants no calibration/data/model authority.
"""
import argparse,email,hashlib,importlib,json,math,os,platform,re,stat,sys,zipfile
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit

PACKAGES={"scikit-learn":("sklearn","scikit_learn"),
          "joblib":("joblib","joblib"),"threadpoolctl":("threadpoolctl","threadpoolctl")}
MAX_WHEEL=128*2**20;MAX_TREE=1024*2**20
def need(value,message):
    if not value:raise ValueError(message)
def reference(path):
    p=Path(path)
    need(p.is_absolute()and".."not in p.parts and p.is_file(),"absolute existing regular Ref")
    for q in(p,*p.parents):need(not q.is_symlink(),"no source/evidence symlink")
    h=hashlib.sha256()
    with p.open("rb")as f:
        for raw in iter(lambda:f.read(2**20),b""):h.update(raw)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def read(ref,limit=MAX_WHEEL):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and
      type(ref["bytes"])is int and 0<ref["bytes"]<=limit and
      type(ref["sha256"])is str and re.fullmatch("[a-f0-9]{64}",ref["sha256"]),"bounded exact three-key Ref")
    need(reference(ref["path"])==ref,"entire file bytes/SHA")
    raw=Path(ref["path"]).read_bytes();need(reference(ref["path"])==ref,"immutable read");return raw
def normalized(name):return re.sub("[-_.]+","-",name).lower()
def abi_tags(tags,compiled):
    need(tags and len(tags)==len(set(tags)),"complete unique wheel tags")
    allowed={"cp312-cp312-manylinux_2_17_aarch64","cp312-cp312-manylinux2014_aarch64"}if compiled else{"py3-none-any","py2-none-any"}
    need(set(tags)<=allowed and (compiled or "py3-none-any"in tags),"only CPython3.12 aarch64 or pure Python3 wheel")
def wheel_tree(row,root,expected):
    need(type(row)is dict and set(row)=={"name","version","wheel_ref","pypi_metadata_ref","download_url"},"exact reviewed distribution row")
    name=row["name"];need(name in PACKAGES and normalized(name)==name and
      type(row["version"])is str and re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}",row["version"]),"explicit exact stable version; no latest/range")
    module,stem=PACKAGES[name];wr=row["wheel_ref"];read(wr)
    meta=json.loads(read(row["pypi_metadata_ref"],2**20));url=row["download_url"];u=urlsplit(url)
    need(u.scheme=="https"and u.hostname=="files.pythonhosted.org"and not u.username and not u.password and not u.port and not u.query and not u.fragment,
      "exact official wheel URL, not a mirror or unverified artifact")
    files=[x for x in meta["urls"]if x["filename"]==Path(wr["path"]).name]
    need(normalized(meta["info"]["name"])==name and meta["info"]["version"]==row["version"]and len(files)==1,
      "source-bound official version/file metadata")
    f=files[0];need(f["url"]==url and f["digests"]["sha256"]==wr["sha256"]and
      f["size"]==wr["bytes"]and f["packagetype"]=="bdist_wheel"and not f["yanked"],"official size/SHA and non-yanked binary wheel")
    dist=stem+"-"+row["version"]+".dist-info";allowed={module,module+".py",stem+".libs",dist}
    requires=None;tags=None
    with zipfile.ZipFile(wr["path"])as z:
        infos=z.infolist();need(len(infos)==len({x.filename for x in infos}),"no duplicate ZIP member")
        for info in infos:
            p=PurePosixPath(info.filename)
            need(not p.is_absolute()and p.parts and".."not in p.parts and"\\"not in info.filename and
              p.parts[0]in allowed and not info.filename.endswith(".pth"),"only exact three-package members; no traversal/pth/shadow NumPy/Torch")
            mode=info.external_attr>>16
            need(not stat.S_ISLNK(mode)and (not stat.S_IFMT(mode)or stat.S_ISREG(mode)or stat.S_ISDIR(mode)),"ordinary wheel member")
            if info.is_dir():continue
            need(info.file_size<=64*2**20 and info.filename not in expected,"bounded unique combined wheel member")
            raw=z.read(info);path=root.joinpath(*p.parts)
            for q in(path,*path.parents):need(not q.is_symlink(),"no extracted member/parent link")
            need(path.is_file()and path.read_bytes()==raw,"complete extracted bytes equal original wheel, including metadata/RECORD")
            expected[info.filename]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if info.filename==dist+"/METADATA":
                m=email.message_from_bytes(raw)
                need(normalized(m["Name"])==name and m["Version"]==row["version"],"original wheel METADATA identity")
                requires=dict(python=m.get("Requires-Python"),dist=m.get_all("Requires-Dist",[]))
            if info.filename==dist+"/WHEEL":tags=email.message_from_bytes(raw).get_all("Tag",[])
    abi_tags(tags,name=="scikit-learn");need(requires is not None and dist+"/RECORD"in expected,"original dependency metadata/RECORD exists")
    need(sum(x["bytes"]for x in expected.values())<=MAX_TREE,"bounded complete supply tree")
    return dict(name=name,version=row["version"],wheel_ref=wr,pypi_metadata_ref=row["pypi_metadata_ref"],tags=tags,requires=requires)
def qualify(manifest_ref,*,native=True):
    manifest=json.loads(read(manifest_ref,2**20))
    need(type(manifest)is dict and set(manifest)=={"schema","root","python","machine","glibc_min","distributions","baseline"}and
      manifest["schema"]=="skvq.calibration-ro-three-wheel-bundle/v1"and manifest["python"]==[3,12]and
      manifest["machine"]=="aarch64"and manifest["glibc_min"]==[2,17],"source-bound three-package ABI contract")
    root=Path(manifest["root"]);need(root.is_absolute()and root.is_dir()and root.resolve()==root,"actual canonical extracted bundle root")
    for q in(root,*root.parents):need(not q.is_symlink(),"no bundle root link")
    rows=manifest["distributions"];need(type(rows)is list and len(rows)==3 and
      {x["name"]for x in rows}==set(PACKAGES),"all and only sklearn/joblib/threadpoolctl; native SciPy preserved")
    baseline=manifest["baseline"];need(type(baseline)is dict and set(baseline)=={"torch","numpy","scipy"},"native unchanged Torch/NumPy/SciPy, no replacement")
    for name,b in baseline.items():
        need(type(b)is dict and set(b)=={"version","origin_ref"}and type(b["version"])is str and b["version"],"actual inventoried native baseline version/origin")
        r=b["origin_ref"];ref_shape(r,2**20)
        if native:read(r,2**20)
        p=Path(r["path"])
        need(root!=p and root not in p.parents,"baseline not provided or shadowed by overlay")
    expected={};dist=[wheel_tree(row,root,expected)for row in rows];actual=set()
    for parent,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:need(not Path(parent,name).is_symlink(),"no extra extracted link")
        for name in files:
            p=Path(parent,name);need(stat.S_ISREG(p.stat().st_mode),"no FIFO/device/socket in dependency tree")
            actual.add(p.relative_to(root).as_posix())
    need(actual==set(expected),"complete extracted tree; no ambient extra package/pycache")
    return manifest,dict(schema="skvq.calibration-ro-three-wheel-supply-checked/v1",manifest_ref=manifest_ref,
      root=str(root),distributions=dist,files=len(actual),bytes=sum(x["bytes"]for x in expected.values()),
      full_wheel_and_extracted_bytes_checked=True,actual_sameimage_import_fit_checked=False,
      calibration_executed=False,native_ready=False,model_ready=False)

BOUND=None
LOCK=Path(__file__).resolve().parent/"DOWNLOAD_LOCK.json"
BUNDLE_ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-three-wheel-bundle-v1-001")
NATIVE_SITE=Path("/usr/local/python3.12.13/lib/python3.12/site-packages")
def ref_shape(ref,limit=MAX_WHEEL):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and
      type(ref["path"])is str and Path(ref["path"]).is_absolute()and".."not in Path(ref["path"]).parts and
      type(ref["bytes"])is int and 0<ref["bytes"]<=limit and
      type(ref["sha256"])is str and re.fullmatch("[a-f0-9]{64}",ref["sha256"]),"bounded exact origin3Ref")
    return ref
def reviewed(manifest_ref,*,native):
    manifest,proof=qualify(manifest_ref,native=native)
    lock=json.loads(LOCK.read_bytes());rows={r["name"]:r for r in lock["packages"]}
    need(set(rows)==set(PACKAGES)and lock["total_wheel_bytes"]==11827308,"source-qualified reviewed three-package lock")
    need(Path(manifest_ref["path"])==BUNDLE_ROOT/"BUNDLE.json"and Path(manifest["root"])==BUNDLE_ROOT/"site",
      "one reviewed small same-path dependency input tree, not broad mount")
    for row in manifest["distributions"]:
        want=rows[row["name"]]
        need(row["version"]==want["version"]and row["wheel_ref"]["bytes"]==want["bytes"]and
          row["wheel_ref"]["sha256"]==want["sha256"]and row["download_url"]==want["url"]and
          Path(row["wheel_ref"]["path"])==BUNDLE_ROOT/"wheels"/want["filename"]and
          Path(row["pypi_metadata_ref"]["path"]).parent==BUNDLE_ROOT/"metadata",
          "only reviewed actual wheel/metadata identities, no substitution")
    for n,b in manifest["baseline"].items():
        need(b["version"]==lock["native_baseline"][n]and b["origin_ref"]==lock["native_origin_refs"][n]and
          Path(b["origin_ref"]["path"])==NATIVE_SITE/n/"__init__.py","actual unchanged same660 native baseline origin/version")
    proof["download_lock_ref"]=reference(LOCK)
    return manifest,proof
def cached_origins(root):
    for prefix,_ in PACKAGES.values():
        for name,module in tuple(sys.modules.items()):
            if name!=prefix and not name.startswith(prefix+"."):continue
            p=getattr(module,"__file__",None);spec=getattr(module,"__spec__",None)
            need(type(p)is str and spec is not None and spec.origin==p,"actual cached module/spec origin, no ambient substitute")
            path=Path(p)
            need(root in path.parents and path.resolve()==path and path.is_file(),"same reviewed overlay origin for every cached namespace")
            reference(path)
def bind(manifest_ref):
    global BOUND
    need("torch_npu"not in sys.modules,"CPU fitting supply must not import NPU framework")
    manifest,proof=reviewed(manifest_ref,native=True);root=Path(manifest["root"])
    identity=dict(manifest_ref=manifest_ref,root=str(root),pid=os.getpid())
    if BOUND is None:
        for prefix,_ in PACKAGES.values():
            need(not any(n==prefix or n.startswith(prefix+".")for n in sys.modules),"cold package namespace before explicit supply bind")
        need(str(root)not in sys.path,"no ambient path injection before explicit supply bind")
        sys.path.insert(0,str(root));BOUND=identity
    else:
        need(BOUND==identity and sys.path[0]==str(root),"same process/manifest/root explicit idempotent binding")
        cached_origins(root)
    return manifest,proof
def smoke_loaded(modules,manifest_ref):
    # Caller has already set Torch intra/interop ONCE; never reset them here.
    manifest,proof=reviewed(manifest_ref,native=True)
    need(BOUND==dict(manifest_ref=manifest_ref,root=manifest["root"],pid=os.getpid()),"actual explicit cold bind preceded library smoke")
    libc,version=platform.libc_ver()
    need(sys.version_info[:2]==(3,12)and platform.machine()=="aarch64"and libc=="glibc"and
      tuple(int(x)for x in version.split(".")[:2])>=tuple(manifest["glibc_min"]),"actual CPython3.12/aarch64/glibc ABI")
    allmods={n:importlib.import_module(n)for n in("torch","numpy","sklearn","scipy","joblib","threadpoolctl")}
    for n in("torch","numpy","sklearn","threadpoolctl"):need(modules[n]is allmods[n],"one actual fitting library namespace")
    for n,b in manifest["baseline"].items():
        need(reference(allmods[n].__file__)==b["origin_ref"]and allmods[n].__version__==b["version"],"unchanged native baseline imported")
    for d in manifest["distributions"]:
        n=PACKAGES[d["name"]][0]
        need(Path(manifest["root"])in Path(allmods[n].__file__).parents and allmods[n].__version__==d["version"],"actual reviewed overlay version/origin")
    torch=modules["torch"]
    need(torch.get_num_threads()==torch.get_num_interop_threads()==1,"caller already established unique one-thread budget")
    from sklearn.cluster import KMeans
    need(KMeans is modules["actual_sklearn_KMeans"],"same original real KMeans class")
    x=torch.tensor([[i//64+(i%64)/10000.,(i//64)*2.]for i in range(256)],dtype=torch.float32,device="cpu")
    fitted=KMeans(4,n_init=10).fit(x);pools=modules["threadpoolctl"].threadpool_info()
    need(len(fitted.labels_)==256 and fitted.cluster_centers_.shape==(4,2)and math.isfinite(float(fitted.inertia_)),"real compiled synthetic KMeans completed")
    need(torch.get_num_threads()==torch.get_num_interop_threads()==1 and"torch_npu"not in sys.modules and
      all(type(p.get("num_threads"))is int and p["num_threads"]==1 for p in pools),"unchanged CPU thread/device budget after fit")
    cached_origins(Path(manifest["root"]))
    proof.update(actual_sameimage_import_fit_checked=True,actual_glibc=[libc,version],
      actual_modules={n:reference(v.__file__)for n,v in allmods.items()},
      actual_versions={n:v.__version__ for n,v in allmods.items()},actual_threadpools=pools,
      synthetic_library_smoke_only=True,original_128_fit_verified=False,
      parameters=fitted.get_params(deep=False),iterations=int(fitted.n_iter_),inertia=float(fitted.inertia_))
    return proof
def verify_saved(proof,*,captured=False):
    need(type(captured)is bool,"explicit actual live or captured namespace")
    manifest,static=reviewed(proof["manifest_ref"],native=not captured)
    for key,value in static.items():
        if key=="actual_sameimage_import_fit_checked":continue
        need(proof[key]==value,"exact reviewed supply/tree/static provenance")
    need(proof["actual_sameimage_import_fit_checked"]is True and proof["synthetic_library_smoke_only"]is True and
      proof["original_128_fit_verified"]is False and proof["calibration_executed"]is False and
      proof["native_ready"]is False and proof["model_ready"]is False,"synthetic before-fit ABI only, no author calibration grant")
    need(set(proof["actual_modules"])==set(proof["actual_versions"])=={"torch","numpy","sklearn","scipy","joblib","threadpoolctl"},"all native/supply module origins and versions")
    for n,b in manifest["baseline"].items():
        need(proof["actual_modules"][n]==b["origin_ref"]and proof["actual_versions"][n]==b["version"],"exact native baseline origin/version preserved")
    for d in manifest["distributions"]:
        n=PACKAGES[d["name"]][0];r=ref_shape(proof["actual_modules"][n],2**20)
        need(Path(manifest["root"])in Path(r["path"]).parents and proof["actual_versions"][n]==d["version"]and reference(r["path"])==r,"actual imported overlay complete origin bytes")
    expected=dict(n_clusters=4,init="k-means++",n_init=10,max_iter=300,tol=1e-4,verbose=0,random_state=None,copy_x=True,algorithm="lloyd")
    need(proof["parameters"]==expected and type(proof["iterations"])is int and proof["iterations"]>0 and
      type(proof["inertia"])in(int,float)and math.isfinite(proof["inertia"])and proof["inertia"]>=0,"explicit unchanged constructor defaults; not library1.2.1 bitwise equivalence")
    need(all(type(p.get("num_threads"))is int and p["num_threads"]==1 for p in proof["actual_threadpools"]),"actual synthetic threadpool1")
    libc,version=proof["actual_glibc"]
    need(libc=="glibc"and tuple(int(x)for x in version.split(".")[:2])>=tuple(manifest["glibc_min"]),"actual smoke glibc floor")
    return manifest,static
def smoke(manifest_ref):
    need(os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD")=="0"and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")==""and
      not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",n).exists()for n in("devmm_svm","hisi_hdc")),"actual Devices[] CPU gate")
    need(all(os.environ.get(k)=="1"for k in("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS","NUMEXPR_NUM_THREADS")),"pre-import thread budget")
    bind(manifest_ref)
    import torch,numpy,sklearn,threadpoolctl
    from sklearn.cluster import KMeans
    torch.set_num_threads(1);torch.set_num_interop_threads(1)
    return smoke_loaded(dict(torch=torch,numpy=numpy,sklearn=sklearn,threadpoolctl=threadpoolctl,actual_sklearn_KMeans=KMeans),manifest_ref)
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--manifest-ref-json");p.add_argument("--import-fit-smoke",action="store_true");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,calibration_executed=False,native_ready=False,model_ready=False)));return
    need(a.manifest_ref_json,"MAIN reviewed exact dependency manifest Ref required")
    ref=json.loads(Path(a.manifest_ref_json).read_bytes())
    proof=smoke(ref)if a.import_fit_smoke else qualify(ref)[1]
    print(json.dumps(proof,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
