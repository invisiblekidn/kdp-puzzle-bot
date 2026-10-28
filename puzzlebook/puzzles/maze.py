"""Mazes on square, honeycomb and round grids, cut into fun shapes, with straight, wavy or outlined walls.

Every maze is a spanning tree of its cells (recursive backtracker), so there is exactly one way through.
Geometry is built in abstract units first, then optionally warped and fitted onto the page.
"""
import math

from ..icons import draw_icon
from ..layout import BOTTOM, frame, header, level_name
from ..lib import S, font
from ..shapes import SHAPE_NAMES, SHAPES
from ..style import title_font

SQ3 = math.sqrt(3)
THIN_SHAPES = {"star", "tree", "moon", "rocket", "gift", "ghost"}
FLOOR = 238                     # gray of the maze floor


def label_and_icon(C, x, y, label, icon, side, x0, x1):
    """Label on one side of the arrow at x and the story picture on the other; swapped near the page edge."""
    w = font(title_font(), 15).getlength(label) / S + 12
    if (side < 0 and x - w < x0) or (side > 0 and x + w > x1):
        side = -side
    C.text(x + side * 9, y, label, title_font(), 15, "ls" if side > 0 else "rs")
    draw_icon(C, icon, x - side * 30, y + 2, 38)


def arrow_down(C, x, y_from, y_to):
    C.stroke([(x, y_from), (x, y_to + 6)], 2.6)
    C.arrow(x, y_to, -90, 9)


# ------------------------------------------------------------------ grids
def square_cells(n):
    s = 2 / n
    return [[(-1 + c * s, 1 - r * s), (-1 + (c + 1) * s, 1 - r * s), (-1 + (c + 1) * s, 1 - (r + 1) * s),
             (-1 + c * s, 1 - (r + 1) * s)] for r in range(n) for c in range(n)], s


def hex_cells(n):
    w = 2 / n                       # pointy-top hexagons, n across
    R = w / SQ3
    out = []
    for r in range(math.ceil(2 / (1.5 * R)) + 1):
        for c in range(-1, n + 1):
            cx, cy = -1 + c * w + (r % 2) * w / 2, 1 - r * 1.5 * R
            out.append([(cx + R * math.cos(math.radians(90 + 60 * k)), cy + R * math.sin(math.radians(90 + 60 * k)))
                        for k in range(6)])
    return out, w


def masked_graph(polys, inside):
    """Cells whose centre lies in the shape -> centres + walls [(a, b or None, polyline)]."""
    centres = [(sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)) for P in polys]
    keep = [i for i, c in enumerate(centres) if abs(c[0]) <= 1 and abs(c[1]) <= 1 and inside(*c)]
    edges = {}
    for i in keep:
        P = polys[i]
        for a, b in zip(P, P[1:] + P[:1]):
            key = tuple(sorted(((round(a[0], 5), round(a[1], 5)), (round(b[0], 5), round(b[1], 5)))))
            edges.setdefault(key, []).append((i, [a, b]))
    # largest connected piece only
    adj = {i: [] for i in keep}
    for owners in edges.values():
        if len(owners) == 2:
            adj[owners[0][0]].append(owners[1][0])
            adj[owners[1][0]].append(owners[0][0])
    best = set()
    seen = set()
    for i in keep:
        if i in seen:
            continue
        comp, queue = {i}, [i]
        for j in queue:
            for k in adj[j]:
                if k not in comp:
                    comp.add(k)
                    queue.append(k)
        seen |= comp
        if len(comp) > len(best):
            best = comp
    index = {old: new for new, old in enumerate(sorted(best))}
    walls = []
    for owners in edges.values():
        mine = [(i, line) for i, line in owners if i in best]
        if len(mine) == 2:
            walls.append((index[mine[0][0]], index[mine[1][0]], mine[0][1]))
        elif len(mine) == 1:
            walls.append((index[mine[0][0]], None, mine[0][1]))
    return [centres[i] for i in sorted(best)], walls, [polys[i] for i in sorted(best)]


def arc(r, a0, a1, step=0.12):
    n = max(2, math.ceil(abs(a1 - a0) * r / step))
    return [(r * math.cos(a0 + (a1 - a0) * t / n), r * math.sin(a0 + (a1 - a0) * t / n)) for t in range(n + 1)]


def polar_graph(rings):
    """Round maze: one centre cell, then rings whose cell count doubles when cells get too wide."""
    counts = [1, 6]
    for i in range(2, rings + 1):
        counts.append(counts[-1] * 2 if 2 * math.pi * i / counts[-1] > 2.0 else counts[-1])
    ids, centres = {}, []
    for i, n in enumerate(counts):
        for j in range(n):
            ids[i, j] = len(centres)
            if i == 0:
                centres.append((0.0, 0.0))
            else:
                a = 2 * math.pi * (j + 0.5) / n
                centres.append(((i + 0.5) * math.cos(a), (i + 0.5) * math.sin(a)))
    walls = []
    for i in range(1, rings + 1):
        n = counts[i]
        k = n // counts[i - 1]
        for j in range(n):
            a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
            walls.append((ids[i, j], ids[i - 1, j // k], arc(i, a0, a1)))
            if n > 1:
                walls.append((ids[i, j], ids[i, (j + 1) % n], [(i * math.cos(a1), i * math.sin(a1)),
                                                                ((i + 1) * math.cos(a1), (i + 1) * math.sin(a1))]))
            if i == rings:
                walls.append((ids[i, j], None, arc(i + 1, a0, a1)))
    return centres, walls


# ------------------------------------------------------------ generation
def carve(n_cells, walls, rnd):
    """Recursive backtracker over the cell graph. Returns the set of opened wall indices and the tree."""
    adj = [[] for _ in range(n_cells)]
    for w, (a, b, _) in enumerate(walls):
        if b is not None:
            adj[a].append((b, w))
            adj[b].append((a, w))
    start = rnd.randrange(n_cells)
    seen, stack, opened = {start}, [start], set()
    tree = [[] for _ in range(n_cells)]
    while stack:
        cur = stack[-1]
        opts = [(nb, w) for nb, w in adj[cur] if nb not in seen]
        if not opts:
            stack.pop()
            continue
        nb, w = rnd.choice(opts)
        opened.add(w)
        tree[cur].append((nb, w))
        tree[nb].append((cur, w))
        seen.add(nb)
        stack.append(nb)
    return opened, tree


def path_between(tree, a, b):
    prev = {a: None}
    queue = [a]
    for cur in queue:
        for nb, w in tree[cur]:
            if nb not in prev:
                prev[nb] = (cur, w)
                queue.append(nb)
    out, cur = [], b
    while prev[cur] is not None:
        p, w = prev[cur]
        out.append((cur, w))
        cur = p
    out.append((a, None))
    return out[::-1]


def mid(line):
    return line[len(line) // 2] if len(line) > 2 else ((line[0][0] + line[-1][0]) / 2, (line[0][1] + line[-1][1]) / 2)


def densify(pts, step):
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n) for t in range(1, n + 1)]
    return out


def chains(lines):
    """Joins wall segments that meet end to end into longer polylines (so they can be smoothed)."""
    key = lambda p: (round(p[0], 5), round(p[1], 5))
    ends = {}
    for i, line in enumerate(lines):
        for p in (line[0], line[-1]):
            ends.setdefault(key(p), []).append(i)
    used, out = set(), []

    def walk(i, from_end):
        line = lines[i] if key(lines[i][0]) == from_end else lines[i][::-1]
        used.add(i)
        chain = list(line)
        while True:
            k = key(chain[-1])
            nxt = [j for j in ends[k] if j not in used]
            if len(ends[k]) != 2 or not nxt:
                return chain
            j = nxt[0]
            seg = lines[j] if key(lines[j][0]) == k else lines[j][::-1]
            used.add(j)
            chain += seg[1:]

    for k, ids in ends.items():
        if len(ids) != 2:
            for i in ids:
                if i not in used:
                    out.append(walk(i, k))
    for i in range(len(lines)):
        if i not in used:
            out.append(walk(i, key(lines[i][0])))
    return out


def chaikin(pts, rounds=2):
    closed = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-6
    for _ in range(rounds):
        if len(pts) < 3:
            return pts
        out = [] if closed else [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = out + ([out[0]] if closed else [pts[-1]])
    return pts


class Warp:
    """Smooth wobble applied to every point, so walls stay joined and the maze stays solvable."""

    def __init__(self, rnd, cell, strength):
        self.a = cell * strength
        self.f = [2 * math.pi / (cell * rnd.uniform(3.5, 5.5)) for _ in range(4)]
        self.p = [rnd.uniform(0, 2 * math.pi) for _ in range(4)]

    def __call__(self, x, y):
        f, p, a = self.f, self.p, self.a
        return (x + a * (math.sin(f[0] * y + p[0]) + 0.5 * math.sin(f[1] * (x + y) + p[1])) / 1.5,
                y + a * (math.sin(f[2] * x + p[2]) + 0.5 * math.sin(f[3] * (x - y) + p[3])) / 1.5)


# ----------------------------------------------------------------- designs
def plan_designs(rnd, theme, count):
    """A varied sequence of (grid, shape, walls) so that no two mazes in a row look alike.

    walls: "straight", "rounded" (soft bubbly corners), "wavy" (wobbly lines) or "outlined" (double walls).
    """
    shapes = list(theme.get("maze_shapes", ["heart", "star", "circle"]))
    rnd.shuffle(shapes)
    styles = {"square": ["straight", "rounded", "wavy", "outlined"], "hex": ["straight", "rounded", "outlined"],
              "round": ["straight", "outlined"]}
    out, used = [], {}
    for i in range(count):
        grid = ["square", "hex", "round", "square", "hex", "square"][i % 6]
        shape = "circle" if grid == "round" else (shapes[i % len(shapes)] if i % 5 else "square")
        k = used.get(grid, 0)
        used[grid] = k + 1
        out.append((grid, shape, styles[grid][(k + i) % len(styles[grid])]))
    return out


class Maze:
    kind = "maze"
    section = "Mazes"
    answer_title = "Maze"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        if "designs" not in ctx:
            ctx["designs"] = plan_designs(rnd, theme, 64)
        self.grid, self.shape, self.style = ctx["designs"][number - 1]
        self.outlined = self.style == "outlined"
        target = 40 + 260 * level ** 1.3                 # cells: about 40 for the youngest, 300 at the end
        if self.shape not in ("square", "circle"):       # a shape needs enough cells to be recognisable
            target = max(target, 170 if self.shape in THIN_SHAPES else 90)
        if self.outlined:
            target *= 0.6                                # outlined walls need wider paths
        if self.grid == "round":
            rings = max(3, round(math.sqrt(target / 3.2)))
            centres, walls = polar_graph(rings)
            cells = [arc(rings + 1, 0, 2 * math.pi)[:-1]]
            cell = 1.0
            self.finish_inside = True
        else:
            inside = SHAPES[self.shape]
            fill = sum(inside(-1 + (i + 0.5) / 20, -1 + (j + 0.5) / 20) for i in range(40) for j in range(40)) / 1600
            n = max(5, round(math.sqrt(target / max(fill, 0.2))))
            if self.grid == "hex":
                polys, cell = hex_cells(round(n * 0.93))
            else:
                polys, cell = square_cells(n)
            centres, walls, cells = masked_graph(polys, inside)
            self.finish_inside = False
        opened, tree = carve(len(centres), walls, rnd)
        outer = [w for w, (a, b, _) in enumerate(walls) if b is None]
        ys = [mid(walls[w][2])[1] for w in outer]
        top = max(ys)
        cand = [w for w, y in zip(outer, ys) if y >= top - cell * 0.6]
        w_in = rnd.choice(cand)
        start = walls[w_in][0]
        if self.finish_inside:
            finish, w_out = 0, None
        else:
            bot = min(ys)
            cand = [w for w, y in zip(outer, ys) if y <= bot + cell * 0.6]
            sx = mid(walls[w_in][2])[0]
            w_out = max(cand, key=lambda w: abs(mid(walls[w][2])[0] - sx) + rnd.random() * cell)
            finish = walls[w_out][0]
        opened |= {w_in} | ({w_out} if w_out is not None else set())
        warp = Warp(rnd, cell, 0.24) if self.style == "wavy" else (lambda x, y: (x, y))
        step = cell * 0.12
        lines = [line for w, (_, _, line) in enumerate(walls) if w not in opened]
        if self.style == "rounded":
            lines = [chaikin(c, 3) for c in chains(lines)]
        self.walls = [[warp(*p) for p in densify(line, step)] for line in lines]
        self.cells = [[warp(*p) for p in densify(P + P[:1], step)] for P in cells]
        # solution: cell centres joined through the middles of the opened walls
        route = path_between(tree, start, finish)
        pts = [mid(walls[w_in][2])]
        for cell_id, w in route:
            if w is not None:
                pts.append(mid(walls[w][2]))
            pts.append(centres[cell_id])
        if w_out is not None:
            pts.append(mid(walls[w_out][2]))
        self.solution = [warp(*p) for p in densify(pts, step)]
        self.entry = warp(*mid(walls[w_in][2]))
        self.exit = warp(*mid(walls[w_out][2])) if w_out is not None else warp(*centres[finish])
        self.cell = cell
        allp = [p for line in self.walls for p in line]
        self.bbox = (min(p[0] for p in allp), min(p[1] for p in allp), max(p[0] for p in allp), max(p[1] for p in allp))
        pair = theme["pairs"][(number - 1) % len(theme["pairs"])]
        self.a, self.b = pair[:2]
        self.line = pair[2] if len(pair) > 2 else f"Help the {self.a} find the {self.b}!"

    def _fit(self, x0, y0, x1, y1):
        bx0, by0, bx1, by1 = self.bbox
        k = min((x1 - x0) / (bx1 - bx0), (y1 - y0) / (by1 - by0))
        ox = (x0 + x1) / 2 - (bx0 + bx1) / 2 * k
        oy = (y0 + y1) / 2 - (by0 + by1) / 2 * k
        return k, lambda p: (ox + p[0] * k, oy + p[1] * k)

    def _draw(self, C, T, k, lw, answer=False):
        cpt = self.cell * k
        for P in self.cells:                             # pale floor inside the maze, as in the MAZES book
            C.poly([T(p) for p in P], FLOOR, seam=True)
        if self.outlined and not answer:
            outer = max(lw * 3.2, cpt * 0.34)
            for line in self.walls:
                C.stroke([T(p) for p in line], outer)
            for line in self.walls:
                C.stroke([T(p) for p in line], outer - 2 * lw * 0.8, gray=255)
        else:
            for line in self.walls:
                C.stroke([T(p) for p in line], lw)
        if answer:
            C.stroke([T(p) for p in self.solution], max(1.8, cpt * 0.16), gray=120)

    def page(self, C, n):
        x0, x1 = frame(n)
        shape = SHAPE_NAMES.get(self.shape, self.shape) if self.grid != "round" else "Round maze"
        top = header(C, n, f"MAZE #{self.number}", f"{shape} · {level_name(self.level)} level · {self.line}")
        area_top = top - 62
        area_bot = BOTTOM + (8 if self.finish_inside else 62)
        k, T = self._fit(x0 + 6, area_bot, x1 - 6, area_top)
        lw = max(2.0, min(4.6, self.cell * k * 0.09))
        self._draw(C, T, k, lw)
        # START above the entrance and FINISH below the exit, each with an arrow and the story picture
        top_y = T((0, self.bbox[3]))[1]
        bot_y = T((0, self.bbox[1]))[1]
        ex, _ = T(self.entry)
        arrow_down(C, ex, top_y + 34, top_y + 6)
        label_and_icon(C, ex, top_y + 24, "START", self.a, -1, x0, x1)
        fx, fy = T(self.exit)
        if self.finish_inside:
            draw_icon(C, self.b, fx, fy, min(40, self.cell * k * 0.9))
        else:
            arrow_down(C, fx, bot_y - 6, bot_y - 34)
            label_and_icon(C, fx, bot_y - 26, "FINISH", self.b, 1, x0, x1)

    def answer(self, C, x0, y0, x1, y1):
        k, T = self._fit(x0, y0, x1, y1)
        self._draw(C, T, k, max(1.0, min(2.2, self.cell * k * 0.08)), answer=True)
