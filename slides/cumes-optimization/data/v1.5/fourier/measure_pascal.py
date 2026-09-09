import json
import os
from pathlib import Path
import random
import statistics as st
import subprocess

ROOT = Path(__file__).parent
OUT = ROOT / 'final-pascal'
OUT.mkdir(exist_ok=True)
EXES = {
    'baseline': ROOT / 'baseline-source/build/cumes_benchmark_fixed_iteration',
    'candidate': ROOT / 'weighted-bench',
}
os.sched_setaffinity(0, {8})

def quantile(values, fraction):
    values = sorted(values)
    pos = (len(values) - 1) * fraction
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)

def sample(config, variant, index, warmup=100, passes=500):
    path = OUT / f'{config}-{variant}-{index}.json'
    with path.with_suffix('.log').open('w') as log:
        subprocess.run([str(EXES[variant]), '--config', config,
                        '--warmup', str(warmup), '--passes', str(passes),
                        '--out', str(path)], stdout=log,
                       stderr=subprocess.STDOUT, check=True)
    result = json.loads(path.read_text())
    clocks = subprocess.check_output([
        'nvidia-smi', '--query-gpu=clocks.gr,clocks.mem,temperature.gpu,power.draw,pstate',
        '--format=csv,noheader'], text=True).strip()
    result['clock_sample'] = clocks
    path.write_text(json.dumps(result, indent=2) + '\n')
    print(config, variant, index, result['median_us_per_iter'],
          result['state_hash'], clocks, flush=True)
    return result

summary = {}
for config in ['w7x', 'solovev']:
    for variant in EXES:
        sample(config, variant, 'preheat', 1000, 1000)
    pairs = []
    for index in range(16):
        pair = {}
        for variant in (['baseline', 'candidate'] if index % 2 == 0
                        else ['candidate', 'baseline']):
            pair[variant] = sample(config, variant, index)
        assert pair['baseline']['state_hash'] == pair['candidate']['state_hash']
        pairs.append(pair)
    gains = [100 * (1 - p['candidate']['median_us_per_iter'] /
                        p['baseline']['median_us_per_iter']) for p in pairs]
    rng = random.Random(20260908)
    bootstrap = [st.median(rng.choices(gains, k=len(gains)))
                 for _ in range(20000)]
    result = {'paired_gain_percent': st.median(gains),
              'paired_gain_95_ci': [quantile(bootstrap, .025),
                                    quantile(bootstrap, .975)]}
    for variant in EXES:
        rows = [p[variant] for p in pairs]
        medians = [r['median_us_per_iter'] for r in rows]
        center = st.median(medians)
        result[variant] = {
            'median_us': center,
            'p95_us': st.median([r['p95_us_per_iter'] for r in rows]),
            'setup_us': st.median([r['setup_us'] for r in rows]),
            'median_mad_percent': 100 * st.median([abs(m-center) for m in medians]) / center,
            'state_hash': rows[0]['state_hash'],
            'arena_bytes': rows[0]['arena_bytes'],
            'cufft_work_bytes': rows[0]['cufft_work_bytes'],
        }
    summary[config] = result
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(config, json.dumps(result), flush=True)
