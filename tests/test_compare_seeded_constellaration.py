"""Synthetic controls for the frozen #112 compatibility decision; no model calls."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import compare_seeded_constellaration as comparison  # noqa: E402

PROTOCOL = ROOT / 'docs/qi/seeded-comparison-v1.json'


class SeededComparisonTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
        self.reports = {}
        for row in self.protocol['rows']:
            record = dict(completed=True, input_sha256=row['input_sha256'],
                          settings=self.protocol['settings'], vmec=self.protocol['vmec'].copy(),
                          conversion=dict(R00=row['R00'], **row['conversion'],
                                          max_abs_difference_to_vmecpp_reader=0.),
                          geometry_check=dict(surface_vs_input=0., vmec_boundary_vs_input=0.,
                                              surface_coefficient_bound=0.,
                                              vmec_boundary_coefficient_bound=0.),
                          conversion_validation=dict(passed=True),
                          metrics=row['stored_metrics'].copy())
            self.reports[str(row['global_row'])] = dict(
                targets={row['target_id']: record}, physical_admission=False,
                geometry_relative_tolerance=1e-10, versions=self.protocol['report_versions'].copy(),
                **{k: self.protocol['environment'][k] for k in ('python', 'platform', 'machine')})
        self.row = self.protocol['rows'][0]
        self.report = self.reports[str(self.row['global_row'])]
        self.record = self.report['targets'][self.row['target_id']]

    def result(self):
        return comparison.compare(self.protocol, self.reports)

    def test_complete_matrix_and_every_metric_can_fail(self):
        result = self.result()
        self.assertTrue(result['all_agree'])
        self.assertEqual([len(row['metrics']) for row in result['rows']], [12, 12, 12])
        for name, value in self.row['stored_metrics'].items():
            with self.subTest(metric=name):
                self.record['metrics'][name] = value + 1
                self.assertEqual(self.result()['rows'][0]['status'], 'mismatch')
                self.assertFalse(self.result()['all_agree'])
                self.record['metrics'][name] = value

    def test_signed_zero_and_inclusive_tolerance(self):
        name = 'vacuum_well'
        self.row['stored_metrics'][name] = 0.
        self.record['metrics'][name] = -1e-8
        result = self.result()['rows'][0]['metrics'][name]
        self.assertTrue(result['passed'])
        self.assertEqual(result['signed_difference'], -1e-8)
        self.record['metrics'][name] = -1.000001e-8
        self.assertFalse(self.result()['all_agree'])

    def test_missing_extra_nonfinite_or_boolean_metric_never_passes(self):
        original = self.record['metrics'].copy()
        for bad in (float('nan'), float('inf'), True, '0', None):
            with self.subTest(value=bad):
                self.record['metrics']['qi'] = bad
                self.assertEqual(self.result()['rows'][0]['status'], 'invalid')
        for metrics in ({k: v for k, v in original.items() if k != 'qi'},
                        dict(original, extra=0)):
            self.record['metrics'] = metrics
            self.assertEqual(self.result()['rows'][0]['status'], 'invalid')

    def test_failures_and_unstarted_rows_retained(self):
        self.record['completed'] = False
        self.assertEqual(self.result()['rows'][0]['status'], 'invalid')
        del self.reports[str(self.row['global_row'])]
        result = self.result()
        self.assertEqual(result['rows'][0]['status'], 'not-run')
        self.assertEqual(len(result['rows']), 3)
        self.assertFalse(result['all_agree'])
        self.reports['999'] = {}
        with self.assertRaisesRegex(ValueError, 'unexpected dataset row'):
            self.result()

    def test_identity_runtime_settings_and_geometry_gates(self):
        mutations = [
            lambda r: r.update(input_sha256='0' * 64),
            lambda r: r.update(settings='different'),
            lambda r: r['vmec'].update(ier_flag=1),
            lambda r: r['vmec'].update(ns=199),
            lambda r: r['conversion'].update(R00=float('inf')),
            lambda r: r['conversion'].update(scale=2),
            lambda r: r['conversion_validation'].update(passed=False),
            lambda r: r['geometry_check'].update(vmec_boundary_coefficient_bound=1),
            lambda r: r['geometry_check'].update(surface_vs_input=float('nan')),
        ]
        for mutate in mutations:
            report = copy.deepcopy(self.report)
            mutate(report['targets'][self.row['target_id']])
            with self.subTest(mutation=mutate), self.assertRaises((ValueError, KeyError)):
                comparison.compare_row(self.protocol, self.row, report)
        for key, value in [('versions', {}), ('python', 'other'), ('platform', 'other'),
                           ('physical_admission', True), ('targets', {})]:
            report = dict(self.report, **{key: value})
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                comparison.compare_row(self.protocol, self.row, report)

    def test_cli_binds_bytes_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            output = directory / 'comparison.json'
            command = [sys.executable, str(ROOT / 'scripts/compare_seeded_constellaration.py'),
                       '--protocol', str(PROTOCOL), '--protocol-sha256',
                       hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(), '--output', str(output)]
            for number, report in self.reports.items():
                path = directory / (number + '.json')
                path.write_text(json.dumps(report), encoding='utf-8')
                command.extend(['--report', number, str(path),
                                hashlib.sha256(path.read_bytes()).hexdigest()])
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            original = output.read_bytes()
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(output.read_bytes(), original)
            output.unlink()
            path.write_text('{}', encoding='utf-8')
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
