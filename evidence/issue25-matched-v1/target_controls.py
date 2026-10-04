import json,hashlib,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/private/tmp/fusion-issue25-Hg6Meh/repo/src')
from fusion_baselines import coil_check as check
from fusion_baselines.clear_coil_field_audit import archived_target
root=Path('/Users/sebastianwirkert/workspace/fusion')
index=json.loads((root/check.INDEX).read_text())
rows=[]
for target,label in [('reference401','reference-401'),('selected401','selected-401')]:
 state=next(s for s in index['states'] if s['label']==label)
 _,targets,_,_=check.portable_intake(state['wout']['path'],target_id=target)
 archives=[]
 for f in state['fields']:
  if f['n']!=64:continue
  p=Path(f['arrays']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==f['arrays']['sha256']
  with np.load(p) as a: archives.append(dict(s=f['s'],n=64,arrays={k:a[k] for k in a.files}))
 expected=archived_target(archives,64)
 errors={k:float(np.max(abs(targets[64][k]-expected[k]))) for k in ('inner_points','inner_target')}
 rows.append(dict(target=target,errors=errors,B2_scale=expected['B2_scale'],passed=max(errors.values())<=1e-12,archive_sha256=[f['arrays']['sha256'] for f in state['fields'] if f['n']==64]))
(root/'artifacts/issue25-matched-v1/target-controls.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
