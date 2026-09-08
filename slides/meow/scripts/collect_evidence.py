#!/usr/bin/env python3
"""Freeze selected local evidence and re-evaluate the original VMEC outputs.

Requires sibling meow and the extracted Landreman-Paul Zenodo v2 archive.
Does not run GPU optimizations. Plot/deck generation uses only saved data.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

import numpy as np
from scipy.io import netcdf_file

DECK = Path(__file__).resolve().parents[1]
WORKSPACE = DECK.parents[2]
MEOW = WORKSPACE / "meow"
ARCHIVE = WORKSPACE / "20211102-01-precise_quasisymmetry_zenodo"
CALCULATIONS = ARCHIVE / "calculations/20210704-01-simsopt_new_quasisymmetry_metric"
DATA = DECK / "data"
manifest = []


def source_record(path, destination=None):
    contents = path.read_bytes()
    record = {"source": str(path.relative_to(WORKSPACE)),
              "sha256": hashlib.sha256(contents).hexdigest(),
              "bytes": len(contents)}
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
        record["saved_as"] = str(destination.relative_to(DECK))
    manifest.append(record)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def parse_log(path):
    stages, accepted = [], []
    if not path.exists():
        return {"stages": [], "accepted": [], "log_available": False}
    for line in path.read_text().splitlines():
        if line.startswith("finished max_mode="):
            fields = dict(re.findall(r"(\w+)=(\S+)", line))
            fields.pop("status", None)
            stages.append({k: float(v) if k == "objective" else int(v)
                           for k, v in fields.items()})
        elif line.startswith("accepted mode="):
            fields = dict(re.findall(r"(\w+)=(\S+)", line))
            accepted.append({k: float(v) if k == "objective" else int(v)
                             for k, v in fields.items()})
    counters = {}
    for key in ("iterations", "equilibrium_evaluations", "nonlinear_iterations",
                "analytic_jacobians", "linear_iterations", "jacobian_updates"):
        if stages and all(key in stage for stage in stages):
            counters[key] = sum(stage[key] for stage in stages)
    return {"stages": stages, "accepted": accepted,
            "counters": counters, "log_available": True}


def wall_time(path):
    text = path.read_text()
    simple = re.search(r"wall_seconds=([\d.]+)", text)
    if simple:
        return float(simple[1])
    elapsed = re.search(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\S+)", text)
    value = 0.0
    for field in elapsed[1].split(":"):
        value = 60 * value + float(field)
    return value


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(["git", "-C", str(MEOW), "rev-parse", "HEAD"], text=True).strip()
    for name in ("README.md", "docs/landreman-paul-reproduction.md", "docs/relaxation-rundown.md",
                 "examples/landreman/README.md"):
        source_record(MEOW / name, DATA / "sources/meow" / name)
    for path in sorted((MEOW / "examples/landreman").glob("*.json")):
        source_record(path, DATA / "inputs" / path.name)
    source_record(ARCHIVE / "README", DATA / "sources/zenodo-README.txt")
    for name in ("apps/cumes_landreman_optimize.cpp", "src/trf.cpp",
                 "include/meow/cumes/quasisymmetry_target.hpp",
                 "include/meow/cumes/boundary_parameterization.hpp",
                 "include/meow/cumes/quasisymmetry_target_jvp.hpp",
                 "examples/cumes_landreman_evaluate.cpp"):
        source_record(MEOW / name)

    experiments = {
        "early-tangent": ("benchmark-forward-tangent-20260902", ["qa-analytic", "qa-finite-difference", "qh-analytic", "qh-finite-difference"]),
        "corrected-tangent": ("benchmark-forward-tangent-corrected-20260903", ["qa-analytic", "qh-analytic"]),
        "four-worker-broyden": ("benchmark-four-worker-aggressive-broyden-20260904", ["qa", "qh"]),
    }
    runs = {}
    for campaign, (directory, cases) in experiments.items():
        for case in cases:
            original = WORKSPACE / directory / case
            saved = DATA / "archived" / campaign / case
            for path in sorted(original.iterdir()):
                if path.suffix in (".json", ".txt", ".log"):
                    source_record(path, saved / path.name)
            entry = parse_log(saved / "run.log")
            entry["wall_seconds"] = wall_time(saved / "time.txt")
            entry["objective"] = entry["stages"][-1]["objective"] if entry["stages"] else {
                "qa-analytic": 6.29151469581e-4, "qa-finite-difference": 5.94683530877e-7,
            }[case]
            entry["endpoint_source"] = "run.log" if entry["stages"] else "meow reproduction document; raw QA log absent from this local archive"
            entry["measurement"] = "archived single whole-process wall time, not a repeated median"
            runs[campaign + "/" + case] = entry
    constructions = {}
    for case in ("qa", "qh"):
        original = WORKSPACE / f"opt-{case}-analytic-accepted-axis"
        saved = DATA / "archived/accepted-axis" / case
        for path in sorted(original.iterdir()):
            if path.name in ("run.log", "latest.json") or path.name.startswith("latest.json.construction"):
                source_record(path, saved / path.name)
        constructions[case] = parse_log(saved / "run.log")

    module_path = MEOW / "scripts/evaluate_landreman_qs.py"
    source_record(module_path, DATA / "sources/evaluate_landreman_qs.py")
    spec = importlib.util.spec_from_file_location("vmec_reference", module_path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    references, geometry, boozer = {}, {}, {}
    for case, construction_tag, refinement_tag in (("qa", "021", "050"), ("qh", "039", "059")):
        construction = next(next(CALCULATIONS.glob(f"20210704-01-{construction_tag}_*")).glob("abs_step*"))
        refinement = next(next(CALCULATIONS.glob(f"20210704-01-{refinement_tag}_*")).glob("weight_3.00e+01*" if case == "qa" else "weight_2.00e+00*"))
        published = ARCHIVE / f"configurations/new_{case.upper()}"
        nfp, helicity, aspect = (2, 0, 6) if case == "qa" else (4, -1, 8)
        stage_ids = [63, 113, 176, 248] if case == "qa" else [48, 92, 144, 205, 276]
        files = {f"construction-mode{mode}": construction / f"wout_nfp{nfp}_{case.upper()}_000_{index:06d}.nc"
                 for mode, index in enumerate(stage_ids, 1)}
        files["terminal"] = next(refinement.glob(f"wout_*_{63 if case == 'qa' else 90:06d}.nc"))
        files["published"] = next(published.glob("wout*"))
        for label, path in files.items():
            source_record(path)
            construction_case = label.startswith("construction")
            result = oracle.evaluate(path, m=1, n=helicity, surfaces=np.linspace(0, 1, 11),
                                     weights=np.linspace(1, 1 if construction_case else (30 if case == "qa" else 2), 11))
            result["wout"] = str(path.relative_to(WORKSPACE))
            with netcdf_file(str(path), "r", mmap=False) as file:
                values = file.variables
                result["mean_iota"] = float(np.mean(values["iotas"].data[1:]))
                result["ns"] = int(values["ns"].data)
                result["mpol"] = int(values["mpol"].data)
                result["ntor"] = int(values["ntor"].data)
                if label in (f"construction-mode{len(stage_ids)}", "published"):
                    geometry[f"{case}-{label}"] = {
                        "source": result["wout"], "nfp": nfp,
                        "m": values["xm"].data.astype(int).tolist(),
                        "n_physical": values["xn"].data.astype(int).tolist(),
                        "rbc": values["rmnc"].data[-1].tolist(),
                        "zbs": values["zmns"].data[-1].tolist(),
                    }
            result["objective"] = result["qs_total"] + (result["aspect_ratio"] - aspect) ** 2
            if construction_case and case == "qa":
                result["objective"] += (result["mean_iota"] - 0.42) ** 2
            result["measurement"] = "new CPU evaluation of archived VMEC fields; no new VMEC solve"
            references[f"{case}-{label}"] = result
            print(f"{case}-{label}: {result['objective']:.12g}", flush=True)

        path = next(published.glob("boozmn*"))
        source_record(path)
        with netcdf_file(str(path), "r", mmap=False) as file:
            values = file.variables
            m = values["ixm_b"].data.astype(int)
            n = values["ixn_b"].data.astype(int)
            bmn = values["bmnc_b"].data.astype(float)
            b00 = bmn[:, (m == 0) & (n == 0)][:, 0]
            ns = int(values["ns_b"].data)
            s = (values["jlist"].data.astype(float) - 1.5) / (ns - 1)
            nonsymmetric = n != (helicity * nfp * m)
            boozer[case] = {"source": str(path.relative_to(WORKSPACE)),
                            "s": s.tolist(), "maximum_nonqs_over_b00": (np.max(np.abs(bmn[:, nonsymmetric]), axis=1) / b00).tolist(),
                            "m": m.tolist(), "n_physical": n.tolist(),
                            "edge_bmn": bmn[-1].tolist(), "edge_b00": float(b00[-1]),
                            "edge_s": float(s[-1]), "nfp": nfp,
                            "measurement": "original BOOZ_XFORM spectrum; reference only"}
    # Reference numbers from the final accepted optimizer log, not nearby perturbed wouts.
    archived_stage_objectives = {"qa": [9.6408e-3, 1.5611e-4, 3.5144e-6, 2.92794425995e-7],
                                 "qh": [1.39906e-1, 2.8614e-3, 1.79572e-4, 4.1688e-5, 3.07486398207e-5]}
    save(DATA / "summary.json", {"meow_revision": revision, "runs": runs,
                                "accepted_axis_construction": constructions,
                                "archived_stage_objectives": archived_stage_objectives})
    save(DATA / "reference/metrics.json", references)
    save(DATA / "reference/boundaries.json", geometry)
    save(DATA / "reference/boozer.json", boozer)
    save(DATA / "source-manifest.json", manifest)
    print(f"Preserved {len(manifest)} source fingerprints; {len(runs)} benchmark runs")


if __name__ == "__main__":
    main()
