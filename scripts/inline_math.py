#!/usr/bin/env python3
"""Apply the decks' inline-math typography to static HTML, never at runtime.

Existing data-tex, code, metadata, and navigation labels are preserved. The
symbol vocabulary below is deliberately limited to the notation in these decks;
use an explicit data-tex span for additional or context-dependent expressions.
Both generated decks run this after rendering. The directly edited run deck can
be formatted with: python3 scripts/inline_math.py --write PATH/index.html
"""

import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re


SYMBOLS = {
    "R/Z": r"R/Z", "R₀₀": r"R_{00}", "R00": r"R_{00}",
    "JᵀJ": r"J^TJ", "Jᵀr": r"J^Tr", "J^T J": r"J^TJ", "J^T r": r"J^Tr",
    "u(x)": r"u(x)", "r(x)": r"r(x)", "F(u,x)": r"F(u,x)",
    "F_u": r"F_u", "F_xj": r"F_{x_j}", "F_x": r"F_x",
    "T_u": r"T_u", "T_x": r"T_x", "u_j": r"u_j", "J_j": r"J_j",
    "B₀₀": r"B_{00}", "B00": r"B_{00}", "Bmn": r"B_{mn}",
    "|Bmn|/B₀₀": r"|B_{mn}|/B_{00}", "|Bmn|/B00": r"|B_{mn}|/B_{00}",
    "|B|/B₀₀": r"|B|/B_{00}", "|B|": r"|B|",
    "√g": r"\sqrt{g}", "|√g|": r"|\sqrt{g}|", "sᵐᐟ²": r"s^{m/2}",
    "ῑ": r"\bar\iota", "Δt": r"\Delta t", "π/nfp": r"\pi/n_{\mathrm{fp}}",
    "RBC(0,0)": r"\mathrm{RBC}(0,0)", "ZBS(0,0)": r"\mathrm{ZBS}(0,0)",
    "rbc(0,n)": r"\mathrm{rbc}(0,n)", "zbs(0,n)": r"\mathrm{zbs}(0,n)",
    "rbc(0,1)": r"\mathrm{rbc}(0,1)", "zbs(0,1)": r"\mathrm{zbs}(0,1)",
    "4k(k+1)": r"4k(k+1)", "du/dx": r"\mathrm{d}u/\mathrm{d}x",
    "dT/dx": r"\mathrm{d}T/\mathrm{d}x", "lambda": r"\lambda", "Lambda": r"\lambda",
    "theta": r"\theta", "iota": r"\iota", "phi": r"\phi",
    "theta_B": r"\theta_B", "zeta_B": r"\zeta_B", "pi/nfp": r"\pi/n_{\mathrm{fp}}",
    "nfp": r"n_{\mathrm{fp}}", "ns": r"n_s", "n_s": r"n_s",
    "mpol": r"m_{\mathrm{pol}}", "ntor": r"n_{\mathrm{tor}}",
    "FSQR": r"\mathrm{FSQR}", "FSQZ": r"\mathrm{FSQZ}", "FSQL": r"\mathrm{FSQL}",
    "ftol": r"f_{\mathrm{tol}}", "xtol": r"x_{\mathrm{tol}}", "gtol": r"g_{\mathrm{tol}}",
    "dtau": r"\mathtt{dtau}", "b1": r"b_1", "fac": r"\mathrm{fac}",
    "rCon": r"\mathtt{rCon}", "zCon": r"\mathtt{zCon}",
    "rCon0": r"\mathtt{rCon0}", "zCon0": r"\mathtt{zCon0}",
    "tcon": r"\mathtt{tcon}", "brmn": r"\mathtt{brmn}", "bzmn": r"\mathtt{bzmn}",
    "xmpq": r"\mathtt{xmpq}", "p95": r"p_{95}",
    "RBC": r"\mathrm{RBC}", "ZBS": r"\mathrm{ZBS}",
}
SYMBOLS.update({s: s for s in ("R", "Z", "B", "I", "G", "M", "N", "F", "T", "J", "x", "u", "s", "m", "n", "k", "c")})
SYMBOLS.update({s: "\\" + name for s, name in {
    "λ": "lambda", "θ": "theta", "ζ": "zeta", "ι": "iota", "ψ": "psi", "π": "pi", "Φ": "Phi",
}.items()})

SYMBOL = re.compile(r"(?<![\w'’])(?:" + "|".join(re.escape(k) for k in sorted(SYMBOLS, key=len, reverse=True)) + r")(?![\w])")
# Bare number values, grouped thousands, e notation, Unicode superscripts,
# percentage / throughput suffixes, and arithmetic/range sequences.
VALUE = r"[+−-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][+−-]?\d+|[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)?"
UNITS = {"μs": r"\mu\mathrm{s}", "µs": r"\mu\mathrm{s}", "ms": r"\mathrm{ms}",
         "s": r"\mathrm{s}", "MB": r"\mathrm{MB}", "GB": r"\mathrm{GB}", "KiB": r"\mathrm{KiB}",
         "MiB": r"\mathrm{MiB}", "bytes": r"\mathrm{bytes}", "T": r"\mathrm{T}"}
NUMBER = re.compile(r"(?<![\w.])(?:[≈~]\s*)?" + VALUE +
                    r"(?:\s*(?:→|±|×(?=\s*\d)|[+−=]|–|…|/|:(?=\d))\s*" + VALUE +
                    r")*(?:\s*[%×])?(?:\s+(?P<unit>" + "|".join(UNITS) + r"))?(?!\w|\.\d)")
PROTECTED = re.compile(
    r"\b\d{4}-\d{2}(?:-\d{2})?\b|\b(?:Aug|Sep|September|August)\s+\d+(?:[–-]\d+)?\b|"
    r"\b(?:CUDA|CMake|KaTeX|NetCDF|HDF5|C\+\+|driver|RTX|GPU|sm_)[ -]?\d+(?:\.\d+)*\b|"
    r"\bv\d+(?:\.\d+)+(?:→v\d+(?:\.\d+)+)?\b|\b\d+\.\d+\.\d+\b|"
    r"\b(?:Phase|mode|step|run|Run|class|Class|chapter|Chapter|stage|Stage)\s+[ABCF]|"
    r"\b(?:Phase|run|Run|step|Step|Layer)\s+\d+[A-Z]?(?:[/–-]\d+[A-Z]?)?\b|"
    r"\bPRL\s+\d+,\s*\d+\s*\(\d{4}\)|\bB-splines?\b|\bSHA-256\b|"
    r"\b(?:ADR-\d+(?:…\d+)?|CUMES\d+)\b|§+\s*\d+(?:\.\d+)*(?:[–-]\d+(?:\.\d+)*)?|"
    r"(?:https?://|\.\./|data/|scripts/|examples/|include/|src/|docs/)[^\s<>]+|"
    r"\b[\w./*-]+\.(?:md|json|txt|log|py|cpp|hpp|cuh|cu|bin|nc|h5|html|css|js)\b|"
    r"\b(?:N|F|O)\s+(?:for|or|to)\b|\b(?:N|F|O)\s+·|\bPress\s+[A-Z?](?:\s+or\s+Esc)?|"
    r"\b16:9\b|(?<![\w.,+−-])0\d+\b(?![.\deE])"
)
SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")


def span(tex):
    return '<span class="math-inline" data-tex="' + escape(tex, quote=True) + '"></span>'


def number_tex(value):
    value = value.strip()
    value = re.sub(r"(\d+(?:,\d{3})*(?:\.\d+)?)[eE]([+−-]?\d+)",
                   lambda m: m[1] + r"\times10^{" + str(int(m[2].replace("−", "-"))) + "}", value)
    value = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)", lambda m: "^{" + m[1].translate(SUPERSCRIPTS) + "}", value)
    value = re.sub(r"(?<=\d),(?=\d)", "{,}", value)
    for before, after in {"→": r"\to ", "±": r"\pm ", "×": r"\times ", "≈": r"\approx ",
                          "~": r"\sim ", "–": r"\text{–}", "…": r"\ldots ", "−": "-", "%": r"\%"}.items():
        value = value.replace(before, after)
    return value.strip()


def format_text(text):
    """Replace only actual text-node contents, never tags or attributes."""
    protected = [m.span() for m in PROTECTED.finditer(text)]
    # Leading numbered headings identify sections, not mathematical values.
    lead = re.match(r"\s*0[1-9]\s*·", text)
    if lead:
        protected.append(lead.span())
    def overlaps(start, end, spans):
        return any(start < b and end > a for a, b in spans)
    candidates = []
    for match in SYMBOL.finditer(text):
        if not overlaps(*match.span(), protected):
            tex = SYMBOLS[match[0]]
            if match[0] == "s" and (re.search(r"[·(]\s*$", text[:match.start()]) or text.strip() == "s"):
                tex = r"\mathrm{s}"
            candidates.append((*match.span(), tex))
    for match in NUMBER.finditer(text):
        if not overlaps(*match.span(), protected):
            value = match[0]
            unit = match["unit"]
            if unit:
                value = value[:-(len(unit))].rstrip()
            candidates.append((*match.span(), number_tex(value) + (r"\," + UNITS[unit] if unit else "")))
    # Prefer complete quantities and named expressions over their inner tokens.
    replacements = []
    for start, end, tex in sorted(candidates, key=lambda item: item[1]-item[0], reverse=True):
        if not overlaps(start, end, [(a,b) for a,b,_ in replacements]):
            replacements.append((start,end,tex))
    # Keep a short mathematical equality / comparison in one nonbreaking span.
    joined = []
    operators = {"=": "=", "≤": r"\le ", "≥": r"\ge ", "<": "<", ">": ">", "≠": r"\ne ",
                 "−": "-", "+": "+", "→": r"\to ", "/": "/", "×": r"\times ", "±": r"\pm "}
    for start,end,tex in sorted(replacements):
        gap = text[joined[-1][1]:start].strip() if joined else None
        if gap in operators:
            a, _, previous = joined.pop()
            joined.append((a,end,previous+operators[gap]+tex))
        else:
            joined.append((start,end,tex))
    for start, end, tex in reversed(joined):
        text = text[:start] + span(tex) + text[end:]
    return text


class MathFormatter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        classes = set(attr.get("class", "").split())
        skip = tag in {"script", "style", "code", "pre", "kbd", "title", "svg", "button"} or "data-tex" in attr or "data-math-ignore" in attr or bool(classes & {
            "slide-index", "section-number", "index", "node-step", "node-kicker", "key", "source-ref", "hud", "slide-count",
        }) or bool(self.stack and self.stack[-1][1])
        self.output.append(self.get_starttag_text())
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, skip))

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.output.append(f"</{tag}>")
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.output.append(data if not self.stack or self.stack[-1][1] else format_text(data))

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")


def format_html(html):
    parser = MathFormatter()
    parser.feed(html)
    parser.close()
    return "".join(parser.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for path in args.files:
        old = path.read_text()
        formatted = format_html(old)
        added = formatted.count('class="math-inline"') - old.count('class="math-inline"')
        print(f"{path}: {added} added inline spans")
        if args.write:
            path.write_text(formatted)
