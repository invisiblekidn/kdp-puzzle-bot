"""Word search: theme words hidden in a letter grid, listed under it."""
import string

from ..layout import BOTTOM, footer_level, frame, header
from ..lib import BOLD, REG

RIGHT, DOWN, DOWN_RIGHT = (0, 1), (1, 0), (1, 1)
BACKWARDS = [(0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1)]


def place_words(words, size, dirs, rnd, tries=400):
    grid = [[None] * size for _ in range(size)]
    placed = []
    for word in sorted(words, key=len, reverse=True):
        for _ in range(tries):
            dr, dc = rnd.choice(dirs)
            r, c = rnd.randrange(size), rnd.randrange(size)
            er, ec = r + dr * (len(word) - 1), c + dc * (len(word) - 1)
            if not (0 <= er < size and 0 <= ec < size):
                continue
            cells = [(r + dr * i, c + dc * i) for i in range(len(word))]
            if all(grid[y][x] in (None, ch) for (y, x), ch in zip(cells, word)):
                for (y, x), ch in zip(cells, word):
                    grid[y][x] = ch
                placed.append((word, cells))
                break
    return grid, placed


class WordSearch:
    kind = "wordsearch"
    section = "Word Search"
    answer_title = "Word Search"

    def __init__(self, rnd, level, theme, number, ctx):
        self.level, self.number = level, number
        self.size = 8 + round(4 * level)                 # 8x8 .. 12x12
        count = 6 + round(4 * level)                     # 6 .. 10 words
        dirs = [RIGHT, DOWN] + ([DOWN_RIGHT] if level >= 0.34 else []) + (BACKWARDS if level >= 0.67 else [])
        pool = [w for w in theme["words"] if len(w) <= self.size]
        # rotate through the theme words so consecutive puzzles do not repeat the same list
        start = ctx.get("next", 0)
        ctx["next"] = start + count
        pick = [pool[(start + i) % len(pool)] for i in range(min(count, len(pool)))]
        rnd.shuffle(pick)
        self.grid, self.placed = place_words(pick, self.size, dirs, rnd)
        for row in self.grid:
            for i, ch in enumerate(row):
                if ch is None:
                    row[i] = rnd.choice(string.ascii_uppercase)
        self.words = sorted(w for w, _ in self.placed)
        self.hint = ("Words go across and down." if level < 0.34 else
                     "Words go across, down and diagonally." if level < 0.67 else
                     "Words go in every direction, even backwards!")

    def _grid(self, C, x0, top, cell, answer=False):
        pt = cell * 0.56
        if answer:
            for _, cells in self.placed:
                (r0, c0), (r1, c1) = cells[0], cells[-1]
                C.stroke([(x0 + (c0 + 0.5) * cell, top - (r0 + 0.5) * cell),
                          (x0 + (c1 + 0.5) * cell, top - (r1 + 0.5) * cell)], cell * 0.8, gray=205)
        for r, row in enumerate(self.grid):
            for c, ch in enumerate(row):
                C.text(x0 + (c + 0.5) * cell, top - (r + 0.5) * cell, ch, BOLD, pt, "mm")
        side = self.size * cell
        C.stroke([(x0 - 6, top + 6), (x0 + side + 6, top + 6), (x0 + side + 6, top - side - 6),
                  (x0 - 6, top - side - 6)], max(1.2, cell * 0.06), closed=True)

    def page(self, C, n):
        x0, x1 = frame(n)
        top = header(C, n, f"Word Search {self.number}", f"Find and circle every word. {self.hint}")
        cols = 2 if len(self.words) <= 8 else 3
        list_h = ((len(self.words) + cols - 1) // cols) * 30 + 20
        avail_h = top - 16 - (BOTTOM + list_h)
        cell = min((x1 - x0 - 30) / self.size, avail_h / self.size, 44)
        side = self.size * cell
        gx = (x0 + x1) / 2 - side / 2
        self._grid(C, gx, top - 10, cell)
        y = top - 10 - side - 46
        colw = (x1 - x0) / cols
        for i, w in enumerate(self.words):
            cx = x0 + colw * (i % cols) + 30
            cy = y - 30 * (i // cols)
            C.stroke([(cx, cy - 2), (cx + 14, cy - 2), (cx + 14, cy + 12), (cx, cy + 12)], 1.6, closed=True)
            C.text(cx + 24, cy, w, REG, 16, "ls")
        footer_level(C, n, self.level)

    def answer(self, C, x0, y0, x1, y1):
        cell = min((x1 - x0) / self.size, (y1 - y0) / self.size) * 0.94
        side = self.size * cell
        self._grid(C, (x0 + x1) / 2 - side / 2, y1 - ((y1 - y0) - side) / 2, cell, answer=True)
