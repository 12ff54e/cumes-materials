#!/usr/bin/env python3
"""Regenerate decks and stage the files served by GitHub Pages."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or output in ROOT.parents or (ROOT / "slides") == output or (ROOT / "slides") in output.parents:
        parser.error("The output must be a separate staging directory, not a source directory")
    if output.exists() and not (output / ".nojekyll").exists():
        parser.error("Refusing to replace an existing directory without the .nojekyll staging marker")

    for generator in sorted((ROOT / "slides").glob("*/scripts/build_deck.py")):
        subprocess.run([sys.executable, str(generator)], check=True, cwd=ROOT)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / ".nojekyll").touch()
    for name in ("index.html", "site.css", "typography.css", "typography.js"):
        shutil.copy2(ROOT / name, output / name)
    shutil.copytree(ROOT / "licenses", output / "licenses")
    for deck in sorted((ROOT / "slides").iterdir()):
        if not (deck / "index.html").is_file():
            continue
        destination = output / "slides" / deck.name
        destination.mkdir(parents=True)
        for path in sorted(deck.iterdir()):
            if path.name in {"index.html", "deck.js"} or path.suffix in {".css", ".pdf"}:
                shutil.copy2(path, destination / path.name)
        if (deck / "assets").is_dir():
            shutil.copytree(deck / "assets", destination / "assets")
        html = (destination / "index.html").read_text()
        if "vendor/katex" in html or "https://cdn.jsdelivr.net/npm/katex@" not in html:
            raise ValueError(f"{deck.name}: hosted decks must use the pinned KaTeX CDN")
    files = [path for path in output.rglob("*") if path.is_file()]
    print(f"Staged {len(files)} files ({sum(path.stat().st_size for path in files):,} bytes) in {output}")


if __name__ == "__main__":
    main()
