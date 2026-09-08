# Optimization commit inventory

Audited every commit reachable in `dc0d0c4..194415d` (including merged history), not just commits named perf. `dc0d0c4` closes the design overhaul; safety/reader closeout ends at `56aa1a4`. Earlier Phase 6 results are explicitly background. Release markers: `dbb0f8e` v1.0, `f7036ab` v1.1, `17867d5` v1.2, `750d6a4` v1.3. The independent, unmerged `webgpu` branch is outside this CUDA deck.

Total commits inspected: 197. The complete file-level inventory is [commit-audit.tsv](commit-audit.tsv). The table below includes retained changes, rejected experiments, relevant supporting work, and measured tooling. Feature-only sensitivity construction commits remain in the complete inventory.

| Commit | Category | Finding |
| --- | --- | --- |
| [5310769](https://github.com/12ff54e/cuMES/commit/531076906f491e491f38b5462eb98a2c75794c49) | tooling | Batched IFFT and process-parallel figure rendering; 42 to 17 s recorded |
| [2dea659](https://github.com/12ff54e/cuMES/commit/2dea659453d2d1fff5ed6fc6d196a80e5cd634d8) | execution | Compile verification event messages out of non-dump builds; no isolated timing |
| [5379fca](https://github.com/12ff54e/cuMES/commit/5379fca726afbe6c58d71184d68a0805106ce21e) | execution | Production CUDA graphs; parallel Jacobian statistics; full-theta inverse mapping |
| [933b80a](https://github.com/12ff54e/cuMES/commit/933b80a13b4a62fc67967ed9134d78c1a6b48dbb) | execution | Vacuum dependency be6d6cd: contiguous Makegrid response storage; no isolated timing |
| [5d5e380](https://github.com/12ff54e/cuMES/commit/5d5e380381981fa204d592717e796b4e534cea46) | execution | Capture scientific fields only on finest stage; 3 to 1 captures for three-grid inputs |
| [e507b36](https://github.com/12ff54e/cuMES/commit/e507b36372013f26d06959775a44ab2422e4fd55) | execution | Vacuum dependency 110748f: parallel Makegrid; no isolated timing |
| [fa119ea](https://github.com/12ff54e/cuMES/commit/fa119eaa798bf31cdc2d8b9d167250b7d689cc0d) | execution | Host snapshot spans for Boozer; no copy of six spectral/seven field arrays; not GPU zero-copy |
| [7541ff6](https://github.com/12ff54e/cuMES/commit/7541ff61091b1db07bd12f413172e137ca93c26f) | trajectory | Single-grid one-shot step recovery |
| [774363f](https://github.com/12ff54e/cuMES/commit/774363fd197e7ca095a5b7049568eeba77a2a9d1) | trajectory | Extend recovery to each fixed-boundary stage |
| [f270790](https://github.com/12ff54e/cuMES/commit/f2707901ce26a4406d4a1e94f3272cd8cbe29a59) | trajectory | Fixed 3-D shaped cold start |
| [3d08aef](https://github.com/12ff54e/cuMES/commit/3d08aef73e05e5b35e2353b2d6a564bf8897512d) | trajectory | Coarse axisymmetric envelope |
| [27c5e39](https://github.com/12ff54e/cuMES/commit/27c5e391656a66c591c2e64f9a4d93875f9357c0) | trajectory | Axisymmetric initial-step policy |
| [9f4d7c1](https://github.com/12ff54e/cuMES/commit/9f4d7c128864730aa284066b3e90339cbc92ca99) | trajectory | Geometric axisymmetric lambda seed |
| [355c10c](https://github.com/12ff54e/cuMES/commit/355c10c9b8671adf47a430a17998e1c34dd8439f) | trajectory | Free-boundary cold predictors |
| [57f86b7](https://github.com/12ff54e/cuMES/commit/57f86b7aeadb32d3701be522916a8a6586057814) | trajectory | Coarse free-boundary step scaling |
| [f5eeba6](https://github.com/12ff54e/cuMES/commit/f5eeba6e4f5a63b7bf1f4faae1e5e6ef438d76d6) | trajectory | Earlier vacuum activation |
| [d2d8b81](https://github.com/12ff54e/cuMES/commit/d2d8b81333f688c380a96895d93a42d9c5302712) | evidence | Free-boundary paired timings |
| [cad3daa](https://github.com/12ff54e/cuMES/commit/cad3daada71dc4fbd1618d5ea7b7cae206ae0b37) | measurement | CUDA stream elapsed-time reporting |
| [6d9e593](https://github.com/12ff54e/cuMES/commit/6d9e593e85fc4ef013514ed4805444d74eaa7549) | trajectory | Single-grid 3-D envelope 0.129 |
| [1a10037](https://github.com/12ff54e/cuMES/commit/1a10037e414db76ad38d6bbc46fa16010e595b84) | trajectory | Catmull-Rom multigrid transfer |
| [b13cd87](https://github.com/12ff54e/cuMES/commit/b13cd873c9ae48cf7d81e15408e2eb97633933bc) | both | Global B-spline transfer matrix applied on GPU |
| [12435fa](https://github.com/12ff54e/cuMES/commit/12435fa16c427ceb07b2a11a4534f92d9987116a) | execution | Prepare transfer matrices asynchronously during coarse solve |
| [f79214c](https://github.com/12ff54e/cuMES/commit/f79214cf11344f9a3e122f0fc7384498f7fb40ac) | support | Pin direct B-spline dependency e7f5207 |
| [8a07964](https://github.com/12ff54e/cuMES/commit/8a07964363bfc6c80be226aa4213aacda1417a84) | support | Portable dependency URL |
| [05abfde](https://github.com/12ff54e/cuMES/commit/05abfdeb0e8b89d98b7453b0d50e7d58f39ec977) | support | Relative dependency protocol |
| [4658ea0](https://github.com/12ff54e/cuMES/commit/4658ea007718aac917e8a6f1c5a8aa75148159a9) | support | Centralize tuning constants; no separate speedup |
| [2d07d47](https://github.com/12ff54e/cuMES/commit/2d07d47a974a741941443a9f57b47acc264868e3) | sensitivity | Retained residual JVP session; no isolated timing |
| [0064e98](https://github.com/12ff54e/cuMES/commit/0064e98aa8d3de725b6c5c4280a18df61712445f) | sensitivity | Matrix-free equilibrium tangent solve; not nonlinear convergence optimization |
| [c1abf20](https://github.com/12ff54e/cuMES/commit/c1abf20307e426032729e63f515c45d13719f85c) | sensitivity | Right-preconditioned retained tangent GMRES; different linear problem |
| [d0f408b](https://github.com/12ff54e/cuMES/commit/d0f408b0805a760ebfb3e5985e26db49288d0caa) | execution | Coordinate concurrent graph capture and device-wide stage fence |
| [6106e0b](https://github.com/12ff54e/cuMES/commit/6106e0bbb31015a335238db54f81ccddd9c93ffa) | measurement | Solve phase timings |
| [5720583](https://github.com/12ff54e/cuMES/commit/5720583bda38fe87e536fb0905b2326da477dd5e) | measurement | Stage lifecycle timings |
| [480c91d](https://github.com/12ff54e/cuMES/commit/480c91da549699c06c4096f869fe49ca2defefdb) | rejected | Resource reuse ceiling too small |
| [17d731c](https://github.com/12ff54e/cuMES/commit/17d731cc97f3e058f6bef554376a750a931a5551) | rejected | Transform launch tiles below 5% acceptance gate |
| [b0d6758](https://github.com/12ff54e/cuMES/commit/b0d67580b81c922990650d3a8daf871df87221da) | rejected | Inverse pack remapping / derived-table load experiments |
| [d36025f](https://github.com/12ff54e/cuMES/commit/d36025f56d46c44331e41a3987348084285b9c20) | rejected | Concurrent tile tuning below acceptance gate |
| [a7f605d](https://github.com/12ff54e/cuMES/commit/a7f605deaec07badc9bc00e0f79712b984ec3eac) | trajectory | Very coarse fixed 3-D seed -0.10 for initial_ns <= 12 |
| [f61c959](https://github.com/12ff54e/cuMES/commit/f61c959334bb62e14c049c66335580b45f63610d) | evidence | Very coarse predictor qualification |
| [a880051](https://github.com/12ff54e/cuMES/commit/a88005177892f84462d0b050bacdc9e08f3cbca7) | accuracy | Float reference-plus-displacement radius storage |
| [3cebb49](https://github.com/12ff54e/cuMES/commit/3cebb495fcb5c5bab634a698905fc49bf3a26440) | accuracy | Selective compensated odd R/Z reconstruction |
| [bd01518](https://github.com/12ff54e/cuMES/commit/bd01518cf58a6e6dd65f4a89c47642696d7bced5) | accuracy | Default float 3-D radius displacement representation |
| [194415d](https://github.com/12ff54e/cuMES/commit/194415df8590e7523048b3904e1a59b07e789148) | execution | Cache immutable radius reference once per stage |
