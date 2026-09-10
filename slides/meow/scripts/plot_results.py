#!/usr/bin/env python3
"""Generate presentation figures using only the frozen data in this deck."""

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import numpy as np

DECK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DECK.parents[1] / "scripts"))
from figure_typography import configure, scale_labels

FIGURE_FONT, FIGURE_SCALE = configure()
DATA, ASSETS = DECK / "data", DECK / "assets"
CYAN, AMBER, GREEN, RED = "#43d9ff", "#ffb454", "#72e5b3", "#ff8390"
INK, MUTED, BG = "#e8f4fc", "#a0b8c9", "#071725"
plt.rcParams.update({
    "font.family": FIGURE_FONT, "font.size": 14,
    "axes.facecolor": BG, "figure.facecolor": BG, "savefig.facecolor": BG,
    "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": "#34536a",
    "xtick.color": MUTED, "ytick.color": MUTED, "grid.color": "#294257",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.formatter.use_mathtext": True, "mathtext.fontset": "cm",
    # Embed glyph outlines so math labels also work without installed TeX fonts.
    "legend.frameon": False, "svg.fonttype": "path", "svg.hashsalt": "meow-slides",
})


def read(name):
    return json.loads((DATA / name).read_text())


def finish(fig, name):
    scale_labels(fig, FIGURE_SCALE)
    fig.savefig(ASSETS / name, dpi=190, bbox_inches="tight", pad_inches=0.12,
                metadata={"Date": None} if name.endswith(".svg") else None)
    plt.close(fig)


def boundary_from_json(value):
    modes = {(h["m"], h["n"]) for family in ("rbc", "zbs") for h in value[family]}
    modes = sorted(modes)
    coefficients = {family: {(h["m"], h["n"]): h["value"] for h in value[family]}
                    for family in ("rbc", "zbs")}
    return {"nfp": value["nfp"], "m": [m for m, n in modes],
            "n_physical": [n * value["nfp"] for m, n in modes],
            **{family: [coefficients[family].get(mode, 0) for mode in modes]
               for family in coefficients}}


def surface(ax, boundary, color, title):
    theta, phi = np.meshgrid(np.linspace(0, 2 * np.pi, 81),
                             np.linspace(0, 2 * np.pi, 241))
    r, z = np.zeros_like(theta), np.zeros_like(theta)
    for m, n, rc, zs in zip(boundary["m"], boundary["n_physical"], boundary["rbc"], boundary["zbs"]):
        phase = m * theta - n * phi
        r += rc * np.cos(phase)
        z += zs * np.sin(phase)
    x, y = r * np.cos(phi), r * np.sin(phi)
    ax.plot_surface(x, y, z, color=color, rstride=2, cstride=2,
                    linewidth=0, antialiased=True, shade=True,
                    lightsource=LightSource(azdeg=330, altdeg=35))
    ax.set(xlim=(-1.4, 1.4), ylim=(-1.4, 1.4), zlim=(-.65, .65))
    ax.set_box_aspect((2.8, 2.8, 1.3), zoom=1.15)
    ax.view_init(elev=27, azim=-53)
    ax.set_axis_off()
    ax.set_title(title, color=color, pad=-12, fontsize=17)


def geometry_figures():
    boundaries = read("reference/boundaries.json")
    for case, color, mode in (("qa", CYAN, 4), ("qh", AMBER, 5)):
        fig = plt.figure(figsize=(13, 4.2))
        shapes = [boundary_from_json(read(f"inputs/{case}_analytic.json")),
                  boundary_from_json(read(f"archived/accepted-axis/{case}/latest.json")),
                  boundaries[f"{case}-construction-mode{mode}"]]
        titles = ["Analytic seed", "meow construction", "VMEC construction reference"]
        if case == "qa":
            # Axisymmetric seeds do not select a toroidal phase. Align the
            # reconstructed QA branch by a rigid pi/nfp rotation for display.
            parity = [1 if (n // shapes[1]["nfp"]) % 2 == 0 else -1
                      for n in shapes[1]["n_physical"]]
            for family in ("rbc", "zbs"):
                shapes[1][family] = [value * sign for value, sign in zip(shapes[1][family], parity)]
            titles[1] = "meow · toroidal phase aligned"
        for index, (shape, title) in enumerate(zip(shapes, titles), 1):
            surface(fig.add_subplot(1, 3, index, projection="3d"), shape, color, title)
        fig.subplots_adjust(left=0, right=1, top=.85, bottom=0, wspace=-.15)
        finish(fig, f"{case}-construction-shapes.png")
    fig = plt.figure(figsize=(11.5, 4.5))
    for index, (case, color) in enumerate((("qa", CYAN), ("qh", AMBER)), 1):
        surface(fig.add_subplot(1, 2, index, projection="3d"),
                boundaries[f"{case}-published"], color,
                f"{case.upper()} · ${2 if case == 'qa' else 4}$ field periods")
    fig.subplots_adjust(left=0, right=1, top=.85, bottom=0, wspace=-.18)
    finish(fig, "published-boundaries.png")


def convergence_figures(summary):
    for case in ("qa", "qh"):
        stages = summary["accepted_axis_construction"][case]["stages"]
        fast = summary["runs"][f"four-worker-broyden/{case}"]["stages"]
        modes = [s["max_mode"] for s in stages]
        fig, ax = plt.subplots(figsize=(11.8, 4.4), layout="constrained")
        for values, name, color, marker in (
            (summary["archived_stage_objectives"][case], "Landreman construction", MUTED, "s"),
            ([s["objective"] for s in stages], "meow · accepted-axis cold FD", CYAN, "o"),
            ([s["objective"] for s in fast], "meow · $4$ workers + Broyden", GREEN, "^"),
        ):
            ax.semilogy(modes, values, color=color, marker=marker, markersize=8,
                        linewidth=2.4, label=name)
        ax.set(xlabel="Maximum active boundary mode $k$", ylabel=r"Composite objective $\|r\|^2$",
               xticks=modes)
        ax.grid(True, which="major", alpha=.7)
        ax.legend(loc="upper right", fontsize=12)
        finish(fig, f"{case}-convergence.svg")


def performance_figure(summary):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.7), layout="constrained")
    for case, ax in zip(("qa", "qh"), axes):
        baseline = summary["runs"][f"early-tangent/{case}-finite-difference"]
        variants = [
            (baseline, "Cold FD", CYAN, (-70, 13)),
            (summary["runs"][f"early-tangent/{case}-analytic"], "Early tangent", RED, (12, -8)),
            (summary["runs"][f"corrected-tangent/{case}-analytic"], "Corrected tangent", AMBER, (-12, 14)),
            (summary["runs"][f"four-worker-broyden/{case}"], "$4$ workers + Broyden", GREEN, (12, 6)),
        ]
        for result, label, color, offset in variants:
            x = result["wall_seconds"] / baseline["wall_seconds"]
            y = result["objective"] / baseline["objective"]
            ax.scatter([x], [y], color=color, s=90, zorder=3)
            ax.annotate(label, (x, y), textcoords="offset points", xytext=offset,
                        color=color, fontsize=12, ha="right" if label == "Corrected tangent" else "left")
        ax.axvline(1, color=MUTED, linewidth=1, linestyle=":")
        ax.axhline(1, color=MUTED, linewidth=1, linestyle=":")
        ax.set_yscale("log")
        ax.set(xlim=(.15, 1.88), ylim=(.42, 2200 if case == "qa" else 55),
               xlabel="Wall time / cold FD", title=case.upper())
        ax.grid(axis="y", alpha=.35)
    axes[0].set_ylabel("Final objective / cold FD")
    finish(fig, "speed-and-quality.svg")


def qs_profiles():
    reference = read("reference/metrics.json")
    for case in ("qa", "qh"):
        local = read(f"local/published-boundaries-20260908/{case}.json")
        fig, ax = plt.subplots(figsize=(11.8, 4.4), layout="constrained")
        s = np.linspace(0, 1, 11)
        for y, label, color, marker in (
            (reference[f"{case}-terminal"]["unweighted_qs_profile"], "VMEC · terminal optimization ($n_s=75$)", MUTED, "s"),
            (reference[f"{case}-published"]["unweighted_qs_profile"], "VMEC · published re-solve ($n_s=201$)", AMBER, "^"),
            (local["unweighted_qs_profile"], "cuMES f61c959 · new re-solve ($n_s=201$)", CYAN, "o"),
        ):
            ax.semilogy(s, y, color=color, marker=marker, markersize=6,
                        linewidth=2.3, label=label)
        ax.set(xlabel=r"Normalized toroidal flux $s$", ylabel="Unweighted surface QS error", xticks=s)
        ax.grid(True, which="major", alpha=.6)
        ax.legend(loc="upper left" if case == "qa" else "lower right", fontsize=12)
        finish(fig, f"{case}-qs-profile.svg")


def boozer_figures():
    data = read("reference/boozer.json")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.5), layout="constrained")
    theta, alpha = np.meshgrid(np.linspace(0, 2 * np.pi, 129),
                               np.linspace(0, 2 * np.pi, 129), indexing="ij")
    for case, ax in zip(("qa", "qh"), axes):
        d = data[case]
        field = np.zeros_like(theta)
        for m, n, coefficient in zip(d["m"], d["n_physical"], d["edge_bmn"]):
            field += coefficient * np.cos(m * theta - n / d["nfp"] * alpha)
        image = ax.imshow(field / d["edge_b00"], origin="lower", extent=(0, 1, 0, 1),
                          cmap="cividis", aspect="auto", interpolation="none")
        ax.set(title=f"{case.upper()} · reference at $s={d['edge_s']:.4f}$",
               xlabel=r"$n_{\mathrm{fp}}\,\zeta_B\,/\,2\pi$", ylabel=r"$\theta_B\,/\,2\pi$")
        fig.colorbar(image, ax=ax, label=r"$|B|/B_{00}$", fraction=.047, pad=.025)
    finish(fig, "reference-boozer-contours.png")
    fig, ax = plt.subplots(figsize=(11.8, 4.3), layout="constrained")
    for case, color in (("qa", CYAN), ("qh", AMBER)):
        d = data[case]
        ax.semilogy(d["s"], d["maximum_nonqs_over_b00"], color=color,
                    linewidth=2.6, label=f"{case.upper()} · original BOOZ_XFORM spectrum")
    ax.set(xlabel=r"Normalized toroidal flux $s$", ylabel=r"Largest nonsymmetric $|B_{mn}|/B_{00}$")
    ax.grid(True, alpha=.6)
    ax.legend(fontsize=13)
    finish(fig, "reference-boozer-spectrum.svg")


def main():
    ASSETS.mkdir(exist_ok=True)
    summary = read("summary.json")
    geometry_figures()
    convergence_figures(summary)
    performance_figure(summary)
    qs_profiles()
    boozer_figures()
    print("Generated 10 figures from frozen data")


if __name__ == "__main__":
    main()
