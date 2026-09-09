# RTX 4090 optimization validation, 2026-09-08

Baseline: f0c17f76bcdc319f88c4c9dd0f89e7364bf7bc91. Candidate: inverse specialization plus weighted forward basis, equivalent to commits 66a557a and 21b6043 before whitespace formatting. Exact tested sources and executable SHA-256 values are recorded in extracted/results/build-identity.json and preserved remotely.

Artifacts: final-results.tar.gz contains JSON, logs, timing scripts, build logs, PTXAS/cuobjdump reports, and the Nsight CUDA API summary. Extracted files are under extracted/. Complete binary outputs, checkpoints, dumps, source trees and Nsight trace remain on gervais:/tmp/cumes-speed-rtx4090.YhIlVy. No tracked project files were edited by this validation task.

## Machine and build

Gervais: RTX 4090 GPU 2, UUID GPU-ec158e07-801d-366e-1e7e-68f32df0c75a, 24091 MiB, sm89; Intel Xeon Platinum 8375C, 64 cores, two NUMA nodes. Final runs pinned to NUMA-local CPU8; GPU2 remained exclusive to this task (other GPUs had unrelated jobs). Driver570.169, CUDA12.9.41, GCC12.4.0, CMake3.28.1, Debian13, precise verify-double Release, native sm89, warnings-as-errors. NetCDF/HDF5/vacuum/magnetic-coordinate disabled. BSplineInterpolation headers enabled at revision e7f5207680f5305ef51326181409febda0295b57.

The installed CUDA12.9 toolkit conflicts with Debian13 glibc exception specifications. Both builds used an identical scratch copy of CUDA headers with noexcept(true) added to exactly six declarations: rsqrt, rsqrtf, sinpi, sinpif, cospi, cospif. No system headers or numerical implementations were changed. Build flags contain the scratch include override and no fast-math flag.

## Qualified fixed-iteration measurement

Per configuration and variant, discard one preheat run of100 warmup+1000 measured passes. Then collect16 pairs, alternating baseline/candidate and candidate/baseline order; every recorded run has100 warmup+500 measured passes. Report medians across each run's median and p95. Paired gains are100*(1-candidate_median/baseline_median). Bootstrap20,000 paired resamples with replacement, fixed Python seed8961; statistic is the median paired gain and bounds are sorted bootstrap values[500] and[19499]. Noise is median absolute deviation of per-run medians, divided by their median. No recorded outlier was discarded.

| Case | Baseline median us | Candidate median us | Baseline p95 us | Candidate p95 us | Paired gain | Bootstrap95% | Median MAD baseline/candidate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Solovev ns55 |83.950|83.935|128.340|127.200|0.0179%|[-0.0119%,0.1303%]|0.02978% /0.03574%|
| W7-X ns99 |535.545|500.770|622.805|588.895|6.4963%|[6.4732%,6.5137%]|0.00654% /0.00699%|

All16 pairs per case have identical final hashes: Solovev3d04b6eb619453ff, W7-Xf9feb62e18f39758. Primary data: extracted/results/weighted-runs.json and extracted/results/weighted/summary.json.

A separate12-pair clean incremental comparison (inverse-only, baseline solver graph code, versus inverse+weighted) gave W7-X508.895→500.760us, paired gain1.5879%,95%CI[1.5705%,1.6054%]. All hashes identical. Raw data: extracted/results/weighted-vs-inverse-runs.json.

Arena allocation increases1920B for Solovev(704456→706376) and6144B for W7-X(69318752→69324896); cuFFT work bytes remain0. Setup medians/p95 across final fixed runs were: Solovev baseline1790.6/4892.875us, candidate2220.7/3169.45us; W7-X baseline1695.0/28389.1us, candidate1941.3/4452.7us. The baseline W7-X setup sample includes an isolated104265.1us driver/context initialization outlier. Setup is excluded from iteration measurements.

Unfixed clocks/power: the final fixed experiment began idle at210MHz/405MHz,30C,8.70W and ended2760MHz/10501MHz,39C,100.21W. During full-solve active samples(utilization>50%,200ms intervals), graphics clocks2520–2760MHz(median2760), memory10501MHz,35–46C,55.08–169.18W(median134.67W). The subsequent held-context session sampled32–45C and39.69–169.50W. No GPU clock, power or persistence settings were changed.

## Correctness and resources

Default complete Solovev and W7-X multigrid solves pass compare_bitwise --full with241 and472 identical dump files respectively, exact per-pass residual records and all six final state families. compare_runs used1e-30 tolerances and zero iteration delta; all restarts, residuals and iteration counts match. Default native trajectories are235→193→326(754) and1315→1419→1372(4106), respectively. Every baseline/candidate×direct(dump enabled)/graph checkpoint matches byte-for-byte:

- Solovev SHA256:0a5f2cd4b517c63d517a35602470a00a23dae644ef813174d6f81904014c3d7a
- W7-X SHA256:be15275c1a2a0b1a0f877f1114e28115298906c2d54177574e5fd0c322829477

Diagnostic opt-outs(CUMES_SEED_ENVELOPE=0,CUMES_AXISYM_LAMBDA_SEED=0,CUMES_DELT0=0.9,CUMES_DISABLE_STEP_RECOVERY=1,CUMES_FORCE_CATMULL_PROLONGATION=1) also pass full bitwise comparisons233/532 dumps and baseline/candidate×direct/graph checkpoint equivalence. Their trajectories match their own native baseline exactly; these are not claimed to reproduce the historical documented frozen toolchain counts.

Compute Sanitizer memcheck of test_fourier passes all double and float cases with0 errors, including theta32,mpol2 de-alias plans and typed-view routes. PTXAS reports18 Fourier entry functions with0 stack/spill stores/spill loads. Default fused R/Z inverse kernels remain48 registers; lambda56; forward_reduce remains72; the new setup-only basis kernel uses26 registers. Full ptxas and cuobjdump logs are included.

## Full-process timing limitation and A/A control

Eight pinned default graph pairs preserve all checkpoint hashes. W7-X median CUDA-stream solve time1815.929→1766.226ms, paired gain2.416%,95%CI[-4.512%,5.623%]; process wall2.6184→2.3447s, gain10.315%,CI[0.389%,23.664%]. These samples are too noisy to establish a full-solve percentage. Solovev device67.720→67.5855ms, but alternating candidate-second process runs suffered0.79–1.03s startup outliers.

Nsight locates one such delay in the FIRST cudaMalloc:653.074ms; remaining mallocs are approximately3us. An idle CUDA context did not eliminate it. Crucially, an A/A experiment using the EXACT SAME baseline executable through an alias reproduces the same alternating process anomaly: medians0.2783 versus0.5661s, with alias-second runs0.87–0.90s. Therefore this is not evidence of a code regression, and no robust full-process gain is claimed.

Eight held-context pairs gave W7-X device1812.820→1784.724ms, gain0.682%,CI[-2.863%,3.188%], wall2.5591→2.4343s,gain4.791%,CI[0.836%,19.742%]. A/A, ordinary full and held-context full data are all retained, including hardware samples and Nsight API summary. The reliable performance claim is the6.50% W7-X fixed-iteration reduction; Solovev iteration cost is unchanged within noise.

The idle CUDA context was released. Final GPU2 status:4MiB,0% utilization. No background validation process remains.
