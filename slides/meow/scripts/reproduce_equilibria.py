#!/usr/bin/env python3
"""Re-solve the published boundaries; these are accuracy checks, not benchmarks."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


DECK = Path(__file__).resolve().parents[1]
WORKSPACE = DECK.parents[2]


def command(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, text=True,
                          capture_output=True, **kwargs).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--meow", type=Path, default=WORKSPACE / "meow")
    parser.add_argument("--output", type=Path, required=True,
                        help="A new output directory; existing runs are preserved.")
    args = parser.parse_args()
    build, meow, output = args.build.resolve(), args.meow.resolve(), args.output
    output.mkdir(parents=True, exist_ok=False)
    executable = build / "cumes_landreman_evaluate"
    dependency = build / "_deps/cumes-src"
    metadata = {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "one accuracy re-solve per published boundary; no timing speed claim",
        "meow_revision": command(["git", "-C", meow, "rev-parse", "HEAD"]).strip(),
        "cumes_revision": command(["git", "-C", dependency, "rev-parse", "HEAD"]).strip(),
        "gpu": command(["nvidia-smi", "--query-gpu=name,driver_version,pstate,utilization.gpu,memory.used",
                        "--format=csv,noheader"]).strip(),
        "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "build": str(build),
        "runs": [],
    }
    (output / "CMakeCache.txt").write_text((build / "CMakeCache.txt").read_text())
    for case in ("qa", "qh"):
        source = meow / f"examples/landreman/{case}.json"
        argv = [str(executable), str(source), case]
        started = time.perf_counter()
        result = subprocess.run(argv, check=True, text=True, capture_output=True)
        elapsed = time.perf_counter() - started
        values = json.loads(result.stdout)
        assert values["converged"] and max(values[k] for k in ("fsqr", "fsqz", "fsql")) <= 1e-12
        (output / f"{case}.json").write_text(result.stdout)
        (output / f"{case}.stderr.txt").write_text(result.stderr)
        (output / f"{case}-input.json").write_bytes(source.read_bytes())
        metadata["runs"].append({"case": case, "command": argv,
                                 "wall_seconds_diagnostic_only": elapsed,
                                 "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"{case}: objective={values['objective']:.12g}; converged; {elapsed:.2f} s", flush=True)


if __name__ == "__main__":
    main()
