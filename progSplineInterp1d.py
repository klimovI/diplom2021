from math import sin, cos, exp, radians, acos
from sys import argv
from spline import spline
from scipy.interpolate import interp1d


# общие параметры
R0 = 6371000 # радиус земли (в метрах)
Hmax = 2000000 # высота максимума ионосферы (в метрах)
c = 299792458 # скорость света (м/с)


# Параметры которые принимает программа (по порядку):
# dX - шаг по дуге от приёмника до проекции спутника (в метрах)
# f_cr - критическая частота ионосферы (в МГц)
# k - угловой коэффициент изменения критической частоты
# theta - угол возвышения спутника над горизонтом (в градусах)
# Zm - высота максимальной концентрации электронов (в километрах)
# Wm - полутолщина ионосферы (в километрах)
# f_w - рабочая частота (в МГц)


# получение параметров от пользователя (консоли) (закомментировал для теста программы)
# params = argv[1:] # приходит массив а параметры идут только со 2го элемента массива

params = [100, 6, -1.5, 30, 300, 100, 1575.42] # параметры для теста программы (после теста будут убраны)
params = list(map(float, params)) # от пользователя параметры пришли строкой нужно перевести в числа
dX, f_cr, k, theta_degree, Zm, Wm, f_w = params # создание переменных из массива параметров


f_cr *= 1000000 # МГц в Гц
f_w *= 1000000 # МГц в Гц
theta = radians(theta_degree) # градусы в радианы
Zm *= 1000 # километры в метры
Wm *= 1000 # километры в метры



# вычисление критической частоты, от расстояния по дуге на плоскости земли
def F0(x):
  return f_cr + k * x

step = 2 # 1/step
def getSplineFunc():
  alp = acos(cos(theta)/(Hmax/R0 + 1)) - theta
  xMax = alp * R0

  xArr = []
  yArr = []
  stepSize = xMax / step
  for i in range(0, step + 1):
    xi = i * stepSize
    xArr.append(i * stepSize)
    yArr.append(F0(xi))

  # return spline(xArr, yArr)
  print(xArr)
  return interp1d(xArr, yArr, kind='quadratic')
f = getSplineFunc()
  
# вычисление высоты, от расстояния по дуге на плоскости земли
def H(x):
  a = cos(theta)
  b = cos(theta + x / R0)
  return R0 * (a / b - 1)

# вычисление электронной концентрации, от расстояния по дуге на плоскости земли и высоты
def N(x, h):
  try:
    f(x)
  except:
    print(x)
    return 0
  a = f(x) ** 2 / 80.8
  b = (h - Zm) / Wm
  c = -b ** 2
  return a * exp(c)

# вычисление длины траектории по прямой линии от приёмника до спутника в зависимости от x
def Z(x):
  a = sin(x / R0)
  b = cos(theta + x / R0)
  return R0 * a / b

def DeltaL(TEC):
  return 40.26 * TEC / f_w ** 2


# Цикл вычисления наклонного ПЭС
# начинаем с 0
x = 0
TECu = 0
h = 0
z = 0
while (h <= Hmax): 
  x += dX # увеличивается на заданный шаг
  # print('x = ', x)

  h = H(x) # используется процедура H(x)
  # print('h = ', h)

  currZ = Z(x)
  dZ = currZ - z # увеличение шага по дельта z
  # print('dZ = ', dZ)

  z = currZ

  n = N(x, h) # концентрация электронов для данных координат
  # print('N = ', n)

  TECu += n * dZ # увеличиваем значение электронной концентрации
  # print('TECu = ', TECu)

print('TEC = ', round(TECu / 10**16, 2))
print('задержка', round((DeltaL(TECu) / c) * 10**9, 2))
print('поправка', round(DeltaL(TECu), 2))


# выводится из формулы для процедуры H(x) только здесь получаем x(h)
alpha = acos(cos(theta)/(Zm/R0 + 1)) - theta
x_max_of_N = alpha * R0 # x для которого h = Zm (для расчёта вертикального ПЭС)

# Цикл вычисления вертикального ПЭС
TECu = 0
h = 60000 # начинаем с высоты начала ионосферы (60км)
while (h <= Hmax): 
  h += dX # увеличивается на заданный шаг (для простоты шаг такой-же как и для x)
  # print('h = ', h)

  n = N(x_max_of_N, h) # концентрация электронов для данных координат
  # print('N = ', n)

  TECu += n * dX # увеличиваем значение электронной концентрации
  # print('TECu = ', TECu)

# перевод вертикального в наклонный ПЭС
TECu *= 1 + 16 * (0.53 - theta_degree / 180) ** 3
#print(TECu)
