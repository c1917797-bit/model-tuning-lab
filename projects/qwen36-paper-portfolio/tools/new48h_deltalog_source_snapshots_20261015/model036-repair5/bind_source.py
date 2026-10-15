"""One-shot actual023repair1+024full160 binding; no weights or device."""
import argparse,importlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owner_overlay as O

def bind_actual_bridge(m,bridge,bm):
 reviewed=O.obj(m['reviewed_domain_template_ref'])
 O.need(bm['prepared_template']==m['reviewed_domain_template_ref']and bm['root']==reviewed['root']and bm['files']==reviewed['files']==m['reviewed_domain_files'],'actual source bound from final035repair1 template/files')
 O.need(bm['prepared_only']is False and bm['validation_contract']==reviewed['validation_contract'],'actual035repair1 source/reference domain, never future template')
 O.need(m['expected_bound_bridge_ref']is None or m['expected_bound_bridge_ref']==bridge,'no substitution of previously bound bridge')
 m['expected_bound_bridge_ref']=bridge
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256');p.add_argument('--plugin-source-ref');p.add_argument('--bridge-owner-ref');p.add_argument('--bridge-source-ref');a=p.parse_args()
 if not a.execute:print('disabled');return 0
 template=P/'SOURCE_TEMPLATE.json';b=template.read_bytes();import hashlib
 O.need(hashlib.sha256(b).hexdigest()==a.template_sha256,'MAIN reviewed template');m=json.loads(b)
 O.need(m['root']==str(P)and m['prepared_only']is True,'actual immutable deployed scope')
 plugin=json.loads(a.plugin_source_ref);O.need(plugin==m['expected_bound_plugin_ref'],'exact MAIN deployed actual023repair1 source');pm=O.obj(plugin);expected=O.obj(m['plugin_template_ref'])
 O.need(pm['prepared_template']==m['plugin_template_ref']and pm['root']==expected['root']and pm['files']==expected['files'],'actual023repair1 only, no old023')
 bridge=json.loads(a.bridge_source_ref);bm=O.obj(bridge);bind_actual_bridge(m,bridge,bm)
 O.need(bm['schema']=='deltalog.deadpayload-native-bridge-source/v024'and bm['library_ref']==m['library_ref']and bm['prepared_only']is False,'actual MAIN-reviewed same B010 bridge successor')
 if m.get('admission_mode')=='actual035-directRNE-domain-diagnostic-only':
  O.need(type(m.get('reviewed_domain_files'))is dict and m['reviewed_domain_files']and bm['files']==m['reviewed_domain_files'],'MAIN-reviewed exact035 source pins; pending refuses')
 else:
  for name,pin in m['bridge_math_file_pins'].items():
   r=bm['files'][name];O.need((r['bytes'],r['sha256'])==(pin['bytes'],pin['sha256']),'same bridge numerical/oracle/qualification source '+name)
 m.update(plugin_source=plugin,composite_source_ref=pm['composite_source_ref'],composite_cpu_owner_ref=pm['composite_cpu_owner_ref'],bridge024_source_ref=bridge,bridge024_qualification_api_ref=bm['files']['qualification.py'],bridge024_owner_ref=json.loads(a.bridge_owner_ref),prepared_only=False)
 sys.path.insert(0,str(Path(plugin['path']).parent));from qwen36_deltalog_service import admission as A
 A.consume(plugin,m['composite_source_ref']);O.model_gate(m)
 for r in [*m['files'].values(),*m['dependencies'],*O.transitive_refs(m)]:O.obj_file(r)
 O.need('torch'not in sys.modules and'torch_npu'not in sys.modules,'host pure lightweight qualification')
 path=P/'SOURCE_MANIFEST.json'
 with path.open('x',encoding='utf8')as f:json.dump(m,f,sort_keys=True);f.write('\n')
 print(json.dumps(dict(source=dict(path=str(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),model_numeric_qualified=False,NPU=False)))
 return 0
if __name__=='__main__':raise SystemExit(main())
