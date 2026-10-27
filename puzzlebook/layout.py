"""Page-level layout helpers shared by all puzzle types."""
from .icons import draw_icon
from .lib import BOLD, PH, PW, REG, TITLE_FONT, wrap

INNER, OUTER = 54.0, 40.0       # gutter side / outer side margins (pt); KDP minimum is 27 / 18
TOP = 40.0                      # highest content stays this far below the top edge
BOTTOM = 66.0                   # lowest y used by page content (page number sits below it)


def frame(n):
    """Left/right content edges for page n (odd pages are right-hand pages, gutter on the left)."""
    left = INNER if n % 2 else OUTER
    right = OUTER if n % 2 else INNER
    return left, PW - right


def header(C, n, title, sub=None):
    """Big page title plus an optional wrapped instruction line. Returns the y below it."""
    x0, x1 = frame(n)
    cx = (x0 + x1) / 2
    C.text(cx, PH - 80, title, TITLE_FONT, 36)
    y = PH - 80 - 12
    if sub:
        for line in wrap(sub, REG, 16, x1 - x0):
            y -= 24
            C.text(cx, y, line, REG, 16)
    return y - 24


def para(C, x, y, text, name=REG, pt=13, width=400, leading=1.35, anchor="ls"):
    for line in wrap(text, name, pt, width):
        C.text(x, y, line, name, pt, anchor)
        y -= pt * leading
    return y


def bullets(C, x, y, items, pt=13, width=400, gap=10):
    for item in items:
        draw_icon(C, "star", x + 7, y + pt * 0.3, 14)
        y = para(C, x + 24, y, item, REG, pt, width - 24) - gap
    return y


def grid_cells(x0, x1, top, bottom, cols, rows):
    cw, ch = (x1 - x0) / cols, (top - bottom) / rows
    return [(x0 + cw * (c + 0.5), top - ch * (r + 0.5)) for r in range(rows) for c in range(cols)], cw, ch


def level_name(level):
    return "Easy" if level < 0.34 else ("Medium" if level < 0.67 else "Tricky")


def footer_level(C, n, level):
    x0, x1 = frame(n)
    C.text(x0, 30, f"Level: {level_name(level)}", BOLD, 11, "ls")
