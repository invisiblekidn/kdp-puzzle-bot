"""Seek and find: a busy scene of icons; the child finds and counts the ones shown in the legend."""
import math

from ..icons import draw_icon
from ..layout import BOTTOM, frame, header, level_name
from ..lib import BOLD, REG, rounded

ASPECT = 1.12          # scene height / width


def scatter(rnd, count, size, aspect, tries=6000):
    """Up to count non-overlapping circles (x, y, diameter) in a 1 x aspect box, sizes varying a little."""
    out = []
    for _ in range(tries):
        if len(out) == count:
            break
        d = size * rnd.uniform(0.85, 1.2)
        r = d * 0.56
        x, y = rnd.uniform(r, 1 - r), rnd.uniform(r, aspect - r)
        if all(math.hypot(x - ox, y - oy) > r + od * 0.56 + 0.012 for ox, oy, od in out):
            out.append((x, y, d))
    return out


class Hidden:
    kind = "hidden"
    section = "Seek and Find"
    answer_title = "Seek and Find"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        icons = list(theme["icons"])
        rnd.shuffle(icons)
        n_targets = 3 if level < 0.67 else 4
        self.targets = [(name, rnd.randint(2, 3 + round(3 * level))) for name in icons[:n_targets]]
        others = icons[n_targets:]
        total = round(20 + 24 * level)                   # items on the page, targets included
        size = 0.14 - 0.05 * level                       # icon diameter as a share of the scene width
        spots = scatter(rnd, total, size, ASPECT)
        rnd.shuffle(spots)
        names = [name for name, k in self.targets for _ in range(k)]
        names += [rnd.choice(others) for _ in range(len(spots) - len(names))]
        spin = 50 * level
        self.items = [(name, x, y, d, rnd.uniform(-spin, spin)) for name, (x, y, d) in zip(names, spots)]
        self.targets = [(name, sum(1 for it in self.items if it[0] == name)) for name, _ in self.targets]

    def _scene(self, C, x0, top, w, answer=False):
        h = w * ASPECT
        if not answer:
            C.stroke(rounded(x0, top - h, x0 + w, top, 14), 2.4, closed=True)
        wanted = {name for name, _ in self.targets}
        for name, x, y, d, rot in self.items:
            cx, cy = x0 + x * w, top - y * w
            draw_icon(C, name, cx, cy, d * w * 0.92, rot)
            if answer and name in wanted:
                C.ring(cx, cy, d * w * 0.6, max(1.4, w * 0.006))
        return h

    def page(self, C, n):
        x0, x1 = frame(n)
        top = header(C, n, f"SEEK AND FIND #{self.number}", f"{level_name(self.level)} level · find every picture "
                     "from the list, count them and write the number in the box")
        legend_h = 96
        w = min(x1 - x0 - 8, (top - 10 - BOTTOM - legend_h) / ASPECT)
        sx = (x0 + x1) / 2 - w / 2
        h = self._scene(C, sx, top - 6, w)
        y = top - 6 - h - 52
        k = len(self.targets)
        slot = w / k                                     # the legend spans exactly the picture's width
        for i, (name, _) in enumerate(self.targets):
            cx = sx + slot * (i + 0.5) + 10
            draw_icon(C, name, cx - 34, y, 46)
            C.text(cx + 2, y, "=", BOLD, 22, "mm")
            C.shape(rounded(cx + 18, y - 20, cx + 58, y + 20, 7), 2.0)

    def answer(self, C, x0, y0, x1, y1):
        w = min(x1 - x0, (y1 - y0 - 20) / ASPECT)
        h = self._scene(C, (x0 + x1) / 2 - w / 2, y1, w, answer=True)
        counts = ", ".join(f"{name} {k}" for name, k in self.targets)
        C.text((x0 + x1) / 2, y1 - h - 14, counts, REG, 11, "ms")
