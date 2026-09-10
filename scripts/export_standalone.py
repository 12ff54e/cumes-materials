#!/usr/bin/env python3
"""Export a deck as one HTML file with scripts, styles, fonts, and images."""

import argparse
import base64
import hashlib
from html import escape
from html.parser import HTMLParser
import mimetypes
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CSS_URL = re.compile(r"""url\(\s*(['"]?)([^)'"]+)\1\s*\)""", re.I)


class Resources:
    def __init__(self, cache):
        self.cache = cache
        self.cache.mkdir(parents=True, exist_ok=True)

    def read(self, url, integrity=""):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme == "file":
            data = Path(urllib.request.url2pathname(parts.path)).read_bytes()
        elif parts.scheme == "https":
            cached = self.cache / hashlib.sha256(url.encode()).hexdigest()
            if not cached.exists():
                request = urllib.request.Request(url, headers={"User-Agent": "cumes-materials-export/1"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = response.read()
                temporary = cached.with_suffix(".tmp")
                temporary.write_bytes(data)
                temporary.replace(cached)
            data = cached.read_bytes()
        else:
            raise ValueError(f"Unsupported resource URL: {url}")
        if integrity:
            matches = []
            for token in integrity.split():
                algorithm, expected = token.split("-", 1)
                if algorithm in {"sha256", "sha384", "sha512"}:
                    actual = base64.b64encode(hashlib.new(algorithm, data).digest()).decode()
                    matches.append(actual == expected)
            if not any(matches):
                raise ValueError(f"Integrity mismatch for {url}; remove its cached copy and retry")
        return data

    def data_url(self, url):
        if url.startswith(("data:", "#")):
            return url
        resource, fragment = urllib.parse.urldefrag(url)
        mime = mimetypes.guess_type(urllib.parse.urlsplit(resource).path)[0] or "application/octet-stream"
        encoded = base64.b64encode(self.read(resource)).decode()
        return f"data:{mime};base64,{encoded}" + (f"#{fragment}" if fragment else "")

    def css(self, text, base_url):
        if re.search(r"@import\b", text):
            raise ValueError("CSS @import is unsupported; link the stylesheet directly before exporting")
        return CSS_URL.sub(
            lambda match: 'url("' + self.data_url(match[2] if match[2].startswith(("data:", "#"))
                else urllib.parse.urljoin(base_url, match[2])) + '")',
            text,
        )


def attributes(attrs):
    return "".join(" " + key + (f'="{escape(value, quote=True)}"' if value is not None else "")
                   for key, value in attrs)


class Exporter(HTMLParser):
    def __init__(self, source, resources):
        super().__init__(convert_charrefs=False)
        self.base_url = source.resolve().as_uri()
        self.resources = resources
        self.output = []
        self.external_script = False

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "link" and attr.get("rel") == "stylesheet":
            url = urllib.parse.urljoin(self.base_url, attr["href"])
            css = self.resources.read(url, attr.get("integrity", "")).decode()
            css = self.resources.css(css, url).replace("</style", r"<\/style")
            kept = [(key, value) for key, value in attrs if key in {"media", "title"}]
            self.output.append(f"<style{attributes(kept)}>\n{css}\n</style>")
        elif tag == "script" and "src" in attr:
            if attr.get("type") == "module":
                raise ValueError("Module scripts need a module bundler before standalone export")
            url = urllib.parse.urljoin(self.base_url, attr["src"])
            script = self.resources.read(url, attr.get("integrity", "")).decode()
            script = re.sub(r"(?im)^//# sourceMappingURL=.*$", "", script)
            script = re.sub(r"</script", r"<\\/script", script, flags=re.I)
            kept = [(key, value) for key, value in attrs
                    if key not in {"src", "integrity", "crossorigin", "defer", "async"}]
            self.output.append(f"<script{attributes(kept)}>\n{script}\n</script>")
            self.external_script = True
        elif tag in {"img", "image"} or "style" in attr:
            if "srcset" in attr:
                raise ValueError("Choose a single image source before standalone export")
            rewritten = []
            for key, value in attrs:
                if tag in {"img", "image"} and key in {"src", "href", "xlink:href"}:
                    value = self.resources.data_url(urllib.parse.urljoin(self.base_url, value))
                elif key == "style":
                    value = self.resources.css(value, self.base_url)
                rewritten.append((key, value))
            ending = "/>" if self.get_starttag_text().endswith("/>") else ">"
            self.output.append(f"<{tag}{attributes(rewritten)}{ending}")
        else:
            self.output.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "script" and self.external_script:
            self.external_script = False
        else:
            self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.external_script:
            self.output.append(data)

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")


def export(source, destination, resources):
    source_decks = {path.resolve() for path in (ROOT / "slides").glob("*/index.html")}
    if destination.resolve() in source_decks | {source.resolve()}:
        raise ValueError("Choose an output file other than the source deck")
    parser = Exporter(source, resources)
    parser.feed(source.read_text())
    parser.close()
    license_html = '<template id="third-party-licenses">' + "".join(
        "<h2>" + escape(path.stem) + "</h2><pre>" + escape(path.read_text()) + "</pre>"
        for path in sorted((ROOT / "licenses").glob("*.txt"))
    ) + "</template>"
    html = "".join(parser.output).replace("</body>", license_html + "\n</body>")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(html)
    temporary.replace(destination)
    print(f"{destination}: {destination.stat().st_size:,} bytes, all presentation resources embedded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deck", nargs="?", help="Deck name, directory, or index.html")
    parser.add_argument("--all", action="store_true", help="Export every deck in slides/")
    parser.add_argument("--output", type=Path, help="Output HTML for one deck")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "exports")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/standalone",
                        help="Cache for the pinned CDN resources; reused by subsequent exports")
    args = parser.parse_args()
    if bool(args.deck) == args.all or (args.all and args.output):
        parser.error("Choose one deck or --all; --output is only for one deck")
    if args.all:
        sources = sorted((ROOT / "slides").glob("*/index.html"))
    else:
        source = Path(args.deck)
        if not source.exists():
            source = ROOT / "slides" / args.deck
        sources = [source / "index.html" if source.is_dir() else source]
        if not sources[0].is_file():
            parser.error(f"Deck does not exist: {sources[0]}")
    resources = Resources(args.cache)
    for source in sources:
        destination = args.output or args.output_dir / f"{source.parent.name}.html"
        export(source, destination, resources)


if __name__ == "__main__":
    main()
