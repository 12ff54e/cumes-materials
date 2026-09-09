import json,os,subprocess,time,pathlib,statistics,random,sys
root=pathlib.Path('/tmp/cumes-speed-rtx4090.YhIlVy')
label=sys.argv[1]
n=int(sys.argv[2]) if len(sys.argv)>2 else 16
env=dict(os.environ,CUDA_VISIBLE_DEVICES='2')
for k in list(env):
    if k.startswith('CUMES_'): env.pop(k)
out=root/'results'/label
out.mkdir(parents=True,exist_ok=True)
subprocess.run(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu,clocks.gr,clocks.mem,temperature.gpu,power.draw','--format=csv'],stdout=(out/'gpu-before.csv').open('w'),check=True)
os.sched_setaffinity(0,{8})
(out/'cpu-affinity.txt').write_text(str(sorted(os.sched_getaffinity(0)))+'\n')
rows=[]
for case in ['solovev','w7x']:
    for variant in ['baseline',label]:
        prefix=out/f'{case}-preheat-{variant}'
        cmd=[str(root/variant/'bin'/'cumes_benchmark_fixed_iteration'),'--config',case,'--warmup','100','--passes','1000','--out',str(prefix.with_suffix('.json'))]
        with prefix.with_suffix('.log').open('w') as log:
            subprocess.run(cmd,cwd=root/'source',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)

    for i in range(n):
        order=['baseline',label] if i%2==0 else [label,'baseline']
        pair={}
        for variant in order:
            prefix=out/f'{case}-{i:02d}-{variant}'
            cmd=[str(root/variant/'bin'/'cumes_benchmark_fixed_iteration'),'--config',case,'--warmup','100','--passes','500','--out',str(prefix.with_suffix('.json'))]
            with prefix.with_suffix('.log').open('w') as log:
                subprocess.run(cmd,cwd=root/'source',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            result=json.loads(prefix.with_suffix('.json').read_text())
            pair[variant]=result
            rows.append(dict(case=case,pair=i,variant=variant,result=result))
        a,b=pair['baseline'],pair[label]
        print(case,i,'us',a['median_us_per_iter'],b['median_us_per_iter'],'gain%',round(100*(1-b['median_us_per_iter']/a['median_us_per_iter']),2),'hashmatch',a['state_hash']==b['state_hash'],flush=True)
(root/'results'/f'{label}-runs.json').write_text(json.dumps(rows,indent=2))
summary={}
rng=random.Random(8961)
for case in ['solovev','w7x']:
    pairs=[]
    for i in range(n):
        a=next(r['result'] for r in rows if r['case']==case and r['pair']==i and r['variant']=='baseline')
        b=next(r['result'] for r in rows if r['case']==case and r['pair']==i and r['variant']==label)
        pairs.append((a,b))
    gains=[100*(1-b['median_us_per_iter']/a['median_us_per_iter']) for a,b in pairs]
    boots=sorted(statistics.median(rng.choices(gains,k=n)) for _ in range(20000))
    stats={}
    for name,idx in [('baseline',0),(label,1)]:
        vals=[p[idx]['median_us_per_iter'] for p in pairs]
        med=statistics.median(vals)
        stats[name]={'median_us':med,'p95_us_median':statistics.median(p[idx]['p95_us_per_iter'] for p in pairs),'run_median_min':min(vals),'run_median_max':max(vals),'run_median_mad_pct':100*statistics.median(abs(v-med) for v in vals)/med,'hashes':sorted(set(p[idx]['state_hash'] for p in pairs)),'arena_bytes':pairs[0][idx]['arena_bytes'],'cufft_work_bytes':pairs[0][idx]['cufft_work_bytes']}
    stats['paired_median_gain_pct']=statistics.median(gains)
    stats['paired_median_gain_bootstrap95_pct']=[boots[500],boots[19499]]
    stats['hashes_match']=all(a['state_hash']==b['state_hash'] for a,b in pairs)
    summary[case]=stats
(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
subprocess.run(['nvidia-smi','--query-gpu=index,uuid,name,memory.used,utilization.gpu,clocks.gr,clocks.mem,temperature.gpu,power.draw','--format=csv'],stdout=(out/'gpu-after.csv').open('w'),check=True)
