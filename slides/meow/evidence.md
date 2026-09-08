# Evidence ledger

Reviewed 2026-09-08. All displayed objectives are **‖r‖²**, twice the TRF cost.
All times in the main comparison are complete-process wall times in seconds.

## Source identity

Current code was checked against meow
`de1b324` (`main`, clean at research time). Its integration pins cuMES
`f61c959334bb62e14c049c66335580b45f63610d`. The sibling cuMES working tree's newer
HEAD is not the dependency used in the new measurements.

The primary publication is Matt Landreman and Elizabeth Paul,
[Magnetic Fields with Precise Quasisymmetry for Plasma Confinement,
PRL 128, 035001 (2022)](https://doi.org/10.1103/PhysRevLett.128.035001), also
[arXiv:2108.03711v2](https://arxiv.org/abs/2108.03711v2).
The reference data are [Zenodo v2, DOI 10.5281/zenodo.5645413](https://zenodo.org/records/5645413),
locally extracted as `../20211102-01-precise_quasisymmetry_zenodo/`.
The dataset contains the original SIMSOPT, VMEC, and BOOZ_XFORM code and outputs.
The deck concerns the vacuum QA/QH cases without an added magnetic-well target.

The manifest [data/source-manifest.json](data/source-manifest.json) identifies
108 source artifacts by path, size, and SHA-256, including the original wouts
used in each derived figure. Large equilibrium binary and NetCDF files remain
in the sibling archives. All data required to redraw the presented figures are
included here.

## Code and numerical contracts

| Slides | Source at meow de1b324 | Verified behavior |
|---|---|---|
| 3–5 | `include/meow/trf.hpp`, `src/trf.cpp` | Independent C++20/Eigen dense TRF; optional bounds, Coleman–Li scaling, trust-region solve, acceptance and stopping |
| 3–4, 7 | `include/meow/cumes/boundary_parameterization.hpp` | Absolute RBC/ZBS variables, fixed RBC(0,0), 4k(k+1) DOFs, signed-to-folded tangent mapping, m=0 FD policy |
| 3, 6–7 | `apps/cumes_landreman_optimize.cpp`, `LandremanResidual` | Cached residual/center; fixed-boundary solve; analytic, FD and parallel callbacks; failed-trial barrier; accepted axis and checkpoints |
| 6–7, 20 | `include/meow/cumes/quasisymmetry_target_jvp.hpp`, `plasma_size_target_jvp.hpp` | meow's analytic target chain applied to cuMES materialized field/profile tangents |
| 13–14 | `src/trf.cpp`, `LandremanResidual::parallel_finite_difference_jacobian` | Safeguarded rank-one secant reuse and independent column workers |
| 19–23, 34 | `examples/landreman/`, `docs/relaxation-rundown.md` | Separate equilibrium and optimization JSON; strict schema; target, steps, continuation, and output owned by rundown |
| 20–21 | `quasisymmetry_target.hpp`, `fourier_resampling.hpp`, `scripts/evaluate_landreman_qs.py` | Archived invariant QS residual, surface quadrature, target resampling, weights, and scalar residuals |

The cuMES API is `EquilibriumSolver::solve`, `EquilibriumLinearization`,
`solve_boundary_tangent`, and `materialize_tangent`. Implicit differentiation
solves F_u u_j = −F_xj using analytic force JVPs and a retained iterative session;
meow supplies the target JVP. This is a forward directional method, not an
adjoint, and does not remove linear cost proportional to the number of columns.
Current meow uses relative tangent tolerance 5e−6, absolute 1e−11, restart 300,
and cap 1000, with cold FD for m=0 and unsuccessful tangent columns. This differs
from the early benchmark's 1e−4 setting.

The physical QS expression, numerical residual vector, and Boozer Fourier
amplitudes are different quantities. The 63×64 target grid spans one field
period at each of 11 surfaces s=0,0.1,…,1. The 44,352 QS residuals are supplemented
by aspect, and by mean iota only for QA construction. Surface weights act on
squared residuals. Linear half-grid interpolation/extrapolation, including the
axis and edge, matches the original target; it is unrelated to the solver's
multigrid prolongation method. QH's per-period helicity −1 means physical N=−4.

## Archived performance evidence

The investigation is frozen in
[data/sources/meow/docs/landreman-paul-reproduction.md](data/sources/meow/docs/landreman-paul-reproduction.md).
Its dated plans and early conclusions are superseded by later results; the
deck reads through the corrected tangent and worker/Broyden qualification.

### Tangent experiments: slides 8–12 and 16

| Campaign | meow | cuMES | Local raw evidence |
|---|---|---|---|
| Early, 2026-09-02 | `8eac01e82b8d1eaa508d53afd8acae2b2f223740` | `4bf4d881943a73835a090702689f5fa0e4eb3789` | [data/archived/early-tangent](data/archived/early-tangent) |
| Corrected, 2026-09-03 | `fc7e66b` | `f1a3ed7`, including `8c61395` | [data/archived/corrected-tangent](data/archived/corrected-tangent) |

Hardware: NVIDIA TITAN Xp, driver 580.173.02, Release double precision. Runs
were sequential complete QA modes 1→4 or QH modes 1→5 from the sparse analytic
boundaries. Both methods received the same deterministic QA chiral seed,
target, stage schedule, equilibrium gate, and accepted-axis policy. Per-iteration
equilibrium serialization was disabled. The current presentation **did not
repeat** these long optimizations. Each timing is a single recorded run, with
no confidence interval, spread estimate, or claim of a repeated median.

| Case | Cold FD wall / objective | Early tangent wall / objective | Corrected tangent wall / objective |
|---|---|---|---|
| QA | 1537.26 / 5.94683530877e−7 | 473.29 / 6.29151469581e−4 | 2628.35 / 1.34526695087e−6 |
| QH | 3262.78 / 5.36939265810e−5 | 1387.86 / 1.28435967198e−3 | 3516.16 / 9.71167722426e−5 |

The cold controls are the September 2 records reused in the corrected campaign,
not new paired runs of the corrected dependency. Early raw speeds are 3.248×
and 2.351×, with 1058× and 23.9× worse objectives. Corrected raw speeds are
0.585× and 0.928×, with 2.26× and 1.81× worse objectives. **Neither campaign
qualifies a tangent optimization speedup.**

All available result JSON and time files are copied. The two early QA `run.log`
files are absent from the local archive: their objective values come from the
frozen meow investigation, while their times and boundary endpoints have raw
artifacts. The QH and corrected raw logs are present. `summary.json` marks this
missing-log provenance explicitly. No work counters are invented for early QA.

QH early counts are sums of the per-stage `finished` records: tangent has 218
accepted iterations, 253 equilibrium evaluations, 474719 nonlinear iterations,
223 Jacobians, and 635648 linear iterations. FD has 88, 4303, and 12203424
respectively. Hence 17.008× fewer equilibrium evaluations and 25.707× fewer
nonlinear iterations; these are not wall-speed estimates.

Tangent correction/qualification numbers come from the investigation's later
sections: cuMES connected tangent constraint buffers (`8c61395`) and initialized
dual de-aliasing scratch (`f1a3ed7`). The corrected centered Solovev oracle gives
0.228% spectral-state and 0.514% published-field differences. QH residual
columns still differ by 2.95–11.68%, while hybrid objective directional
derivatives differ by at most 0.705%. Tightening relative GMRES to 1e−8 leaves
7.77% worst column error. These focused diagnostics are archived reports, not
newly repeated tests. The nonlinear target chain itself was much closer in the
isolation experiment, so zeroing lambda or changing the target is not supported
as a correction.

The historical CLI used positional arguments, for example from the corresponding
meow checkout (the actual `/usr/bin/time` command is preserved in `time.txt`):

```bash
./build-cumes-tests/cumes_landreman_optimize \
  examples/landreman/qa_analytic.json qa-construction RESULT.json \
  0 1 4 0 '' analytic
```

QH uses `qh_analytic.json qh-construction`, ending at mode 5. Cold controls select
`finite-difference`. Current JSON commands are intentionally documented
separately; do not pass historical positional arguments to current meow.

### Broyden and worker comparisons: slides 13–16

Implementation lineage: `95afe0d` introduces safeguarded Broyden;
`0b33846`/`e314677` record aggressive construction results; `f5275bc`/`ea3580a`
implement/qualify concurrent FD; `b1fda33`/`33c6866` combine parallel refresh and
Broyden; `be8bb6a`/`5de945d` add/promote four workers. Full QA/QH four-worker
results are documented by `2da8c95` and `487380a`, then reviewed in `dca3ccd`.

| Strategy | QA wall (s) | QH wall (s) | QA objective | QH objective |
|---|---:|---:|---:|---:|
| Historical cold FD | 1537.26 | 3262.78 | 5.94683530877e−7 | 5.36939265810e−5 |
| Serial aggressive Broyden | 1209.77 | 2681.44 | 4.09894575473e−7 | 3.99555777572e−5 |
| Two workers + Broyden | 800.78 | 1741.81 | 4.09894575473e−7 | 3.99555777572e−5 |
| Four workers + Broyden | 563.79 | 1232.17 | 4.09894575473e−7 | 3.99555777572e−5 |

The [four-worker raw campaign](data/archived/four-worker-broyden) includes logs,
GNU time records, and every stage checkpoint. Serial and two-worker values are
preserved in the investigation document. As in the tangent campaign, these are
single full-run timings on TITAN Xp in Release double, not a repeated statistical
benchmark. The exact dependency/executable identity of the four-worker runs is
not recoverable from their retained time files; implementation commits and the
recorded workload are known. Do not imply that the September 8 pinned build was
used for those September 4 timings.

Four-worker QA: 77 accepted steps, 2130 equilibrium evaluations, 4450488 nonlinear
iterations, 35 secant updates, peak RSS 325656 KiB. QH: 113, 3520, 9876526, 52,
356088 KiB. The corresponding two-worker runs have the same work and endpoints.
This supports a scheduling speed comparison: 1.420× QA, 1.414× QH. Comparison
with historical cold FD also includes a different optimization trajectory:
2.727× QA, 2.648× QH, with lower objectives. Neither gain is attributed to
analytic cuMES tangents.

The first mode has eight columns. Separate worker diagnostics report serial /
2-worker / 4-worker wall times QA 2.829 / 1.263 / 0.867 s and QH 2.282 / 1.035 /
0.735 s, with bit-exact matrices. Eight workers failed the QA convergence gate;
QH remained exact but regressed 0.718→0.789 s in that different session.
Those diagnostic values come from the frozen investigation. No ratio from that
session is combined with the full run to manufacture an additional speedup.

## Construction evidence: slides 19–27

[data/archived/accepted-axis](data/archived/accepted-axis) contains the original
meow construction logs and stage boundaries. Relevant commits are `dee632f`
(construction FD steps), `ce1f6e0` (accepted-axis continuation), `ae309f9` and
`d46c5ba` (completed QA and QH), followed by `f7f8f8d` (chiral QA seed).

| Case | k | meow accepted steps | meow objective | Landreman construction objective |
|---|---:|---:|---:|---:|
| QA | 1 | 23 | 9.62215079953e−3 | ≈9.6408e−3 |
| QA | 2 | 18 | 1.40881439229e−4 | ≈1.5611e−4 |
| QA | 3 | 13 | 3.74704919717e−6 | ≈3.5144e−6 |
| QA | 4 | 7 | 4.57544450735e−7 | 2.92794425995e−7 |
| QH | 1 | 21 | 1.40503531818e−1 | ≈1.39906e−1 |
| QH | 2 | 32 | 1.91355839667e−3 | ≈2.8614e−3 |
| QH | 3 | 15 | 1.20166888048e−4 | ≈1.79572e−4 |
| QH | 4 | 8 | 7.30668510539e−5 | ≈4.1688e−5 |
| QH | 5 | 12 | 5.36939265810e−5 | 3.07486398207e−5 |

The Landreman accepted-endpoint values above are taken from the frozen
investigation's comparison with the original optimizer record. Fresh evaluation
of the retained stage-transition wouts gives slightly different values because
these files can represent a final finite-difference sample. Both are preserved:
plots/tables use the accepted-endpoint ledger; surface renderings use the retained
VMEC boundary coefficients. The original SIMSOPT `.dat` records were also
checked to confirm their objective scale, including perturbed samples.

Do not mix the early QA accepted-axis construction endpoint 4.57544e−7 with the
later timing control endpoint 5.94684e−7. The former starts exactly axisymmetric;
the latter is paired with tangent experiments using the shared 1e−4 seed.
QA accepted-axis construction totals 61 accepted steps plus four initial stage
equilibria; QH totals 88 plus five. Broyden endpoints have different trajectories.

Original construction source directories below the Zenodo `calculations/
20210704-01-simsopt_new_quasisymmetry_metric/` directory:

- QA `20210704-01-021_QA_multiple_surfaces_relStepScan_A6_iota0.42/abs_step_1.00e-07_rel_step_3.16e-03_forward/`
- QH `20210704-01-039_QH_multiple_surfaces_relStepScan_A8/abs_step_1.00e-07_rel_step_1.00e-03_forward/`

QA reference surface uses saved wout `000248`; QH uses `000276`. Middle surfaces
use the meow `latest.json` accepted-axis construction endpoints. QA is rigidly
rotated by π/nfp around the toroidal axis to align the arbitrary phase selected
from its axisymmetric seed; QH is unrotated. Colors/shading represent geometry
only. No coefficient-identity, new field-line, or coil-reproduction claim is made.

The four-stage/five-stage constructions complete. The available independent
final-refinement logs under `../opt-qa-test` and `../opt-qh-test` complete mode 4
only. Full independent final-refinement completion is not established here.

## New reference evaluation and GPU solves: slides 28–31

`collect_evidence.py` imports the frozen meow VMEC evaluator and re-evaluates the
original wouts without running VMEC. It preserves the 11 weighted/unweighted
surface values, aspect, mean iota, and resolution in
[data/reference/metrics.json](data/reference/metrics.json).

| Final-refinement target | VMEC terminal (ns=75) | VMEC published re-solve (ns=201) | New cuMES pinned re-solve (ns=201) |
|---|---:|---:|---:|
| QA objective | 1.31838917076796e−6 | 2.5929305644895486e−5 | 2.600088352343219e−6 |
| QH objective | 3.4476418370230285e−5 | 4.146057373305437e−5 | 6.6731562953733795e−5 |

The terminal totals reproduce the previously frozen SIMSOPT values to their
printed precision. Terminal files are `wout_nfp2_QA_000_000063.nc` in run 050's
weight-30 refinement directory and `wout_nfp4_QH_000_000090.nc` in run 059's
weight-2 refinement directory. Published files are the `configurations/new_QA`
and `configurations/new_QH` wouts. A direct coefficient comparison found maximum
boundary differences of 2.776e−17 between each terminal and published file;
their fields and resolutions differ. The larger high-resolution QA target value
is the measured value of that particular archived wout. It is not replaced by
the terminal value or presented as evidence of physical accuracy ordering.

The new GPU campaign is in
[data/local/published-boundaries-20260908](data/local/published-boundaries-20260908).
Commands, input/executable hashes, source revisions, the CMake cache, and
diagnostic wall times are recorded in `environment.json`. Measured hardware:
TITAN Xp, driver 580.173.02, CUDA compiler 12.1, Release `verify-double`, float off,
B-spline prolongation enabled. At the pre-run check the GPU was idle (P8, 0%
utilization, 318 MiB allocated); the existing graphical process was left running.
QA and QH were run sequentially. The existing build reported `ninja: no work to
do` for both relevant targets before measurement.

| New solve | QA | QH |
|---|---:|---:|
| Total / final-stage iterations | 5616 / 463 | 5766 / 976 |
| FSQR | 9.988055103947057e−13 | 9.968774355012988e−13 |
| FSQZ | 5.178669538612113e−13 | 8.020845512858953e−13 |
| FSQL | 9.355144023657134e−14 | 1.536532211941600e−13 |
| Aspect | 6.000007793589530 | 8.000011266147551 |
| Mean iota | 0.419325608826590 | −1.243299682409723 |
| Weighted QS | 2.600027612305454e−6 | 6.673143602765316e−5 |
| Unweighted QS | 1.368690355924601e−7 | 3.933788525126665e−5 |

Both solves pass the explicitly adapted 1e−12 force gate. The original published
VMEC inputs requested 1e−17/2e−17; meow imports clamp these to 1e−12 and import
the archived axis. Work allowances are explicit. QH selects Catmull-Rom radial
transfer; QA uses the default. These are current pinned-build accuracy results,
not a reproduction of the earlier investigation's cuMES cross-check values
(1.78081249318e−6 / 4.72745833797e−5). The cause of this revision-to-revision
target difference was not isolated. Force convergence does not imply identical
target quality. No GPU speed comparison is made from the one-shot diagnostics.

## Reference Boozer figures: slides 32–33

`data/reference/boozer.json` records selected arrays from the **original**
`boozmn` files: all edge cosine coefficients and the largest nonsymmetric
amplitude normalized by local B00 on each of 200 half-grid surfaces.
The edge is s=0.9975, not an extrapolated s=1 sample. QA excludes n=0 from its
nonsymmetric set; QH excludes physical n=−4m. Across the retained surfaces the
maxima are QA 4.757785944611692e−5 and QH 4.822433734306845e−4.

These are newly rendered reference data. They are not a new BOOZ_XFORM run,
cuMES Boozer output, or a replacement for the invariant QS residual objective.
`scripts/plot_results.py` reconstructs the full retained edge Fourier sum. The
deck makes no assertion of a matched new cuMES spectrum, SPEC Poincare map,
island suppression, or particle-orbit confinement.

## Validation scope

Both pinned GPU equilibrium checks ran successfully. The original terminal
VMEC target totals, current CLI help, and both supplied four-worker JSON
rundowns were checked. Figure/HTML generation uses saved evidence. Every slide
was rendered at 1600×900 and 1280×720; screenshots/contact sheets were reviewed,
including chart labels and the executable-command panel. Local math and image
loading, navigation, hashes, overview, notes, help, mobile scroll/swipe behavior,
and 16:9 print layout were checked by `scripts/validate_deck.py`.

The machine-readable browser report is [data/validation.json](data/validation.json).
`node --check` and whitespace checks cover the authored files; vendored KaTeX
was copied with its license unchanged. No solver implementation was changed,
and no full solver test suite or historical optimization was rerun for the deck.
