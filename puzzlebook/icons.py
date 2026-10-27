"""Simple outline icons (black line art, white fill) so children can colour them in.

Each icon is designed in a -50..50 box (y up) and scaled to the requested size in points.
"""
import math

from .lib import ellipse_pts


class Ctx:
    def __init__(self, C, cx, cy, size, rot=0.0):
        self.C, self.cx, self.cy, self.k = C, cx, cy, size / 100.0
        self.lw = max(1.5, 3.2 * self.k)
        self.cr, self.sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def pt(self, x, y):
        x, y = x * self.cr - y * self.sr, x * self.sr + y * self.cr
        return (self.cx + x * self.k, self.cy + y * self.k)

    def pts(self, ps):
        return [self.pt(x, y) for x, y in ps]

    def poly(self, ps, fill=255, closed=True, w=None):
        P = self.pts(ps)
        if closed and fill is not None:
            self.C.poly(P, fill)
        self.C.stroke(P, w or self.lw, closed=closed)

    def ell(self, cx, cy, rx, ry, rot=0, fill=255, w=None):
        self.poly(ellipse_pts(cx, cy, rx, ry, rot, n=64), fill, True, w)

    def circ(self, cx, cy, r, fill=255, w=None):
        self.ell(cx, cy, r, r, 0, fill, w)

    def line(self, ax, ay, bx, by, w=None):
        self.C.stroke(self.pts([(ax, ay), (bx, by)]), w or self.lw)

    def arc(self, cx, cy, rx, ry, a0, a1, w=None):
        self.C.stroke(self.pts(ellipse_pts(cx, cy, rx, ry, 0, a0, a1, 24)), w or self.lw)

    def dot(self, x, y, r):
        self.C.poly(self.pts(ellipse_pts(x, y, r, r, n=24)), 0)

    def union(self, circles, w=None):
        """Outline of the union of circles (clean cloud / tree / petal shapes)."""
        for cx, cy, r in circles:
            self.C.poly(self.pts(ellipse_pts(cx, cy, r, r, n=90)), 255)
        for i, (cx, cy, r) in enumerate(circles):
            N = 720
            keep = []
            for s in range(N):
                a = 2 * math.pi * s / N
                x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                inside = any(j != i and math.hypot(x - ox, y - oy) < orr - 1e-6
                             for j, (ox, oy, orr) in enumerate(circles))
                keep.append(None if inside else (x, y))
            if all(p is not None for p in keep):
                self.C.stroke(self.pts(keep), w or self.lw, closed=True)
                continue
            start = keep.index(None)
            seq = keep[start:] + keep[:start]
            run = []
            for p in seq + [None]:
                if p is None:
                    if len(run) > 1:
                        self.C.stroke(self.pts(run), w or self.lw)
                    run = []
                else:
                    run.append(p)


def star(c):
    pts = []
    for i in range(10):
        r = 46 if i % 2 == 0 else 19
        a = math.radians(90 + 36 * i)
        pts.append((r * math.cos(a), r * math.sin(a) - 2))
    c.poly(pts)


def heart(c):
    pts = []
    for i in range(120):
        t = 2 * math.pi * i / 120
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * 2.6, y * 2.6 + 5))
    c.poly(pts)


def flower(c):
    c.line(0, -8, 0, -46)
    c.ell(12, -30, 12, 5, rot=35)
    c.union([(21 * math.cos(math.radians(a)), 16 + 21 * math.sin(math.radians(a)), 13)
             for a in range(90, 450, 60)])
    c.circ(0, 16, 10)


def apple(c):
    c.line(0, 15, 4, 34)
    c.ell(16, 30, 12, 5, rot=20)
    c.union([(-13, -6, 28), (13, -6, 28)])


def house(c):
    c.poly([(18, 16), (18, 36), (29, 36), (29, 14)])
    c.poly([(-32, -40), (32, -40), (32, 4), (-32, 4)])
    c.poly([(-42, 4), (0, 42), (42, 4)])
    c.poly([(-9, -40), (9, -40), (9, -14), (-9, -14)])
    c.poly([(14, -26), (26, -26), (26, -14), (14, -14)])


def fish(c):
    c.poly([(26, 0), (48, 20), (48, -20)])
    c.poly([(-10, 20), (6, 36), (14, 18)])
    c.ell(-6, 0, 36, 24)
    c.dot(-26, 5, 4)
    c.arc(-34, -2, 7, 7, 280, 350, w=c.lw * 0.8)


def cloud(c):
    c.union([(-24, -4, 20), (0, 2, 26), (26, -4, 20)])


def sun(c):
    for i in range(12):
        a = math.radians(30 * i)
        c.line(30 * math.cos(a), 30 * math.sin(a), 46 * math.cos(a), 46 * math.sin(a))
    c.circ(0, 0, 22)
    c.dot(-8, 5, 3)
    c.dot(8, 5, 3)
    c.arc(0, -2, 11, 9, 200, 340, w=c.lw * 0.8)


def moon(c):
    R = 40
    outer = ellipse_pts(0, 0, R, R, 0, 75, 285, 60)
    px, py = outer[0]
    cx2 = 21.0
    rho = math.hypot(px - cx2, py)
    b0 = math.degrees(math.atan2(py, px - cx2))
    inner = ellipse_pts(cx2, 0, rho, rho, 0, 360 - b0, b0, 60)
    c.poly([(x + 15, y) for x, y in outer + inner])


def balloon(c):
    c.C.stroke(c.pts([(5 * math.sin(t * 0.9), -32 - t * 2.4) for t in range(8)]), c.lw * 0.8)
    c.poly([(-5, -23), (5, -23), (0, -31)])
    c.ell(0, 12, 27, 34)
    c.arc(-8, 18, 9, 14, 100, 170, w=c.lw * 0.7)


def flag(c):
    c.poly([(-20, 46), (42, 32), (-20, 18)])
    c.line(-20, -46, -20, 48, w=c.lw * 1.4)


def ball(c):
    c.circ(0, 0, 40)
    c.ell(0, 0, 16, 40, fill=None)
    c.line(-40, 0, 40, 0)


def carrot(c):
    c.ell(0, 28, 6, 15)
    c.ell(-11, 25, 6, 14, rot=35)
    c.ell(11, 25, 6, 14, rot=-35)
    c.poly([(-15, 12), (15, 12), (0, -46)])
    for y, hw in ((2, 7), (-12, 5), (-26, 3)):
        c.line(-hw, y, 0, y, w=c.lw * 0.7)


def cheese(c):
    c.poly([(-46, -24), (46, -24), (46, 6), (-46, 34)])
    for x, y, r in ((-22, -8, 6), (2, -14, 4.5), (26, -8, 7), (-4, 6, 4)):
        c.circ(x, y, r)


def tree(c):
    c.poly([(-7, -46), (7, -46), (7, -6), (-7, -6)])
    c.union([(0, 16, 24), (-17, -2, 19), (17, -2, 19)])


def boat(c):
    c.poly([(0, 44), (0, -4), (34, -4)])
    c.poly([(0, 30), (0, -4), (-26, -4)])
    c.poly([(-46, -6), (46, -6), (30, -32), (-30, -32)])


def car(c):
    c.poly([(-44, -18), (44, -18), (44, 2), (24, 2), (14, 22), (-18, 22), (-30, 2), (-44, 2)])
    c.poly([(-24, 4), (-15, 18), (-2, 18), (-2, 4)])
    c.poly([(2, 4), (2, 18), (13, 18), (20, 4)])
    for x in (-26, 26):
        c.circ(x, -20, 11)
        c.circ(x, -20, 4)


def bunny(c):
    c.ell(-12, 26, 8, 22, rot=8)
    c.ell(12, 26, 8, 22, rot=-8)
    c.ell(-12, 26, 3.5, 15, rot=8, fill=None, w=c.lw * 0.7)
    c.ell(12, 26, 3.5, 15, rot=-8, fill=None, w=c.lw * 0.7)
    c.circ(0, -12, 26)
    c.dot(-9, -6, 3)
    c.dot(9, -6, 3)
    c.poly([(-4, -14), (4, -14), (0, -19)], fill=0, w=c.lw * 0.5)
    c.arc(-4, -24, 4, 4, 180, 360, w=c.lw * 0.7)
    c.arc(4, -24, 4, 4, 180, 360, w=c.lw * 0.7)


def mouse(c):
    for sx in (-1, 1):
        c.circ(sx * 24, 22, 15)
        c.circ(sx * 24, 22, 8)
    c.ell(0, -4, 30, 26)
    c.dot(-11, 2, 3.5)
    c.dot(11, 2, 3.5)
    c.dot(0, -12, 4.5)
    for sx in (-1, 1):
        c.line(sx * 10, -16, sx * 42, -12, w=c.lw * 0.6)
        c.line(sx * 10, -20, sx * 42, -26, w=c.lw * 0.6)


def bee(c):
    c.ell(-4, 26, 11, 17, rot=20)
    c.ell(14, 26, 11, 17, rot=-20)
    c.ell(4, -2, 30, 19)
    for x in (-6, 10):
        c.line(x, -15, x, 11, w=c.lw * 2.2)
    c.circ(-30, -2, 12)
    c.dot(-34, 0, 2.5)
    c.line(-34, 9, -42, 22, w=c.lw * 0.7)
    c.line(-26, 10, -26, 24, w=c.lw * 0.7)
    c.poly([(34, -2), (46, -2), (34, 4)], fill=0, w=c.lw * 0.5)


def scissors(c):
    for sy in (-1, 1):
        c.circ(-32, sy * 17, 12)
        c.line(-24, sy * 13, 46, -sy * 22, w=c.lw * 1.3)
    c.circ(0, 0, 3.5)


def pumpkin(c):
    c.poly([(-4, 26), (4, 26), (8, 42), (0, 44)])
    c.union([(-22, -6, 24), (22, -6, 24), (0, -4, 28)])
    c.arc(-10, -6, 9, 26, 110, 250, w=c.lw * 0.8)
    c.arc(10, -6, 9, 26, -70, 70, w=c.lw * 0.8)


def ghost(c):
    pts = ellipse_pts(0, 8, 30, 34, 0, 0, 180, 40)
    pts.append((-30, -40))
    for i in range(1, 7):
        pts.append((-30 + 10 * i, -32 if i % 2 else -40))
    c.poly(pts)
    c.ell(-11, 14, 5, 7, fill=0)
    c.ell(11, 14, 5, 7, fill=0)
    c.ell(0, -4, 6, 8, fill=None, w=c.lw * 0.8)


def gift(c):
    c.poly([(-38, -40), (38, -40), (38, 12), (-38, 12)])
    c.poly([(-44, 12), (44, 12), (44, 28), (-44, 28)])
    c.poly([(-8, -40), (8, -40), (8, 28), (-8, 28)], fill=None)
    c.ell(-14, 36, 14, 9, rot=20)
    c.ell(14, 36, 14, 9, rot=-20)
    c.circ(0, 31, 5)


def snowman(c):
    c.circ(0, -22, 26)
    c.circ(0, 18, 18)
    c.poly([(-16, 32), (16, 32), (12, 34), (12, 50), (-12, 50), (-12, 34)])
    c.dot(-6, 22, 2.6)
    c.dot(6, 22, 2.6)
    c.poly([(0, 16), (12, 13), (0, 12)], fill=0, w=c.lw * 0.5)
    for y in (-12, -22, -32):
        c.dot(0, y, 2.8)


def rocket(c):
    c.poly([(-14, -20), (-30, -40), (-14, -38)])
    c.poly([(14, -20), (30, -40), (14, -38)])
    c.poly([(0, 48), (14, 26), (14, -34), (-14, -34), (-14, 26)])
    c.circ(0, 10, 7)
    c.poly([(-8, -34), (8, -34), (0, -48)])


def planet(c):
    c.ell(0, 0, 48, 12, rot=-18)
    c.circ(0, 0, 26)
    c.C.stroke(c.pts(ellipse_pts(0, 0, 48, 12, -18, 192, 348, 30)), c.lw)


ICONS = {f.__name__: f for f in (
    star, heart, flower, apple, house, fish, cloud, sun, moon, balloon, flag, ball,
    carrot, cheese, tree, boat, car, bunny, mouse, bee, scissors,
    pumpkin, ghost, gift, snowman, rocket, planet)}


def draw_icon(C, name, cx, cy, size, rot=0.0):
    ICONS[name](Ctx(C, cx, cy, size, rot))
