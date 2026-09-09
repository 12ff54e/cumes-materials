# Evidence ledger: optimization during cuMES development

This deck separates implementation/execution improvements from changes to the
convergence trajectory. It audits the CUDA history reachable in
`dc0d0c4..6756fd6` (v1.5.0): 244 commits including merged ancestry. `dc0d0c4` marks design
closure; reader/safety closure finishes at `56aa1a4`. Phase 6 numbers are clearly
marked as earlier background. The independent, unmerged `webgpu` branch is outside
this CUDA deck. Optimizer policy in `../meow` is not a cuMES equilibrium change.

The 2026-09-09 update adds 47 commits after the previous `194415d` audit,
including the v1.4.0/v1.4.1 release completions and all 33 v1.5 commits after
v1.4.1. It reviews the three pinned vacuum-field dependency commits as well.
The inventory highlights 81 implementation, evidence, support and rejected
records. New slide content uses archived release qualification; no new solver
timings or independent reference solves were run for this update.

The full inventory is [commit-audit.tsv](data/commit-audit.tsv); the selected
implementation, evidence, support, and rejected-experiment records are in
[optimization-commits.md](data/optimization-commits.md). Classification covers
optimization candidates even when their subject does not contain `perf`.

## Sources and version boundaries

All technical sources were read from the local `../cuMES` checkout and its git
history. The links below pin their content for later review:

- [Overhaul design closure dc0d0c4](https://github.com/12ff54e/cuMES/commit/dc0d0c4)
  and [final closeout 56aa1a4](https://github.com/12ff54e/cuMES/commit/56aa1a4).
- [v1.0 dbb0f8e](https://github.com/12ff54e/cuMES/commit/dbb0f8e),
  [v1.1 f7036ab](https://github.com/12ff54e/cuMES/commit/f7036ab),
  [v1.2 17867d5](https://github.com/12ff54e/cuMES/commit/17867d5), and
  [v1.3 750d6a4](https://github.com/12ff54e/cuMES/commit/750d6a4).
- [v1.4.0 ef67884](https://github.com/12ff54e/cuMES/commit/ef67884),
  [v1.4.1 f0c17f7](https://github.com/12ff54e/cuMES/commit/f0c17f7), and
  [v1.5.0 6756fd6](https://github.com/12ff54e/cuMES/commit/6756fd6).
- [Performance ledger at v1.5.0](https://github.com/12ff54e/cuMES/blob/6756fd6/docs/performance.md).
- [Archived overhaul record](https://github.com/12ff54e/cuMES/blob/194415d/docs/overhaul-history.md).
- [CUDA graph ADR](https://github.com/12ff54e/cuMES/blob/5379fca/docs/adr/0003-cuda-graphs.md).
- [Recovery ADR-0007](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0007-single-grid-step-recovery.md).
- [Seed ADR-0008](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0008-shaped-cold-start.md).
- [Axisymmetric ADR-0009](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0009-axisymmetric-start-policy.md).
- [Free-boundary ADR-0010](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0010-free-boundary-start-policy.md).
- [Cubic ADR-0011](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0011-cubic-multigrid-transfer.md).
- [B-spline ADR-0012](https://github.com/12ff54e/cuMES/blob/17867d5/docs/adr/0012-bspline-fixed-boundary-transfer.md).
- [Forward tangent ADR-0013](https://github.com/12ff54e/cuMES/blob/194415d/docs/adr/0013-equilibrium-forward-tangents.md).
- [Float radius ADR-0014](https://github.com/12ff54e/cuMES/blob/194415d/docs/adr/0014-float-radius-reference.md)
  and [selective reconstruction evidence](https://github.com/12ff54e/cuMES/blob/194415d/docs/w7x-float-float.md).

Some living documents contain earlier trajectories or archived plans alongside
later updates. The deck uses milestone-specific numbers. In particular, the
0.12 single-grid seed's 2627 passes and wall measurements are distinct from the
later 0.129 seed's 2465 passes. The actual later very-coarse predictor is selected
by `initial_ns <= 12` and multiple stages, not a boundary-spectrum classifier
suggested by the initial plan.

## Part 1: execution and data movement

| Change | Evidence and scope |
| --- | --- |
| One-fence loop, earlier overhaul background | Five ordinary host barriers become one in `36403ad`; force-norm work later removes its refresh fence and synchronous array copies. W7-X cuFFT workspace approximately 10.4 MB to 5.5 MB. Seed slab upload/zeroing becomes one copy and one memset rather than six each. These are not newly attributed post-closeout gains. |
| Fixed-boundary bundle `5379fca` | RTX 4090 / CUDA 12.9, precise double, optional backends and vacuum disabled. Solovev fixed-pass wall 115.59 to 82.33 μs; W7-X 660.81 to 534.53 μs. Bundle includes graph integration, Jacobian statistics, and full-theta mapping. |
| Jacobian reduction within `5379fca` | W7-X kernel time 104.7 to 7.2 μs. Up to 128 blocks of 256 threads plus finalize. Three double and two int partials per block imply at most 4096 bytes before alignment. No claim that 14.54× kernel speedup equals solve speedup. |
| Full-theta mapping within `5379fca` | Per-output poloidal arithmetic retained. W7-X theta thread dimension 15 to 30; removes two serial theta-half passes. No isolated timing; measured within the bundle. |
| Production graphs within `5379fca` | 1000-pass preheat, six order-alternated pairs, 50 warmup + 300 measured passes each. Solovev direct/graph 117.14/82.33 μs; W7-X 562.10/534.53 μs. Hashes identical within each graph A/B: `3c09fd3260b003a8` and `ce46a7cbe693601a`. |
| Graph schedule semantics | Lazy refresh/non-refresh variants; invalidate non-refresh variants after new host normalization factors. Host controller stays behind the control fence. Free-boundary and verification-dump paths remain direct. |
| Finest-grid fields `5d5e380` | Three-grid runs perform one derived-field capture instead of three. Two coarse capture/evaluation calls disappear. Structural count; no isolated wall timing recorded. |
| Boozer bridge `fa119ea` | Six spectral and seven half-field host spans alias the existing snapshot. Avoids owning host-array copies and a native-file handoff; not a zero-copy GPU transfer. No isolated timing recorded. |
| Flat Makegrid `933b80a` | cuMES submodule update to vacuum-field `be6d6cd`: three contiguous field-component vectors, coil-major and R-fast. No isolated timing recorded. |
| Parallel Makegrid `e507b36` | vacuum-field `110748f`: independent points; chunks of eight; worker cap `min(thread_limit, ceil(work_items/32), work_items)`, minimum one. Serial control `VFIELD_MAKEGRID_THREADS=1`. One-time construction; no isolated timing recorded. |
| Figure tooling `5310769` | Commit records 42 to 17 s for the combined rendering change, approximately 100× IFFT synthesis gain, and direct-sum agreement to 1e-14. No hardware/repetition protocol; not a solver speedup or isolated parallel-rendering gain. |
| Event lines `2dea659` | Compiled out when verification dumps are compiled out. Verify path and frozen output retained. No isolated timing. |
| B-spline execution `b13cd87`, `12435fa` | Direct host batch: 1.90 and 2.94 ms for W7-X 33→66 and 66→99. Prior GPU Catmull boundaries: 0.084 and 0.232 ms. Small map generation: 36.7 and 136.5 μs medians over 10,000 warmed optimized host calls on gervais; total 173.3 μs vs about 462 μs per average device iteration. Coarse solve has 1315 passes. Maps built asynchronously, applied to 936 profiles on GPU. |
| Map payload accounting | `66*33*8=17424` bytes and `99*66*8=52272` bytes. Derived sizes, not a PCIe measurement. Numerical transfer benefit belongs to part 2. |
| Concurrent coordination `d0f408b` | Eight QA columns 2.823 to 1.247 s; QH 2.250 to 1.025 s with two workers. Identical Jacobians, 96 verify tests. Focused throughput diagnostics; no repeated full optimizer speedup claimed. |

## Part 2: trajectory changes through v1.2

| Milestone | Solovev multigrid | W7-X multigrid |
| --- | --- | --- |
| v1.1 | 251→199→456 = 906 | 1877→1617→2011 = 5505 |
| Recovery `7541ff6`, `774363f` | unchanged | 1741→1568→1635 = 4944 |
| Fixed 3-D envelope `f270790` | unchanged | 1315→1559→1633 = 4507 |
| Axis envelope `3d08aef` | 241→199→455 = 895 | unchanged |
| Axis stage step `27c5e39` | 238→193→387 = 818 | unchanged |
| Axis lambda `9f4d7c1` | 235→193→387 = 815 | unchanged |
| Catmull-Rom `1a10037` | 235→190→341 = 766 | 1315→1443→1402 = 4160 |
| B-spline `b13cd87`, dependency `f79214c` | 235→193→326 = 754 | 1315→1419→1372 = 4106 |

The asynchronous setup commit does not provide a separate convergence reduction.
`4658ea0` centralizes policy constants; `cad3daa` adds observability. Neither
is attributed another numerical gain. B-spline support must be present: absent
dependency selects Catmull-Rom and would not reproduce the release counts.

Recovery uses `min(delt0,1.1*delt)` after 250 accepted passes since the latest
restart, once per fixed-boundary stage. W7-X single grid: 2953→2711 (8.20%).
Final FSQR 9.988e-13; multigrid FSQR/FSQZ/FSQL
9.989e-13 / 1.590e-13 / 5.116e-14. The ADR records one-pass final-grid replay.
Archived RTX single-grid wall medians 2.0583/1.9217 s, MAD 6.1/7.6 ms, ranges
2.0510–2.5015/1.9102–2.5244 s; multigrid medians 3.3109/3.0021 s,
MAD 0.1090/0.2123 s, ranges 3.1856–3.6662/2.7096–3.5031 s.

Shaping multiplies `s^(m/2)` by `1+c(1-s)`. Fixed 3-D multigrid uses c=0.12;
single-grid 0.12 first yielded 2627 passes; `6d9e593` selects 0.129 and 2465.
The older single-grid wall 1.9238→1.8823 s (MAD 6.3/14.8 ms) is for the earlier
policy, not the 2465 result. Multigrid shaping wall 3.4419→3.2983 s had large
MAD 0.331/0.388 s. Later single-grid device time 1.334 s is a different metric.

Axisymmetric envelope c=-0.07 applies at initial ns<=11. Initial precise-double
step multipliers are 7/6 single, 17/15 first continuation, 6/5 prolonged.
The geometric predictor uses `lambda_theta=1-q/<q>` with `q=sqrt(g)/R^2`,
projected by host quadrature and scaled 0.65. Cold Solovev ns=55: 533→416 with
step scaling, then 354 with lambda. Final FSQR 9.835e-17. Mixed float retains
the original step policy.

| Free-boundary precise-double workload | Reference | Seed | + step | + activation | + selected cubic |
| --- | ---: | ---: | ---: | ---: | ---: |
| CTH-like ns=15 | 489 | 384 | 347 | 309 | single grid |
| CTH-like 15→25 | 592 | 563 | 446 | 431 | 424 |
| W7-X ns=51 | 1831 | 1797 | 1797 | 1733 | single grid |
| Solovev 16→32 | 1047 | 1025 | 1025 | 1025 | linear retained |

`355c10c`: free 3-D envelope c=0.12 through ns=25, c=0.03 above;
axisymmetric free lambda scale 1.0. `57f86b7`: precise-double coarse free 3-D
step 17/14 (0.7→0.85). `f5eeba6`: vacuum activation residual gate
`FSQR+FSQZ < 3e-2` instead of `1e-3`. Existing restart/reset/validation remains.

`d2d8b81` records TITAN Xp wall before cubic: seven CTH pairs, medians
1.93/1.50 s, ranges 1.91–2.01/1.48–1.50 s; five W7-X pairs,
8.37/7.93 s, ranges 8.32–8.39/7.85–7.97 s. All counts repeat. These archived
free-boundary inputs were not rebuilt or rerun in this presentation task.

Cubic/B-spline transfer preserves odd-mode regularization, exact LCFS, axis
rules, and zero velocity. Selected defaults: B-spline for double fixed,
Catmull-Rom for double 3-D free, linear for axisymmetric free and mixed float.
Rejected free spline results: CTH 424→425 and Solovev 1025→1074; rejected
axisymmetric free Catmull result: 1025→1045.

## Later work and rejected experiments

All following numbers are archived evidence rather than new task measurements.

- Force splitting, earlier overhaul: 108 registers→82/54 but 1.20–1.45× slower.
- RTX register caps and split-forward prototypes removed for not clearing 5%.
- `17d731c`: best forward tile 4 gave W7-X 1.584→1.528 ms direct and
  1.573→1.518 ms graph (3.5%, three alternating runs). All hashes retained.
- `b0d6758`: inverse packing flat/slower after five production-graph pairs;
  deriving poloidal tables approximately 0.5% slower, also removed.
- `d36025f`: four-worker tile 4 QA 0.814→0.801 s, QH 0.678→0.682 s;
  three alternating runs, identical Jacobians and 12171/8347 nonlinear counts.
- `480c91d`: facade setup 0.12% QA/0.19% QH. Eight-solve aggregate profile:
  QA multigrid 3.1525 s = setup .13690 + iteration 2.89850 + capture .06035
  + teardown .04174 + other .01505 (rounded); QH 2.6627 s = .14062 + 2.40979
  + .06185 + .03798 + .01246. Caching ceiling 5.6%/6.7%, ~69 MB retained per
  W7-X worker. Rejected without implementation; timing instrumentation retained.
- `a7f605d`/`f61c959`: very-coarse 3-D multigrid c=-0.10, initial_ns<=12.
  QA centers 1548→1212; QH 1108→910. Three four-worker Jacobian medians
  .827→.658 s QA, .693→.687 s QH. Complete mode-1 optimizer work
  242168→208099 QA and 269787→229078 QH, objectives differing .032%/.0015%.
  No equivalent total wall-time claim; standard W7-X/Solovev untouched.
- `2d07d47`/`0064e98`/`c1abf20`: retained JVP and preconditioned GMRES
  sensitivity solve. QH residual derivative difference 5.2%, invariant objective
  derivative difference .14%; do not interpret those accuracy checks as speed.
- `a880051`/`3cebb49`/`bd01518`: float accuracy branch. Quantized absolute
  R00 diagnostic FSQR 2.1083e-4 vs displacement diagnostic 4.8304e-9.
  Reference alone still stalls with best final max residual 1.4070e-5;
  reference plus poloidal float-float converges at all-stage 1e-5 in
  149→277→322, FSQR 9.837748e-6. Compensation is opt-in.
- `194415d`: cached constant reference removes one captured inverse node and
  allocates no additional buffer. Three 300-warmup/500-measured-pass alternating
  TITAN Xp runs: native reference 541.90→525.55 μs; poloidal compensation
  559.29→543.02 μs; absolute control 526.46 μs. Same checkpoint/trajectory.
  Not comparable to double at 1e-12 as an accuracy-matched speedup.

## v1.5 execution: archived qualification

The tagged documents, benchmark inputs/runners/results and original transform
samples are frozen in [data/v1.5/](data/v1.5/).
[provenance.json](data/v1.5/provenance.json) gives source revisions/paths and
SHA-256 hashes; [summary.json](data/v1.5/summary.json) feeds the slide tables.
`scripts/import_v15_evidence.py` checks all displayed transform medians against
the 128 individual timed samples, free-boundary variant medians against their
raw process samples, and every paired percentage median against its saved
reductions. Original confidence intervals, outliers and failures are retained.

| Comparison | Pinned baseline | Retained candidate | Timing scope |
| --- | --- | --- | --- |
| Fourier | v1.4.1 `f0c17f7` | `66a557a` + `21b6043` | Steady fixed-shape pass wall latency; excludes setup/output |
| Free boundary | `bcdd3da`, vacuum `edbbb280` | `cc2d91d`, vacuum `4d19939` | Summed configured-stage CUDA-event intervals and separate process wall |
| Newton | Same preserved private binary with hook disabled | Hook enabled; later promoted in `ca33025` / `bcdd3da` | CUDA-event solver intervals including operator/Newton construction and every extra evaluation |

These comparisons do not form a single v1.4.1-to-v1.5 end-to-end speedup.
The free-boundary baseline already contains the Fourier changes. Newton's
76 promotion checks reproduce the experiment's corresponding native outputs,
fields, stage reports and correction counts exactly on both architectures;
they are numerical equivalence checks, not new timing measurements.

### Fourier: preserve rounding, remove repeated work

[Pinned implementation](https://github.com/12ff54e/cuMES/blob/6756fd6/src/kernels/fourier_impl.cuh)
and [qualification](data/v1.5/docs/performance.md) show that inverse R/Z each
retain one required constraint sum and lambda retains neither. Basis/sign
expressions remain runtime expressions to preserve FMA contraction. The four
weighted forward tables use the original device-rounded products, caching them
once per stage. W7-X adds 6,144 arena bytes; per-iteration graph topology,
allocation count and control fences are unchanged.

| GPU / shape | Median μs/pass, before → after | Median run p95 μs | Paired reduction, 95% CI |
| --- | ---: | ---: | ---: |
| TITAN Xp / W7-X | 1584.330 → 1501.220 | 1735.455 → 1652.895 | 5.1905% [5.1588, 5.2391] |
| TITAN Xp / Solovev | 124.565 → 124.335 | 193.810 → 193.985 | 0.3346% [-0.1685, 0.5740] |
| RTX 4090 / W7-X | 535.545 → 500.770 | 622.805 → 588.895 | 6.4963% [6.4732, 6.5137] |
| RTX 4090 / Solovev | 83.950 → 83.935 | 128.340 → 127.200 | 0.0179% [-0.0119, 0.1303] |

Sixteen alternating pairs per workload/GPU, 100 warmup + 500 timed passes per
recorded run, production graphs, precise double, CPU 8. W7-X uses ns=99 and
Solovev ns=55. TITAN Xp uses CUDA 12.1/native sm_61; RTX 4090 uses CUDA
12.9.41/GCC 12.4/native sm_89. Both had unlocked clocks. Full numerical dump
manifests match within each architecture (241 Solovev and 472 W7-X files).

The original artifacts refine a shorthand in the living performance document:
Pascal's preheat is 1000 warmup + 1000 timed passes, while the Ada report and
runner use 100 + 1000. The measured windows are identical. Bootstrap uses
20,000 paired resamples; Pascal seed 20260908 and interpolated percentiles,
Ada seed 8961 and sorted indices 500/19499. These original intervals are kept.
Stage setup grows by 0.743/0.762 ms for Pascal W7-X/Solovev and 0.246/0.430 ms
for Ada. An Ada 653 ms first-allocation outlier and same-executable A/A control
preclude using these iteration percentages as process-wall gains.

### Free boundary: ordered vacuum kernels and fewer blocking copies

The three vacuum-field commits `4acd589`, `2eb53c9`, `4d19939` were inspected
at their exact revisions in the existing `../cumes-opt/deps/vacuum-field`
checkout, because the primary cuMES submodule is checked out at another
revision. Neither checkout was changed. The source/image/target terms for
axisymmetric `gstore` are evaluated in parallel, with the original ordered
weighted accumulation retained in a second kernel. The Solovev scratch is
240 KiB. Singular RHS systems with at most 256 modes use eight-thread blocks;
larger systems retain the original 256-thread launch and all per-mode sums.
`cc2d91d` moves `buco/bvco` and guarded `delbsq` readbacks ahead of existing
fences using pinned storage. Its zero-initialized diagnostic fixes an inherited
pre-activation uninitialized read. The two dependency fences remain.

The [complete qualification tables](data/v1.5/docs/free-boundary-performance.md)
include median, p95, MAD, extrema, paired intervals and all limits. Seven
alternating pairs per case/GPU follow two warmups per variant. The 20,000-pair
bootstrap uses seed 20260909. The precise-double hardware/toolchain matrix is
TITAN Xp/CUDA 12.1.105/GCC 12.4/sm_61 and RTX 4090/CUDA 12.9.41/GCC 12.4/sm_89,
CPU 8, unlocked clocks. These are different baselines from the earlier
free-boundary seed/cubic measurements.

| Case | Solver reduction TITAN Xp / RTX 4090 | Process reduction TITAN Xp / RTX 4090 |
| --- | ---: | ---: |
| Solovev mgrid | 37.01% / 29.69% | 26.05% / -1.78% |
| Solovev embedded MAKEGRID | 36.90% / 30.73% | 23.08% / 18.55% |
| CTH-like | 3.84% / 2.73% | 3.16% / -0.51% |
| W7-X positive flux | 6.77% / 23.70% | 6.15% / 22.14% |

These are median paired percentages, not ratios of the separate medians.
Ada CTH solver time is inconclusive; neither Ada CTH nor Ada mgrid Solovev has
an established process-wall gain. Solovev's two rows are field-setup paths for
the same geometry. W7-X's original `phiedge=-1.74` rejects against the pinned
field in both variants; the separately predeclared positive-flux fixture uses
`+1.74`. No original-W7-X speedup is claimed. All 180 attempts remain: 144
completed solves including warmups and 36 sign rejections. Completed counts
remain 389/636 for both Solovev forms, 198/226 for CTH, and 1733 effective
iterations for positive-flux W7-X. Every successful pair has identical native
state, published fields and numerical reports within its architecture.
All 1281 dump files per variant/GPU match, including full stage/controller
traces. The original float Solovev/CTH failures remain unqualified; float kernel
equivalence alone does not establish float solve convergence.

## v1.5 trajectory: optional Newton and rejected alternatives

The [complete 19-case study](data/v1.5/docs/axisymmetric-newton-qualification.md)
and [ADR-0016](data/v1.5/docs/adr/0016-opt-in-newton-corrections.md) retain the
original five-pair results and all 15-pair uncertainty-selected follow-ups.
The operator is the negative derivative of the frozen preconditioned descent
map, using forward differences with maximum physical coefficient perturbation
1e-6 and GPU GMRES with 32 steps/basis vectors. Trial scales 1, 1/2, 1/4, 1/8
must preserve valid geometry and reduce the sum of invariant residuals by more
than 5%. Every original component tolerance, grid and cap remains in force.
The flag supports only fixed-boundary axisymmetric double and is off by default.

The original 16-case matrix was committed before timing; a separate three-case
finite-pressure supplement followed. All stage tolerances are 1e-16, grids
5/11/55 except the declared 5/11/99 case, and caps 1000/2000/2000. The family
contains correlated Solovev variations, not 19 independent devices. CPU 8,
precise double, CUDA 12.1/sm_61 on TITAN Xp and CUDA 12.9.41/sm_89 on RTX 4090;
clocks remain unlocked. Intervals are exploratory per-case 95% paired bootstrap
intervals, 20,000 resamples, seed 20260908, with no multiple-comparison adjustment.

Prescribed-current Solovev improves from 142.061→114.822 ms on Pascal and
97.442→83.310 ms on Ada: 19.21% [19.11,19.63] and 14.51% [11.08,14.98].
Outer stages change 249/211/344→152/103/200, with 136 extra equilibrium
evaluations included in timing. Original Solovev changes 754→484 outer passes
plus 136 evaluations, giving only 10.39%/3.96% solver-time reductions. These
intervals include operator/Newton construction and every probe/trial/rollback,
but exclude outer stage construction, interstage transfer, process startup
and output. They are not whole-process or production-flag timing claims.

Fresh Ada follow-ups confirm negative paired gains for cuMES circular
(-3.11%), mpol=4 (-3.53%), VMEC++ circular (-3.77%) and the 5000 Pa linear case
(-0.71%). Their intervals exclude zero. All four still save outer passes.
Selection used initial interval width above 10 percentage points, regardless
of gain sign; it did not select only favorable cases. Initial and follow-up
samples remain separate. The complete rows and intervals are in the frozen study.

All 982 configured solves converge and pass native/checkpoint checks. All
76 Newton-disabled checkpoint replays converge at the original final tolerance
in one pass. Twelve states are bit exact; 64 only canonicalize 68 dependent-axis
signed-zero entries. No active/boundary/nonzero value changes a bit. Maximum
candidate/baseline diagnostics are R/Z displacement 6.7212e-7 m, lambda relative
L2 3.4835e-6 and native B² relative L2 7.0656e-8. Seven independent VMEC++
references converge; maximum Newton/reference R/Z displacement is 6.7807e-8 m.
These equal-coordinate diagnostics do not impose a blanket equivalence bound;
VMEC++ B² equivalence was not assessed. The CUDA 12.1 graph-initcheck pivot-scale
report occurs with Newton disabled too and remains unresolved in the archive.

Rejected residual extrapolation, lambda/RZ block corrections, full 3-D Newton
and two-level FAS are documented in the frozen experiment reports. The FAS
8-smooth/period-100 screens cost 68.315→74.665 ms for Solovev and
1695.322→1796.907 ms for W7-X on Ada, including extra coarse/trial work but
excluding corrector construction. These single screens are not paired gains.
The explicitly added final-grid CLI option and its qualification were removed
in `a93db11`; schedule-changing experiments are not shipped optimizations.

### Complete the v1.4 baseline without rewriting the old measurements

Historical poloidal-only float/cache slides retain their original numbers.
The [v1.4.1 report](data/v1.5/docs/w7x-single-grid-float.md) adds four m=1
toroidal position sums and split odd scaling, retaining single-word higher
mode products. Tight-checkpoint median pass costs are 546.79 μs for prior
poloidal compensation, 562.85 μs for the retained correction and 660.94 μs
for full odd float-float, from three alternating 300-warmup/500-pass runs.
The old path does not complete the same ns=99 cold solve; per-pass ratios are
not solution-time speedups. Released single-grid convergence takes 1354
effective passes and multigrid 149/277/311 at 1e-5, with one-pass replays.
Device arithmetic is float/float-float; native geometry remains default.
Double-double compensated geometry remains a separate opt-in accuracy/cost
choice, not a new native-double speedup. No float result is compared as
accuracy-matched to W7-X double at 1e-12.

## Local reproduction on 2026-09-07: protocol and limits

The reproducible raw evidence is in [data/local/](data/local/), with exact
environment in [environment.json](data/local/environment.json) and all samples
and statistics in [summary.json](data/local/summary.json).

- Date: 2026-09-07 local time; NVIDIA TITAN Xp sm_61, driver 580.173.02,
  CUDA toolkit/runtime 12.1; host compiler g++-12; Release precise double.
- Four detached worktrees: `7c6508a` (parent), `5379fca` (CUDA bundle),
  `f7036ab` (v1.1), `17867d5` (v1.2). No production source edits.
- Native sm_61 build, no fast math, NetCDF/HDF5/vacuum/magnetic-coordinate
  disabled. The v1.2 B-spline dependency is exactly
  `e7f5207680f5305ef51326181409febda0295b57`, extracted from the local git object.
- Fixed harness: 1000-pass preheat per shape; six alternating before/direct/graph
  triples, 50 warmup + 300 timed passes each. Medians of per-run medians.
  `ftol=0` fixed window, so controller/restart behavior is still present. A cold
  fixed window is not an equilibrium convergence measurement.
- CLI: same physical JSON for both releases; single-grid variants retain only
  the final ns/niter/ftol entries. One untimed alternating pair per case precedes
  five timed pairs. All CUMES_* environment overrides removed. Process wall
  includes final output. Checkpoint tests are separate untimed runs.
- CPU pinned to the first allowed core (recorded in environment.json).
  Clocks were not locked and an existing graphical GPU process remained active.
  No slow sample was discarded. This is not a controlled-clock full acceptance
  campaign, and no new free-boundary or mixed-float run is claimed.
- Within-run p95 is reported by the harness. Across-run MAD/ranges summarize
  the run medians; they are not the same quantity. Paired bootstrap percentile
  intervals use 20,000 resamples (seed 20260907) of matched run indices and the
  ratio of medians. With only five/six samples they are descriptive, particularly
  when a single slow process launch changes the bootstrap distribution.
- Fixed hashes are identical across all three local variants. W7-X local hash
  is `9bd652f7efcea4df`, different from the archived RTX session; no cross-stack
  identity is asserted. Solovev is `3c09fd3260b003a8`.
- All release counts reproduce. Local Solovev v1.2 final FSQR prints 9.972e-17,
  while the archived record prints 9.973e-17. The deck labels local and archived
  values separately rather than asserting cross-stack residual bit identity.
- Both v1.2 checkpoints replay in one final-grid pass. The new gate checks the
  logged count and residual triple; archived exact checkpoint/state comparisons
  are attributed to their ADRs. No fresh independent VMEC++ solve is claimed.

### New results at a glance

| Fixed shape | Before μs | Optimized direct μs | Optimized graph μs | Combined reduction |
| --- | ---: | ---: | ---: | ---: |
| Solovev ns=55 | 162.660 | 165.155 | 152.375 | 6.32% |
| W7-X ns=99 | 1739.590 | 1573.820 | 1561.670 | 10.23% |

| CLI case | v1.1 median s | v1.2 median s | Wall reduction | Passes |
| --- | ---: | ---: | ---: | --- |
| Solovev multigrid | .465130 | .443208 | 4.71% | 906→754 |
| Solovev single | .404368 | .438471 | **−8.43% (slower median)** | 533→354 |
| W7-X multigrid | 7.258995 | 5.599446 | 22.86% | 5505→4106 |
| W7-X single | 6.174045 | 5.313453 | 13.94% | 2953→2465 |

Solovev multigrid includes one v1.2 1.3146 s sample; W7-X single v1.1 ranges
5.5080–11.5251 s. Solovev wall reduction confidence intervals cross zero;
the single-grid median is slower despite 33.58% fewer passes. The W7-X multigrid
wall reduction interval is [21.77%, 23.45%]. Prefer that stable measured example
for the release wall-time headline, and deterministic passes for short cases.
Do not multiply archived RTX kernel/iteration gains by these pass reductions.

The residual chart joins printed W7-X single-grid samples. It plots
max(FSQR,FSQZ,FSQL) on a log axis against the reported iteration index. It does
not invent unlogged residual points, wall timestamps, or restart details.
