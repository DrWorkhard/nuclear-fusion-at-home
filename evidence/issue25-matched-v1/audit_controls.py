from pathlib import Path
import json, hashlib, sys
import numpy as np
sys.path.insert(0,'/private/tmp/fusion-issue25-Hg6Meh/repo/src')
from fusion_baselines.coil_bounce import measure
root=Path('/Users/sebastianwirkert/workspace/fusion')
study=root/'artifacts/issue25-matched-v1'
index=json.loads((root/'evidence/plasma-balanced-v1/validation.json').read_text())
results=[]
for target,label in [('reference401','reference-401'),('selected401','selected-401')]:
 state=next(s for s in index['states'] if s['label']==label)
 measurement=Path(state['measurements'][0]['path'])
 assert hashlib.sha256(measurement.read_bytes()).hexdigest()==state['measurements'][0]['sha256']
 old=json.loads(measurement.read_text())
 rows=[]
 for trace in old['traces']:
  path=Path(trace['arrays']['path'])
  assert hashlib.sha256(path.read_bytes()).hexdigest()==trace['arrays']['sha256']
  with np.load(path,allow_pickle=False) as d:
   arrays={k:d[k].copy() for k in d.files}
  for key in ('B','theta','speed'):
   arrays[key]=arrays[key][::2,::2]
  arrays['alpha']=arrays['alpha'][::2];arrays['phi']=arrays['phi'][::2]
  arrays['length']=np.zeros_like(arrays['B'])
  arrays['length'][1:]=np.cumsum((arrays['speed'][:-1]+arrays['speed'][1:])*np.diff(arrays['phi'])[:,None]/2,axis=0)
  rebuilt=measure(arrays)
  actual=study/target/'bounce'/f"ideal-s{trace['s']}.npz"
  if not actual.exists(): continue
  with np.load(actual,allow_pickle=False) as d:
   errors={k:float(np.max(abs(d[k]-arrays[k]))) for k in ('B','length','theta')}
   current=measure(d)
  score_error=abs(current['score']/rebuilt['score']-1)
  rows.append(dict(s=trace['s'],archive_sha256=trace['arrays']['sha256'],array_max_errors=errors,score_relative_error=score_error,passed=score_error<=1e-8))
 results.append(dict(target=target,source_measurement_sha256=state['measurements'][0]['sha256'],rows=rows,all_pass=len(rows)==5 and all(r['passed'] for r in rows)))
(study/'ideal-controls.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
