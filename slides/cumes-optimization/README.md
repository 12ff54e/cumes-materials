# Making cuMES faster

A 64-slide web presentation in the existing Technical Blueprint style,
updated through cuMES v1.5.0 (`6756fd6`).
The two main parts cover CUDA execution/data movement and convergence-trajectory
changes. An appendix covers later concurrency, cold-start, sensitivity, and float
work. The history audit includes 244 commits after design closeout, with 81
highlighted changes and evidence records.

Open [index.html](index.html), or read the exported
[64-page PDF](cumes-optimization.pdf). To serve from the repository root:

```bash
python3 -m http.server 8000
```

Visit `http://localhost:8000/slides/cumes-optimization/`. Arrow keys/Space/Page Up/Page Down navigate;
`O` opens overview, `N` opens notes, `F` requests fullscreen, `?` opens help,
and Escape closes overlays. Home/End jump to the first/last slide. Touch supports
horizontal swipes; narrow layouts scroll vertically and wide tables horizontally.
Browser printing uses 16:9 pages. KaTeX and the Libertine/Biolinum fonts load
from pinned CDN URLs. Adjust fonts and sizes in the shared
[`../../typography.css`](../../typography.css); see the
[font-size guide](../../README.md#fonts-and-font-sizes).
For a single-file offline deck, run this from the repository root:

```bash
python3 scripts/export_standalone.py cumes-optimization
```

The exported `exports/cumes-optimization.html` includes all scripts, styles,
fonts, figures, and third-party licenses. Only the first export needs to download
the dependencies. See the repository [README](../../README.md) for deployment.

## Content

- Slides 1–4: scope, version boundaries, measurement definitions.
- Slides 5–20: execution, CUDA graphs, reduction/mapping changes, data movement,
  Makegrid, asynchronous transfer setup, concurrency, rejected experiments.
- Slides 21–29: v1.5 Fourier reuse, vacuum kernels and pinned transfers,
  two-GPU timing intervals, process wall time, failures and exact trajectories.
- Slides 30–48: recovery, seeds, axisymmetric policy, vacuum activation, radial
  interpolation, release comparison, local residuals and checkpoint replay.
- Slides 49–56: v1.5 opt-in Newton, extra work, measured gains and regressions,
  endpoint checks, and rejected block/FAS/three-dimensional corrections.
- Slides 57–62: v1.3/v1.4 appendix, including released v1.4.1 float results.
- Slides 63–64: supported conclusions and evidence access.

Each slide has source references and speaker notes. Consult
[evidence.md](evidence.md) for pinned sources, exact attribution, and limitations;
[the commit inventory](data/optimization-commits.md) links individual changes.
The separate unmerged WebGPU branch is outside this CUDA deck.

## v1.5 release evidence

The update uses archived release qualification, not new solver measurements:

- Fourier: 16 alternating pairs on TITAN Xp and RTX 4090. W7-X steady-pass
  reductions are 5.19% and 6.50%; the Solovev intervals cross zero.
- Free boundary: seven pairs per case/GPU. Solovev mgrid solver intervals fall
  37.01% / 29.69%, and separately declared positive-flux W7-X falls
  6.77% / 23.70%. Process-wall intervals and original-W7-X failures stay visible.
- Newton: 19 predeclared axisymmetric cases, five initial pairs and separate
  uncertainty-selected follow-ups. Prescribed-current Solovev improves
  19.21% / 14.51%, while Ada follow-ups confirm four regressions. The flag stays
  off by default; extra equilibrium evaluations are included in solver timing.

[data/v1.5/](data/v1.5/) freezes the tagged source documents, complete input
manifests, runners, timing records and numerical checks. Its
[provenance.json](data/v1.5/provenance.json) records the origin and SHA-256 of
every imported file. The slide tables read [summary.json](data/v1.5/summary.json),
whose medians were checked against the saved samples/paired reductions.
Different baselines and timing scopes are not combined into a release speedup.

## Local measurements from 2026-09-07

The deck preserves the TITAN Xp / CUDA 12.1 / precise-double comparisons:

- Exact parent/child of CUDA optimization `5379fca`: six alternating
  before/direct/graph triples per shape, 50 warmup + 300 timed passes.
- v1.1 vs v1.2: five timed alternating pairs for Solovev and W7-X, both
  single-grid and multigrid, after one untimed pair per workload.
- Exact input files, raw JSON/logs, GPU provenance, statistics and separate
  final-grid checkpoint replay gates in [data/local/](data/local/).

W7-X multigrid reproduced 5505→4106 passes and 7.2590→5.5994 s median complete
CLI time. Short Solovev timings are noisy and do not establish a wall-time gain;
the single-grid median was slower despite fewer passes. No sample was discarded.
Archived RTX/free-boundary/float results are explicitly labeled separately.

## Reproduce and edit

From this directory, the historical benchmark sequence is:

```bash
python3 scripts/build_history.py
python3 scripts/measure.py
python3 scripts/summarize.py
python3 scripts/build_deck.py
```

Building requires the sibling cuMES git history, its local B-spline dependency
objects, CMake/Ninja, CUDA and g++-12. Measurements require an accessible NVIDIA
GPU. The scripts create detached worktrees, binaries, logs and large solver
outputs in `../tmp/cumes-optimization-slides-20260907` relative to this
repository's root; they do not switch the cuMES working checkout. The scripts
write fresh portable measurement records into this deck, so preserve the current
records first if making a new comparison. The build targets sm_61 for the
recorded TITAN Xp; change that explicit setting for another GPU and report it.

Edit narrative/tables in `scripts/build_deck.py`, then regenerate `index.html`.
The generator reuses the original deck's control markup and the measured summary.
It applies the shared `../../scripts/inline_math.py` formatter to variables and
quantities in prose, tables, and notes. Use `inline(r"...")` for complete or
ambiguous expressions, and `<code>` for literal program text. Chart labels use
the same KaTeX renderer. Regeneration does not rerun measurements.
The checked-in HTML is static and requires no Python to present. `styles.css`
and `deck.js` were copied from the original deck; `optimization.css` contains
the new tables/charts/layouts. The standalone exporter embeds the pinned library
and its license; library binaries are not shipped in the hosted site.

`scripts/audit_history.py` regenerates the complete commit inventory from the
pinned range. `scripts/summarize.py` preserves all samples and calculates median,
MAD, ranges, and paired bootstrap intervals. `evidence.md` records the original
measurement campaign; update its numerical summary when replacing measurements.

`scripts/import_v15_evidence.py` imports the v1.5.0 source snapshot and the
original transform campaign at `../tmp/cumes-opt-20260908`, then validates and
summarizes the archived measurements. It does not run solvers and refuses to
replace imported files with different bytes. It needs the original campaign
only when reimporting; ordinary slide/site builds use the checked-in frozen data.

## Validation

The completed deck was checked in headless Chrome at 1600×900 and 1280×720:
all 64 slides had no detected content overflow, footer collision, or KaTeX
error. All slide screenshots were visually reviewed. The print layout was
checked separately, and the PDF has 64 pages of 16:9 dimensions.
Navigation, overview, notes, help, Home/End, and mobile scrolling were exercised.
JavaScript and Python syntax and whitespace were checked. Detailed results are
in [data/validation.json](data/validation.json).

Solver validation here consists of the measured historical runs, repeated
state-hash checks, convergence counts/residuals, and checkpoint replays. The
full cuMES test suite, GPU qualification campaigns and VMEC++ comparisons were
not rerun for this presentation update. The v1.5 test, sanitizer and reference
results are explicitly attributed to the archived release campaigns.
