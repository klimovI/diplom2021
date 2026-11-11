# Ionospheric TEC calculation

[![test](https://github.com/klimovI/diplom2021/actions/workflows/test.yml/badge.svg)](https://github.com/klimovI/diplom2021/actions/workflows/test.yml)

English | [Русский](README.ru.md)

The program computes the total electron content of the ionosphere (TEC) along the ray from a receiver to a GNSS satellite and the signal delay it causes. TEC is computed in two ways: exactly, by integrating along the slant ray, and approximately, from the vertical TEC above the ionospheric pierce point.

## Model

The ionosphere is a layer with a Gaussian height profile; the peak density varies along the path. The layer can have different thicknesses below and above the peak:

```
N(x, h) = foF2(x)² / 80.8 · exp(−((h − Zm) / W)²),   W = Wm for h < Zm, Wt for h ≥ Zm
```

- `x`: arc distance from the receiver along the Earth's surface, `h`: height;
- `foF2(x)`: critical frequency, given at points spaced `profile_step` apart and interpolated with a quadratic spline (`src/tec/spline.py`);
- `Zm`: height of the density peak, `Wm` and `Wt`: half-thickness of the layer below and above the peak.

**Exact method.** The ray leaves the receiver at elevation angle `θ`; `N` is integrated along the ray with step `step` along the arc up to a height of 2000 km.

**Approximate method.** The vertical TEC at the pierce point (where the ray crosses the height `Zm`) is integrated from 60 to 2000 km with a step of at most `step` and converted to slant TEC with the factor `1 + 16 · (0.53 − θ/180)³`.

For both methods the program prints TEC in TECU (10¹⁶ el/m²) and the ionospheric delay `ΔL = 40.26 · TEC / f²` in metres and in nanoseconds.

## Running

Only [uv](https://docs.astral.sh/uv/getting-started/installation/) is required; it installs Python 3.11+ itself, and there are no other dependencies.

```sh
# Linux, macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Run without downloading the repository:

```sh
uvx --from git+https://github.com/klimovI/diplom2021 tec --elevation 45
```

Inside the repository folder (a clone or the [zip](https://github.com/klimovI/diplom2021/archive/refs/heads/master.zip)) use `uv run tec …`. Without uv: `pip install .`, then `tec …`.

## Parameters

Without arguments `tec` computes an example with the default parameters. Any parameter can be set with a flag, and a set of parameters can be saved in a TOML file; flags override the file.

```sh
tec                                         # default parameters
tec --elevation 45 --frequency 1227.6       # custom angle and frequency (GPS L2)
tec my.toml                                 # parameters from a file
tec my.toml --elevation 60                  # the file, but a different angle
tec --elevation 30,45,60                    # several angles in one run
tec --elevation 30,45,60 --format csv > tec.csv   # CSV output, json is also available
tec --help                                  # all parameters
```

| Parameter | Flag | Units | Default | |
|---|---|---|---|---|
| `elevation` | `--elevation` | degrees | 30 | elevation angle of the satellite above the horizon, from 0 to 90; several values are allowed: `--elevation 30,45` or `elevation = [30, 45]` |
| `frequency` | `--frequency` | MHz | 1575.42 | operating frequency (GPS L1 by default) |
| `step` | `--step` | m | 100 | integration step along the arc and along the height |
| `peak_height` | `--peak-height` | km | 300 | height of the electron density peak, from 60 to 2000 |
| `half_thickness` | `--half-thickness` | km | 100 | half-thickness of the layer below the peak |
| `top_half_thickness` | `--top-half-thickness` | km | same as `half_thickness` | half-thickness of the layer above the peak; `peak_height + 2 · top_half_thickness` must not exceed 2000 |
| `profile_step` | `--profile-step` | km | 500 | spacing between the foF2 profile points |
| `profile` | `--profile` | MHz | 4.923 4.84 4.86 5 5.275 5.8 6.22 | critical frequency foF2 along the path, the first point is above the receiver |

`top_half_thickness` can be omitted, and the layer is then symmetric. If `half_thickness` comes from an ionosonde, set the top thickness separately, see [Comparison with measurements](#comparison-with-measurements).

A file with the same values: [`example.toml`](example.toml). Copy it and keep only what you change. Parameter names are validated: a typo in the file produces an error, not a silent default.

The profile must reach the point where the ray rises to 2000 km; the lower the angle, the farther that point is. If there are not enough points, the program reports how many are needed.

## Example

```
$ tec
угол возвышения 30°, частота 1575.42 МГц

                  точный  приближённый
ПЭС, TECU          9.180         9.100
поправка, м        1.489         1.476
задержка, нс       4.967         4.924
```

The table is printed in Russian. The header line gives the elevation angle and the frequency in MHz, the columns are the exact and the approximate method, the rows are TEC in TECU, the range correction in metres and the delay in nanoseconds.

CSV and JSON are printed without rounding, and the column names carry the units: `tec_*_tecu`, `correction_*_m`, `delay_*_ns`.

```
$ tec --elevation 30,60 --format csv
elevation_deg,frequency_mhz,tec_exact_tecu,tec_approx_tecu,correction_exact_m,correction_approx_m,delay_exact_ns,delay_approx_ns
30.0,1575.42,9.18015112542703,9.09970459039116,1.4891240994635788,1.4760747637387621,4.9671833287533165,4.923655430113462
60.0,1575.42,5.984463106795736,5.895626162311553,0.9707474433614702,0.9563370885484985,3.2380649261078815,3.1899971564611493
```

## Comparison with measurements

The foF2 and hmF2 profile was taken from the [GIRO](https://giro.uml.edu/) ionosondes on the path Juliusruh, Pruhonice, Rome, Gibilmanna (7 days in 2021–2022, at 10, 12 and 14 UTC), and the exact TEC of the program was compared with the [CODE](https://www.aiub.unibe.ch/) TEC map and with TEC from dual-frequency GPS observations of the POTS station (Potsdam). In both variants `Wm` is taken from the ionosonde parameter `B0` (`Wm ≈ B0 / 1.2`), and `Wt` is fitted to the CODE vertical TEC above the receiver.

| | Difference from CODE | Difference from GNSS |
|---|---|---|
| `Wt = Wm` | 47% | 50% |
| `Wt` fitted | 3.4% | 6.0% |

An ionosonde sees only the bottom side of the layer, so with a single thickness TEC comes out almost half the real value. With a separate thickness for the top side the difference drops to a few percent.

Ionosonde data: Global Ionosphere Radio Observatory; Reinisch, B. W., and I. A. Galkin, *Global ionospheric radio observatory (GIRO)*, Earth, Planets and Space, 63, 377–381, [doi:10.5047/eps.2011.03.001](https://doi.org/10.5047/eps.2011.03.001), 2011; http://spase.info/SMWG/Observatory/GIRO. Stations: Juliusruh (JR055, Leibniz-Institut für Atmosphärenphysik), Pruhonice (PQ052, Institute of Atmospheric Physics CAS), Rome (RO041) and Gibilmanna (GM037), both operated by Istituto Nazionale di Geofisica e Vulcanologia. TEC maps: Center for Orbit Determination in Europe (CODE), Astronomical Institute, University of Bern. GNSS observations: IGS station POTS (GFZ Helmholtz Centre for Geosciences), archive of the BKG GNSS Data Center; Johnston, G., A. Riddell, and G. Hausler, *The International GNSS Service*, Springer Handbook of Global Navigation Satellite Systems, 967–982, [doi:10.1007/978-3-319-42928-1_33](https://doi.org/10.1007/978-3-319-42928-1_33), 2017.

## Tests

```sh
python -m unittest discover -s tests
```

`tests/test_program.py` checks the result against reference values and checks parameter parsing; `tests/test_spline.py` checks the spline properties: passing through the knots, smoothness, and refusal outside the knots.

## License

[MIT](LICENSE)
