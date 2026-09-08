from pathlib import Path
import subprocess
import io
import tarfile

root = Path(__file__).resolve().parents[1].parents[2]
repo = root / 'cuMES'
scratch = root / 'tmp/cumes-optimization-slides-20260907'
scratch.mkdir(exist_ok=True)
versions = [('pre-cuda', '5379fca^'), ('cuda', '5379fca'),
            ('v1.1', 'v1.1.0'), ('v1.2', 'v1.2.0')]
for name, ref in versions:
    src = scratch / name
    if not src.exists():
        subprocess.run(['git', '-C', str(repo), 'worktree', 'add', '--detach', str(src), ref], check=True)
    if name == 'v1.2':
        entry = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', ref, 'deps/BSplineInterpolation'], text=True)
        sha = entry.split()[2]
        dep = src / 'deps/BSplineInterpolation'
        archive = subprocess.check_output(['git', '-C', str(repo / 'deps/BSplineInterpolation'), 'archive', sha])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(dep, filter='data')
    build = scratch / (name + '-build')
    with (scratch / (name + '-build.log')).open('w') as log:
        command = ['cmake', '-S', str(src), '-B', str(build), '-G', 'Ninja',
                   '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CUDA_ARCHITECTURES=61',
                   '-DCUMES_PRECISION_POLICY=verify-double', '-DCUMES_USE_NETCDF=OFF',
                   '-DCUMES_USE_HDF5=OFF', '-DCUMES_USE_VACUUM_FIELD=OFF',
                   '-DCUMES_BUILD_MAGNETIC_COORDINATE=OFF']
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        subprocess.run(['cmake', '--build', str(build), '--target', 'cumes',
                        'cumes_benchmark_fixed_iteration', '-j', '6'],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    print('Built ' + name, flush=True)
