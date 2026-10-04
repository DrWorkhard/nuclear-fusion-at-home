"""Run reviewed isolated checkout code with optional MPI disabled for this sandbox."""
import runpy
import sys
from pathlib import Path
sys.modules['mpi4py'] = None
sys.path.insert(0, str(Path.cwd() / 'src'))
mode, target, *args = sys.argv[1:]
sys.argv = [target, *args]
if mode == '-m':
    runpy.run_module(target, run_name='__main__', alter_sys=True)
else:
    runpy.run_path(target, run_name='__main__')
