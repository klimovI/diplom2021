from math import sin, cos, exp, radians
from sys import argv


# радиус земли в метрах
R0 = 6371000
# высота максимума ионосферы
Hmax = 2000000


# 
params = argv[1:]
params = list(map(float, params))
dX, f0, k, theta, Zm, Wm = params

# критическая частота
def F0(x):
  return f0 + k * x
  
# высота
def H(x):
  a = cos(theta)
  b = cos(theta + x / R0)
  return R0 * (a / b - 1)

# электронная концентрация
def N(x, h):
  a = F0(x) ** 2 / 80.8
  b = (h - Zm) / Wm
  c = -b ** 2
  return a * exp(c)

# z
def Z(x):
  a = sin(x / R0)
  b = cos(theta + x / R0)
  return R0 * a / b


x = 0
TECu = 0
while(x <= Hmax): 
  x += dX
  h = H(x)
  dZ = Z(x) - Z(x - dX)
  n = N(x, h)
  TECu += n * dZ

print(TECu)
