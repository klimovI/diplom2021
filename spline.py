from scipy.interpolate import interp1d
from math import sin, cos, exp, radians, acos, pi, ceil

x = []
y = []
for i in range(0, 5):
  xi = i * pi / 4
  yi = sin(xi)
  x.append(xi)
  y.append(yi)

def spline(xArr, yArr):
  a = []
  a.append(yArr[0])
  for i in yArr: a.append(i)
  a.append(yArr[len(yArr) - 1])

  b = []
  b.append(yArr[0])
  for i in range(1, len(yArr)):
    h = yArr[i] - yArr[i - 1]
    b.append(2 * (yArr[i] - yArr[i-1])/h-b[i-1])
  b.append(yArr[len(yArr) - 1])
   
  print(a)
  print(b)

f = interp1d(x, y, kind='quadratic')
print(sin(pi / 7))
print(f(pi / 7))

spline(x, y)