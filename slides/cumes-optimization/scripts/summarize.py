"""Summarize preserved samples without dropping slow runs."""
from pathlib import Path
import json
import random
import re
import statistics as st

folder=Path(__file__).resolve().parents[1]/'data/local'
def stats(a):
    med=st.median(a)
    return dict(n=len(a),median=med,mad=st.median(abs(x-med) for x in a),
                min=min(a),max=max(a),samples=a)
def improvement(a,b):
    rng=random.Random(20260907)
    boots=[]
    for _ in range(20000):
        indices=[rng.randrange(len(a)) for _ in a]
        boots.append(100*(1-st.median(b[i] for i in indices)/st.median(a[i] for i in indices)))
    boots.sort()
    return dict(reduction_percent=100*(1-st.median(b)/st.median(a)),
                paired_bootstrap_95_percent=[boots[499],boots[19499]])
summary={'fixed':{},'cli':{},'comparisons':{}}
for case in ('solovev','w7x'):
    summary['fixed'][case]={}
    for variant in ('pre-cuda','cuda-direct','cuda-graph'):
        rows=[json.loads(f.read_text()) for f in sorted(folder.glob(f'fixed-{case}-{variant}-*.json'))]
        assert len(rows)==6
        summary['fixed'][case][variant]={
            'median_us':stats([x['median_us_per_iter'] for x in rows]),
            'p95_us':stats([x['p95_us_per_iter'] for x in rows]),
            'setup_us':stats([x['setup_us'] for x in rows]),
            'hashes':sorted({x['state_hash'] for x in rows}),
            'arena_bytes':sorted({x['arena_bytes'] for x in rows}),
            'cufft_work_bytes':sorted({x['cufft_work_bytes'] for x in rows})}
    for label,a,b in [('combined','pre-cuda','cuda-graph'),('graphs','cuda-direct','cuda-graph')]:
        summary['comparisons'][f'{case}-{label}']=improvement(summary['fixed'][case][a]['median_us']['samples'],summary['fixed'][case][b]['median_us']['samples'])
    for grid in ('multigrid','single'):
        key=f'{case}-{grid}'
        summary['cli'][key]={}
        for version in ('v1.1','v1.2'):
            rows=[json.loads((folder/f'cli-{case}-{grid}-{version}-{i}.json').read_text()) for i in range(1,6)]
            logs=[(folder/f'cli-{case}-{grid}-{version}-{i}.log').read_text() for i in range(1,6)]
            stages=[list(map(int,re.findall(r'CONVERGED at iter (\d+)',log))) for log in logs]
            assert all(x==stages[0] for x in stages)
            # Labels are FSQR, FSQZ and FSQL in the final summary.
            residuals=[[re.search(r'\b'+k+r':\s*([\deE.+-]+)',log).group(1) for k in ('FSQR','FSQZ','FSQL')] for log in logs]
            assert all(x==residuals[0] for x in residuals)
            obj={'wall_s':stats([x['wall_s'] for x in rows]),'stages':stages[0],
                 'iterations':sum(stages[0]),'residuals':residuals[0]}
            times=[re.search(r'total device time:\s*([\d.]+) ms',log) for log in logs]
            if all(times): obj['device_ms']=stats([float(x.group(1)) for x in times])
            summary['cli'][key][version]=obj
        summary['comparisons'][key]=improvement(summary['cli'][key]['v1.1']['wall_s']['samples'],summary['cli'][key]['v1.2']['wall_s']['samples'])
summary['checkpoint_replays']={}
for case in ('solovev','w7x'):
    log=(folder/f'checkpoint-{case}-replay.log').read_text()
    stages=list(map(int,re.findall(r'CONVERGED at iter (\d+)',log)))
    assert stages==[1]
    summary['checkpoint_replays'][case]={'stages':stages,'residuals':[re.search(r'\b'+k+r':\s*([\deE.+-]+)',log).group(1) for k in ('FSQR','FSQZ','FSQL')]}
for case in ('solovev','w7x'):
    assert summary['checkpoint_replays'][case]['residuals'] == summary['cli'][case+'-multigrid']['v1.2']['residuals']
(folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary['comparisons'],indent=2))
