from spline import spline

from scipy.interpolate import interp1d
from math import sin, cos, exp, radians, acos, pi, ceil


x = []
y = []
for i in range(0, 3):
  xi = i * pi / 4
  yi = sin(xi)
  x.append(xi)
  y.append(yi)

finterp1d = interp1d(x, y, kind='quadratic')

f = spline(x, y)
x = pi / 5

print(f(x))
print(sin(x))
print(finterp1d(x))

