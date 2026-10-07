"""Inspect one saved community row/requirements join; no upstream code or native work."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'inputs/issue65-sample'
REVISION = '286a268c664938519af6ceacfb4ec8143f64e20e'


def load(name):
    return json.loads((DATA/name).read_text(encoding='utf-8'))


def row(name):
    response = load(name+'.json')
    assert len(response['rows']) == 1 and response['partial'] is False
    assert response['rows'][0]['truncated_cells'] == []
    assert 'x-revision: '+REVISION in (DATA/(name+'.headers')).read_text(encoding='utf-8')
    return response['rows'][0]['row']


def main(output):
    assert not output.exists(), 'fresh output required'
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    result = row('results-row-v1')
    requirement_row = row('requirements-row-v1')
    assert result['requirements_id'] == requirement_row['id']
    requirements = json.loads(requirement_row['json'])
    for key, value in requirements.items():
        if 'reqs/'+key in result:
            assert result['reqs/'+key] == value, key
    checks = []
    for arm in ['regcoil', 'desc']:
        prefix = arm+'_metrics/'
        radius = result[prefix+'minor_radius']
        assert radius > 0 and math.isfinite(radius)
        for metric, power in [('coil_to_coil_min_distances', -1),
                              ('coil_to_plasma_min_distances', -1),
                              ('coil_lengths', -1), ('coil_curvatures', 1), ('coil_torsions', 1)]:
            for stat in ['min', 'mean', 'max', 'std']:
                raw = result[prefix+metric+'/'+stat]
                normalized = result[prefix+'normalized_'+metric+'/'+stat]
                calculated = raw*radius if power == 1 else raw/radius
                relative = abs(calculated-normalized)/max(1, abs(normalized))
                assert relative <= 1e-12
                checks.append(dict(arm=arm, metric=metric, statistic=stat,
                                   reported=normalized, recomputed=calculated,
                                   scaled_error=relative))
    requested = requirements['normalized_min_coil_plasma_distance']
    achieved = result['desc_metrics/normalized_coil_to_plasma_min_distances/min']
    report = dict(
        producer=head, completed=True, physical_admission=False,
        decision='inconclusive for a qualified joint-design sample; only partial intake verified',
        task='predict achieved normalized coil-field error from boundary, requirements and coils',
        dataset_revision_header=REVISION, full_parquet_hash_verified=False,
        joined_requirements_id=requirement_row['id'],
        unavailable_joins={k: result[k] for k in
                           ['constellaration_boundary_id', 'desc_coilset_id']},
        requested_plasma_clearance=requested, reported_achieved_plasma_clearance=achieved,
        fractional_clearance_shortfall=(requested-achieved)/requested,
        upstream_baseline_flag=result['baseline_labels/meets_relative_error_thresholds'],
        reported_representation=dict(unique_coils=requirements['n_coils_per_half_period'],
                                     fourier_order=requirements['coil_fourier_order'],
                                     field_periods=result['boundary.n_field_periods']),
        public_contract_compatible=False, independent_families_established=False,
        fetched_code_executed=False, geometry_or_field_replayed=False,
        arithmetic_checks=checks,
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in [*sorted(DATA.iterdir()), Path(__file__),
                                 ROOT/'src/fusion_public/data.py'] if p.is_file()})
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ['source_hashes', 'arithmetic_checks']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
