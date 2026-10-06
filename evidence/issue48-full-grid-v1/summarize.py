"""Reduce recorded grid observations without promoting failed points to qualified maps."""
import json
from pathlib import Path

PAYLOAD = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    supervisor = read(PAYLOAD/'supervisor-result.json')
    result = dict(software_completed=supervisor['completed'], producer=supervisor['producer'],
                  physical_admission=False, equal_alpha_verified=False, nestedness_proven=False,
                  original_matching_verdict='inconclusive', arms=[])
    for target in ('reference401', 'selected401'):
        status = read(PAYLOAD/target/'supervisor-result.json')
        report = read(PAYLOAD/target/'run/result.json')
        lines = report['lines']
        arm = dict(target=target, completed=status['completed'],
                    driver_elapsed_s=report['elapsed_s'],
                    supervisor_elapsed_s=status['monotonic_elapsed_s'],
                    clock_discrepancy_s=status['clock_discrepancy_s'],
                    sources_unchanged=bool(report.get('sources_before'))
                    and report['sources_before'] == report.get('sources_after'),
                    controls_pass=report.get('controls_pass', False),
                    recorded_lines=len(lines),
                    qualified_lines=sum(line.get('passed', False) for line in lines),
                    surface_summary=report.get('surface_summary'),
                    failures=[dict(index=line['index'], s=line['s'], theta=line['theta'],
                                   failures=line.get('failures', ['incomplete']))
                              for line in lines if not line.get('passed', False)])
        final = [line['prefixes'][-1] for line in lines
                 if line.get('prefixes') and 'error' not in line['prefixes'][-1]]
        subsets = [sub for row in final for sub in row['subsets'] if 'error' not in sub]
        arm['recorded_final_diagnostic_maxima'] = {
            'max_gap_rad': max((row['max_gap_rad'] for row in final), default=None),
            'heldout_radius_max_m': max((s['heldout_radius_max_m'] for s in subsets), default=None),
            'quadrature_label_change': max((row['quadrature_label_change'] for row in final),
                                           default=None),
            'independent_label_error': max((row['independent_label_error'] for row in final),
                                           default=None),
        }
        result['arms'].append(arm)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
