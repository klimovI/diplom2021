import contextlib
import csv
import json
from math import erf, pi, sqrt
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from tec.program import H_MAX, H_MIN, calculate, main, parse_args

EXPECTED = '''угол возвышения 30°, частота 1575.42 МГц

                  точный  приближённый
ПЭС, TECU          9.180         9.100
поправка, м        1.489         1.476
задержка, нс       4.967         4.924
'''


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        main(list(argv))
    return out.getvalue()


def exit_message(*argv):
    with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
        try:
            main(list(argv))
        except SystemExit as error:
            return str(error.code)
    raise AssertionError('main() не завершился с ошибкой')


class ProgramTest(unittest.TestCase):
    def config(self, text):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / 'params.toml'
        path.write_text(text, encoding='utf-8-sig')  # с BOM, как сохраняет Блокнот
        return str(path)

    def test_reference_values(self):
        exact, approx = calculate(parse_args([]), 30)
        self.assertAlmostEqual(exact / 10**16, 9.18015112542703, places=12)
        self.assertAlmostEqual(approx / 10**16, 9.09970459039116, places=12)

    def test_example_matches_defaults(self):
        self.assertEqual(run(str(ROOT / 'example.toml')), EXPECTED)
        self.assertEqual(run(), EXPECTED)

    def test_top_half_thickness(self):
        symmetric = calculate(parse_args([]), 30)
        self.assertEqual(calculate(parse_args(['--top-half-thickness', '100']), 30), symmetric)
        thicker = calculate(parse_args(['--top-half-thickness', '200']), 30)
        self.assertGreater(thicker[0], symmetric[0])
        self.assertGreater(thicker[1], symmetric[1])

    def test_top_half_thickness_follows_half_thickness(self):
        params = parse_args([self.config('half_thickness = 150\n')])
        self.assertEqual(params['top_half_thickness'], 150)
        params = parse_args([self.config('half_thickness = 150\ntop_half_thickness = 250\n'), '--half-thickness', '120'])
        self.assertEqual((params['half_thickness'], params['top_half_thickness']), (120, 250))

    def test_top_half_thickness_limits(self):
        self.assertIn('больше нуля', exit_message('--top-half-thickness', '0'))
        self.assertIn('ниже 2000 км', exit_message('--top-half-thickness', '900'))

    def test_vertical_integral_matches_analytic(self):
        # однородный профиль: приближённый ПЭС = вертикальный интеграл гауссова слоя × множитель
        params = parse_args(['--profile', '5', '5', '5', '5', '5', '5', '5', '--top-half-thickness', '250'])
        _, approx = calculate(params, 30)
        nm = (5e6) ** 2 / 80.8
        zm, wb, wt = 300e3, 100e3, 250e3
        vertical = nm * sqrt(pi) / 2 * (wb * erf((zm - H_MIN) / wb) + wt * erf((H_MAX - zm) / wt))
        factor = 1 + 16 * (0.53 - 30 / 180) ** 3
        self.assertAlmostEqual(approx / (vertical * factor), 1, places=6)

    def test_flags_override_config(self):
        params = parse_args([self.config('elevation = 45\nstep = 50\n'), '--elevation', '60'])
        self.assertEqual(params['elevation'], [60])
        self.assertEqual(params['step'], 50)

    def test_unknown_key(self):
        self.assertIn('неизвестные параметры elevaton', exit_message(self.config('elevaton = 45\n')))

    def test_wrong_type(self):
        self.assertIn('profile: нужен список чисел', exit_message(self.config('profile = 5\n')))

    def test_several_elevations(self):
        text = run('--elevation', '30,60')
        self.assertTrue(text.startswith(EXPECTED))
        self.assertIn('угол возвышения 60°', text)
        self.assertEqual(parse_args([self.config('elevation = [30, 45]\n')])['elevation'], [30, 45])
        self.assertEqual(parse_args([self.config('elevation = 45\n')])['elevation'], [45])
        self.assertEqual(parse_args(['--elevation', '50', self.config('elevation = 45\n')])['elevation'], [50])

    def test_csv_and_json(self):
        rows = list(csv.DictReader(io.StringIO(run('--elevation', '30,45', '--format', 'csv'))))
        self.assertEqual([float(r['elevation_deg']) for r in rows], [30, 45])
        self.assertAlmostEqual(float(rows[0]['tec_exact_tecu']), 9.18015112542703, places=12)
        data = json.loads(run('--format', 'json'))
        self.assertEqual(len(data), 1)
        self.assertAlmostEqual(data[0]['delay_exact_ns'], 4.9671833287533165, places=12)

    def test_elevation_range(self):
        self.assertIn('угол 90°', exit_message('--elevation', '90'))
        self.assertIn('угол 95°', exit_message('--elevation', '30,95'))
        self.assertIn('хотя бы один угол', exit_message(self.config('elevation = []\n')))

    def test_peak_height_range(self):
        for value in ('-50', '2500'):
            self.assertIn('peak_height', exit_message('--peak-height', value))

    def test_not_finite(self):
        self.assertIn('step: нужно конечное число', exit_message('--step', 'nan'))
        self.assertIn('step: нужно конечное число', exit_message('--step', 'inf'))

    def test_unreadable_config(self):
        self.assertIn('не удалось прочитать', exit_message(str(ROOT)))

    def test_short_profile(self):
        self.assertIn('нужно хотя бы 8 точек', exit_message('--elevation', '10'))


if __name__ == '__main__':
    unittest.main()
