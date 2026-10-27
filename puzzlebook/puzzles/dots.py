"""Dot-to-dot pictures: numbered points that reveal a shape when joined in order."""
import math

from ..layout import BOTTOM, footer_level, frame, header
from ..lib import BOLD, REG, ellipse_pts, fit_to_box, heart_pts, resample, star_pts


def smooth_shapes():
    heart = resample(heart_pts(8, 400), 12, closed=True)
    flower = [((1 + 0.4 * math.cos(6 * t)) * math.cos(t), (1 + 0.4 * math.cos(6 * t)) * math.sin(t))
              for t in [2 * math.pi * k / 24 for k in range(24)]]
    # crescent moon: outer arc + inner arc
    R = 5.0
    outer = ellipse_pts(0, 0, R, R, 0, 75, 285, 7)
    px, py = outer[0]
    cx2 = 2.6
    rho = math.hypot(px - cx2, py)
    b0 = math.degrees(math.atan2(py, px - cx2))
    inner = ellipse_pts(cx2, 0, rho, rho, 0, 360 - b0, b0, 7)[1:-1]
    moon = outer + inner
    # ice cream: cone + round scoop
    scoop = ellipse_pts(4, 7.3, 3.6, 3.6, 0, 190, -10, 7)
    ice = [(4, 0), (2.8, 2.3), (2.1, 4.5), (0.5, 5.3)] + scoop + [(7.5, 5.3), (5.9, 4.5), (5.2, 2.3)]
    sun = star_pts(5, 3.1, 8)
    return heart, flower, moon, ice, sun


def dot_shapes():
    heart, flower, moon, ice, sun = smooth_shapes()
    shapes = [
        ("crown", [(0, 0), (0, 6), (2, 3.4), (4, 7), (6, 3.4), (8, 6), (8, 0)]),
        ("fish", [(0, 4), (1.8, 6), (4.5, 6.8), (7.2, 5.6), (9, 7.5), (9, 0.5), (7.2, 2.4), (4.5, 1.2), (1.8, 2)]),
        ("house", [(0, 0), (0, 5), (4, 9), (6, 7), (6, 9), (7.4, 9), (7.4, 5.6), (8, 5), (8, 0)]),
        ("star", star_pts(5, 2, 5)),
        ("rocket", [(4, 11), (5.4, 8.6), (5.4, 3.4), (7.4, 1.6), (7.4, 0), (5.2, 1.1), (2.8, 1.1), (0.6, 0),
                    (0.6, 1.6), (2.6, 3.4), (2.6, 8.6)]),
        ("cat", [(0.8, 9.6), (3.0, 7.7), (5.0, 7.7), (7.2, 9.6), (7.7, 6.3), (8, 4), (7, 1.8), (5.2, 0.5),
                 (2.8, 0.5), (1, 1.8), (0, 4), (0.3, 6.3)]),
        ("heart", heart),
        ("ice cream", ice),
        ("moon", moon),
        ("tree", [(3.2, 0), (3.2, 2), (0, 2), (2.2, 4.6), (0.8, 4.6), (3, 7.4), (1.8, 7.4), (4, 10), (6.2, 7.4),
                  (5, 7.4), (7.2, 4.6), (5.8, 4.6), (8, 2), (4.8, 2), (4.8, 0)]),
        ("sun", sun),
        ("flower", flower),
    ]
    return sorted(shapes, key=lambda s: len(s[1]))


def label_dirs(pts):
    """Unit vector pointing away from the polygon at every vertex (for number labels)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sign = 1 if area > 0 else -1
    out = []
    for i in range(n):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % n]
        e1 = (p[0] - a[0], p[1] - a[1])
        e2 = (b[0] - p[0], b[1] - p[1])
        l1, l2 = math.hypot(*e1) or 1, math.hypot(*e2) or 1
        s = (-e1[0] / l1 + e2[0] / l2, -e1[1] / l1 + e2[1] / l2)
        ls = math.hypot(*s)
        cross = e1[0] * e2[1] - e1[1] * e2[0]
        if ls < 0.08:
            d = (sign * (e1[1] / l1 + e2[1] / l2), -sign * (e1[0] / l1 + e2[0] / l2))
        else:
            convex = cross * sign > 0
            d = (-s[0], -s[1]) if convex else s
        ld = math.hypot(*d) or 1
        out.append((d[0] / ld, d[1] / ld))
    return out


SHAPES = dot_shapes()
MAX_COUNT = len(SHAPES)


class Dots:
    kind = "dots"
    section = "Dot to Dot"
    answer_title = "Dot to Dot"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        used = ctx.setdefault("used", set())
        want = round(level * (len(SHAPES) - 1))
        free = [i for i in range(len(SHAPES)) if i not in used] or list(range(len(SHAPES)))
        idx = min(free, key=lambda i: abs(i - want))
        used.add(idx)
        self.name, self.raw = SHAPES[idx]

    def page(self, C, n):
        x0, x1 = frame(n)
        N = len(self.raw)
        top = header(C, n, f"Dot to Dot {self.number}", f"Join the dots from 1 to {N} to find the hidden picture!")
        pts, _ = fit_to_box(self.raw, x0 + 70, BOTTOM + 84, x1 - 70, top - 28)
        dirs = label_dirs(pts)
        pt = 17 if N <= 12 else (15 if N <= 16 else 13)
        for i, ((x, y), (dx, dy)) in enumerate(zip(pts, dirs)):
            C.dot(x, y, 4.6)
            d = 4.6 + pt * 0.62 + 3
            C.text(x + dx * d, y + dy * d, str(i + 1), BOLD, pt, "mm")
        C.ring(pts[0][0], pts[0][1], 9.5, 1.6)
        C.text((x0 + x1) / 2, BOTTOM + 14, "Then join the last dot back to dot 1 and colour the picture!", REG, 13, "ms")
        footer_level(C, n, self.level)

    def answer(self, C, x0, y0, x1, y1):
        pts, _ = fit_to_box(self.raw, x0 + 20, y0 + 26, x1 - 20, y1 - 6)
        C.stroke(pts, 2.4, closed=True)
        art = "an" if self.name[0] in "aeiou" else "a"
        C.text((x0 + x1) / 2, y0 + 4, f"It's {art} {self.name}!", REG, 12, "ms")
