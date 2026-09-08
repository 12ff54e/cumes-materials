"""Export a complete commit inventory and pinned local source references."""
from pathlib import Path
import csv
import subprocess

deck = Path(__file__).resolve().parents[1]
repo = deck.parents[2] / 'cuMES'
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True)

groups = {
 '5310769': ('tooling','Batched IFFT and process-parallel figure rendering; 42 to 17 s recorded'),
 '2dea659': ('execution','Compile verification event messages out of non-dump builds; no isolated timing'),
 '5379fca': ('execution','Production CUDA graphs; parallel Jacobian statistics; full-theta inverse mapping'),
 '933b80a': ('execution','Vacuum dependency be6d6cd: contiguous Makegrid response storage; no isolated timing'),
 '5d5e380': ('execution','Capture scientific fields only on finest stage; 3 to 1 captures for three-grid inputs'),
 'e507b36': ('execution','Vacuum dependency 110748f: parallel Makegrid; no isolated timing'),
 'fa119ea': ('execution','Host snapshot spans for Boozer; no copy of six spectral/seven field arrays; not GPU zero-copy'),
 '7541ff6': ('trajectory','Single-grid one-shot step recovery'),
 '774363f': ('trajectory','Extend recovery to each fixed-boundary stage'),
 'f270790': ('trajectory','Fixed 3-D shaped cold start'),
 '3d08aef': ('trajectory','Coarse axisymmetric envelope'),
 '27c5e39': ('trajectory','Axisymmetric initial-step policy'),
 '9f4d7c1': ('trajectory','Geometric axisymmetric lambda seed'),
 '355c10c': ('trajectory','Free-boundary cold predictors'),
 '57f86b7': ('trajectory','Coarse free-boundary step scaling'),
 'f5eeba6': ('trajectory','Earlier vacuum activation'),
 'd2d8b81': ('evidence','Free-boundary paired timings'),
 'cad3daa': ('measurement','CUDA stream elapsed-time reporting'),
 '6d9e593': ('trajectory','Single-grid 3-D envelope 0.129'),
 '1a10037': ('trajectory','Catmull-Rom multigrid transfer'),
 'b13cd87': ('both','Global B-spline transfer matrix applied on GPU'),
 '12435fa': ('execution','Prepare transfer matrices asynchronously during coarse solve'),
 'f79214c': ('support','Pin direct B-spline dependency e7f5207'),
 '8a07964': ('support','Portable dependency URL'),
 '05abfde': ('support','Relative dependency protocol'),
 '4658ea0': ('support','Centralize tuning constants; no separate speedup'),
 'c1abf20': ('sensitivity','Right-preconditioned retained tangent GMRES; different linear problem'),
 '0064e98': ('sensitivity','Matrix-free equilibrium tangent solve; not nonlinear convergence optimization'),
 '2d07d47': ('sensitivity','Retained residual JVP session; no isolated timing'),
 'd0f408b': ('execution','Coordinate concurrent graph capture and device-wide stage fence'),
 '6106e0b': ('measurement','Solve phase timings'),
 '5720583': ('measurement','Stage lifecycle timings'),
 '480c91d': ('rejected','Resource reuse ceiling too small'),
 '17d731c': ('rejected','Transform launch tiles below 5% acceptance gate'),
 'b0d6758': ('rejected','Inverse pack remapping / derived-table load experiments'),
 'd36025f': ('rejected','Concurrent tile tuning below acceptance gate'),
 'a7f605d': ('trajectory','Very coarse fixed 3-D seed -0.10 for initial_ns <= 12'),
 'f61c959': ('evidence','Very coarse predictor qualification'),
 'a880051': ('accuracy','Float reference-plus-displacement radius storage'),
 '3cebb49': ('accuracy','Selective compensated odd R/Z reconstruction'),
 'bd01518': ('accuracy','Default float 3-D radius displacement representation'),
 '194415d': ('execution','Cache immutable radius reference once per stage'),
}
lines=git('log','--reverse','--topo-order','--format=%H\t%ad\t%s','--date=short','dc0d0c4..194415d').splitlines()
with (deck/'data/commit-audit.tsv').open('w') as f:
    writer=csv.writer(f,delimiter='\t',lineterminator='\n',quoting=csv.QUOTE_ALL)
    writer.writerow(['commit','date','subject','classification','assessment','files'])
    for line in lines:
        sha,date,title=line.split('\t',2)
        category,assessment=groups.get(sha[:7],('context','Feature, correctness, documentation, release, or maintenance; no separately attributed solver speedup'))
        paths=git('diff-tree','--no-commit-id','--name-only','-r',sha).splitlines()
        writer.writerow([sha,date,title,category,assessment,', '.join(paths)])

with (deck/'data/optimization-commits.md').open('w') as f:
    f.write('# Optimization commit inventory\n\n')
    f.write('Audited every commit reachable in `dc0d0c4..194415d` (including merged history), not just commits named perf. `dc0d0c4` closes the design overhaul; safety/reader closeout ends at `56aa1a4`. Earlier Phase 6 results are explicitly background. Release markers: `dbb0f8e` v1.0, `f7036ab` v1.1, `17867d5` v1.2, `750d6a4` v1.3. The independent, unmerged `webgpu` branch is outside this CUDA deck.\n\n')
    f.write(f'Total commits inspected: {len(lines)}. The complete file-level inventory is [commit-audit.tsv](commit-audit.tsv). The table below includes retained changes, rejected experiments, relevant supporting work, and measured tooling. Feature-only sensitivity construction commits remain in the complete inventory.\n\n')
    f.write('| Commit | Category | Finding |\n| --- | --- | --- |\n')
    for line in lines:
        sha,_,_=line.split('\t',2)
        if sha[:7] in groups:
            category,assessment=groups[sha[:7]]
            f.write(f'| [{sha[:7]}](https://github.com/12ff54e/cuMES/commit/{sha}) | {category} | {assessment} |\n')
print(f'Exported {len(lines)} commits; {len(groups)} highlighted records')
