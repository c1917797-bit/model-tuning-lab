"""Independent structure/bitwise-boundary interpretation, never qualification."""
def need(v,m):
 if not v:raise ValueError(m)
def consume(w,comparisons):
 p=w['projection_trace'];need(p['schema']=='bole.root-projection-internal-trace/v1'and p['qualified']is False,'typed diagnostic trace')
 calls=[tuple(x)for x in p['calls']]
 for c in(0,2):
  need(calls.count((c,'projection.forward','call'))==calls.count((c,'projection.forward','return'))==1,'exact repeated-root projection once')
  rows=[r for r in w['rows']if r['kind']=='out_proj'and r['call']==c]
  need(rows and all(r['layer']==0 for r in rows),'complete GDN0 projection rows')
  stages=[r['stage']for r in rows];need(len(stages)==len(set(stages)),'no duplicate internal stages')
  need('projection.forward.entry'in stages and'projection.forward.return'in stages,'real projection input and return')
 selected=[r for r in comparisons if r['key'][0]=='out_proj']
 need(selected,'independent original-byte comparisons present')
 geometry=[]
 for a in w['rows']:
  if a['kind']!='out_proj'or a['call']!=0:continue
  b=next(r for r in w['rows']if r['kind']=='out_proj'and r['call']==2 and r['stage']==a['stage'])
  if 'tensors'not in a or'tensors'not in b:continue
  for name,x in a['tensors'].items():
   y=b['tensors'][name]
   fields=('shape','stride','offset','dtype','device','storage_bytes')
   geometry.append(dict(stage=a['stage'],field=name,geometry_equal=all(x['source_identity'][k]==y['source_identity'][k]for k in fields),format_equal=x['format_code']==y['format_code']))
 return dict(schema='bole.independent-projection-root-attribution/v1',complete=True,qualified=False,
  comparisons=selected,geometry=geometry,first_difference=next((r for r in selected if not r['bitwise_equal']),None),
  branch=p['active'],fused_local_result_not_invented=True)
