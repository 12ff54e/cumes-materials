"""Export a complete commit inventory and pinned local source references."""
from pathlib import Path
import csv
import subprocess

deck = Path(__file__).resolve().parents[1]
repo = deck.parents[2] / 'cuMES'
end = '6756fd6'  # v1.5.0; keep the audit reproducible when cuMES advances.
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
 '057d753': ('support','Expose native/compensated geometry precision without another numerical gain'),
 '1e4ffbc': ('accuracy','Double-double odd geometry reconstruction; opt-in accuracy/cost tradeoff'),
 '2f30c6c': ('evidence','Document double compensation error and additional arithmetic cost'),
 'f1a14f6': ('accuracy','Float-only device arithmetic including control/norm reductions; new qualification counts'),
 '4b666f8': ('evidence','FP64 instruction audit and float-only device policy; not a double-matched speedup'),
 '9c59702': ('accuracy','Compensate only four m=1 toroidal position sums to complete float single-grid convergence'),
 '0d8482a': ('execution','Retain single-word higher odd-mode products; float corrected pass 562.85 vs full diagnostic 660.94 us'),
 '1f6e654': ('evidence','Float single-grid 1354 passes, multigrid 149/277/311, replay and correction cost'),
 '66a557a': ('execution','Inverse R/Z compute only their required constraint sum; lambda computes neither'),
 '21b6043': ('execution','Cache four weighted forward bases per stage with original device-rounded products'),
 '9316169': ('evidence','16 transform pairs on each architecture; W7-X 5.19% Pascal and 6.50% Ada, exact trajectories'),
 'e14316d': ('rejected','Residual extrapolation adds evaluations; schedule experiments change caller inputs and are not defaults'),
 '03110b5': ('reverted','Explicit final-grid-only CLI option; subsequently removed in a93db11'),
 'c639d61': ('reverted','Final-grid schedule qualification removed with its option; not a shipped v1.5 speedup'),
 'a93db11': ('reverted','Remove final-grid option and its qualification; preserve caller-specified stages'),
 '6888b7c': ('experiment','GPU lambda inner solve and coupled R/Z probes; no retained production correction'),
 '8e75151': ('support','Validate probe arguments and exact rollback before interpreting reductions'),
 '23ec41b': ('rejected','Lambda and radial block corrections fail whole-solve work/cost gates'),
 'e4e6f68': ('support','GPU restarted GMRES with reorthogonalization; later promoted for Newton'),
 'd1a449c': ('support','Exact production descent-coordinate maps and boundary/gauge tests'),
 '6825031': ('experiment','Fully coupled frozen-epoch finite-difference Newton probe with GPU GMRES'),
 '77ad7be': ('rejected','Two-level FAS screen adds enough coarse/trial work to slow both complete solves'),
 'fad9e8b': ('support','Translation-unit-local probe kernel; build correctness, no independent speedup'),
 'fd10788': ('evidence','Full Newton/FAS outcomes; W7-X Newton lacks reliable gain across architectures'),
 '8e2ae73': ('measurement','Predeclare 16 axisymmetric inputs and provenance before timing'),
 'e809507': ('measurement','Separately predeclare three finite-pressure Newton cases'),
 '8e81087': ('measurement','Validate native fields, input provenance, physical geometry and independent VMEC++ references'),
 'c1c7ca6': ('measurement','Paired axisymmetric runner; unchanged schedules, native report checks and full cost accounting'),
 'cd153ee': ('measurement','Audit checkpoint signed-zero exceptions and physical validity'),
 '26d266c': ('measurement','Replay checkpoints at original final-stage tolerance'),
 'ade135f': ('evidence','19 Newton cases; preserve initial and fresh follow-up pairs, gains and Ada regressions'),
 'ca33025': ('support','Promote exact tested Newton/GMRES implementation into reusable CUDA library'),
 'bcdd3da': ('trajectory','Off-by-default --newton for fixed-boundary axisymmetric double; 76 promotion equivalence solves'),
 '4df6dae': ('measurement','Pin five free-boundary fixture variants, field hashes and original W7-X sign rejection'),
 '0bc92e2': ('execution','Vacuum dependency 4acd589: parallel axisymmetric terms, original ordered weighted sum'),
 'f8bbfa2': ('execution','Vacuum dependency 2eb53c9: spread singular RHS modes over eight-thread blocks'),
 'cc2d91d': ('execution','Pinned copies before existing fences; guard uninitialized diagnostic; dependency 4d19939 keeps large RHS fallback'),
 'be654be': ('evidence','Seven free-boundary pairs per GPU/case; separate process time, exact full traces and retained failures'),
 '336c4ca': ('support','Preserve saved benchmark protocols before rejecting incompatible reruns'),
}
lines=git('log','--reverse','--topo-order','--format=%H\t%ad\t%s','--date=short',f'dc0d0c4..{end}').splitlines()
with (deck/'data/commit-audit.tsv').open('w') as f:
    writer=csv.writer(f,delimiter='\t',lineterminator='\n',quoting=csv.QUOTE_ALL)
    writer.writerow(['commit','date','subject','classification','assessment','files'])
    for line in lines:
        sha,date,title=line.split('\t',2)
        category,assessment=groups.get(sha[:7],('context','Feature, correctness, documentation, release, or maintenance; no separately attributed solver speedup'))
        paths=git('show','--format=','--name-only','--diff-merges=first-parent',sha).splitlines()
        writer.writerow([sha,date,title,category,assessment,', '.join(paths)])

with (deck/'data/optimization-commits.md').open('w') as f:
    f.write('# Optimization commit inventory\n\n')
    f.write(f'Audited every commit reachable in `dc0d0c4..{end}` (including merged history), not just commits named perf. `dc0d0c4` closes the design overhaul; safety/reader closeout ends at `56aa1a4`. Earlier Phase 6 results are explicitly background. Release markers: `dbb0f8e` v1.0, `f7036ab` v1.1, `17867d5` v1.2, `750d6a4` v1.3, `ef67884` v1.4.0, `f0c17f7` v1.4.1, `{end}` v1.5.0. The independent, unmerged `webgpu` branch is outside this CUDA deck.\n\n')
    f.write(f'Total commits inspected: {len(lines)}. The complete file-level inventory is [commit-audit.tsv](commit-audit.tsv). The table below includes retained changes, rejected experiments, relevant supporting work, and measured tooling. Feature-only sensitivity construction commits remain in the complete inventory.\n\n')
    f.write('| Commit | Category | Finding |\n| --- | --- | --- |\n')
    for line in lines:
        sha,_,_=line.split('\t',2)
        if sha[:7] in groups:
            category,assessment=groups[sha[:7]]
            f.write(f'| [{sha[:7]}](https://github.com/12ff54e/cuMES/commit/{sha}) | {category} | {assessment} |\n')
print(f'Exported {len(lines)} commits; {len(groups)} highlighted records')
