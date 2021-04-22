def spline(xArr, yArr):
  h = xArr[1] - xArr[0]
  xArrLen = len(xArr)
  yArrLen = len(yArr)

  # append x
  x = {}
  x[-1] = xArr[0]
  index = 0
  for i in xArr:
    x[index] = i
    index += 1
  x[xArrLen] = xArr[xArrLen - 1]

  # append y
  y = {}
  y[-1] = (yArr[1] - yArr[0]) / (xArr[1] - xArr[0])
  index = 0
  for i in yArr:
    y[index] = i
    index += 1
  y[yArrLen] = (yArr[yArrLen - 1] - yArr[yArrLen - 2]) / (xArr[xArrLen - 1] - xArr[xArrLen - 2])

  # calc a
  a = list(y.values())[1:-1]

  # calc b
  b = []
  b.append(y[-1])
  for i in range(1, yArrLen + 1): b.append((2 * (y[i] - y[i - 1]) / h) - b[i - 1])
  b.append(y[yArrLen])

  #calc c
  c = []
  for i in range(0, yArrLen + 1): c.append((b[i + 1] - b[i]) / (2 * h))

  def f(newX):
    part = int(newX // h)
    A = a[part]
    B = b[part]
    C = c[part]
    X = xArr[part]

    xx = newX - X
    return A + B * xx + C * xx ** 2


  return f
