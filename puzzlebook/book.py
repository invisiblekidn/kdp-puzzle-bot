"""Assembles a complete KDP interior (front matter, puzzles, certificate, answers) into interior.pdf."""
import os
import random
import time
from dataclasses import dataclass, field
from functools import partial

from .icons import draw_icon
from .layout import BOTTOM, bullets, frame, grid_cells, header, para
from . import style
from .lib import OUT_H, OUT_W, PH, PW, REG, Canvas, PdfWriter, logo, rounded, wrap
from .puzzles.dots import Dots
from .puzzles.hidden import Hidden
from .puzzles.maze import Maze
from .puzzles.wordsearch import WordSearch
from .themes import custom_theme, get_theme

PUZZLES = {cls.kind: cls for cls in (Maze, WordSearch, Hidden, Dots)}
ORDER = ["maze", "wordsearch", "hidden", "dots"]
LIMITS = {}
LEVELS = {"easy": 0.15, "medium": 0.5, "hard": 0.85}
MIN_PAGES = 24                       # KDP paperback minimum


@dataclass
class BookSpec:
    theme: str = "animals"
    counts: dict = field(default_factory=lambda: {"maze": 10, "wordsearch": 10, "hidden": 6, "dots": 6})
    difficulty: str = "progressive"  # easy / medium / hard / progressive
    title: str = ""                  # empty: made from the theme
    subtitle: str = ""
    author: str = "Invisible KID"
    ages: str = "Ages 6-8"
    year: int = 2026
    seed: int = 0                    # same seed + same settings = the same book
    theme_name: str = ""             # the author's own theme, drawn in the style of `theme`
    words: list = None               # the author's own word search words
    theme_pack: str = ""             # folder of a theme made by the neural network (aitheme.build)
    answers: bool = True


def level_for(difficulty, i, count):
    if difficulty == "progressive":
        return 0.05 + 0.9 * (i / (count - 1) if count > 1 else 0.5)
    return LEVELS[difficulty]


def section_names(kinds):
    names = [PUZZLES[k].section for k in kinds]
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


class Book:
    def __init__(self, spec):
        self.spec = spec
        if spec.theme_pack:
            from .aitheme import load
            self.theme = dict(load(spec.theme_pack))
            self.theme_key = "ai"
            if spec.words:
                self.theme["words"] = list(spec.words)
        else:
            self.theme = get_theme(spec.theme)
            if spec.theme_name or spec.words:
                self.theme = custom_theme(self.theme, spec.theme_name, spec.words)
            self.theme_key = (spec.theme or "animals").strip().lower()
        style.set_theme(self.theme_key, self.theme)
        if spec.difficulty not in LEVELS and spec.difficulty != "progressive":
            raise ValueError(f"Unknown difficulty '{spec.difficulty}'")
        self.kinds = [k for k in ORDER if spec.counts.get(k, 0) > 0]
        unknown = set(spec.counts) - set(PUZZLES)
        if unknown:
            raise ValueError(f"Unknown puzzle types: {', '.join(sorted(unknown))}")
        if not self.kinds:
            raise ValueError("The book needs at least one puzzle")
        self.title = spec.title or f"{self.theme['name']} Puzzle Fun!"
        self.subtitle = spec.subtitle or f"{section_names(self.kinds)} for Kids {spec.ages}"
        rnd = random.Random(f"{spec.seed}:{spec.theme}")
        self.puzzles = {}
        for kind in self.kinds:
            count = min(spec.counts[kind], LIMITS.get(kind, 999))
            ctx = {}
            self.puzzles[kind] = [PUZZLES[kind](rnd, level_for(spec.difficulty, i, count), self.theme, i + 1, ctx)
                                  for i in range(count)]
        self.pages, self.sections = [], {}
        self._assemble()

    # ------------------------------------------------------------ structure
    def add(self, fn, footer=True):
        self.pages.append((fn, footer))

    def _assemble(self):
        self.add(self.title_page, footer=False)
        self.add(self.copyright_page, footer=False)
        self.add(self.welcome_page)
        for kind in self.kinds:
            first = len(self.pages) + 1
            for p in self.puzzles[kind]:
                self.add(p.page)
            self.sections[kind] = (first, len(self.pages))
        self.add(self.certificate_page, footer=False)
        if self.spec.answers:
            answers = [p for kind in self.kinds for p in self.puzzles[kind]]
            first = len(self.pages) + 1
            for i in range(0, len(answers), 4):
                self.add(partial(self.answers_page, items=answers[i:i + 4]))
            self.sections["answers"] = (first, len(self.pages))
        while len(self.pages) < MIN_PAGES or len(self.pages) % 2:
            self.add(self.doodle_page)

    # ---------------------------------------------------------------- pages
    def title_page(self, C, n):
        cx = PW / 2
        C.text(cx, PH - 196, style.TAGLINES[style.theme_key()], style.sub_font(), 20, gray=40)
        y = PH - 262
        lines = wrap(self.title, style.title_font(), 62, 440)
        for line in lines:
            style.display_text(C, cx, y, line, style.fit_size(line, style.title_font(), 62, 470))
            y -= 66
        icon_top, icon_bottom = y + 20, 290                 # between the title and the level pills
        size = min(150, icon_top - icon_bottom - 20)
        draw_icon(C, style.HEROES[style.theme_key()], cx, (icon_top + icon_bottom) / 2, size)
        pills = ["EASY", "MEDIUM", "TRICKY"]
        for i, label in enumerate(pills):
            px = cx + (i - 1) * 118
            C.shape(rounded(px - 50, 244, px + 50, 274, 15), 2.2)
            C.text(px, 259, label, style.title_font(), 15, "mm")
        total = sum(len(v) for v in self.puzzles.values())
        info = f"{total} puzzles for kids {self.spec.ages.lower()}" + (" · answers included" if self.spec.answers else "")
        C.text(cx, 214, info, style.sub_font(), 16, gray=40)
        C.stroke([(cx - 170, 192), (cx + 170, 192)], 1.4, dash=(6, 6))
        C.image(logo("horizontal_black"), cx, 150, w=270)

    def copyright_page(self, C, n):
        x0, x1 = frame(n)
        cx = (x0 + x1) / 2
        style.display_text(C, cx, PH - 180, "This book belongs to", 36)
        C.stroke([(cx - 170, PH - 250), (cx + 170, PH - 250)], 2.4)
        for i, name in enumerate(self.theme["icons"][:3]):
            draw_icon(C, name, cx + (i - 1) * 120, PH - 330, 54)
        C.image(logo("compact_black"), cx, 382, h=66)
        y = 300
        for line in (self.title, f"Copyright (c) {self.spec.year} {self.spec.author}. All rights reserved."):
            C.text(cx, y, line, REG, 12, "ms")
            y -= 18
        y -= 4
        para(C, x0 + 30, y, "No part of this book may be reproduced, stored in a retrieval system or transmitted in "
             "any form or by any means without the written permission of the author, except for brief quotations "
             "in reviews. First edition.", REG, 10, x1 - x0 - 60)

    def welcome_page(self, C, n):
        x0, x1 = frame(n)
        x0, x1 = x0 + 10, x1 - 10
        w = x1 - x0
        top = header(C, n, "WELCOME!", "hello, puzzle explorer · grab a pencil and some crayons")
        y = para(C, x0, top - 8, "This book is full of fun puzzles. Let's begin! "
                 "The puzzles get a little harder as you go.", REG, 14, w)
        how = {"maze": "find the way from START to FINISH.",
               "wordsearch": "find and circle the hidden words.",
               "hidden": "find the pictures, count them and write the number.",
               "dots": "join the numbers in order to reveal a picture, then color it in."}
        items = []
        for kind in self.kinds:
            a, b = self.sections[kind]
            items.append(f"{PUZZLES[kind].section} (pages {a}-{b}): {how[kind]}")
        if "answers" in self.sections:
            a, b = self.sections["answers"]
            items.append(f"Answers are at the back of the book (pages {a}-{b}).")
        y = bullets(C, x0, y - 22, items, 13, w)
        C.text(x0, y - 14, "Tips for grown-ups", style.title_font(), 20, "ls")
        bullets(C, x0, y - 46, [
            "Short sessions work best. Stop when it stops being fun.",
            "Praise the effort, not just the result.",
            "Stuck? Peek at the answers together and try again.",
        ], 13, w)

    def certificate_page(self, C, n):
        x0, x1 = frame(n)
        cx = (x0 + x1) / 2
        draw_icon(C, "star", cx, PH - 200, 96)
        style.display_text(C, cx, PH - 318, "GREAT JOB!", 58)
        C.text(cx, PH - 362, "Certificate of Achievement", style.sub_font(), 22, gray=40)
        C.text(cx, PH - 430, "This certificate is awarded to", REG, 16)
        C.stroke([(cx - 170, PH - 485), (cx + 170, PH - 485)], 2.4)
        y = PH - 535
        for line in wrap(f"for finishing the whole book: {self.title}", REG, 16, 420):
            C.text(cx, y, line, REG, 16)
            y -= 24
        C.text(x0 + 60, 168, "Date", REG, 13, "ls")
        C.stroke([(x0 + 60, 188), (x0 + 178, 188)], 2.0)
        C.text(x1 - 178, 168, "Signed", REG, 13, "ls")
        C.stroke([(x1 - 178, 188), (x1 - 60, 188)], 2.0)
        C.image(logo("horizontal_black"), cx, 184, w=112)

    def answers_page(self, C, n, items):
        x0, x1 = frame(n)
        top = header(C, n, "ANSWERS", "no peeking until you have tried!")
        cells, cw, ch = grid_cells(x0, x1, top, BOTTOM, 2, 2)
        for p, (cx, cy) in zip(items, cells):
            C.text(cx, cy + ch / 2 - 16, f"{p.answer_title} #{p.number}", style.title_font(), 15)
            p.answer(C, cx - cw / 2 + 14, cy - ch / 2 + 10, cx + cw / 2 - 14, cy + ch / 2 - 30)

    def doodle_page(self, C, n):
        x0, x1 = frame(n)
        top = header(C, n, "DOODLE TIME!", "draw your favorite picture from this book")
        C.stroke(rounded(x0 + 4, BOTTOM, x1 - 4, top - 10, 18), 2.4, dash=(12, 9), closed=True)

    # -------------------------------------------------------------- output
    def draw_page(self, n):
        """Page n (1-based) with its decoration, on a fresh canvas."""
        style.set_theme(self.theme_key, self.theme)
        fn, footer = self.pages[n - 1]
        C = Canvas()
        fn(C, n)
        label = f"page {n} of {len(self.pages)}" if footer else None
        style.decorate(C, n, label, sparkles=getattr(fn, "__name__", "") != "doodle_page")
        return C

    def render(self, out_dir, preview_pages=(), progress=None):
        """Writes interior.pdf (and PNG previews of preview_pages) into out_dir. Returns their paths."""
        os.makedirs(out_dir, exist_ok=True)
        pdf_path = os.path.join(out_dir, "interior.pdf")
        pdf = PdfWriter(pdf_path, self.title, self.spec.author)
        previews, margins = [], []
        t0 = time.time()
        for n, (fn, footer) in enumerate(self.pages, 1):
            C = self.draw_page(n)
            img = C.final_bytes()
            box = img.point(lambda v: 255 if v < 250 else 0).getbbox()
            if box:
                k = 72 / 300
                margins.append((n, box[0] * k, (OUT_W - box[2]) * k, box[1] * k, (OUT_H - box[3]) * k))
            pdf.add_page(img)
            if n in preview_pages:
                path = os.path.join(out_dir, f"preview_{n:02d}.png")
                img.resize((img.width // 3, img.height // 3)).save(path)
                previews.append(path)
            if progress:
                progress(n, len(self.pages), time.time() - t0)
        pdf.close()
        self.margins = margins
        return pdf_path, previews

    def margin_report(self):
        """Closest ink to each edge in inches; KDP needs >= 0.25 outside and >= 0.375 at the gutter."""
        m = self.margins
        out = {name: min(x[i] for x in m) / 72 for i, name in ((1, "left"), (2, "right"), (3, "top"), (4, "bottom"))}
        out["gutter"] = min((x[1] if x[0] % 2 else x[2]) for x in m) / 72
        return out

    def summary(self):
        parts = [f"{PUZZLES[k].section}: {len(self.puzzles[k])}" for k in self.kinds]
        return f"{self.title} | {len(self.pages)} pages | " + ", ".join(parts)
