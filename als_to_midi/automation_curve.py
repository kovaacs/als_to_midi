# import matplotlib.pyplot as plt


def de_casteljau(points, u, k=None, i=None, dim=None) -> list:
    """Return the evaluated point by a recursive deCasteljau call
    Keyword arguments aren't intended to be used, and only aid
    during recursion.

    Args:
    points -- list of list of floats, for the control point coordinates
              example: [[0.,0.], [7,4], [-5,3], [2.,0.]]
    u -- local coordinate on the curve: $u \\in [0,1]$

    Keyword args:
    k -- first parameter of the bernstein polynomial
    i -- second parameter of the bernstein polynomial
    dim -- the dimension, deduced by the length of the first point
    """
    if k is None:  # topmost call, k is supposed to be undefined
        # control variables are defined here, and passed down to recursions
        k = len(points) - 1
        i = 0
        dim = len(points[0])

    # return the point if downmost level is reached
    if k == 0:
        return points[i]

    # standard arithmetic operators cannot do vector operations in python,
    # so we break up the formula
    a = de_casteljau(points, u, k=k - 1, i=i, dim=dim)
    b = de_casteljau(points, u, k=k - 1, i=i + 1, dim=dim)
    result = []

    # finally, calculate the result
    for j in range(dim):
        result.append((1 - u) * a[j] + u * b[j])

    return result


def b_curve(time1, value1, time2, value2, cc_x, cc_y, q) -> dict:
    points = {}
    delta_time = time2 - time1
    delta_value = value2 - value1
    points_num = int(delta_time / q)
    p = [[time1, value1],
         [time1 + cc_x * delta_time, value1 + cc_y * delta_value],
         [time1 + delta_time * cc_x, value1 + cc_y * delta_value],
         [time2, value2]]
    x = []
    y = []
    for point in range(0, points_num):
        # p = point / points_num
        coor = de_casteljau(p, p)
        points[point] = {'Time': float(coor[0]), 'Value': int(coor[1])}
        # print(point, points[point])
        x.append(coor[0])
        y.append(coor[1])

    # verification graphic
    # plt.plot(x, y, marker='o')
    # plt.show()

    return points


def affine(time1, value1, time2, value2, q) -> dict:
    points = {}
    a = float((float(value2) - float(value1)) / (float(time2) - float(time1)))
    b = value1 - a * time1
    # print('coefficient:', a)
    # print('test: a * {} = {}'.format(time1, a*time1))

    delta_time = time2 - time1
    points_num = int(delta_time / q)
    for point in range(1, points_num + 1):
        p = point * delta_time / points_num + time1
        # print('test: a * {} = {}'.format(p, a * p))
        points[point] = {'Time': float(p), 'Value': int(a * p + b)}
        # print(point, points[point])

    # print('test: a * {} = {}'.format(time2, a * time2))
    # print('time:', time, 'nombre de points générés:', points_num,"\n")

    return points

# bCurve(0,0,4,127,0,1,0.25)
