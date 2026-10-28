"""Full-wrap KDP paperback cover (back, spine, front) as one colour page: cover.pdf + a PNG preview.

KDP rules used here (checked 2026-10): 0.125" bleed on every side; spine width = pages x 0.002252"
(black ink, white paper) or x 0.0025" (cream); spine text only for books with more than 79 pages, kept
0.0625" from the spine edges; a clear 2" x 1.2" barcode area in the lower right of the back cover.
"""
import math
import os
import random

from PIL import Image

from .icons import draw_icon
from .lib import BOLD, DPI, REG, TITLE_FONT, Canvas, S, font, logo, rounded, star_pts, wrap
from .puzzles.maze import Maze
from .themes import theme_word

BLEED = 9.0                                   # 0.125 in
TRIM_W, TRIM_H = 612.0, 792.0                 # 8.5 x 11 in
SAFE = 27.0                                   # text stays 0.375 in inside the trim
PAPER = {"white": 0.002252, "cream": 0.0025}  # spine inches per page, black ink
SPINE_TEXT_MIN_PAGES = 80
BARCODE_W, BARCODE_H, BARCODE_GAP = 144.0, 86.4, 18.0
WHITE, BLACK = (255, 255, 255), (0, 0, 0)

ABOUT = {"maze": "{n} mazes in fun shapes, from easy to tricky",
         "wordsearch": "{n} word search puzzles with big, clear letters",
         "hidden": "{n} seek-and-find pages: find, count and color",
         "dots": "{n} dot-to-dot pictures to join and color in"}


def spine_width(pages, paper="white"):
    """Spine width in inches."""
    return pages * PAPER[paper]


class Cover:
    def __init__(self, book, paper="white"):
        self.book, self.paper = book, paper
        self.theme = book.theme
        self.col = book.theme["cover"]
        self.pages = len(book.pages)
        self.spine = spine_width(self.pages, paper) * 72
        self.W = 2 * BLEED + 2 * TRIM_W + self.spine
        self.H = 2 * BLEED + TRIM_H
        self.back = (BLEED, BLEED + TRIM_W)
        self.front = (BLEED + TRIM_W + self.spine, BLEED + 2 * TRIM_W + self.spine)
        self.y0, self.y1 = BLEED, BLEED + TRIM_H
        self.rnd = random.Random(f"cover:{book.spec.seed}:{book.spec.theme}")
        self.total = sum(len(v) for v in book.puzzles.values())

    def size_inches(self):
        return self.W / 72, self.H / 72

    # ------------------------------------------------------------ helpers
    def sticker(self, C, name, x, y, size, color, rot=0.0):
        C.colors[255] = color
        draw_icon(C, name, x, y, size, rot)
        C.colors.pop(255)

    def title_text(self, C, x, y, s, pt, outline=None):
        w = outline or pt * 0.07
        C.text(x + pt * 0.05, y - pt * 0.07, s, TITLE_FONT, pt, gray=self.col["dark"], outline=w, outline_gray=self.col["dark"])
        C.text(x, y, s, TITLE_FONT, pt, gray=WHITE, outline=w, outline_gray=self.col["dark"])

    def fit_lines(self, text, name, pt, width, max_lines):
        while True:
            lines = wrap(text, name, pt, width)
            if len(lines) <= max_lines or pt < 20:
                return lines, pt
            pt -= 2

    # ------------------------------------------------------------- panels
    def background(self, C):
        C.rect(0, 0, self.W, self.H, self.col["bg"])
        for _ in range(int(self.W * self.H / 2600)):
            x, y = self.rnd.uniform(0, self.W), self.rnd.uniform(0, self.H)
            r = self.rnd.uniform(3, 9)
            if self.rnd.random() < 0.45:
                C.poly(star_pts(r * 1.6, r * 0.7, 5, x, y), self.col["light"])
            else:
                C.dot(x, y, r * 0.6, self.col["light"])

    def front_panel(self, C):
        x0, x1 = self.front
        cx = (x0 + x1) / 2
        y = self.y1 - 92
        lines, pt = self.fit_lines(self.book.title, TITLE_FONT, 66, TRIM_W - 2 * SAFE - 20, 2)
        for line in lines:
            self.title_text(C, cx, y, line, pt)
            y -= pt * 1.08
        # ribbon with the puzzle types
        kinds = " • ".join(self.book.puzzles[k][0].section for k in self.book.kinds)
        rl, rpt = self.fit_lines(kinds, BOLD, 18, TRIM_W - 2 * SAFE - 70, 2)
        rh = 16 + len(rl) * rpt * 1.3
        top = y + pt * 0.55 - 6
        rw = max(font(BOLD, rpt).getlength(s) / S for s in rl) + 50
        C.poly(rounded(cx - rw / 2, top - rh, cx + rw / 2, top, rh / 2 if len(rl) == 1 else 18), self.col["highlight"])
        C.stroke(rounded(cx - rw / 2, top - rh, cx + rw / 2, top, rh / 2 if len(rl) == 1 else 18), 3.0, closed=True,
                 gray=self.col["dark"])
        ty = top - 8 - rpt * 0.95
        for s in rl:
            C.text(cx, ty, s, BOLD, rpt, gray=self.col["dark"])
            ty -= rpt * 1.3
        # card with a real maze in the theme's shape
        card = (cx - 205, self.y0 + 150, cx + 205, top - rh - 24)
        C.poly(rounded(*card, 26), WHITE)
        C.stroke(rounded(*card, 26), 5.0, closed=True, gray=self.col["dark"])
        self.maze(C, card)
        icons = [i for i in self.theme["icons"] if i not in ("tree", "house", "cloud", *self.maze_icons)]
        spots = [(card[0] + 8, card[3] - 10, -14), (card[2] - 8, card[3] - 14, 12),
                 (card[0] + 2, card[1] + 70, 10), (card[2] - 2, card[1] + 66, -10)]
        for i, (x, yy, rot) in enumerate(spots):
            self.sticker(C, icons[i % len(icons)], x, yy, 78, self.col["sticker"][i % len(self.col["sticker"])], rot)
        # age badge, puzzle count burst, logo
        bx, by = x0 + SAFE + 58, self.y0 + SAFE + 60
        C.dot(bx, by, 56, self.col["dark"])
        C.dot(bx, by, 51, self.col["highlight"])
        age = self.book.spec.ages.split()
        C.text(bx, by + 14, age[0].upper(), BOLD, 15, "mm", gray=self.col["dark"])
        C.text(bx, by - 12, age[-1], TITLE_FONT, 30, "mm", gray=self.col["dark"])
        sx, sy = x1 - SAFE - 62, self.y0 + SAFE + 62
        C.poly(star_pts(72, 56, 14, sx, sy), self.col["dark"])
        C.poly(star_pts(66, 51, 14, sx, sy), self.col["accent"])
        C.text(sx, sy + 8, str(self.total), TITLE_FONT, 40, "mm", gray=WHITE)
        C.text(sx, sy - 24, "PUZZLES", BOLD, 12, "mm", gray=WHITE)
        self.brand(C, cx, self.y0 + SAFE + 30, 180)

    def brand(self, C, cx, cy, width):
        """The Invisible KID logo on a white label, so it reads on any cover colour."""
        img = logo("horizontal_black")
        h = width * img.height / img.width
        box = (cx - width / 2 - 20, cy - h / 2 - 13, cx + width / 2 + 20, cy + h / 2 + 13)
        C.poly(rounded(*box, (box[3] - box[1]) / 2), WHITE)
        C.stroke(rounded(*box, (box[3] - box[1]) / 2), 3.0, closed=True, gray=self.col["dark"])
        C.image(img, cx, cy, w=width)

    def maze(self, C, card):
        shapes = self.theme["maze_shapes"]
        ctx = {"designs": [("square", shapes[0], "rounded")]}
        m = Maze(random.Random(f"covermaze:{self.book.spec.seed}"), 0.22, self.theme, 1, ctx)
        k, T = m._fit(card[0] + 50, card[1] + 58, card[2] - 50, card[3] - 58)
        lw = max(2.4, min(4.6, m.cell * k * 0.1))
        for line in m.walls:
            C.stroke([T(p) for p in line], lw, gray=self.col["dark"])
        part = m.solution[:max(2, int(len(m.solution) * 0.4))]
        C.stroke([T(p) for p in part], max(2.0, m.cell * k * 0.16), dash=(7, 7), gray=self.col["accent"])
        ex, ey = T(m.entry)
        top_y = T((0, m.bbox[3]))[1]
        self.sticker(C, m.a, ex, top_y + 28, 46, self.col["sticker"][0])
        self.maze_icons = (m.a, m.b)
        fx, _ = T(m.exit)
        bot_y = T((0, m.bbox[1]))[1]
        self.sticker(C, m.b, fx, bot_y - 28, 46, self.col["sticker"][1])

    def spine_panel(self, C):
        s0 = BLEED + TRIM_W
        C.rect(s0, 0, s0 + self.spine, self.H, self.col["dark"])
        if self.pages < SPINE_TEXT_MIN_PAGES:
            return
        pt = min(16, (self.spine - 2 * 4.5) * 0.8)     # 0.0625 in from each spine edge
        if pt < 6:                                     # too thin to read: leave the spine plain
            return
        text = self.book.title
        f = font(BOLD, pt)
        w, h = round(f.getlength(text)) + 8, round(pt * S * 1.6)
        strip = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(strip).text((w / 2, h / 2), text, font=f, fill=WHITE + (255,), anchor="mm")
        strip = strip.rotate(-90, expand=True)         # reads top to bottom, as on US books
        cx, cy = (s0 + self.spine / 2) * S, (self.H / 2) * S
        C.im.paste(strip, (round(cx - strip.width / 2), round(cy - strip.height / 2)), strip)
        mark = logo("kmark_white")                     # publisher mark at the foot of the spine
        C.image(mark, s0 + self.spine / 2, self.y0 + SAFE + 10, w=min(28, self.spine - 2 * 4.5))

    def back_panel(self, C, thumbs):
        x0, x1 = self.back
        cx = (x0 + x1) / 2
        name = self.theme["name"]
        self.title_text(C, cx, self.y1 - 78, "Hours of puzzle fun!", 38)
        # text panel
        pw = TRIM_W - 2 * SAFE - 20
        top, bottom = self.y1 - 110, self.y0 + 352
        C.poly(rounded(cx - pw / 2, bottom, cx + pw / 2, top, 22), WHITE)
        C.stroke(rounded(cx - pw / 2, bottom, cx + pw / 2, top, 22), 4.0, closed=True, gray=self.col["dark"])
        tx, width = cx - pw / 2 + 26, pw - 52
        items = [ABOUT[k].format(n=len(self.book.puzzles[k])) for k in self.book.kinds]
        if self.book.spec.difficulty == "progressive":
            items.append("Puzzles start easy and get a little harder as you go")
        if self.book.spec.answers:
            items.append("Answer key at the back for grown-ups")
        items.append("Big 8.5 x 11 inch pages and a certificate at the end")
        intro = (f"Grab a pencil! This book is packed with {self.total} {theme_word(self.theme)} puzzles made just for "
                 f"kids {self.book.spec.ages.lower()}. Inside you will find:")
        def block(pt):
            lines = len(wrap(intro, REG, pt, width)) + sum(len(wrap(s, REG, pt, width - 18)) for s in items)
            return lines * pt * 1.35 + 6

        room = top - bottom - 70                       # leaves space for the tagline at the bottom
        pt = 19
        while block(pt) > room and pt > 11:
            pt -= 0.5
        y = top - 22 - (room - block(pt)) / 2 - pt
        for line in wrap(intro, REG, pt, width):
            C.text(tx, y, line, REG, pt, "ls", gray=self.col["dark"])
            y -= pt * 1.35
        y -= 6
        for s in items:
            C.dot(tx + 5, y + pt * 0.33, 3.6, self.col["accent"])
            for line in wrap(s, REG, pt, width - 18):
                C.text(tx + 18, y, line, REG, pt, "ls", gray=self.col["dark"])
                y -= pt * 1.35
        C.text(cx, bottom + 26, "Perfect for home, travel and quiet time!", BOLD, 18, gray=self.col["accent"])
        # page thumbnails
        tw = 150
        th = tw * 11 / 8.5
        n = len(thumbs)
        gap = 22
        left = cx - (n * tw + (n - 1) * gap) / 2
        ty1 = bottom - 22
        for i, img in enumerate(thumbs):
            ax = left + i * (tw + gap)
            C.rect(ax + 5, ty1 - th - 6, ax + tw + 5, ty1 - 6, self.col["dark"])
            px, py = C._p(ax, ty1)
            C.im.paste(img.convert("RGB").resize((round(tw * S), round(th * S)), Image.LANCZOS), (round(px), round(py)))
            C.stroke([(ax, ty1), (ax + tw, ty1), (ax + tw, ty1 - th), (ax, ty1 - th)], 2.0, closed=True,
                     gray=self.col["dark"])
        # brand and the clear barcode area
        self.brand(C, x0 + SAFE + 20 + 70, self.y0 + SAFE + 24, 140)
        bx1, by0 = x1 - BARCODE_GAP, self.y0 + BARCODE_GAP
        C.rect(bx1 - BARCODE_W, by0, bx1, by0 + BARCODE_H, WHITE)
        self.barcode = (bx1 - BARCODE_W, by0, bx1, by0 + BARCODE_H)
        self.thumb_bottom = ty1 - th - 6

    # -------------------------------------------------------------- output
    def thumbnails(self, count=3):
        """Small images of the first page of up to three puzzle sections."""
        out = []
        for kind in self.book.kinds[:count]:
            out.append(self.book.draw_page(self.book.sections[kind][0]).im)
        return out

    def render(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        C = Canvas(self.W, self.H, "RGB", WHITE)
        self.background(C)
        self.spine_panel(C)
        self.back_panel(C, self.thumbnails())
        self.front_panel(C)
        img = C.final_bytes()
        pdf_path = os.path.join(out_dir, "cover.pdf")
        img.save(pdf_path, "PDF", resolution=DPI, quality=95, title=self.book.title, author=self.book.spec.author)
        preview = os.path.join(out_dir, "cover_preview.jpg")
        img.resize((img.width // 3, img.height // 3), Image.LANCZOS).save(preview, quality=88)
        return pdf_path, preview
