from math import sin, cos, exp, radians, acos
from os import path
from spline import spline

params = []
with open('data.txt', encoding = 'utf8') as file:
   for line in file:
      string = line.split('#')[0]
      arr = string.split()
      if (len(arr) >1):
        num = list(map(float, string.split()))
      else:
        num = float(arr[0])
      params.append(num)

# основные параметры
R0 = 6371000 # радиус земли (в метрах)
Hmax = 2000000 # высота максимума ионосферы (в метрах)
c = 299792458 # скорость света (м/с)

# Параметры которые принимает программа (по порядку):
#   dX - шаг по дуге от приёмника до проекции спутника (в метрах)
#   theta - угол возвышения спутника над горизонтом (в градусах)
#   Zm - высота максимальной концентрации электронов (в километрах)
#   Wm - полутолщина ионосферы (в километрах)
#   f_w - рабочая частота (в МГц)
#   step - шаг (в километрах)
#   splineData - данные (в МГц)
dX, theta_degree, Zm, Wm, f_w, step, splineData = params # создание переменных из массива параметров

f_w *= 1000000 # МГц в Гц
theta = radians(theta_degree) # градусы в радианы
Zm *= 1000 # километры в метры
Wm *= 1000 # километры в метры
splineData = [x * 1000000 for x in splineData] # МГц в Гц
dataX = [step * i * 1000 for i,y in enumerate(splineData)] # километры в метры

# вычисление высоты, от расстояния по дуге на плоскости земли
def H(x):
  a = cos(theta)
  b = cos(theta + x / R0)
  return R0 * (a / b - 1)

f = spline(dataX, splineData)

# вычисление электронной концентрации, от расстояния по дуге на плоскости земли и высоты
def N(x, h):
  a = f(x) ** 2 / 80.8
  b = (h - Zm) / Wm
  c = -b ** 2
  return a * exp(c)

# вычисление длины траектории по прямой линии от приёмника до спутника в зависимости от x
def Z(x):
  a = sin(x / R0)
  b = cos(theta + x / R0)
  return R0 * a / b

def printData(TEC):
  print('TEC =', TEC / 10**16, 'TECU') # перевод в TECU
  dL = 40.26 * TEC / f_w ** 2
  print('задержка =', (dL / c) * 10**9, 'нс.')
  print('поправка =', dL, 'м.')


# Цикл вычисления наклонного ПЭС
# начинаем с 0
x = 0
TECu = 0
h = 0
z = 0
while (h <= Hmax): 
  x += dX # x увеличивается на заданный ша
  h = H(x) # текущая высота
  currZ = Z(x)
  dZ = currZ - z
  z = currZ
  n = N(x, h) # концентрация электронов для данных координат
  TECu += n * dZ # увеличиваем значение электронной концентрации

print('Точный способ расчёта ПЭС')
printData(TECu)


# Находится x подионосферной точки
# выводится из формулы для процедуры H(x) только здесь получаем x(h)
alpha = acos(cos(theta) / (Zm / R0 + 1)) - theta
x = alpha * R0

# Цикл вычисления вертикального ПЭС
TECu = 0
h = 60000 # начинаем с высоты начала ионосферы (60км)
while (h <= Hmax): 
  h += dX # h увеличивается на заданный шаг (для простоты шаг такой-же как и для x)
  n = N(x, h) # концентрация электронов для данных координат
  TECu += n * dX # увеличиваем значение электронной концентрации

# перевод вертикального в наклонный ПЭС
TECu *= 1 + 16 * (0.53 - theta_degree / 180) ** 3

print()
print('Приближённый способ расчёта ПЭС')
printData(TECu)
input()
