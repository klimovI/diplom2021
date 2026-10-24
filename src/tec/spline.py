def spline(xs, ys):
    """Квадратичный интерполяционный сплайн по равноотстоящим узлам xs."""
    h = xs[1] - xs[0]

    # производная в первом узле берётся по первой разности
    b = [(ys[1] - ys[0]) / h]
    for i in range(1, len(ys)):
        b.append(2 * (ys[i] - ys[i - 1]) / h - b[i - 1])
    c = [(b[i + 1] - b[i]) / (2 * h) for i in range(len(ys) - 1)]

    def f(x):
        if not xs[0] <= x <= xs[-1]:
            raise ValueError(f'x = {x} вне узлов сплайна [{xs[0]}, {xs[-1]}]')
        i = min(int((x - xs[0]) // h), len(c) - 1)
        dx = x - xs[i]
        return ys[i] + b[i] * dx + c[i] * dx ** 2

    return f
