"""Use the same pinned font bytes and size controls as the HTML presentations."""

import hashlib
from pathlib import Path
import re

from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.ticker import Formatter, LogFormatterMathtext, ScalarFormatter

from export_standalone import Resources

ROOT = Path(__file__).resolve().parents[1]


def configure():
    css = (ROOT / "typography.css").read_text()
    resources = Resources(ROOT / ".cache/standalone")
    family = None
    for url in re.findall(r'url\("(https://[^\"]+/TypoPRO-LinuxBiolinum-[^\"]+\.ttf)"\)', css):
        resources.read(url)
        path = resources.cache / hashlib.sha256(url.encode()).hexdigest()
        font_manager.fontManager.addfont(path)
        if url.endswith("-Regular.ttf"):
            family = font_manager.FontProperties(fname=path).get_name()
    if family is None:
        raise ValueError("typography.css must declare the Biolinum regular face")

    def scale(name):
        match = re.search(r"--" + name + r"-scale:\s*([\d.]+)\s*;", css)
        if not match or float(match[1]) <= 0:
            raise ValueError(f"Set --{name}-scale to a positive number in typography.css")
        return float(match[1])

    return family, scale("font") * scale("figure")


class MathTicks(Formatter):
    """Keep numerical ticks in the math font, including minus signs."""

    def __init__(self, formatter):
        self.formatter = formatter

    def set_axis(self, axis):
        super().set_axis(axis)
        self.formatter.set_axis(axis)

    def set_locs(self, locs):
        super().set_locs(locs)
        self.formatter.set_locs(locs)

    def __call__(self, value, position=None):
        return self.formatter(value, position).replace(r"\mathdefault", r"\mathrm")

    def get_offset(self):
        return self.formatter.get_offset().replace(r"\mathdefault", r"\mathrm")


def scale_labels(figure, scale):
    for axes in figure.axes:
        for axis in (axes.xaxis, axes.yaxis):
            for which in ("major", "minor"):
                formatter = getattr(axis, f"get_{which}_formatter")()
                if isinstance(formatter, (ScalarFormatter, LogFormatterMathtext)):
                    getattr(axis, f"set_{which}_formatter")(MathTicks(formatter))
    # Include explicitly sized legends/titles as well as default-sized labels.
    for label in figure.findobj(Text):
        label.set_fontsize(label.get_fontsize() * scale)
