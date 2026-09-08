# cuMES run — web slides

An offline, dependency-free 60-slide presentation explaining a complete cuMES
run: fixed boundary from prescribed LCFS to equilibrium, and free boundary from
coil configuration through MAKEGRID/NESTOR coupling to the final movable LCFS.

## Present

Open `index.html` directly, or serve this directory locally:

```bash
cd slides/cumes-run
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Controls

- Arrow keys, Space, or Page Up/Down: navigate
- `O`: slide overview
- `N`: speaker notes
- `F`: fullscreen
- `?`: help
- Home/End: first/last slide
- Horizontal swipe: navigate on touch devices

Browser printing exports the full deck as 16:9 pages. The deck has no remote
fonts, scripts, images, or other runtime dependencies. KaTeX 0.18.4 is vendored
under `vendor/katex/` for TeX-quality equations and accessible MathML output.

## Files

- `index.html`: presentation content and code-native diagrams
- `styles.css`: Technical Blueprint visual system and print/mobile layouts
- `deck.js`: navigation, overview, notes, fullscreen, fragments, and URL hashes
- `vendor/katex/`: self-hosted math renderer, fonts, and MIT license

Write mathematical variables and quantities in prose, captions, tables, and
notes as `<span class="math-inline" data-tex="..."></span>`. Preserve literal
code, versions, source references, and navigation labels. The optional static
formatter covers the notation already used in these decks:

```bash
python3 scripts/inline_math.py --write slides/cumes-run/index.html
```

Run this from the repository root and review its output. Use explicit TeX for
new or ambiguous expressions; `data-math-ignore` exempts a literal label. This
deck is edited directly in `index.html`, without a content generator.
