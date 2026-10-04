import json, os, subprocess, time
from pathlib import Path
repo=Path('/private/tmp/fusion-issue25-Hg6Meh/repo')
workspace=Path('/Users/sebastianwirkert/workspace/fusion')
root=workspace/'artifacts/issue25-matched-v1'
python=workspace/'.venv/bin/python'
env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1',
         MKL_NUM_THREADS='1', MPLCONFIGDIR='/private/tmp/fusion-mpl', PYTHONPATH=str(repo/'src'))
wouts={
 'reference401':workspace/'artifacts/plasma-design-v2/reference-fine/wout.nc',
 'selected401':workspace/'artifacts/plasma-balanced-v1/endpoints/selected-fine/native/wout.nc'}
records=[]
def run(target,stage,script,arguments,budget):
 arm=root/target;arm.mkdir(exist_ok=True)
 cmd=[str(python),str(repo/'scripts'/script),*map(str,arguments), '--output',str(arm/stage)]
 started=time.monotonic()
 with (arm/(stage+'.log')).open('x') as log:
  try:
   done=subprocess.run(cmd,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=budget)
   status=done.returncode
  except subprocess.TimeoutExpired:
   status='hard-timeout'
 row=dict(target=target,stage=stage,command=cmd,status=status,elapsed_s=time.monotonic()-started)
 records.append(row);(root/'commands.json').write_text(json.dumps(records,indent=2))
 print(json.dumps(row),flush=True)
 used=sum(p.stat().st_size for p in arm.rglob('*') if p.is_file())
 if used > 256*1024**2: raise RuntimeError('arm aggregate output ceiling exceeded')
 return status
for target,wout in wouts.items():
 if run(target,'control','check_coils.py',['--candidate',repo/'submissions/length-headroom-six-coil/candidate.json','--wout',wout,'--target',target,'--seconds','300'],330):
  raise RuntimeError('control incomplete')
for target,wout in wouts.items():
 run(target,'fit','fit_coils.py',['--snapshot',root/target/'control/seed.json','--wout',wout,'--target',target,'--seconds','300','--check-seconds','300'],630)
for target,wout in wouts.items():
 snapshot=root/target/'fit/selected-snapshot.json'
 if not snapshot.exists(): continue
 run(target,'surfaces','trace_surfaces.py',['--snapshot',snapshot,'--wout',wout,'--target',target,'--transits','200','--direct'],300)
for target,wout in wouts.items():
 snapshot=root/target/'fit/selected-snapshot.json'
 if not snapshot.exists(): continue
 run(target,'bounce','measure_coil_bounce.py',['--snapshot',snapshot,'--wout',wout,'--target',target,'--seconds','600'],630)
complete=all((root/t/'bounce/result.json').exists() and json.loads((root/t/'bounce/result.json').read_text()).get('coil_wide_score') is not None for t in wouts)
if complete:
 for target,wout in wouts.items():
  run(target,'bounce-refined','measure_coil_bounce.py',['--snapshot',root/target/'fit/selected-snapshot.json','--wout',wout,'--target',target,'--seconds','600','--nphi','1601','--nalpha','32'],630)
