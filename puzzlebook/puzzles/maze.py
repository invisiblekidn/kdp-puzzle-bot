"""Rectangular mazes (recursive backtracker) with a guaranteed single solution."""
from ..icons import draw_icon
from ..layout import BOTTOM, footer_level, frame, header
from ..lib import BOLD


def make_maze(cols, rows, cs, ce, rnd):
    hw = [[True] * cols for _ in range(rows + 1)]       # hw[r][c]: wall above cell (r, c)
    vw = [[True] * (cols + 1) for _ in range(rows)]     # vw[r][c]: wall left of cell (r, c)
    seen = [[False] * cols for _ in range(rows)]
    r, c = 0, cs
    seen[r][c] = True
    stack = [(r, c)]
    while stack:
        r, c = stack[-1]
        opts = []
        if r > 0 and not seen[r - 1][c]:
            opts.append((r - 1, c))
        if r < rows - 1 and not seen[r + 1][c]:
            opts.append((r + 1, c))
        if c > 0 and not seen[r][c - 1]:
            opts.append((r, c - 1))
        if c < cols - 1 and not seen[r][c + 1]:
            opts.append((r, c + 1))
        if not opts:
            stack.pop()
            continue
        nr, nc = rnd.choice(opts)
        if nr < r:
            hw[r][c] = False
        elif nr > r:
            hw[nr][c] = False
        elif nc < c:
            vw[r][c] = False
        else:
            vw[r][nc] = False
        seen[nr][nc] = True
        stack.append((nr, nc))
    hw[0][cs] = False                                   # entrance (top)
    hw[rows][ce] = False                                # exit (bottom)
    # solution by BFS
    prev = {(0, cs): None}
    queue = [(0, cs)]
    for r, c in queue:
        steps = []
        if r > 0 and not hw[r][c]:
            steps.append((r - 1, c))
        if r < rows - 1 and not hw[r + 1][c]:
            steps.append((r + 1, c))
        if c > 0 and not vw[r][c]:
            steps.append((r, c - 1))
        if c < cols - 1 and not vw[r][c + 1]:
            steps.append((r, c + 1))
        for nxt in steps:
            if nxt not in prev:
                prev[nxt] = (r, c)
                queue.append(nxt)
    path, cur = [], (rows - 1, ce)
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return dict(cols=cols, rows=rows, hw=hw, vw=vw, cs=cs, ce=ce, sol=path[::-1])


def draw_maze(C, m, mx0, mytop, cell, lw, solution=False, sol_lw=3.0):
    rows, cols = m["rows"], m["cols"]
    half = lw / 2
    for r in range(rows + 1):
        for c in range(cols):
            if m["hw"][r][c]:
                y = mytop - r * cell
                C.rect(mx0 + c * cell - half, y - half, mx0 + (c + 1) * cell + half, y + half)
    for r in range(rows):
        for c in range(cols + 1):
            if m["vw"][r][c]:
                x = mx0 + c * cell
                C.rect(x - half, mytop - r * cell + half, x + half, mytop - (r + 1) * cell - half)
    if solution:
        pts = [(mx0 + (c + 0.5) * cell, mytop - (r + 0.5) * cell) for r, c in m["sol"]]
        pts = [(pts[0][0], mytop + cell * 0.4)] + pts + [(pts[-1][0], mytop - rows * cell - cell * 0.4)]
        C.stroke(pts, sol_lw, gray=110)


class Maze:
    kind = "maze"
    section = "Mazes"
    answer_title = "Maze"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        cols = round(6 + 10 * level)                    # 6x8 for the youngest .. 16x20 at the end
        rows = round(cols * 1.25)
        cs = rnd.randrange(cols)
        ce = rnd.randrange(cols)
        if abs(cs - ce) < cols // 3:
            ce = cols - 1 - cs
        self.m = make_maze(cols, rows, cs, ce, rnd)
        pair = theme["pairs"][(number - 1) % len(theme["pairs"])]
        self.a, self.b = pair[:2]
        self.line = pair[2] if len(pair) > 2 else f"Help the {self.a} find the {self.b}!"

    def page(self, C, n):
        m = self.m
        x0, x1 = frame(n)
        top = header(C, n, f"Maze {self.number}", self.line)
        area_top, area_bot = top - 50, BOTTOM + 52
        cell = min((x1 - x0 - 10) / m["cols"], (area_top - area_bot) / m["rows"])
        mx0 = (x0 + x1) / 2 - m["cols"] * cell / 2
        mytop = area_top - ((area_top - area_bot) - m["rows"] * cell) / 2
        draw_maze(C, m, mx0, mytop, cell, max(2.4, min(5.0, cell * 0.08)))
        sx = mx0 + (m["cs"] + 0.5) * cell
        ex = mx0 + (m["ce"] + 0.5) * cell
        mybot = mytop - m["rows"] * cell
        C.text(sx, mytop + 9, "START", BOLD, 11)
        draw_icon(C, self.a, sx, mytop + 38, 34)
        C.text(ex, mybot - 18, "FINISH", BOLD, 11)
        draw_icon(C, self.b, ex, mybot - 41, 34)
        footer_level(C, n, self.level)

    def answer(self, C, x0, y0, x1, y1):
        m = self.m
        cell = min((x1 - x0) / m["cols"], (y1 - y0) / (m["rows"] + 0.9))
        mx0 = (x0 + x1) / 2 - m["cols"] * cell / 2
        mytop = y1 - 0.45 * cell
        draw_maze(C, m, mx0, mytop, cell, max(1.2, min(2.4, cell * 0.08)), solution=True,
                  sol_lw=max(2.0, cell * 0.14))
