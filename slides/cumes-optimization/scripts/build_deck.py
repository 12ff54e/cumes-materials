"""Render the static, offline deck. Edit narrative here, then rerun this file."""
from pathlib import Path
from html import escape as esc
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from inline_math import format_html, span as inline, number_tex

deck=Path(__file__).resolve().parents[1]
local=json.loads((deck/'data/local/summary.json').read_text())
slides=[]
def table(headers,rows):
    return '<div class="table-wrap"><table class="measure"><thead><tr>'+''.join(f'<th>{v}</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{v}</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def panel(title,text,kind=''):
    return f'<article class="panel {kind}"><div class="panel-title">{title}</div>{text}</article>'
def p(text): return f'<p>{text}</p>'
def callout(text): return f'<div class="callout"><p>{text}</p></div>'
def eq(tex): return f'<div class="equation"><span class="math-display" data-tex="{esc(tex,quote=True)}"></span></div>'
def grid(*items):return '<div class="grid-2">'+''.join(items)+'</div>'
def stack(*items):return '<div class="stack">'+''.join(items)+'</div>'
def bars(rows,unit='',maximum=None):
    maximum=maximum or max(v for _,v,_ in rows)
    return '<div class="bars" role="img" aria-label="'+esc('; '.join(f'{name}: {v:g} {unit}' for name,v,_ in rows),quote=True)+'">'+''.join(f'<div class="bar-row"><span class="bar-label">{name}</span><div class="bar-track"><div class="bar-fill {color}" style="width:{100*v/maximum:.3f}%"></div></div><strong>{v:,.2f} <small>{unit}</small></strong></div>' for name,v,color in rows)+'</div>'
def add(title,body,source,notes='',chapter='Execution',eyebrow=None,cls=''):
    number=len(slides)+1
    slides.append(f'''<section class="slide {cls}" data-title="{esc(title,quote=True)}" data-chapter="{chapter}" data-summary="{esc(eyebrow or title,quote=True)}">
<header class="slide-header"><div><p class="eyebrow">{eyebrow or chapter}</p><h2>{title}</h2></div><span class="slide-index">{number:02d}</span></header>
<div class="content narrative">{body}</div>
<footer class="slide-footer"><span>{source}</span><span class="footer-rule"></span><span>{chapter} · cuMES</span></footer>
<aside class="speaker-notes">{notes or title} Source paths refer to the sibling cuMES repository; pinned references and qualifications are in evidence.md.</aside></section>''')
def chapter(n,title,description):
    add(title,f'<div class="chapter-card"><div class="section-number">{n}</div><p class="dek">{description}</p></div>', 'Development history · 2026-08 to 2026-09',chapter=title,cls='chapter-slide')
def fmt(x):return f'{x:.3f}'

add('Making cuMES faster',
    '<div class="hero"><div><p class="dek">Spend less time on each GPU pass.<br>Then need fewer passes to reach equilibrium.</p><div class="tag-row"><span class="tag">CUDA execution</span><span class="tag free">convergence trajectory</span><span class="tag">commit-backed measurements</span></div></div><div class="hero-metrics">'+
    panel('RTX 4090 · iteration latency','<strong class="hero-number">−19.1%</strong><p>W7-X · 660.81 → 534.53 μs/pass</p>')+
    panel('v1.1 → v1.2 · convergence','<strong class="hero-number amber">−25.4%</strong><p>W7-X · 5,505 → 4,106 passes</p>','free')+'</div></div>',
    '5379fca · 17867d5 · performance.md §§2.1–2.7',
    'These are separate measurements: the first is fixed-iteration wall latency on RTX 4090, the second is deterministic multigrid work. Do not multiply them into an end-to-end claim. New TITAN Xp reproductions appear later.',chapter='Orientation',eyebrow='Optimization during cuMES development')
add('Two levers, two kinds of evidence',stack(
    eq(r'T_{\mathrm{run}}=T_{\mathrm{setup}}+\sum_g\left(N_g\,\bar t_g+T_{\mathrm{transfer},g}\right)+T_{\mathrm{output}}'),
    grid(panel('01 · Execution',p('Reduce submission gaps, redundant transfers, synchronization, and kernel latency. Hold the numerical problem and controller decisions fixed.')),
         panel('02 · Trajectory',p('Change cold seeds, time-step policy, vacuum handover, and radial transfer. Validate the new equilibrium and count every stage.'),'free'))),
    'Timing definitions · performance.md §1; verification.md',
    'The average stage cost includes host control gaps. Class A means exact state and decisions; Class B permits bounded rounding with unchanged decisions; Class C changes the trajectory. Kernel implementation optimizations also belong in part one when they retain the numerical method.',chapter='Orientation')
add('The audit starts at overhaul closeout',table(['Milestone','Commit / date','What this deck covers'],[
    ['Design closure','dc0d0c4 · Aug 17','Starting boundary of the 197-commit inventory'],
    ['Final reader closeout','56aa1a4 · Aug 18','Safety follow-ups complete; frozen trajectories retained'],
    ['v1.0','dbb0f8e · Aug 26','CUDA graphs, Jacobian reduction, inverse mapping'],
    ['v1.1','f7036ab · Aug 30','Finest-grid capture; Makegrid; zero-copy host bridge'],
    ['v1.2','17867d5 · Aug 31','Recovery, seeds, handover, cubic/B-spline transfer'],
    ['Later CUDA work','750d6a4 → 194415d','Concurrency, coarse QA/QH seeds, float accuracy/cache']]),
    'data/commit-audit.tsv · all 197 commits, including merged ancestry',
    'The inventory inspects all reachable commit subjects and changed paths from dc0d0c4 through 194415d, with implementation and evidence review for optimization candidates, including dependency changes. The separate unmerged WebGPU branch is outside this CUDA presentation. Phase 6 measurements are background, not post-closeout gains.',chapter='Orientation')
add('Read every number with its measurement scope',table(['Evidence','Protocol','Interpretation'],[
    ['Archived RTX 4090','CUDA 12.9; precise double; 50 warmup + 300 timed; six alternating graph pairs','Per-pass wall medians; frozen final-state hashes'],
    ['Archived convergence','ADR-0007…0012; case-specific paired runs','Effective passes and final residuals; clocks sometimes noisy'],
    ['New TITAN Xp','CUDA 12.1; sm_61; same source-pinned builds; six fixed triples','Before / optimized-direct / optimized-graph'],
    ['New release comparison','Five timed alternating pairs after one warmup pair','CLI wall time includes startup and native output'],
    ['Structural accounting','Counts and byte sizes derived from implementation','Explicitly not a measured wall-time speedup']]),
    'data/local/environment.json · raw logs and JSON included',
    'New runs use Release precise-double, optional NetCDF/HDF5/vacuum/magnetic-coordinate disabled, pinned CPU, unlocked clocks, existing graphical GPU process left running. No slow samples are dropped. No cross-GPU ratio or full performance certification is claimed.',chapter='Orientation')

chapter('01','Faster execution','Keep the equilibrium method. Improve the way work reaches the GPU and data reaches the host.')
add('The one-fence loop was the foundation',grid(
    panel('Already completed during overhaul',table(['Resource','Before','After'],[
        ['Ordinary host barriers / pass','5','1'],['cuFFT workspace · W7-X','≈10.4 MB','≈5.5 MB'],['Seed slab copy / zeroing','6 + 6 calls','1 + 1 calls']])),
    panel('The control fence carries the decision',p('GPU reductions write one control record. The host checks geometry, residuals, convergence, and restart policy after the same fence.')+p('Timing events and telemetry use that existing boundary; the iteration does not stop just to print.'))),
    'Background only · 36403ad · overhaul-history.md Phase 6A/6B',
    'These savings predate the post-overhaul audit boundary. Five ordinary barriers included inverse timing, Jacobian copy, forward timing, invariant and preconditioned residual synchronization. The later force-norm reduction also removed its refresh fence and three synchronous array transfers. Workspace figures are archived approximate decimal MB.')
add('A graph removes launch gaps, not the control decision',
    '<div class="lane-diagram"><div class="lane-label">Direct stream</div><div class="lane"><b>inverse</b><i>host launch</i><b>geometry</b><i>host launch</i><b>forces</b><i>host launch</i><b>reduce</b></div><div class="lane-label amber">Graph replay</div><div class="lane graph-lane"><b>inverse → geometry → forces → reduce</b></div><div class="lane-label">Both paths</div><div class="lane"><b>pinned control readback</b><span>→</span><b>one host fence</b><span>→</span><b>controller / descent</b></div></div>'+callout('Fixed-boundary schedules can be replayed. Free-boundary vacuum coupling and verification dumps retain direct execution.'),
    '5379fca · src/kernels/solver_impl.cuh',
    'Schematic ordering, not a duration-scaled trace. The graph covers EquilibriumOperator::enqueue, not the host controller. Refresh and non-refresh schedules use separate caches. Non-refresh graphs are invalidated after updated normalization factors are published.')
add('The retained CUDA bundle: RTX 4090',grid(
    panel('Solovev · ns = 55',bars([('Before',115.59,''),('After',82.33,'green')],'μs')+p('<strong>28.8% less wall time per pass</strong> · 1.404× throughput')),
    panel('W7-X · ns = 99',bars([('Before',660.81,''),('After',534.53,'amber')],'μs')+p('<strong>19.1% less wall time per pass</strong> · 1.236× throughput'),'free')),
    '5379fca · performance.md §2.1 · RTX 4090 / CUDA 12.9',
    'Bundle includes parallel Jacobian statistics, full-theta inverse mapping and production graphs. The pre-bundle baseline is the recorded same-session baseline. Do not attribute the whole reduction to graphs or to one kernel.')
add('Parallelize the Jacobian validity reduction',grid(
    panel('W7-X kernel measurement',bars([('Old reduction',104.7,''),('Two-stage',7.2,'green')],'μs')+p('<strong>14.54× kernel speedup</strong> · 93.1% less kernel time')),
    panel('Keep the validity semantics',p('One serially loaded block becomes up to 128 blocks of 256 threads, followed by one final reduction.')+table(['Preserved result','Implementation'],[['Minimum oriented √g','Tie-break by lowest linear index'],['Maximum |√g|','Include sign-flipped samples'],['Non-finite count','Accumulate across all blocks']]))),
    '5379fca · geometry_impl.cuh · archived RTX kernel profile',
    'The partial arrays contain three <code>T</code> values and two ints per block: at most 4096 bytes in double, excluding arena alignment. This is kernel latency, not whole-pass or solve speedup. The reduction remains a geometry-validity gate.')
add('Expose all theta points to the GPU',grid(
    panel('Before',eq(r'(\theta/2,\;\zeta_{\mathrm{tile}})\quad\times\;2\text{ serial }\theta\text{ passes}')+p('One lane synthesizes a point in each poloidal half.')),
    panel('After',eq(r'(\theta,\;\zeta_{\mathrm{tile}})\quad\times\;1\text{ point per lane}')+p('The modal accumulation order for each output is retained. The block policy caps the total thread count.'),'free'))+
    callout('W7-X has 30 theta points: the theta dimension grows from 15 to 30 lanes. Its isolated latency gain was not separately recorded.'),
    '5379fca · fourier_impl.cuh · inverse_accumulate_kernel',
    'This is launch decomposition of the existing inverse synthesis, not a new Fourier method. It is measured as part of the retained CUDA bundle. Register caps and split forward reductions were tried and removed.')
add('Production graph caching earns its complexity',table(['RTX 4090 · precise double','Direct stream','Graph replay','Wall reduction'],[
    ['Solovev · ns=55','117.14 μs','82.33 μs','29.7%'],['W7-X · ns=99','562.10 μs','534.53 μs','4.9%']])+grid(
    panel('Numerical gate',p('Final-state hashes match graph on/off:<br><code>3c09fd3260b003a8</code> · Solovev<br><code>ce46a7cbe693601a</code> · W7-X')),
    panel('Measurement',p('1,000-pass preheat; six alternating pairs; each run discards 50 warmup passes and times 300. No graph-node argument mutation.'))),
    '5379fca · ADR-0003 · GPU 2 on gervais, 2026-08-26',
    'The original Pascal graph experiment was deferred despite a real-pass microbenchmark gain: enqueue 63.9 versus graph launch 9.8 μs, production-pattern wall 124.0 versus 111.3 μs. These older harness numbers are distinct from full production iteration latency.')

rows=[]
for case,label in [('solovev','Solovev · ns=55'),('w7x','W7-X · ns=99')]:
    f=local['fixed'][case]
    rows.append([label,*[f"{f[v]['median_us']['median']:.2f} μs" for v in ('pre-cuda','cuda-direct','cuda-graph')],f"{local['comparisons'][case+'-combined']['reduction_percent']:.2f}%"])
add('Reproduced now: the same CUDA commit on Pascal',table(['TITAN Xp','7c6508a · before','5379fca · direct','5379fca · graph','Bundle reduction'],rows)+callout('Every before/direct/graph repetition has the same final-state hash within each workload.'),
    'NEW · data/local/fixed-*.json · 6 alternating triples / shape',
    'Built exact parent and child commits, sm_61, CUDA 12.1, Release, precise double. Default seed and controls are identical. The W7-X hash differs from the archived RTX session, so equality is asserted within the local controlled comparison only. Clocks are unlocked. The smaller Pascal graph gain does not contradict the separate RTX experiment.')
rows=[]
for case in ('solovev','w7x'):
    for variant,label in [('pre-cuda','before'),('cuda-direct','direct'),('cuda-graph','graph')]:
        r=local['fixed'][case][variant];s=r['median_us']
        rows.append([case+' · '+label,f"{s['median']:.2f} ± {s['mad']:.2f}",f"{r['p95_us']['median']:.2f}",f"{s['min']:.2f}–{s['max']:.2f}"])
add('Keep the timing spread visible',table(['New fixed-iteration runs','Median ± MAD · μs','Median run p95 · μs','Range of run medians · μs'],rows)+p('MAD and range describe six run medians. The p95 column is the median of six within-run p95 values; it is a different statistic.'),
    'NEW · data/local/summary.json · no samples excluded',
    'Paired bootstrap confidence intervals for median latency reduction are retained in summary.json. Six samples with unlocked clocks and a graphical GPU process are descriptive reproduction evidence, not the full two-architecture acceptance gate.')
add('Stop copying results that cannot be published',grid(
    panel('Finest-grid-only field capture',table(['Three-grid solve','Before','After'],[['Derived-field evaluations','3','1'],['Coarse-stage capture calls','2','0']])+p('The two intermediate snapshots would be overwritten. Their field evaluation and device-to-host capture are skipped.')),
    panel('Boozer host view',p('<strong>6 spectral families + 7 half-grid fields</strong> are exposed as spans into the existing host snapshot.')+p('This avoids another owning host copy and the native-file round trip. It does not remove the solver’s device-to-host publication.'))),
    '5d5e380 · fa119ea · stage_solver.hpp / magnetic_coordinate_bridge.hpp',
    'Call counts are derived from implementation for three-grid inputs. No isolated wall-time measurement is available in these commits. Do not label the host span bridge as a zero-copy GPU transfer.')
add('Makegrid: improve one-time host work',grid(
    panel('Flat response storage · v1.0',p('Three contiguous component arrays; coil-major blocks, R-fast indexing. Removes nested vector traversal and simplifies direct in-memory response handoff.')+p('<code>933b80a → vacuum-field be6d6cd</code>')),
    panel('Parallel generation · v1.1',p('Independent grid points run on CPU workers. Dynamic chunks contain <strong>8 items</strong>; useful worker count is capped at roughly <strong>1 per 32 items</strong>.')+p('<code>VFIELD_MAKEGRID_THREADS=1</code> selects serial execution.')))+
    callout('No isolated timing is recorded for either commit. These changes affect construction, not the per-iteration vacuum update.'),
    '933b80a / e507b36 · vacuum-field be6d6cd / 110748f',
    'The worker cap is ceil(work_items/32), also capped by requested or hardware thread count and work_items. Threading preserves the within-point filament evaluation order. Flat storage and CPU parallelism should not be confused with a new vacuum numerical algorithm.')
add('Supporting tools also became faster',grid(
    panel('Figure generation',bars([('Before',42,''),('After',17,'green')],'s')+p('Recorded wall time: <strong>59.5% lower</strong> · 2.47× speedup.')),
    panel('Changes in <code>5310769</code>',p('Batched 2-D IFFT replaces a direct mode sum, checked to 10⁻¹⁴. Figure rendering uses separate processes and copy-on-write input data.')+p('The commit also reports ≈100× synthesis acceleration, without a reproducible timing protocol.'))),
    '<code>5310769</code> · commit message / scripts/plot_w7x.py · Aug 21',
    'This is plotting throughput, not solver convergence or CUDA iteration latency. The archived 42-to-17 s observation changes rendering as well as parallelism; hardware, sample count and dispersion are not recorded. Event-line compilation in 2dea659 is another unquantified tooling/observability optimization.')
add('B-spline setup belongs off the critical path',table(['W7-X transfer','Direct host batch','Host matrix construction','Uploaded map'],[
    ['33 → 66','1.90 ms','36.7 μs','17,424 bytes'],['66 → 99','2.94 ms','136.5 μs','52,272 bytes']])+grid(
    panel('One reusable map, 936 profiles',p('Apply the map to all six spectral families on the GPU. The spectral state stays device-resident.')),
    panel('Overlap with stage 1',p('Both maps take <strong>173.3 μs</strong> in total; one average W7-X device iteration was ≈462 μs. The coarse stage takes <strong>1,315 iterations</strong>.'),'free')),
    'b13cd87 / 12435fa · ADR-0012 · 10,000 warmed host calls',
    'Matrix construction figures are gervais host medians. Direct host batch costs total 4.84 ms before PCIe staging; prior complete Catmull boundaries cost 0.084+0.232=0.316 ms. The asynchronous path builds all scheduled maps in one background task. B-spline numerical benefits are separated in part two. Bytes are derived from ' + inline(r'n_{s,\mathrm{new}}n_{s,\mathrm{old}}\cdot8') + ', not measured PCIe bandwidth.')
add('Later: coordinate capture, overlap independent solves',table(['Eight finite-difference columns','Serial','Two workers','Throughput'],[
    ['QA','2.823 s','1.247 s','2.26×'],['QH','2.250 s','1.025 s','2.20×']])+callout('One process-wide host mutex protects graph capture against a concurrent device-wide stage fence. Ordinary graph execution and the iteration loop remain unlocked.'),
    'd0f408b · performance.md §3.4 · later v1.3 work',
    'Focused single-Jacobian timings; identical serial/concurrent Jacobian columns and 96/96 cuMES verify tests were recorded. These are embedding throughput measurements, not repeated end-to-end optimizer acceptance statistics. QA/QH optimizer policy remains in meow; cuMES owns safe independent execution.')
add('Measured execution ideas that did not ship',table(['Experiment','Measurement','Decision'],[
    ['Split R/Z and λ forces · overhaul context','Registers 108 → 82 / 54; 1.20–1.45× slower','Reject: duplicated input traffic'],
    ['Forward tile 4 · later CUDA','Graph-on W7-X 1.573 → 1.518 ms; 3.5%','Below 5% gate'],
    ['Inverse pack remapping','Five alternating runs; flat to slower','Restore original mapping'],
    ['Derive poloidal tables from sin/cos','≈0.5% slower; hash unchanged','Remove variant'],
    ['Tile 4 · four-worker QA / QH','0.814 → 0.801 s / 0.678 → 0.682 s','Only 1.6% / −0.7%']]),
    'ADR-0002 · 17d731c · b0d6758 · d36025f · performance.md §3.6',
    'Force splitting predates overhaul closeout and is included as background. Launch tiles, mapping and table experiments are post-v1.2. All tile/mapping candidates preserved the relevant state hashes. Register-capping and split forward-reduction prototypes in the August RTX session were likewise removed.')
add('Resource reuse had a small upper bound',table(['Eight-solve aggregate','QA','QH'],[
    ['Multigrid wall','3.1525 s','2.6627 s'],['Stage setup','0.13690 s · 4.3%','0.14062 s · 5.3%'],['Iteration','2.89850 s · 91.9%','2.40979 s · 90.5%'],['Derived-field capture','0.06035 s','0.06185 s'],['Stage teardown','0.04174 s','0.03798 s'],['Other orchestration','0.01505 s','0.01246 s']])+callout('Even deleting all setup and teardown gives only a 5.6% / 6.7% ceiling, while retaining ≈69 MB per W7-X worker. Caching was rejected without implementation.'),
    '6106e0b / <code>5720583</code> / 480c91d · performance.md §3.5',
    'Three-run full-package Release profile, averaged over groups of eight finite-difference solves. Rounded components need not sum exactly. Stream-only facade setup was only 0.12% QA and 0.19% QH. This is an optimistic removable-time bound, not a measured speedup.')

chapter('02','Fewer iterations','Change the starting state and continuation path. Keep the force tolerances and validity gates explicit.')
add('W7-X: account for every saved stage',table(['Policy after each change','ns=33','ns=66','ns=99','Total','Saved vs prior'],[
    ['v1.1 reference','1,877','1,617','2,011','5,505','—'],
    ['Step recovery','1,741','1,568','1,635','4,944','561'],
    ['Shaped cold start','1,315','1,559','1,633','4,507','437'],
    ['Catmull-Rom transfer','1,315','1,443','1,402','4,160','347'],
    ['B-spline · v1.2','1,315','1,419','1,372','4,106','54']])+callout('1,399 fewer full passes: 25.41% less work. This is a cumulative sequence; the individual gains are conditional on earlier changes.'),
    '774363f · f270790 · 1a10037 · b13cd87',
    'Precise-double W7-X, grids 33/66/99, every stage at 1e-12. Final FSQR values at these milestones: 9.778e-13, 9.989e-13, 9.967e-13, 9.986e-13, 9.997e-13. Final residual and replay gates replace trajectory identity for these Class C changes.',chapter='Trajectory')
add('Recover a step reduced by the early transient',grid(
    panel('One conservative attempt',eq(r'\Delta t\leftarrow\min(\Delta t_0,\;1.1\Delta t)')+p('Wait for <strong>250 accepted passes since the latest restart</strong>. Attempt recovery once per fixed-boundary stage.')),
    panel('W7-X · single ns=99',table(['Controller','Passes','FSQR'],[['Reference','2,953','9.924e-13'],['Recovery','2,711','9.988e-13']])+p('<strong>242 fewer passes · 8.20%</strong>'),'free')),
    '7541ff6 · ADR-0007',
    'Five early invalid-Jacobian transients reduced the reference step. Recovery uses the existing rollback/validity gates. No new per-pass CUDA work, allocations or synchronization are introduced. Periodic or repeated recovery caused recurring invalid Jacobians and failed.',chapter='Trajectory')
add('Recovery scales across multigrid stages',table(['W7-X grid','Reference','Recovery','Fewer passes'],[
    ['33','1,877','1,741','136'],['66','1,617','1,568','49'],['99','2,011','1,635','376'],['Total','5,505','4,944','561 · 10.19%']])+grid(
    panel('Archived RTX wall medians',p('Single grid: <strong>2.0583 → 1.9217 s</strong> (6.63%).<br>Multigrid: <strong>3.3109 → 3.0021 s</strong> (9.33%).')),
    panel('Validation',p('Final multigrid residuals:<br>R 9.989e-13 · Z 1.590e-13 · λ 5.116e-14.<br>Final-grid checkpoint replay: <strong>1 pass</strong>.'))),
    '774363f · performance.md §2.2 · six alternating RTX pairs',
    'Multigrid wall MAD: 0.1090/0.2123 s; ranges 3.1856–3.6662 / 2.7096–3.5031 s. Single-grid MAD: 6.1/7.6 ms; ranges 2.0510–2.5015 / 1.9102–2.5244 s. Unlocked P-state transitions produce outliers. Pass reduction is the strongest deterministic evidence.',chapter='Trajectory')
add('Shape the interior; preserve axis order and LCFS',stack(
    eq(r'w_m(s)=s^{m/2}\left[1+c(1-s)\right]'),
    table(['Fixed 3-D cold start','Envelope c','Before → after','Reduction'],[
        ['W7-X multigrid','0.12','4,944 → 4,507','8.84%'],
        ['W7-X single · first policy','0.12','2,711 → 2,627','3.10%'],
        ['W7-X single · tuned policy','0.129','2,711 → 2,465','9.07%']]),
    callout('At s=1 the correction is exactly one. Near the axis it retains the sᵐᐟ² order. The host seed changes once; the per-pass GPU workload is unchanged.')),
    'f270790 / 6d9e593 · ADR-0008; performance.md §2.3',
    'The later schedule-specific 0.129 result must not be paired with the older 0.12 wall measurements. The archived 1.9238→1.8823 s single-grid wall pair and 3.4419→3.2983 s multigrid pair describe the initial shaping experiment. The later 0.129 device time was 1.334 s versus about 1.43 s at 0.12.',chapter='Trajectory')
add('Axisymmetric tuning has three separate contributions',table(['Solovev policy','Stage trajectory','Total','Reduction vs 906'],[
    ['Reference','251 → 199 → 456','906','—'],
    ['Coarse envelope −0.07','241 → 199 → 455','895','1.21%'],
    ['Plus initial-step scaling','238 → 193 → 387','818','9.71%'],
    ['Plus geometric λ predictor','235 → 193 → 387','815','10.04%']])+p('For configured Δt = 0.9: single-grid start <strong>1.05</strong>; first continuation grid <strong>1.02</strong>; prolonged grid <strong>1.08</strong>.'),
    '3d08aef / 27c5e39 / 9f4d7c1 · ADR-0009',
    'Envelope only for coarse fixed-axisymmetric cold starts ns<=11. Step multipliers 7/6, 17/15, 6/5 are precise-double policies; mixed-float retains its configured step. Final FSQR at the three changes: 9.999e-17, 9.781e-17, 9.792e-17.',chapter='Trajectory')
add('A geometric lambda seed helps fine cold starts',grid(
    panel('Straight-field-line predictor',eq(r'q=\sqrt{g}/R^2,\qquad\lambda_\theta=1-q/\langle q\rangle_\theta')+p('Project the derivative on the host. Fixed-boundary starts use <strong>65%</strong> of the predictor. Invalid geometry falls back to zero λ.')),
    panel('Solovev · cold ns=55',bars([('Reference',533,''),('Step only',416,''),('Step + λ',354,'amber')],'passes')+p('<strong>33.58% fewer passes</strong> before any multigrid transfer.'),'free')),
    '9f4d7c1 · ADR-0009',
    'The lambda scale sweep has a broad optimum at 0.64–0.655. Final FSQR is 9.835e-17 at 354 passes. Single-grid runs do not use radial prolongation. This prevents attributing their improvement to B-splines.',chapter='Trajectory')
add('Free-boundary predictors need separate qualification',table(['Precise-double case','Reference','Seeded','Seed / predictor','Seeded FSQR'],[
    ['CTH-like · ns=15','489','384','c=0.12','9.932e-11'],
    ['CTH-like · 15 → 25','592','563','c=0.12','9.942e-11'],
    ['W7-X · ns=51','1,831','1,797','c=0.03','9.705e-13'],
    ['Solovev · 16 → 32','1,047','1,025','λ scale=1.0','9.822e-15']])+callout('Using c=0.12 on fine W7-X regressed to 1,953 passes. The smaller fine-grid correction is a measured stability choice.'),
    '355c10c · ADR-0010',
    '3-D free-boundary c=0.12 applies for initial_ns<=25 and c=0.03 above that. Axisymmetric free-boundary keeps the original R/Z envelope. These archived input families and tolerances differ from the fixed-boundary release comparison and were not rerun for this deck.',chapter='Trajectory')
add('Activate the physical vacuum force earlier',stack(
    eq(r'\mathrm{FSQR}+\mathrm{FSQZ}<3\times10^{-2}\quad\text{instead of}\quad10^{-3}'),
    table(['Free-boundary case','Reference','Seeded','+ coarse step','+ earlier vacuum'],[
        ['CTH-like · single','489','384','347','309'],
        ['CTH-like · multigrid','592','563','446','431'],
        ['W7-X · ns=51','1,831','1,797','1,797','1,733'],
        ['Solovev · multigrid','1,047','1,025','1,025','1,025']]),
    p('The coarse 3-D step multiplier is 17/14: CTH-like starts at <strong>0.85</strong> instead of 0.7. Activation retains the existing reset and validation sequence.')),
    '57f86b7 / f5eeba6 · ADR-0010',
    'The expression denotes the code’s FSQR+FSQZ scalar residual sum, not a new residual definition. Avoid over-solving the temporary no-vacuum model. Coarse step tuning applies only through ns=25; it does not select the fine W7-X or axisymmetric case.',chapter='Trajectory')
add('Free-boundary wall measurements follow the pass counts',table(['TITAN Xp · archived','Reference median','Tuned median','Reduction','Pairs'],[
    ['CTH-like · 15 → 25','1.93 s','1.50 s','22.3%','7'],
    ['W7-X · ns=51','8.37 s','7.93 s','5.3%','5']])+grid(
    panel('CTH-like spread',p('Reference: <strong>1.91–2.01 s</strong><br>Tuned: <strong>1.48–1.50 s</strong><br>Identical 592 / 431 counts in every pair.')),
    panel('W7-X spread',p('Reference: <strong>8.32–8.39 s</strong><br>Tuned: <strong>7.85–7.97 s</strong><br>Identical 1,831 / 1,733 counts in every pair.'))),
    'd2d8b81 · performance.md §2.5 · ADR-0010',
    'These measure the seed, coarse-step and activation combination before cubic transfer. The subsequent CTH cubic result is 424 passes, not the 431-pass trajectory timed here. Free-boundary CUDA-stream time includes the host vacuum-coupling gap.',chapter='Trajectory')
add('A better transfer saves work on refined grids',table(['Linear → Catmull-Rom','Before','After','Fewer passes','Final FSQR'],[
    ['W7-X · fixed','4,507','4,160','347 · 7.70%','9.986e-13'],
    ['Solovev · fixed','815','766','49 · 6.01%','9.695e-17'],
    ['CTH-like · free','431','424','7 · 1.62%','9.920e-11']])+callout('Four coarse samples retain curvature that two-point interpolation discards. The first stage is unchanged; only the refined-stage starting state changes.'),
    '1a10037 · ADR-0011',
    'Interpolate in the same odd-mode regularized coordinate; preserve exact LCFS, explicit odd-axis zeroing and reset velocity. Axisymmetric free Solovev regressed 1025→1045, so it retained linear transfer. This is a Class C numerical change.',chapter='Trajectory')
add('Global B-splines improve the transfer again',table(['Catmull-Rom → B-spline','Before stage counts','After stage counts','Total saved','Final FSQR'],[
    ['W7-X · fixed','1315 → 1443 → 1402','1315 → 1419 → 1372','54 · 1.30%','9.997e-13'],
    ['Solovev · fixed','235 → 190 → 341','235 → 193 → 326','12 · 1.57%','9.973e-17']])+grid(
    panel('Numerical improvement',p('An interpolating cubic B-spline uses the converged radial profile globally. The GPU map matches the direct host B-spline trajectory.')),
    panel('Execution improvement',p('One precomputed map applies to every spectral profile. Asynchronous preparation hides its host construction behind the coarse solve.'),'free')),
    'b13cd87 / 12435fa / f79214c · ADR-0012',
    'B-spline support depends on the exact direct dependency e7f5207 in the reproduced v1.2 build. Missing that dependency silently selects Catmull-Rom and produces 4160/766 instead of 4106/754. The modest extra pass benefit must not be confused with the whole v1.1→v1.2 gain.',chapter='Trajectory')
add('Use the transfer that each solve class qualified',table(['Solve class','Selected transfer','Evidence for limiting scope'],[
    ['Precise-double fixed boundary','Global cubic B-spline','W7-X 4106; Solovev 754'],
    ['Precise-double 3-D free boundary','Catmull-Rom','CTH: spline 424 → 425, so reject'],
    ['Axisymmetric free boundary','Linear','Cubic 1025 → 1045; spline →1074'],
    ['Mixed-float','Linear','Higher-order transfer not selected'],
    ['Fixed without spline dependency','Catmull-Rom fallback','Explicit build/runtime opt-outs retained']]),
    'ADR-0011 / ADR-0012 · v1.2 policy',
    'Policy is solve-class-specific, not universal. CUMES_FORCE_LINEAR_PROLONGATION=1 selects the reference transfer; CUMES_FORCE_CATMULL_PROLONGATION=1 selects the intermediate scheme. These knobs alone do not undo seed and controller changes.',chapter='Trajectory')

rows=[]
for key,label in [('solovev-multigrid','Solovev · 5/11/55'),('w7x-multigrid','W7-X · 33/66/99'),('solovev-single','Solovev · ns=55'),('w7x-single','W7-X · ns=99')]:
    r=local['cli'][key];a=r['v1.1'];b=r['v1.2']
    rows.append([label,f"{a['iterations']:,}",f"{b['iterations']:,}",f"{100*(1-b['iterations']/a['iterations']):.2f}%",b['residuals'][0]])
add('Reproduced now: exact release convergence counts',table(['TITAN Xp · precise double','v1.1 passes','v1.2 passes','Reduction','v1.2 FSQR'],rows)+callout('All five timed repeats agree on every stage count and final printed residual triple. The input JSON is identical between versions.'),
    'NEW · f7036ab vs 17867d5 · data/local/cli-*.log',
    'Single-grid inputs are derived from the shipped v1.1 arrays by keeping only the final ns/niter/ftol entry; all physical parameters are unchanged. Multigrid tolerances are 1e-16 for Solovev and 1e-12 for W7-X. These are local reproductions, not copied archive values.',chapter='Trajectory')
rows=[]
for key,label in [('solovev-multigrid','Solovev · multigrid'),('w7x-multigrid','W7-X · multigrid'),('solovev-single','Solovev · single'),('w7x-single','W7-X · single')]:
    r=local['cli'][key];a=r['v1.1']['wall_s'];b=r['v1.2']['wall_s']
    rows.append([label,f"{a['median']:.4f} ± {a['mad']:.4f}",f"{b['median']:.4f} ± {b['mad']:.4f}",f"{local['comparisons'][key]['reduction_percent']:.2f}%"])
add('Reproduced now: complete CLI wall time',table(['New TITAN Xp · five pairs','v1.1 median ± MAD · s','v1.2 median ± MAD · s','Reduction'],rows)+p('Includes process startup, stage construction, iteration, final scientific fields, and native file output. Warmup runs and checkpoint gates are excluded from these five timed pairs.')+callout('Solovev wall estimates are inconclusive: confidence intervals cross zero. W7-X multigrid has a paired 95% interval of 21.77–23.45% lower wall time.'),
    'NEW · data/local/summary.json · process perf_counter timing',
    'CPU affinity and GPU state are preserved in environment.json. Both versions use binary output with optional backend libraries disabled. Clocks are unlocked; raw ranges and paired bootstrap confidence intervals are retained. These measurements are not equated with CUDA event time.',chapter='Trajectory')
rows=[]
for key,label in [('solovev-multigrid','Solovev'),('w7x-multigrid','W7-X')]:
    r=local['cli'][key]['v1.2']; replay=local['checkpoint_replays'][key.split('-')[0]]
    rows.append([label,' → '.join(map(str,r['stages'])),*r['residuals'],str(replay['stages'][0])])
add('Convergence is a residual and fixed-point claim',table(['v1.2 local result','Stage counts','FSQR','FSQZ','FSQL','Replay passes'],rows)+grid(
    panel('Re-evaluate the result',p('Save a final-grid checkpoint, then restart the same problem on the final grid. Both reproduced cases converge after one evaluation.')),
    panel('Use the right equivalence test',p('Seeds and transfer intentionally change the path. Different λ-gauge representatives can meet the same force tolerances; byte identity to v1.1 is not required.'),'free')),
    'NEW · checkpoint-*-create/replay.log · ADR-0007…0012',
    'The local gate verifies the printed residual triple and one-pass replay, not unprinted full-precision equality. Archived ADRs separately report exact checkpoint/state equality for their qualification runs. Compare_runs / independent VMEC++ comparisons are diagnostic checks, not a replacement for cuMES residual gates.',chapter='Trajectory')

def residual_plot():
    colors=['#43d9ff','#ffb454'];curves=[]
    for version,color in zip(('v1.1','v1.2'),colors):
        log=(deck/f'data/local/cli-w7x-single-{version}-1.log').read_text()
        pts=re.findall(r'^\s*(\d+)\s*\|\s*([\deE.+-]+)\s+([\deE.+-]+)\s+([\deE.+-]+)',log,re.M)
        import math
        coords=[]
        for n,a,b,c in pts:
            residual=max(map(float,(a,b,c)))
            if residual<=0:continue
            x=85+int(n)/3100*925;y=45+(min(0,max(-13,math.log10(residual)))*-1)/13*340
            coords.append(f'{x:.2f},{y:.2f}')
        curves.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" stroke-width="3"/>')
    def label(x, y, width, html, align='left', color='#b6cbd7'):
        # KaTeX needs HTML inside the SVG; text elements cannot contain spans.
        return f'<foreignObject x="{x:.1f}" y="{y:.1f}" width="{width}" height="30"><div xmlns="http://www.w3.org/1999/xhtml" style="font:17px/26px sans-serif;color:{color};text-align:{align};white-space:nowrap">{html}</div></foreignObject>'
    ticks=''.join(f'<line x1="85" y1="{45+i/13*340:.1f}" x2="1010" y2="{45+i/13*340:.1f}" stroke="#224051"/>' + label(0,32+i/13*340,67,inline(f'10^{{-{i}}}'),'right') for i in (2,4,6,8,10,12))
    ticks+=''.join(label(50+i/3100*925,397,70,inline(str(i)),'center') for i in (0,500,1000,1500,2000,2500,3000))
    labels = label(90,5,460,inline(r'\max(\mathrm{FSQR},\mathrm{FSQZ},\mathrm{FSQL})')) + label(850,425,220,'reported iteration')
    labels += label(680,5,180,'v1.1 · '+inline('2953'),color=colors[0]) + label(860,5,180,'v1.2 · '+inline('2465'),color=colors[1])
    return '<svg class="residual-chart" viewBox="0 0 1080 455" role="img" aria-label="Sampled maximum residual against iteration for W7-X single grid; v1.2 reaches tolerance sooner.">'+ticks+labels+''.join(curves)+'</svg>'
add('A shorter convergence path, sampled from the logs',residual_plot()+p('W7-X · single ns=99 · same 10⁻¹² tolerance. Lines join printed samples; early restart details between samples are not resolved.'),
    'NEW · cli-w7x-single-v1.1-1.log / v1.2-1.log',
    'The y-axis is logarithmic and plots the maximum of the three printed residual components. X is the logged iteration index, not wall time. Lines are straight interpolation between printed samples, not a reconstructed every-pass trace.',chapter='Trajectory')
add('Saved passes have different costs on different grids',table(['W7-X stage','v1.1 passes','v1.2 passes','Passes removed','Grid size'],[
    ['Coarse','1,877','1,315','562','33 × 30 × 36'],['Middle','1,617','1,419','198','66 × 30 × 36'],['Fine','2,011','1,372','639','99 × 30 × 36']])+callout('The fine grid contributes 639 of the 1,399 saved passes. A total-pass percentage alone cannot predict the exact wall-time reduction.'),
    'Release trajectories · local logs · performance.md §1',
    'CUDA stream event time is available in v1.2 but not the old CLI. It excludes setup and publication; for free boundary it includes host coupling gaps. Never multiply a final-shape fixed-iteration latency by total multigrid passes and label it measured whole-solve time.',chapter='Trajectory')
add('Numerical ideas rejected by the evidence',table(['Candidate','Measured result','Why it was not retained'],[
    ['Repeated / periodic step recovery','Recurring invalid Jacobians; no convergence','One-shot recovery is the qualified policy'],
    ['Damping floor 0.0025…0.08','No convergence within 5,000 iterations','Does not cure the early transient'],
    ['Preconditioner cadence 10','Best 2,853 vs 2,953 reference','Other intervals regress; larger algorithm change'],
    ['Fine free W7-X envelope 0.12','1,953 vs 1,831 reference','Resolution-limited 0.03 chosen'],
    ['Full fixed-boundary predictor for free W7-X','1,449 + 1,723 = 3,172 passes','More work than 1,831 direct passes']]),
    'ADR-0007 / ADR-0010 · rejected experiments',
    'Rejected policies belong in the development story because fewer iterations in one favorable sample do not establish robust convergence. Aggressive predicate changes also reached states differing by up to 2.34e-3 and were not retained.',chapter='Trajectory')

chapter('A','Appendix: later work','Later releases extend both themes: concurrent solves, coarse-start tuning, and precision-aware execution.')
add('v1.3: very coarse 3-D seeds help QA and QH differently',table(['Analytic center','Reference','Coarse seed −0.10','Fewer passes'],[
    ['QA','1178 → 252 → 118 = 1548','886 → 226 → 100 = 1212','21.7%'],
    ['QH','445 → 302 → 361 = 1108','303 → 293 → 314 = 910','17.9%']])+table(['Four-worker Jacobian · 3 runs','Before','After','Wall reduction'],[
    ['QA','0.827 s','0.658 s','20.4%'],['QH','0.693 s','0.687 s','0.8%']]),
    'a7f605d / f61c959 · performance.md §3.7',
    'Production selection is fixed-boundary 3-D multigrid with initial_ns<=12, not a spectrum-amplitude classifier despite the early plan. Standard W7-X starts at 33 and Solovev is axisymmetric, so their qualified trajectories remain unchanged. A center-point iteration gain does not guarantee a similar full Jacobian gain.',chapter='Later work')
add('Sensitivity reuse solves a different performance problem',grid(
    panel('Retained linearized equilibrium',eq(r'F_u\,\delta u=-F_x\,\delta x')+p('Analytic CUDA JVPs and right-preconditioned restarted GMRES reuse the converged operator session for successive boundary directions.')),
    panel('Reported qualification',p('QH residual-vector derivative difference: <strong>5.2%</strong>.<br>Coordinate-invariant objective derivative difference: <strong>0.14%</strong>.')+p('No isolated timing is used here to claim faster nonlinear equilibrium convergence.'))),
    '2d07d47 / <code>0064e98</code> / c1abf20 · ADR-0013',
    'This replaces repeated nonlinear solves in a derivative workflow with retained linear solves. It is a different algorithm and workload from the v1.1→v1.2 equilibrium trajectory. Dense forward Jacobian cost still scales with parameter count. Gauge differences affect the residual-vector comparison.',chapter='Later work')
add('Current float branch: accuracy unlocks convergence',table(['W7-X float · every stage ftol=10⁻⁵','Result','Extra per-pass work'],[
    ['Absolute R₀₀ quantization diagnostic','Double-evaluated FSQR 2.1083e-4','Precision floor evidence'],
    ['Quantize displacement relative to edge','FSQR 4.8304e-9 in the same diagnostic','Retain small radial structure'],
    ['Reference storage alone','Final grid still stalls; best max residual 1.4070e-5','Does not complete cold convergence'],
    ['Reference + poloidal float-float','149 → 277 → 322; FSQR 9.837748e-6','Fused into existing R/Z launches']])+callout('These are 10⁻⁵ mixed-float accuracy experiments. They cannot be compared as speedups against the 10⁻¹² double W7-X solve.'),
    'a880051 / 3cebb49 / bd01518 · ADR-0014; w7x-float-float.md',
    'Reference representation is default for fixed 3-D float; poloidal compensation remains opt-in. Native odd reconstruction plus reference alone does not finish the qualified 1e-5 cold solve. No additional launch, scratch array or hot-loop allocation is introduced by the minimal fused poloidal option.',chapter='Later work')
add('Cache the immutable float radius reference',table(['TITAN Xp · 300 warmup + 500 measured','Before cache','After cache','Reduction'],[
    ['Reference / native float','541.90 μs','525.55 μs','3.02%'],
    ['Reference / poloidal float-float','559.29 μs','543.02 μs','2.91%'],
    ['Absolute-coefficient control','—','526.46 μs','Same-session control']])+callout('Compute the constant reference Fourier sum once per stage. One graph node disappears; no new buffer is allocated; the 149 → 277 → 322 trajectory is unchanged.'),
    '194415d · ADR-0014 · three alternating executable comparisons',
    'Archived current-branch measurements, not newly reproduced for this deck. Cache validity and buffer lifetime are explicit; reference switching invalidates the prepared binding. Nonlinear geometry still restores absolute radius locally each pass. This is an execution optimization inside the later precision work.',chapter='Later work')
add('The gains that the evidence supports',grid(
    panel('Execute each pass efficiently',p('<strong>RTX W7-X:</strong> 660.81 → 534.53 μs.<br><strong>RTX Solovev:</strong> 115.59 → 82.33 μs.')+p('Graphs matter most when submission is a large fraction of latency. Keep data resident and retain only measured kernel changes.')),
    panel('Spend fewer passes converging',p('<strong>W7-X multigrid:</strong> 5,505 → 4,106.<br><strong>Solovev multigrid:</strong> 906 → 754.')+p('Cold-start policy and smoother continuation reduce full force evaluations while meeting the configured residual tolerances.'),'free'))+
    callout('The new TITAN Xp release comparison confirms the deterministic counts and measures complete wall time. Every headline points to commits, inputs, and raw or archived evidence.'),
    '5379fca · 17867d5 · data/local/summary.json',
    'Do not combine separate archived sessions into a synthetic total speedup. Execution and trajectory gains are complementary but measured under different scopes. The raw local results make the current same-machine comparison reviewable.',chapter='Closing')
add('Evidence and reproduction',table(['Artifact','What it contains'],[
    ['evidence.md','Pinned source citations, measurement scopes, and limits'],
    ['data/commit-audit.tsv','All 197 post-design-closeout commits and changed files'],
    ['data/optimization-commits.md','42 highlighted optimization/support/evidence records'],
    ['data/local/','Raw fixed-iteration JSON, CLI logs, exact inputs, GPU provenance'],
    ['scripts/build_history.py → measure.py → summarize.py','Historical worktrees, controlled measurements, statistical summary'],
    ['scripts/build_deck.py','Static HTML generation from narrative and measured results']])+p('Open locally to present. <strong>O</strong> overview · <strong data-math-ignore>N</strong> notes · <strong>← / →</strong> navigation · browser print for 16:9 PDF.'),
    'Offline deck · Technical Blueprint style · reviewed 2026-09-07',
    'All presentation runtime assets are local, including KaTeX and its fonts. Scratch worktrees and binaries live in ../tmp/cumes-optimization-slides-20260907. This deck does not alter the cuMES working checkout.',chapter='Closing')

template=(deck.parent/'cumes-run/index.html').read_text()
tail=template.split('  </main>',1)[1]
head='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#04101a"><meta name="description" content="Measured optimization history of cuMES: CUDA execution and convergence trajectory changes.">
<title>Making cuMES faster</title><link rel="stylesheet" href="vendor/katex/katex-swap.min.css"><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="optimization.css"></head><body><main class="deck" aria-live="polite">
'''
(deck/'index.html').write_text(format_html(head+'\n'.join(slides)+'\n</main>'+tail))
print(f'Built {len(slides)} slides')
