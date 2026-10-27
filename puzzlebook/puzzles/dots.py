"""Dot-to-dot pictures: the child joins 25-75 numbered dots; eyes, mouths and spots are already printed."""
import math

from ..figures import FIGURES
from ..layout import BOTTOM, footer_level, frame, header
from ..lib import BOLD, REG, S, font

DOT_R = 2.3                 # dot radius (pt)
NUM_PT = 9.5                # number size (pt)


def hermite(p0, p1, m0, m1, n):
    out = []
    for k in range(n):
        t = k / n
        h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        out.append((h00 * p0[0] + h10 * m0[0] + h01 * p1[0] + h11 * m1[0],
                    h00 * p0[1] + h10 * m0[1] + h01 * p1[1] + h11 * m1[1]))
    return out


def spline(pts, closed=True, n=24):
    """Catmull-Rom curve through the points; (x, y, 1) points are sharp corners.
    Returns the dense curve and the index in it of every control point."""
    P = [(p[0], p[1]) for p in pts]
    corner = [len(p) > 2 for p in pts]
    m = len(P)
    if not closed:
        corner[0] = corner[-1] = True

    def tangent(i, j):                 # tangent at control point i on segment i -> j
        if corner[i]:
            return (P[j][0] - P[i][0], P[j][1] - P[i][1]) if j != i else (0, 0)
        a, b = P[(i - 1) % m], P[(i + 1) % m]
        return ((b[0] - a[0]) / 2, (b[1] - a[1]) / 2)

    dense, marks = [], []
    segs = m if closed else m - 1
    for i in range(segs):
        j = (i + 1) % m
        m0 = tangent(i, j)
        m1 = (P[j][0] - P[i][0], P[j][1] - P[i][1]) if corner[j] else tangent(j, j)
        marks.append(len(dense))
        dense += hermite(P[i], P[j], m0, m1, n)
    if not closed:
        marks.append(len(dense))
        dense.append(P[-1])
    return dense, marks, corner


def place_dots(outline, count):
    """count dots along the closed outline: every corner gets one, the rest are spread by length."""
    dense, marks, corner = spline(outline)
    L = len(dense)
    stops = [marks[i] for i in range(len(outline)) if corner[i]] or [0]
    seg = lambda a, b: sum(math.dist(dense[k % L], dense[(k + 1) % L]) for k in range(a, b))
    spans = [(stops[i], stops[(i + 1) % len(stops)] + (L if i + 1 == len(stops) else 0)) for i in range(len(stops))]
    lengths = [seg(a, b) for a, b in spans]
    total = sum(lengths)
    extra = max(0, count - len(stops))
    share = [lengths[i] / total * extra for i in range(len(spans))]
    alloc = [int(s) for s in share]
    for i in sorted(range(len(spans)), key=lambda i: share[i] - alloc[i], reverse=True)[:extra - sum(alloc)]:
        alloc[i] += 1
    out = []
    for (a, b), k, length in zip(spans, alloc, lengths):
        out.append(dense[a % L])
        if k:
            step = length / (k + 1)
            acc, want = 0.0, step
            for j in range(a, b):
                p, q = dense[j % L], dense[(j + 1) % L]
                d = math.dist(p, q)
                while d and acc + d >= want and len(out) < 10 ** 6 and want < length - 1e-9:
                    u = (want - acc) / d
                    out.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u))
                    want += step
                acc += d
    return out, dense


def label_positions(dots, curve, details_pts):
    """Puts each number next to its dot, away from the outline, other dots and other numbers."""
    n = len(dots)
    area = sum(dots[i][0] * dots[(i + 1) % n][1] - dots[(i + 1) % n][0] * dots[i][1] for i in range(n))
    sign = 1 if area > 0 else -1
    f = font(BOLD, NUM_PT)
    boxes = []
    obstacles = curve[::2] + details_pts
    out = []
    for i, (x, y) in enumerate(dots):
        a, b = dots[i - 1], dots[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1
        nx, ny = sign * ty / tl, -sign * tx / tl          # outward normal
        w = f.getlength(str(i + 1)) / S
        h = NUM_PT * 0.72
        best = None
        for dist in (DOT_R + 6, DOT_R + 9, DOT_R + 13):
            for turn in (0, 35, -35, 70, -70, 110, -110, 150, -150, 180):
                c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
                dx, dy = nx * c - ny * s, nx * s + ny * c
                cx, cy = x + dx * (dist + w / 2 * abs(dx)), y + dy * (dist + h / 2 * abs(dy))
                box = (cx - w / 2 - 1, cy - h / 2 - 1, cx + w / 2 + 1, cy + h / 2 + 1)
                if any(box[0] < bx1 and bx0 < box[2] and box[1] < by1 and by0 < box[3] for bx0, by0, bx1, by1 in boxes):
                    continue
                if any(box[0] - 1.5 < px < box[2] + 1.5 and box[1] - 1.5 < py < box[3] + 1.5 for px, py in obstacles):
                    continue
                if any(j != i and box[0] - DOT_R < px < box[2] + DOT_R and box[1] - DOT_R < py < box[3] + DOT_R
                       for j, (px, py) in enumerate(dots)):
                    continue
                own = math.hypot(cx - x, cy - y)
                if any(j != i and math.hypot(cx - px, cy - py) < own for j, (px, py) in enumerate(dots)):
                    continue                             # the number must sit closest to its own dot

                best = (cx, cy, box)
                break
            if best:
                break
        if not best:
            cx, cy = x + nx * (DOT_R + 7), y + ny * (DOT_R + 7)
            best = (cx, cy, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        boxes.append(best[2])
        out.append(best[:2])
    return out


def detail_paths(details):
    """Details as (kind, points, extra) in figure coordinates."""
    out = []
    for d in details:
        kind = d[0]
        if kind == "line":
            out.append(("stroke", spline(d[1], closed=False)[0], False))
        elif kind == "loop":
            out.append(("stroke", spline(d[1])[0], True))
        elif kind in ("circle", "eye"):
            x, y, r = d[1:]
            out.append(("stroke", [(x + r * math.cos(t / 24 * math.pi), y + r * math.sin(t / 24 * math.pi))
                                   for t in range(48)], True))
            if kind == "eye":
                out.append(("fill", [(x + r * 0.5 * math.cos(t / 12 * math.pi), y - r * 0.15 + r * 0.5 * math.sin(t / 12 * math.pi))
                                     for t in range(24)], True))
        elif kind == "dot":
            x, y, r = d[1:]
            out.append(("fill", [(x + r * math.cos(t / 12 * math.pi), y + r * math.sin(t / 12 * math.pi))
                                 for t in range(24)], True))
    return out


class Dots:
    kind = "dots"
    section = "Dot to Dot"
    answer_title = "Dot to Dot"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        if "order" not in ctx:
            own = [f for f in theme.get("dots", []) if f in FIGURES]
            rest = [f for f in FIGURES if f not in own]
            rnd.shuffle(own)
            rnd.shuffle(rest)
            ctx["order"] = own + rest
        order = ctx["order"]
        self.name = order[(number - 1) % len(order)]
        fig = FIGURES[self.name]
        self.count = 25 + round(50 * level)
        self.outline, self.details = fig["outline"], fig["details"]

    def _geometry(self, x0, y0, x1, y1):
        dots, dense = place_dots(self.outline, self.count)
        paths = detail_paths(self.details)
        allp = dense + [p for _, pts, _ in paths for p in pts]
        bx0, by0 = min(p[0] for p in allp), min(p[1] for p in allp)
        bx1, by1 = max(p[0] for p in allp), max(p[1] for p in allp)
        k = min((x1 - x0) / (bx1 - bx0), (y1 - y0) / (by1 - by0))
        ox, oy = (x0 + x1) / 2 - (bx0 + bx1) / 2 * k, (y0 + y1) / 2 - (by0 + by1) / 2 * k
        T = lambda p: (ox + p[0] * k, oy + p[1] * k)
        return [T(p) for p in dots], [T(p) for p in dense], [(kind, [T(p) for p in pts], c) for kind, pts, c in paths]

    def _details(self, C, paths, lw):
        for kind, pts, closed in paths:
            if kind == "fill":
                C.poly(pts, 0)
            else:
                C.stroke(pts, lw, closed=closed)

    def page(self, C, n):
        x0, x1 = frame(n)
        top = header(C, n, f"Dot to Dot {self.number}",
                     f"Join the dots from 1 to {self.count}, then join {self.count} back to 1. Colour your picture!")
        dots, dense, paths = self._geometry(x0 + 30, BOTTOM + 20, x1 - 30, top - 20)
        self._details(C, paths, 2.2)
        labels = label_positions(dots, dense, [p for _, pts, _ in paths for p in pts[::2]])
        for i, ((x, y), (lx, ly)) in enumerate(zip(dots, labels)):
            C.dot(x, y, DOT_R)
            C.text(lx, ly, str(i + 1), BOLD, NUM_PT, "mm")
        C.ring(dots[0][0], dots[0][1], DOT_R + 3.2, 1.2)
        footer_level(C, n, self.level)

    def answer(self, C, x0, y0, x1, y1):
        dots, dense, paths = self._geometry(x0 + 10, y0 + 22, x1 - 10, y1 - 4)
        C.stroke(dense, 1.8, closed=True)
        self._details(C, paths, 1.2)
        name = self.name.replace("gingerbread", "gingerbread man")
        art = "an" if name[0] in "aeiou" else "a"
        C.text((x0 + x1) / 2, y0 + 4, f"It's {art} {name}!", REG, 12, "ms")
