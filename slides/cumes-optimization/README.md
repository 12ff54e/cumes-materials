# Making cuMES faster

A 46-slide, offline presentation in the existing Technical Blueprint style.
The two main parts cover CUDA execution/data movement and convergence-trajectory
changes. An appendix covers later concurrency, cold-start, sensitivity, and float
work. The history audit includes 197 commits after design closeout, with 42
highlighted changes and evidence records.

Open [index.html](index.html), or read the exported
[46-page PDF](cumes-optimization.pdf). To serve from the repository root:

```bash
python3 -m http.server 8000 --directory slides/cumes-optimization
```

Visit `http://localhost:8000`. Arrow keys/Space/Page Up/Page Down navigate;
`O` opens overview, `N` opens notes, `F` requests fullscreen, `?` opens help,
and Escape closes overlays. Home/End jump to the first/last slide. Touch supports
horizontal swipes; narrow layouts scroll vertically and wide tables horizontally.
Browser printing uses 16:9 pages. All KaTeX assets and fonts are local.

## Content

- Slides 1–4: scope, version boundaries, measurement definitions.
- Slides 5–20: execution, CUDA graphs, reduction/mapping changes, data movement,
  Makegrid, asynchronous transfer setup, concurrency, rejected experiments.
- Slides 21–39: recovery, seeds, axisymmetric policy, vacuum activation, radial
  interpolation, release comparison, local residuals and checkpoint replay.
- Slides 40–44: later work appendix.
- Slides 45–46: supported conclusions and evidence access.

Each slide has source references and speaker notes. Consult
[evidence.md](evidence.md) for pinned sources, exact attribution, and limitations;
[the commit inventory](data/optimization-commits.md) links individual changes.
The separate unmerged WebGPU branch is outside this CUDA deck.

## New measurements

The deck includes fresh TITAN Xp / CUDA 12.1 / precise-double comparisons:

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
The checked-in HTML is static and requires no Python to present. `styles.css`
and `deck.js` were copied from the original deck; `optimization.css` contains
the new tables/charts/layouts. Vendor files are copied without modification.

`scripts/audit_history.py` regenerates the complete commit inventory from the
pinned range. `scripts/summarize.py` preserves all samples and calculates median,
MAD, ranges, and paired bootstrap intervals. `evidence.md` records the original
measurement campaign; update its numerical summary when replacing measurements.

## Validation

The completed deck was checked in headless Chrome at 1600×900 and 1280×720:
all 46 slides had no detected content overflow, footer collision, or KaTeX
error. All slide screenshots were visually reviewed. The print layout was
checked separately, and the PDF has 46 pages of 16:9 dimensions.
Navigation, overview, notes, help, Home/End, and mobile scrolling were exercised.
JavaScript and Python syntax and whitespace were checked. Detailed results are
in [data/validation.json](data/validation.json).

Solver validation here consists of the measured historical runs, repeated
state-hash checks, convergence counts/residuals, and checkpoint replays. The
full cuMES test suite and new VMEC++ comparisons were not rerun for this
presentation-only task.
