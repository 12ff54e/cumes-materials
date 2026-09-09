# cuMES & meow presentations

[Open the GitHub Pages site](https://12ff54e.github.io/cumes-materials/).

| Presentation | Content | Editing source |
| --- | --- | --- |
| [A complete cuMES run](slides/cumes-run/) | Fixed/free boundary, CUDA loop, vacuum coupling, output | `slides/cumes-run/index.html` |
| [Making cuMES faster](slides/cumes-optimization/) | History through v1.5: CUDA, Fourier, vacuum and optional Newton measurements | `slides/cumes-optimization/scripts/build_deck.py` |
| [Optimizing with meow](slides/meow/) | Optimizer architecture, tangent measurements, Landreman QA/QH reproduction | `slides/meow/scripts/build_deck.py` |

Each deck includes speaker notes. The optimization and meow directories also
contain PDF exports, evidence ledgers, frozen data, and reproduction commands.
Solver benchmarks are independent of building or publishing the website.

## Preview and publish

From the repository root:

```bash
python3 scripts/build_site.py
python3 -m http.server 8000 --directory _site
```

Open `http://localhost:8000/`. Building needs only Python's standard library.
It regenerates the two generated decks and stages the landing page, presentation
HTML, original CSS/JavaScript, figures, and existing PDFs. Source files and
benchmark archives remain available in the GitHub repository.

Pushing `main` triggers `.github/workflows/pages.yml`. It builds `_site`, uploads
the Pages artifact, and deploys it to the `github-pages` environment. Before the
first deployment, open the repository's [Pages settings](https://github.com/12ff54e/cumes-materials/settings/pages)
and set **Build and deployment → Source → GitHub Actions**. Then run
**Publish presentations** from the Actions tab if the initial push ran before
Pages was enabled. All site paths are relative, so the decks work under the
repository's Pages URL.

Hosted decks load KaTeX 0.18.4 CSS, JavaScript, and fonts from jsDelivr, with
version-pinned URLs and integrity checks on the CSS/JavaScript. These are the
same library bytes used for the validated original decks. No library binaries
or fonts are included in the deployed site or current source tree.

## Standalone export

Export one deck to a single HTML file:

```bash
python3 scripts/export_standalone.py meow --output exports/meow.html
```

Or export all decks:

```bash
python3 scripts/export_standalone.py --all
```

The output files in `exports/` embed styles, scripts, fonts, figures, and the
KaTeX license. Copy one HTML file to another computer and open it directly;
presenting needs no server or internet access. Navigation, equations, notes,
touch controls, and browser printing remain available.

The first export downloads the pinned dependencies and checks their declared
integrity. Later exports reuse `.cache/standalone/`; `--cache PATH` selects
another cache. The cache and exports are ignored by Git and excluded from Pages.
The script never overwrites a source deck and needs no third-party Python packages.
It does not bundle the separate benchmark archives or external reference links.

## Validation

Use each deck's documented checks. The shared browser validator can also inspect
a served URL or a standalone file:

```bash
python3 slides/meow/scripts/validate_deck.py \
  --chrome /path/to/chrome \
  --deck slides/meow \
  --url http://localhost:8000/slides/meow/ \
  --scratch ../tmp/meow-web-preview

python3 slides/meow/scripts/validate_deck.py \
  --chrome /path/to/chrome \
  --deck slides/meow \
  --html exports/meow.html --offline \
  --pdf ../tmp/meow-offline-preview/meow.pdf \
  --report ../tmp/meow-offline-preview/validation.json \
  --scratch ../tmp/meow-offline-preview
```

The validator uses `requests`, `websocket-client`, and Pillow. Offline validation
disables the browser's network and checks that the deck makes no HTTP requests.
It checks rendering, layouts, navigation, notes, and print output; review the
screenshots as well. See `AGENTS.md` for notation and evidence requirements.

The deployment follows GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
The CDN setup follows the [KaTeX browser documentation](https://katex.org/docs/browser.html);
its MIT license is retained in [licenses/KaTeX.txt](licenses/KaTeX.txt).
