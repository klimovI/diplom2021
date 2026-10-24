import argparse
import csv
import json
import sys
import tomllib
from math import sin, cos, exp, radians, acos, ceil, isfinite

from tec.spline import spline

R0 = 6371000  # радиус Земли, м
H_MIN = 60000  # нижняя граница ионосферы, м
H_MAX = 2000000  # верхняя граница интегрирования, м
C = 299792458  # скорость света, м/с

# имя: (значение по умолчанию, единицы, описание)
PARAMS = {
    'elevation': ([30], 'градусы', 'угол возвышения спутника над горизонтом, можно несколько через запятую'),
    'frequency': (1575.42, 'МГц', 'рабочая частота'),
    'step': (100, 'м', 'шаг интегрирования по дуге и по высоте'),
    'peak_height': (300, 'км', 'высота максимума концентрации электронов'),
    'half_thickness': (100, 'км', 'полутолщина слоя ниже максимума'),
    'top_half_thickness': (None, 'км', 'полутолщина слоя выше максимума'),
    'profile_step': (500, 'км', 'шаг между точками профиля foF2'),
    'profile': ([4.923, 4.84, 4.86, 5, 5.275, 5.8, 6.22], 'МГц',
                'критическая частота foF2 вдоль трассы, первая точка над приёмником'),
}
LISTS = [name for name, (default, _, _) in PARAMS.items() if isinstance(default, list)]


def angles(text):
    return [float(v) for v in text.split(',')]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog='tec', description='Расчёт ПЭС ионосферы и задержки сигнала GNSS на луче от приёмника до спутника.')
    parser.add_argument('config', nargs='?', help='TOML-файл с параметрами; флаги перекрывают его значения')
    for name, (default, unit, text) in PARAMS.items():
        parser.add_argument('--' + name.replace('_', '-'), type=angles if name == 'elevation' else float,
                            nargs='+' if name == 'profile' else None, metavar=unit, help=f'{text} (по умолчанию {"как --half-thickness" if default is None else default})')
    parser.add_argument('--format', choices=('text', 'csv', 'json'), default='text', help='формат вывода (по умолчанию text)')
    args = parser.parse_args(argv)

    params = {name: default for name, (default, _, _) in PARAMS.items()}
    if args.config:
        params.update(read_config(args.config))
    params.update({name: value for name, value in vars(args).items() if name in PARAMS and value is not None})
    if params['top_half_thickness'] is None:
        params['top_half_thickness'] = params['half_thickness']
    params['format'] = args.format
    return params


def read_config(path):
    try:
        with open(path, encoding='utf-8-sig') as file:
            config = tomllib.loads(file.read())
    except (OSError, UnicodeDecodeError) as error:
        sys.exit(f'{path}: не удалось прочитать файл ({error})')
    except tomllib.TOMLDecodeError as error:
        sys.exit(f'{path}: {error}; формат файла см. в example.toml')
    unknown = sorted(config.keys() - PARAMS.keys())
    if unknown:
        sys.exit(f'{path}: неизвестные параметры {", ".join(unknown)}; список параметров: tec --help')
    for name, value in config.items():
        if name == 'elevation' and type(value) in (int, float):
            config[name] = value = [value]
        if name in LISTS:
            if not isinstance(value, list) or not all(type(v) in (int, float) for v in value):
                sys.exit(f'{path}: {name}: нужен список чисел')
        elif type(value) not in (int, float):
            sys.exit(f'{path}: {name}: нужно число')
    return config


def pierce_distance(theta, h):
    """Расстояние по дуге до точки, где луч под углом theta поднимается на высоту h."""
    return (acos(cos(theta) / (h / R0 + 1)) - theta) * R0


def check(params):
    for name in PARAMS:
        if not all(isfinite(v) for v in (params[name] if name in LISTS else [params[name]])):
            sys.exit(f'{name}: нужно конечное число')
    if len(params['profile']) < 2:
        sys.exit('profile: нужно хотя бы две точки')
    if not params['elevation']:
        sys.exit('elevation: нужен хотя бы один угол')
    for e in params['elevation']:
        if not 0 < e < 90:
            sys.exit(f'elevation: угол {e:g}° вне интервала (0, 90) градусов')
    for name in ('frequency', 'step', 'half_thickness', 'top_half_thickness', 'profile_step'):
        if params[name] <= 0:
            sys.exit(f'{name}: значение должно быть больше нуля')
    if not H_MIN < params['peak_height'] * 1000 < H_MAX:
        sys.exit(f'peak_height: высота максимума должна быть между {H_MIN // 1000} и {H_MAX // 1000} км')
    if params['peak_height'] * 1000 + 2 * params['top_half_thickness'] * 1000 > H_MAX:
        sys.exit(f'top_half_thickness: слой должен помещаться ниже {H_MAX // 1000} км: '
                 f'peak_height + 2 · top_half_thickness не больше {H_MAX // 1000}')

    profile_step = params['profile_step'] * 1000
    covered = profile_step * (len(params['profile']) - 1)
    lowest = min(params['elevation'])
    needed = pierce_distance(radians(lowest), H_MAX) + params['step']
    if needed > covered:
        points = int(needed // profile_step) + 2
        sys.exit(f'profile: при угле {lowest:g}° луч уходит на {needed / 1000:.0f} км от приёмника, '
                 f'а профиль покрывает {covered / 1000:.0f} км; нужно хотя бы {points} точек '
                 f'с шагом {params["profile_step"]:g} км')


def calculate(params, elevation):
    """Наклонный ПЭС точным и приближённым способом при угле возвышения elevation, эл/м²."""
    theta = radians(elevation)
    dX = params['step']
    Zm = params['peak_height'] * 1000
    Wm = params['half_thickness'] * 1000
    Wt = params['top_half_thickness'] * 1000
    critical_freq = [fc * 1000000 for fc in params['profile']]  # МГц -> Гц
    xs = [params['profile_step'] * i * 1000 for i in range(len(critical_freq))]  # км -> м
    f = spline(xs, critical_freq)

    # x: расстояние по дуге от приёмника вдоль поверхности Земли
    def height(x):
        return R0 * (cos(theta) / cos(theta + x / R0) - 1)

    def slant_range(x):
        return R0 * sin(x / R0) / cos(theta + x / R0)

    def electron_density(x, h):
        return f(x) ** 2 / 80.8 * exp(-((h - Zm) / (Wm if h < Zm else Wt)) ** 2)

    # точный: интегрируем вдоль луча до спутника
    x = 0
    z = 0
    h = 0
    exact = 0
    while h <= H_MAX:
        x += dX
        h = height(x)
        z_next = slant_range(x)
        exact += electron_density(x, h) * (z_next - z)
        z = z_next

    # приближённый: вертикальный ПЭС над подионосферной точкой, пересчитанный в наклонный
    x = pierce_distance(theta, Zm)
    layers = ceil((H_MAX - H_MIN) / dX)
    dh = (H_MAX - H_MIN) / layers
    approx = sum(electron_density(x, H_MIN + (i + 0.5) * dh) for i in range(layers)) * dh
    approx *= 1 + 16 * (0.53 - elevation / 180) ** 3

    return exact, approx


def delay(tec, frequency):
    """Ионосферная задержка в метрах для частоты в МГц."""
    return 40.26 * tec / (frequency * 1000000) ** 2


def results(params):
    f = params['frequency']
    for elevation in params['elevation']:
        exact, approx = calculate(params, elevation)
        exact_delay, approx_delay = delay(exact, f), delay(approx, f)
        yield {
            'elevation_deg': float(elevation),
            'frequency_mhz': float(f),
            'tec_exact_tecu': exact / 10**16,
            'tec_approx_tecu': approx / 10**16,
            'correction_exact_m': exact_delay,
            'correction_approx_m': approx_delay,
            'delay_exact_ns': exact_delay / C * 10**9,
            'delay_approx_ns': approx_delay / C * 10**9,
        }


def print_text(rows):
    for i, r in enumerate(rows):
        if i:
            print()
        print(f'угол возвышения {r["elevation_deg"]:g}°, частота {r["frequency_mhz"]:g} МГц')
        print()
        print(f'{"":14}{"точный":>10}{"приближённый":>14}')
        for label, key, unit in (('ПЭС, TECU', 'tec', 'tecu'), ('поправка, м', 'correction', 'm'), ('задержка, нс', 'delay', 'ns')):
            print(f'{label:14}{r[f"{key}_exact_{unit}"]:10.3f}{r[f"{key}_approx_{unit}"]:14.3f}')


def main(argv=None):
    params = parse_args(argv)
    check(params)
    rows = list(results(params))
    if params['format'] == 'json':
        print(json.dumps(rows, indent=2))
    elif params['format'] == 'csv':
        writer = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys(), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    else:
        print_text(rows)


if __name__ == '__main__':
    main()
