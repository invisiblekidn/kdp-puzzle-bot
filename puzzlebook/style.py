"""Page decoration in the style of the Invisible KID "MAZES" book, in black and white.

Every page gets a rounded double border, theme art in the two top corners, a little landscape along the
bottom with the page number in it, and faint sparkles and pictures in the empty space around the puzzle.
Titles use a display font chosen per theme, drawn as white letters with a black outline and shadow.
"""
import math
import random

from PIL import ImageFilter

from .icons import draw_icon
from .lib import PH, PW, REG, S, TITLE_FONT, ellipse_pts, rounded, star_pts, wrap

GUTTER_EDGE, OUTER_EDGE, EDGE_Y = 34.0, 22.0, 22.0   # border distance from the trim (KDP: >= 27 / 18)
SCENE_H = 80.0                                        # height of the bottom landscape above the border
CONTENT_BOTTOM = EDGE_Y + SCENE_H + 8                 # puzzles stay above this

FONTS = {   # display font for titles, font for the small line under them, title size factor
    "christmas": ("MountainsofChristmas-Bold.ttf", "Griffy-Regular.ttf", 1.1),
    "halloween": ("Creepster-Regular.ttf", "Griffy-Regular.ttf", 1.0),
    "space": ("Audiowide-Regular.ttf", "Griffy-Regular.ttf", 0.82),
    "animals": ("LuckiestGuy-Regular.ttf", "Griffy-Regular.ttf", 0.9),
}
HEROES = {"christmas": "snowman", "halloween": "pumpkin", "space": "rocket", "animals": "bunny"}
TAGLINES = {"christmas": "a merry little puzzle book", "halloween": "a spookily fun puzzle book",
            "space": "an out-of-this-world puzzle book", "animals": "a wild and happy puzzle book"}

_theme = {"key": "animals"}


def set_theme(key):
    _theme["key"] = key if key in FONTS else "animals"


def theme_key():
    return _theme["key"]


def title_font():
    return FONTS[theme_key()][0]


def sub_font():
    return FONTS[theme_key()][1]


def border_box(n):
    """Border rectangle of page n (odd pages are right-hand pages with the gutter on the left)."""
    left = GUTTER_EDGE if n % 2 else OUTER_EDGE
    right = OUTER_EDGE if n % 2 else GUTTER_EDGE
    return left, EDGE_Y, PW - right, PH - EDGE_Y


# -------------------------------------------------------------------- text
def display_text(C, x, y, s, pt, anchor="ms", name=None):
    """White letters, black outline, solid shadow: big titles that children can colour in."""
    name = name or title_font()
    pt *= FONTS[theme_key()][2] if name == title_font() else 1
    w = max(1.4, pt * 0.06)
    C.text(x + pt * 0.05, y - pt * 0.06, s, name, pt, anchor, gray=0, outline=w, outline_gray=0)
    C.text(x, y, s, name, pt, anchor, gray=255, outline=w, outline_gray=0)


def fit_size(s, name, pt, width):
    from .lib import font
    k = FONTS[theme_key()][2] if name == title_font() else 1
    while pt > 14 and font(name, pt * k).getlength(s) / S > width:
        pt -= 1
    return pt


# --------------------------------------------------------------- art bits
def bat(C, x, y, w, gray=0):
    half = [(0.1, 0.1), (0.3, 0.38), (0.5, 0.3), (0.72, 0.52), (1.0, 0.32), (0.84, 0.2), (0.72, 0.04),
            (0.56, 0.12), (0.42, -0.04), (0.27, 0.06), (0.1, -0.12)]
    right = [(x + px * w / 2, y + py * w / 2) for px, py in half]
    left = [(x - px * w / 2, y + py * w / 2) for px, py in reversed(half)]
    C.poly(right + [(x, y - w * 0.1)] + left + [(x - w * 0.05, y + w * 0.14), (x, y + w * 0.08),
                                                 (x + w * 0.05, y + w * 0.14)], gray)


def web(C, x, y, size):
    """Spider web hanging from the top-left corner (x, y)."""
    spokes = [math.radians(a) for a in (-90, -70, -48, -25, 0)]
    for a in spokes:
        C.stroke([(x, y), (x + size * math.cos(a), y + size * math.sin(a))], 1.0)
    for r in (0.25, 0.45, 0.66, 0.88):
        pts = []
        for i, a in enumerate(spokes):
            pts.append((x + size * r * math.cos(a), y + size * r * math.sin(a)))
            if i < len(spokes) - 1:
                m = (a + spokes[i + 1]) / 2
                pts.append((x + size * r * 0.9 * math.cos(m), y + size * r * 0.9 * math.sin(m)))
        C.stroke(pts, 0.9)


def spider(C, x, y, drop):
    C.stroke([(x, y), (x, y - drop)], 0.9)
    cy = y - drop - 6
    for side in (-1, 1):
        for k in range(4):
            a = math.radians(25 - k * 22)
            C.stroke([(x, cy), (x + side * 7 * math.cos(a), cy + 7 * math.sin(a)),
                      (x + side * 11 * math.cos(a), cy + 7 * math.sin(a) - 4)], 1.1)
    C.dot(x, cy, 5.2)
    C.dot(x, cy + 5.5, 3.2)


def snowflake(C, x, y, r, w=1.2):
    for k in range(6):
        a = math.radians(90 + 60 * k)
        ex, ey = x + r * math.cos(a), y + r * math.sin(a)
        C.stroke([(x, y), (ex, ey)], w)
        mx, my = x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a)
        for d in (-35, 35):
            b = a + math.radians(180 + d)
            C.stroke([(mx, my), (mx + r * 0.3 * math.cos(b - math.pi), my + r * 0.3 * math.sin(b - math.pi))], w)


def ornament(C, x, top, length, r):
    C.stroke([(x, top), (x, top - length)], 1.0)
    cy = top - length - r - 3
    C.rect(x - r * 0.35, top - length - 4, x + r * 0.35, top - length + 1, 255)
    C.stroke([(x - r * 0.35, top - length - 4), (x + r * 0.35, top - length - 4), (x + r * 0.35, top - length + 1),
              (x - r * 0.35, top - length + 1)], 1.2, closed=True)
    C.shape(ellipse_pts(x, cy, r, r, n=40), 1.8)
    zig = [(x - r * 0.95 + i * r * 0.19, cy + (2 if i % 2 else -2)) for i in range(11)]
    C.stroke(zig, 1.2)


def sparkle(C, x, y, r, gray):
    C.poly(star_pts(r, r * 0.28, 4, x, y), gray)


def bird(C, x, y, w):
    C.stroke([(x - w, y + w * 0.3), (x - w * 0.45, y + w * 0.45), (x, y)], 1.3)
    C.stroke([(x, y), (x + w * 0.45, y + w * 0.45), (x + w, y + w * 0.3)], 1.3)


def bare_tree(C, x, y, h, flip=1):
    """Spooky bare tree growing up from (x, y)."""
    C.stroke([(x, y), (x + flip * 2, y + h * 0.55), (x - flip * 3, y + h)], 3.2)
    for (t, a, ln) in ((0.45, 40, 0.35), (0.6, -35, 0.3), (0.8, 30, 0.22), (0.72, -60, 0.25)):
        bx, by = x + flip * 2 * t, y + h * t
        a = math.radians(90 - flip * a)
        ex, ey = bx + h * ln * math.cos(a), by + h * ln * math.sin(a)
        C.stroke([(bx, by), (ex, ey)], 2.0)
        C.stroke([(ex, ey), (ex + h * 0.1 * math.cos(a + 0.6), ey + h * 0.1 * math.sin(a + 0.6))], 1.2)


def pine(C, x, y, h):
    """Christmas tree standing on (x, y): three tiers, a trunk and a star."""
    w = h * 0.62
    C.shape([(x - w * 0.09, y), (x + w * 0.09, y), (x + w * 0.09, y + h * 0.14), (x - w * 0.09, y + h * 0.14)], 1.6)
    for i, (b, t, half) in enumerate(((0.12, 0.5, 0.5), (0.36, 0.72, 0.4), (0.58, 0.95, 0.3))):
        C.shape([(x - w * half, y + h * b), (x + w * half, y + h * b), (x, y + h * t)], 1.8)
    C.poly(star_pts(h * 0.09, h * 0.04, 5, x, y + h * 0.97), 0)


def tombstone(C, x, y, w, h, cross=False):
    pts = [(x - w / 2, y)] + ellipse_pts(x, y + h - w / 2, w / 2, w / 2, 0, 180, 0, 16) + [(x + w / 2, y)]
    C.shape(pts, 1.6)
    if cross:
        C.stroke([(x, y + h * 0.3), (x, y + h * 0.75)], 1.6)
        C.stroke([(x - w * 0.22, y + h * 0.6), (x + w * 0.22, y + h * 0.6)], 1.6)


# ---------------------------------------------------------------- corners
def corners(C, n):
    bx0, by0, bx1, by1 = border_box(n)
    key = theme_key()
    lx, rx, ty = bx0 + 6, bx1 - 6, by1 - 6
    if key == "halloween":
        web(C, lx - 4, ty + 4, 74)
        spider(C, lx + 40, ty - 10, 56)
        C.shape(ellipse_pts(rx - 44, ty - 42, 32, 32, n=60), 2.0, fill=238)
        for cx, cy, r in ((-10, 8, 6), (8, -10, 4), (-6, -14, 3)):
            C.ring(rx - 44 + cx, ty - 42 + cy, r, 1.0, gray=170)
        bat(C, rx - 92, ty - 18, 22)
        bat(C, rx - 14, ty - 90, 16)
        bat(C, rx - 20, ty - 4, 12)
    elif key == "christmas":
        for dx, ln, r in ((14, 26, 10), (36, 48, 12), (58, 18, 8)):
            ornament(C, lx + dx, by1, ln, r)
        draw_icon(C, "star", rx - 34, ty - 34, 46, -12)
        snowflake(C, rx - 80, ty - 18, 9)
        snowflake(C, rx - 18, ty - 82, 7)
        snowflake(C, rx - 70, ty - 66, 5, 1.0)
    elif key == "space":
        draw_icon(C, "planet", lx + 36, ty - 34, 58, -14)
        for dx, dy, r in ((78, -18, 6), (14, -78, 5), (70, -70, 4)):
            sparkle(C, lx + dx, ty + dy, r, 0)
        draw_icon(C, "moon", rx - 34, ty - 34, 50)
        draw_icon(C, "rocket", rx - 86, ty - 70, 34, 30)
    else:
        draw_icon(C, "sun", lx + 36, ty - 36, 62)
        draw_icon(C, "cloud", rx - 42, ty - 30, 58)
        bird(C, rx - 92, ty - 30, 8)
        bird(C, rx - 74, ty - 50, 6)


# ------------------------------------------------------------------ scene
def scene(C, n, label):
    bx0, by0, bx1, by1 = border_box(n)
    key = theme_key()
    rnd = random.Random(f"scene:{key}:{n % 2}")
    w = bx1 - bx0
    base = by0 + SCENE_H * 0.42
    amp = 7.0
    phase = rnd.uniform(0, 6.28)

    def top(x):
        return base + amp * math.sin((x - bx0) / w * math.pi * 3 + phase)

    xs = [bx0 + w * i / 80 for i in range(81)]
    fill = {"halloween": 200, "christmas": 250, "space": 222, "animals": 236}[key]
    C.poly([(bx0, by0)] + [(x, top(x)) for x in xs] + [(bx1, by0)], fill)

    def stand(name, f, size, rot=0.0):
        x = bx0 + w * f
        draw_icon(C, name, x, top(x) + size * 0.36, size, rot)

    if key == "halloween":
        bare_tree(C, bx0 + 16, top(bx0 + 16) - 4, 60, 1)
        bare_tree(C, bx1 - 16, top(bx1 - 16) - 4, 60, -1)
        for f, h, cross in ((0.2, 26, False), (0.27, 34, True), (0.72, 30, True), (0.8, 24, False)):
            x = bx0 + w * f
            tombstone(C, x, top(x) - 3, 18, h, cross)
        fx0, fx1 = bx0 + w * 0.36, bx0 + w * 0.64
        C.stroke([(fx0, top(fx0) + 10), (fx1, top(fx1) + 10)], 1.6)
        x = fx0
        while x <= fx1:
            C.stroke([(x, top(x) - 2), (x, top(x) + 22)], 2.2)
            C.poly([(x - 2.4, top(x) + 22), (x, top(x) + 27), (x + 2.4, top(x) + 22)], 0)
            x += 9
        for f, s in ((0.12, 30), (0.9, 30)):
            stand("pumpkin", f, s)
    elif key == "christmas":
        for f, h in ((0.06, 58), (0.94, 58), (0.15, 44)):
            x = bx0 + w * f
            pine(C, x, top(x) - 4, h)
        stand("snowman", 0.3, 46)
        stand("gift", 0.68, 30)
        stand("gift", 0.76, 24, 8)
        stand("house", 0.84, 40)
        for f in (0.42, 0.55):
            snowflake(C, bx0 + w * f, top(bx0 + w * f) + 30, 6, 1.0)
    elif key == "space":
        for f, r in ((0.2, 10), (0.33, 6), (0.62, 8), (0.78, 12), (0.9, 5)):
            x = bx0 + w * f
            C.shape(ellipse_pts(x, top(x) - 14, r * 1.6, r * 0.55, n=30), 1.2, fill=245)
        stand("rocket", 0.07, 54)
        stand("flag", 0.86, 40)
        draw_icon(C, "planet", bx0 + w * 0.26, top(bx0 + w * 0.26) + 34, 30, 10)
        for f in (0.4, 0.58, 0.7):
            sparkle(C, bx0 + w * f, top(bx0 + w * f) + 26, 4, 0)
    else:
        stand("tree", 0.06, 54)
        stand("tree", 0.94, 54)
        stand("flower", 0.2, 30)
        stand("flower", 0.27, 24)
        stand("bunny", 0.36, 34)
        stand("carrot", 0.66, 28, -20)
        stand("flower", 0.75, 28)
        stand("mouse", 0.84, 26)
        for f in (0.13, 0.45, 0.55, 0.6):
            x = bx0 + w * f
            for d in (-3, 0, 3):
                C.stroke([(x + d, top(x) - 6), (x + d * 1.6, top(x) - 14)], 1.0)
    C.stroke([(x, top(x)) for x in xs], 2.0)
    if label:
        from .lib import font
        cx = (bx0 + bx1) / 2
        tw = font(sub_font(), 10).getlength(label) / S + 24
        C.poly(rounded(cx - tw / 2, by0 + 6, cx + tw / 2, by0 + 26, 10), 255)
        C.stroke(rounded(cx - tw / 2, by0 + 6, cx + tw / 2, by0 + 26, 10), 1.3, closed=True)
        C.text(cx, by0 + 16, label, sub_font(), 10, "mm")


# -------------------------------------------------------- background fill
def scatter(C, n, density=1.0):
    """Faint sparkles and theme pictures in the empty space (decided from what is already drawn)."""
    small = C.im.resize((round(PW), round(PH)))          # 1 px per point
    ink = small.point(lambda v: 255 if v < 250 else 0).reduce(3).point(lambda v: 255 if v else 0)  # 3 pt per px
    near = ink.filter(ImageFilter.MaxFilter(7))          # keep ~10 pt away from anything drawn
    far = ink.filter(ImageFilter.MaxFilter(15))          # pictures need more room
    bx0, by0, bx1, by1 = border_box(n)
    rnd = random.Random(f"sparkle:{theme_key()}:{n}")
    pics = {"halloween": ["ghost", "moon"], "christmas": ["star", "gift"], "space": ["star", "planet"],
            "animals": ["flower", "heart"]}[theme_key()]
    placed = []
    for _ in range(int(900 * density)):
        x, y = rnd.uniform(bx0 + 12, bx1 - 12), rnd.uniform(by0 + SCENE_H + 4, by1 - 12)
        px, py = min(near.width - 1, int(x / 3)), min(near.height - 1, int((PH - y) / 3))
        if near.getpixel((px, py)) or any(math.hypot(x - a, y - b) < 44 for a, b in placed):
            continue
        placed.append((x, y))
        roll = rnd.random()
        if roll < 0.12 and not far.getpixel((px, py)):
            C.colors[0] = 205
            draw_icon(C, rnd.choice(pics), x, y, rnd.uniform(18, 26), rnd.uniform(-15, 15))
            C.colors.pop(0)
        elif roll < 0.6:
            sparkle(C, x, y, rnd.uniform(3.5, 6.5), 200)
        else:
            C.dot(x, y, rnd.uniform(1.0, 1.8), 210)


def finish(C, n, label):
    """Wipes everything outside the border and draws the double border itself."""
    bx0, by0, bx1, by1 = border_box(n)
    from PIL import Image, ImageDraw
    mask = Image.new("L", C.im.size, 255)
    ImageDraw.Draw(mask).polygon([C._p(*p) for p in rounded(bx0, by0, bx1, by1, 16)], fill=0)
    C.im.paste(255, (0, 0), mask)
    C.stroke(rounded(bx0, by0, bx1, by1, 16), 3.4, closed=True)
    C.stroke(rounded(bx0 + 6, by0 + 6, bx1 - 6, by1 - 6, 11), 1.0, closed=True)


def decorate(C, n, label, sparkles=True):
    """Everything around the page content; call after the content is drawn."""
    corners(C, n)
    scene(C, n, label)
    if sparkles:
        scatter(C, n)
    finish(C, n, label)


# ---------------------------------------------------------------- headers
def header(C, n, x0, x1, title, sub=None):
    """Big outlined title and a small line under it. Returns the y where content may start."""
    cx = (x0 + x1) / 2
    width = x1 - x0 - 180
    pt = fit_size(title, title_font(), 44, width)
    display_text(C, cx, PH - 86, title, pt)
    y = PH - 86 - 14
    if sub:
        for line in wrap(sub, sub_font(), 14, x1 - x0 - 190):
            y -= 20
            C.text(cx, y, line, sub_font(), 14, "ms", gray=40)
    return y - 22
