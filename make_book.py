"""Builds a puzzle book from the command line (the Telegram bot uses the same code).

Examples:
    python make_book.py                                    animals, default mix
    python make_book.py --theme christmas --maze 12 --wordsearch 10 --hidden 8 --dots 6
    python make_book.py --theme space --difficulty easy --seed 7 --preview 1,4,20
"""
import argparse

import os

from puzzlebook.book import Book, BookSpec, ORDER
from puzzlebook.cover import Cover
from puzzlebook.listing import make_listing
from puzzlebook.themes import THEMES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default="animals", choices=sorted(THEMES))
    ap.add_argument("--difficulty", default="progressive", choices=["progressive", "easy", "medium", "hard"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--title", default="")
    ap.add_argument("--out", default="output")
    ap.add_argument("--preview", default="", help="comma-separated page numbers to save as PNG")
    for kind in ORDER:
        ap.add_argument(f"--{kind}", type=int, default=None, help=f"number of {kind} puzzles")
    args = ap.parse_args()

    spec = BookSpec(theme=args.theme, difficulty=args.difficulty, seed=args.seed, title=args.title)
    given = {k: getattr(args, k) for k in ORDER if getattr(args, k) is not None}
    if given:
        spec.counts = {k: given.get(k, 0) for k in ORDER}
    book = Book(spec)
    print(book.summary())
    preview = {int(p) for p in args.preview.split(",") if p.strip()}
    pdf, previews = book.render(args.out, preview,
                                progress=lambda n, total, t: print(f"page {n}/{total}  {t:.0f}s", flush=True))
    cover = Cover(book)
    cover_pdf, cover_preview = cover.render(args.out)
    listing = os.path.join(args.out, "listing.txt")
    with open(listing, "w", encoding="utf-8") as f:
        f.write(make_listing(book))
    print("wrote", pdf, cover_pdf, listing, cover_preview, *previews)
    print(f"cover {cover.W / 72:.3f} x {cover.H / 72:.3f} in, spine {cover.spine / 72:.3f} in")
    print("closest ink (in):", {k: round(v, 2) for k, v in book.margin_report().items()})


if __name__ == "__main__":
    main()
