"""Reproduce the deck's historical comparisons; requires an accessible CUDA GPU.

Run build_history.py first. Binaries and large outputs stay in ../tmp; portable
JSON and text evidence is written next to this script in ../data/local/.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import platform
import subprocess
import time

deck = Path(__file__).resolve().parents[1]
root = deck.parents[2]
scratch = root / 'tmp/cumes-optimization-slides-20260907'
out = deck / 'data/local'
out.mkdir(parents=True, exist_ok=True)
env = {k: v for k, v in os.environ.items() if not k.startswith('CUMES_')}
cpu = min(os.sched_getaffinity(0))
os.sched_setaffinity(0, {cpu})

def save(name, obj):
    (out / name).write_text(json.dumps(obj, indent=2) + '\n')

def gpu():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=name,driver_version,pstate,temperature.gpu,clocks.sm,clocks.mem,power.draw,utilization.gpu', '--format=csv,noheader'], text=True).strip()

save('environment.json', dict(date=datetime.datetime.now().astimezone().isoformat(),
     host=platform.node(), platform=platform.platform(), cpu_affinity=cpu,
     gpu=gpu(), clocks='unlocked; existing graphical GPU process left running',
     flags='Release; sm_61; verify-double; CUDA 12.1; g++-12; NetCDF/HDF5/vacuum/magnetic-coordinate OFF',
     method='Fixed: 1000-pass preheat per shape, 50 warmup + 300 timed, six alternating triples. CLI: one unmeasured pair per workload then five alternating pairs. No samples discarded.',
     revisions={n: subprocess.check_output(['git','-C',str(scratch/n),'rev-parse','HEAD'],text=True).strip() for n in ('pre-cuda','cuda','v1.1','v1.2')}))

for case in ('solovev', 'w7x'):
    subprocess.run([str(scratch/'cuda-build/cumes_benchmark_fixed_iteration'), '--config', case, '--warmup', '0', '--passes', '1000', '--out', str(scratch/'preheat.json')], cwd=scratch/'cuda', env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    variants = [('pre-cuda', {}), ('cuda-direct', {'CUMES_DISABLE_CUDA_GRAPHS':'1'}), ('cuda-graph', {})]
    for repeat in range(6):
        order = variants if repeat % 2 == 0 else list(reversed(variants))
        for variant, knobs in order:
            name = 'pre-cuda' if variant == 'pre-cuda' else 'cuda'
            stem = f'fixed-{case}-{variant}-{repeat+1}'
            command = [str(scratch/(name+'-build')/'cumes_benchmark_fixed_iteration'), '--config', case, '--warmup', '50', '--passes', '300', '--out', str(out/(stem+'.json'))]
            with (out/(stem+'.log')).open('w') as log:
                subprocess.run(command,cwd=scratch/name,env=env|knobs,stdout=log,stderr=subprocess.STDOUT,check=True)
            obj = json.loads((out/(stem+'.json')).read_text())
            obj.update(repeat=repeat+1, variant=variant, environment=knobs, gpu_after=gpu(), command=command)
            save(stem+'.json',obj)
        print(f'Fixed {case}: pair {repeat+1}/6',flush=True)

for case in ('solovev', 'w7x'):
    original = (scratch/'v1.1/inputs'/f'{case}.json').read_bytes()
    assert original == (scratch/'v1.2/inputs'/f'{case}.json').read_bytes()
    for grid in ('multigrid','single'):
        data = json.loads(original)
        if grid == 'single':
            for key in ('ns_array','niter_array','ftol_array'):
                data[key] = [data[key][-1]]
        input_file = out / f'input-{case}-{grid}.json'
        input_file.write_text(json.dumps(data,indent=2)+'\n')
        for repeat in range(6):
            for version in (('v1.1','v1.2') if repeat%2==0 else ('v1.2','v1.1')):
                stem=f'cli-{case}-{grid}-{version}-{repeat}'
                command=[str(scratch/(version+'-build')/'cumes'),str(input_file),'--output',str(scratch/(stem+'.bin'))]
                begin=time.perf_counter()
                with (out/(stem+'.log')).open('w') as log:
                    result=subprocess.run(command,cwd=scratch/version,env=env,stdout=log,stderr=subprocess.STDOUT)
                wall=time.perf_counter()-begin
                save(stem+'.json',dict(case=case,grid=grid,version=version,repeat=repeat,warmup=repeat==0,wall_s=wall,returncode=result.returncode,command=command,input_sha256=hashlib.sha256(input_file.read_bytes()).hexdigest(),gpu_after=gpu()))
                if result.returncode:
                    raise RuntimeError(f'{stem} failed; inspect log')
            print(f'CLI {case} {grid}: pair {repeat}/5',flush=True)

# Fixed-point gates run separately from all reported timings.
for case in ('solovev','w7x'):
    checkpoint=scratch/(case+'-v1.2.ckpt')
    cli=str(scratch/'v1.2-build/cumes')
    for phase in ('create','replay'):
        grid='multigrid' if phase=='create' else 'single'
        command=[cli,str(out/f'input-{case}-{grid}.json'),'--output',str(scratch/f'{case}-{phase}.bin')]
        command += ['--checkpoint' if phase=='create' else '--restart',str(checkpoint)]
        with (out/f'checkpoint-{case}-{phase}.log').open('w') as log:
            subprocess.run(command,cwd=scratch/'v1.2',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
print('All measurements and checkpoint replays complete',flush=True)
