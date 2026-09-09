"""Freeze the v1.5 sources and archived qualification data; never run a solver.

Run from any directory with the sibling cuMES checkout and original local
transform campaign available. Existing frozen files must have identical bytes.
Slide generation itself only reads the resulting data/v1.5/summary.json.
"""
from pathlib import Path
import hashlib
import json
import statistics as st
import subprocess
import tarfile

DECK = Path(__file__).resolve().parents[1]
ROOT = DECK.parents[1]
REPO = ROOT.parent / 'cuMES'
CAMPAIGN = ROOT.parent / 'tmp/cumes-opt-20260908'
OUT = DECK / 'data/v1.5'
REVISION = '6756fd6'


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def freeze(relative, data, source, records):
    path = OUT / relative
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'Refusing to replace different archived evidence: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    records.append({'path': relative, 'source': source,
                    'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})


def main():
    records = []
    revision = git('rev-parse', REVISION).decode().strip()
    documents = [
        'CHANGELOG.md', 'docs/performance.md', 'docs/free-boundary-performance.md',
        'docs/axisymmetric-newton-qualification.md',
        'docs/adr/0016-opt-in-newton-corrections.md',
        'docs/aggressive-optimization-study.md', 'docs/block-correction-experiments.md',
        'docs/newton-correction-experiments.md', 'docs/coarse-correction-experiments.md',
        'docs/w7x-single-grid-float.md', 'docs/w7x-double-compensation.md',
        'docs/adr/0015-float-only-device-arithmetic.md',
    ]
    fixtures = git('ls-tree', '-r', '--name-only', revision, '--',
                   'benchmarks/free_boundary', 'benchmarks/axisymmetric_newton').decode().splitlines()
    for name in documents + fixtures:
        freeze(name, git('show', f'{revision}:{name}'), f'cuMES:{revision}:{name}', records)
    for path in sorted((CAMPAIGN / 'final-pascal').glob('*.json')):
        freeze('fourier/pascal/' + path.name, path.read_bytes(), str(path), records)
    for name in ['measure_pascal.py', 'ada-report.md']:
        path = CAMPAIGN / name
        freeze('fourier/' + name, path.read_bytes(), str(path), records)
    with tarfile.open(CAMPAIGN / 'ada-results.tar.gz') as archive:
        names = ['results/weighted/summary.json', 'results/weighted-runs.json',
                 'results/build-identity.json', 'benchmark-pinned.py',
                 'results/weighted-vs-inverse-runs.json']
        for name in names:
            freeze('fourier/ada/' + name, archive.extractfile(name).read(),
                   str(CAMPAIGN / 'ada-results.tar.gz') + ':' + name, records)

    # Recompute displayed medians from individual transform samples and check
    # the archived summary. Keep its original paired bootstrap intervals.
    fourier = {}
    pascal = json.loads((OUT / 'fourier/pascal/summary.json').read_text())
    ada = json.loads((OUT / 'fourier/ada/results/weighted/summary.json').read_text())
    ada_runs = json.loads((OUT / 'fourier/ada/results/weighted-runs.json').read_text())
    for gpu in ['pascal', 'ada']:
        fourier[gpu] = {}
        for case in ['w7x', 'solovev']:
            rows = {}
            for variant in ['baseline', 'candidate']:
                if gpu == 'pascal':
                    runs = [json.loads((OUT / f'fourier/pascal/{case}-{variant}-{i}.json').read_text())
                            for i in range(16)]
                    saved = pascal[case][variant]
                else:
                    key = 'weighted' if variant == 'candidate' else 'baseline'
                    runs = [r['result'] for r in sorted(ada_runs, key=lambda r: r['pair'])
                            if r['case'] == case and r['variant'] == key]
                    saved = ada[case][key]
                assert len(runs) == 16
                assert all(r['timed_passes'] == 500 and r['scalar_type'] == 'double' for r in runs)
                medians = [r['median_us_per_iter'] for r in runs]
                assert st.median(medians) == saved['median_us']
                rows[variant] = {
                    'median_us': st.median(medians),
                    'p95_us': st.median(r['p95_us_per_iter'] for r in runs),
                    'setup_ms': st.median(r['setup_us'] for r in runs) / 1000,
                    'mad_us': st.median(abs(x - st.median(medians)) for x in medians),
                    'min_us': min(medians), 'max_us': max(medians),
                    'arena_bytes': runs[0]['arena_bytes'],
                    'cufft_work_bytes': runs[0]['cufft_work_bytes'],
                    'samples_us': medians, 'hashes': [r['state_hash'] for r in runs],
                }
            assert rows['baseline']['hashes'] == rows['candidate']['hashes']
            gains = [100 * (1 - b / a) for a, b in zip(rows['baseline']['samples_us'], rows['candidate']['samples_us'])]
            saved = pascal[case] if gpu == 'pascal' else ada[case]
            gain_key = 'paired_gain_percent' if gpu == 'pascal' else 'paired_median_gain_pct'
            ci_key = 'paired_gain_95_ci' if gpu == 'pascal' else 'paired_median_gain_bootstrap95_pct'
            assert abs(st.median(gains) - saved[gain_key]) < 1e-10
            fourier[gpu][case] = {'variants': rows, 'gain_percent': st.median(gains),
                                  'ci95_percent': saved[ci_key]}

    free = json.loads((OUT / 'benchmarks/free_boundary/results/20260909.json').read_text())
    newton = json.loads((OUT / 'benchmarks/axisymmetric_newton/results-20260908.json').read_text())
    for machine in free['machines'].values():
        assert len(machine['samples']) == 90
        assert sum(r['successful'] for r in machine['samples']) == 72
        for case, result in machine['summary'].items():
            if case == 'w7x_original':
                assert not result['timing_claim_eligible']
                continue
            assert result['all_paired_numerical_exact'] and result['timing_claim_eligible']
            for metric in ['device_ms', 'wall_seconds']:
                paired = result[metric + '_reduction']
                assert len(paired['values_percent']) == 7
                assert abs(st.median(paired['values_percent']) - paired['median_percent']) < 1e-10
                for variant, saved in result['variants'].items():
                    runs = [r for r in machine['samples'] if r['case'] == case
                            and r['variant'] == variant and not r['warmup']]
                    assert st.median(r[metric] for r in runs) == saved[metric]['median']
    for machine in newton['gpus'].values():
        assert len(machine['initial']) == 19
        for phase, pairs in [('initial', 5), ('followup', 15)]:
            for result in machine[phase].values():
                assert len(result['paired_gain_percent']) == pairs
                assert st.median(result['paired_gain_percent']) == result['median_gain_percent']
                assert all(v['converged'] == pairs and v['repeat_trajectory_exact']
                           for v in result['variants'].values())

    summary = {'revision': revision, 'classification': 'Archived release qualification; no new solver runs',
               'fourier': fourier, 'free_boundary': {g: m['summary'] for g, m in free['machines'].items()},
               'newton': newton['gpus'], 'newton_science': newton['science']}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (OUT / 'provenance.json').write_text(json.dumps({'cuMES_revision': revision, 'files': records}, indent=2) + '\n')
    print(f'Archived {len(records)} source/evidence files; verified Fourier, free-boundary and Newton summaries.')


if __name__ == '__main__':
    main()
