from spline import spline

from scipy.interpolate import interp1d
from math import sin, cos, exp, radians, acos, pi, ceil


a = 7
x = []
y = []
for i in range(0, a + 1):
  xi = i * pi / (a + 2)
  yi = sin(xi)
  x.append(xi)
  y.append(yi)


print(x)

finterp1d = interp1d(x, y, kind='quadratic')

f = spline(x, y)

x = pi / 5
print(a)
print('pi / 5')
f1 = f(x)
print('f', round(f1, 3))
s1 = sin(x)
print('s', round(s1, 3))
abs1 = abs(f(x) - sin(x))
print('abs', round(abs1, 3))
o1 = abs1 / s1
print('o', round(o1 * 100, 3))

x = pi / 3
print('pi / 3')
f1 = f(x)
print('f', round(f1, 3))
s1 = sin(x)
print('s', round(s1, 3))
abs1 = abs(f(x) - sin(x))
print('abs', round(abs1, 3))
o1 = abs1 / s1
print('o', round(o1 * 100, 3))
