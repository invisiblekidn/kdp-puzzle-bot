"""Outline shapes used as masks for shaped mazes.

Each shape is a test inside(u, v) on the square -1..1 x -1..1 (y up).
"""
import math

from .lib import fit_to_box, heart_pts, star_pts


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def poly(pts):
    P, _ = fit_to_box(pts, -1, -1, 1, 1)
    return lambda u, v: point_in_poly(u, v, P)


def circles(*cs):
    return lambda u, v: any((u - x) ** 2 + (v - y) ** 2 <= r * r for x, y, r in cs)


def union(*tests):
    return lambda u, v: any(t(u, v) for t in tests)


def box(x0, y0, x1, y1):
    return lambda u, v: x0 <= u <= x1 and y0 <= v <= y1


SHAPES = {
    "square": lambda u, v: True,
    "circle": circles((0, 0, 1)),
    "heart": poly(heart_pts(2, 160)),
    "star": poly(star_pts(1, 0.6, 5)),
    "diamond": poly([(0, 1), (-0.8, 0), (0, -1), (0.8, 0)]),
    "tree": poly([(3.2, 0), (3.2, 2), (0, 2), (2.2, 4.6), (0.8, 4.6), (3, 7.4), (1.8, 7.4), (4, 10), (6.2, 7.4),
                  (5, 7.4), (7.2, 4.6), (5.8, 4.6), (8, 2), (4.8, 2), (4.8, 0)]),
    "snowman": circles((0, -0.4, 0.6), (0, 0.5, 0.42)),
    "gift": union(box(-0.85, -1, 0.85, 0.45), box(-1, 0.45, 1, 0.75), circles((-0.3, 0.82, 0.2), (0.3, 0.82, 0.2))),
    "pumpkin": union(circles((-0.42, -0.12, 0.56), (0.42, -0.12, 0.56), (0, -0.08, 0.62)), box(-0.12, 0.4, 0.14, 0.88)),
    "ghost": poly([(math.cos(math.radians(a)) * 0.8, 0.2 + math.sin(math.radians(a)) * 0.8) for a in range(0, 181, 10)]
                  + [(-0.8, -1), (-0.53, -0.8), (-0.27, -1), (0, -0.8), (0.27, -1), (0.53, -0.8), (0.8, -1)]),
    "moon": lambda u, v: u * u + v * v <= 1 and (u - 0.5) ** 2 + (v - 0.2) ** 2 > 0.72 ** 2,
    "rocket": poly([(0, 10), (1.6, 7.6), (1.8, 2.6), (3.4, 0.4), (3.4, -1), (1.2, 0), (-1.2, 0), (-3.4, -1), (-3.4, 0.4),
                    (-1.8, 2.6), (-1.6, 7.6)]),
    "fish": union(lambda u, v: (u + 0.18) ** 2 / 0.72 ** 2 + v * v / 0.55 ** 2 <= 1,
                  lambda u, v: 0.42 <= u <= 1 and abs(v) <= (u - 0.42) * 0.95),
    "apple": union(circles((-0.36, -0.12, 0.66), (0.36, -0.12, 0.66)), box(-0.08, 0.45, 0.1, 0.9)),
    "cloud": circles((-0.55, -0.15, 0.45), (0, 0.15, 0.6), (0.55, -0.15, 0.45), (0, -0.3, 0.45)),
}
