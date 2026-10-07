"""Summarize the registered grid without promoting incomplete surfaces."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def summarize():
    receipt = read(BASE/'raw/receipt.json')
    report_path = BASE/'raw/run/result.json'
    report = read(report_path)
    reference_path = BASE/'context/reference-grid-result.json'
    reference = read(reference_path)
    context = read(BASE/'context/provenance.json')
    if hashlib.sha256(reference_path.read_bytes()).hexdigest() != context['sha256']:
        raise ValueError('Historical reference context changed')
    if not (receipt['completed'] and report['completed'] and report['deadline_met']):
        raise ValueError('Incomplete execution cannot yield a qualified grid summary')
    rows = []
    for current, old in zip(report['surface_summary'], reference['surface_summary'], strict=True):
        if current['s'] != old['s'] or not old['numerically_qualified']:
            raise ValueError('Matched nominal surface and qualified historical context required')
        row = dict(s=current['s'], numerically_qualified=current['numerically_qualified'],
                   labels=current['labels'], line_qualified=current['line_qualified'],
                   historical_reference_max_offset=old['max_absolute_offset'],
                   historical_reference_phase_spread=old['phase_spread'])
        if current['numerically_qualified']:
            row.update(max_absolute_offset=current['max_absolute_offset'],
                       phase_spread=current['phase_spread'])
        rows.append(row)
    all_pass = report['all_points_numerically_qualified']
    result = dict(producer_evaluator=receipt['revision'], execution_completed=True,
                  numerical_grid_qualified=all_pass,
                  qualified_points=sum(line['passed'] for line in report['lines']),
                  decision=('supports-later-launch-matching' if all_pass
                            else 'diagnose-failed-reconstructions-before-matching'),
                  failed_points=[dict(index=line['index'], s=line['s'], theta=line['theta'],
                                      failures=line['failures'])
                                 for line in report['lines'] if not line['passed']],
                  surface_summary=rows, current_A=report['current_A'],
                  result_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                  historical_context=context, original_reference_retraced=False,
                  elapsed_s=receipt['elapsed_s'], physical_admission=False,
                  common_realized_surface_proven=False, benefit_transfer_confirmed=False)
    with (BASE/'summary.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    summarize()
