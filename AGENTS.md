# Repository guidance

## Purpose and working scope

This repository stores presentation slides and supporting materials about the
cuMES magnetic equilibrium solver in `../cuMES`.

Carry requested slide work through research, implementation, measurement when
needed, and validation. Make reasonable presentation and implementation choices
without asking for confirmation of routine, reversible steps. State material
assumptions; ask when missing information would substantially change the result
and cannot be resolved from the repository or task context.

Keep presentation sources and evidence here. Temporary benchmark harnesses,
instrumentation, and build-compatibility fixes in isolated solver checkouts are
within scope when needed to obtain slide data. Changes to the primary solver
checkout or permanent solver features require a task that includes those changes.
Preserve unrelated work in this repository and sibling repositories.

## Layout and editable sources

- `slides/cumes-run/`: the complete fixed- and free-boundary run presentation.
  Edit its content directly in `index.html`.
- `slides/cumes-optimization/`: optimization history, archived evidence, and
  reproduced measurements. Edit narrative and tables in `scripts/build_deck.py`,
  then run that script to regenerate `index.html`.
- Each deck's `README.md` describes its editing, preview, and reproduction workflow.
- HTML decks use `styles.css`, `deck.js`, and local `vendor/katex/` assets. The
  optimization deck also has `optimization.css`, `evidence.md`, `data/`, and
  reproduction scripts.

Place new decks under `slides/<topic>/` with their assets and usage instructions.
Check the target deck's source/generator relationship before editing. Update
generators rather than making changes that the next generation step will erase.
Regenerate affected outputs; rendering slides does not require rerunning benchmarks.

## Technical accuracy

Use the relevant cuMES implementation, tests, documentation, and commit history
to verify added or changed technical claims. Match the source revision to the
claim: current behavior comes from the current implementation; historical behavior
comes from the relevant commit or tag. Documentation can contain stale summaries
or superseded plans; resolve conflicts against code and recorded run evidence.

For development-history requests, inspect the requested commit range, including
merged changes and relevant dependency updates. Do not rely only on commit titles
or messages containing `perf`. Respect the requested version and branch scope.

Distinguish physical equations, numerical methods, and implementation choices;
fixed- and free-boundary behavior; and execution improvements versus changes to
the convergence trajectory. Retain useful commit IDs, source paths, or symbols
in footers, speaker notes, or an evidence ledger.

Label archived measurements, newly reproduced results, and derived estimates.
Performance claims should identify the workload, revision, hardware, precision,
and measurement method to the extent recorded. Keep iteration counts, per-pass
latency, kernel time, CUDA-stream elapsed time, and whole-process wall time
distinct. Do not invent missing numbers or combine unrelated measurements into
an apparent total speedup. Report uncertainty or missing provenance plainly.

## Obtaining data

Feel free to compile and run programs, including GPU benchmarks, when data are
needed for the slides. Reuse adequate existing evidence; reproduce results when
needed to answer the task, resolve conflicting evidence, or fill a measurement gap.

- Use isolated checkouts or worktrees under `../tmp/<task>/` for historical
  builds and experiments. Keep build products and large temporary outputs there.
- Reproduce the relevant dependency revisions and build options. Record any
  instrumentation or compatibility patches separately from the original commit.
- For timing comparisons, hold inputs and measurement scope constant, warm up,
  alternate variant order, and repeat enough to reveal variability. Avoid running
  competing benchmarks on the same GPU; record unavoidable concurrent activity.
- Preserve raw samples and report spread, failures, regressions, and relevant
  convergence/state checks. Explain any excluded samples. Scale the experiment
  to the claim rather than running the full solver test suite by default.
- Keep the evidence needed to reproduce presented results in the deck's `data/`
  directory or evidence ledger. Record commands and inputs. Preserve previous
  measurement campaigns before running scripts that overwrite their outputs.

## Slide editing

Keep slides concise and legible at presentation size; put supporting detail in
speaker notes or the evidence ledger. Use plots, diagrams, and comparison tables
when they explain the result better than prose. Follow the target deck's visual
language unless the task requests a new style. For the existing HTML decks:

- Keep runtime dependencies local so presenting works offline.
- Reuse CSS layout classes and code-native diagrams where practical; choose other
  tools or assets when they improve the presentation.
- Write equations with the existing `data-tex` convention.
- Maintain slide metadata (`data-title`, `data-chapter`, `data-summary`) and
  `.speaker-notes` where relevant.
- Preserve semantic structure, accessibility, keyboard/touch navigation, and
  16:9 print output.
- Avoid hand-editing vendored libraries; retain their licenses.

## Preview and validation

There is no repository-wide build or automated test suite. Use the target deck's
documented workflow. Open its `index.html` directly, or serve this repository:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000/slides/<topic>/` for the target deck.

Validate in proportion to the change:

- Content/layout: inspect affected slides for clipping, readable tables/plots,
  and equation rendering. Review all slides when a shared layout change affects
  the whole deck. Check print layout when changed and refresh affected PDF exports.
- Interactions: exercise the affected navigation, hashes, overview, notes, help,
  and touch behavior. Use `node --check` on changed JavaScript when available.
- Data/generators: verify source attribution, units, calculations, and agreement
  between the displayed values and saved evidence. Refresh affected outputs and
  documentation together.
- Documentation-only edits: check clarity, paths, consistency, and whitespace;
  browser checks and solver runs are unnecessary.

Use available browser/headless tools for visual checks. If a tool is unavailable,
perform the useful checks that remain and report the specific limitation.
Run `git diff --check`; it does not cover untracked files, so inspect newly created
text files for whitespace problems too. Avoid adding tests that merely mirror
content or repeating expensive checks without a relevant change or open concern.

Finish with links to the deliverables, the main changes or findings, checks
actually performed, and any material limitations. Keep sources, generated slides,
exports, and the evidence they cite consistent.
