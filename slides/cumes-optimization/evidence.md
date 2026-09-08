# Evidence ledger: optimization during cuMES development

This deck separates implementation/execution improvements from changes to the
convergence trajectory. It audits the CUDA history reachable in
`dc0d0c4..194415d`: 197 commits including merged ancestry. `dc0d0c4` marks design
closure; reader/safety closure finishes at `56aa1a4`. Phase 6 numbers are clearly
marked as earlier background. The independent, unmerged `webgpu` branch is outside
this CUDA deck. Optimizer policy in `../meow` is not a cuMES equilibrium change.

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
- [Performance ledger at reviewed HEAD](https://github.com/12ff54e/cuMES/blob/194415d/docs/performance.md).
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

## New local reproduction: protocol and limits

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
