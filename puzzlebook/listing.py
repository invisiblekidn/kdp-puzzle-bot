"""listing.txt: everything to paste into the KDP paperback setup pages (title, description, keywords...)."""
from .cover import spine_width
from .themes import theme_word

GENERAL_CATEGORIES = ["Juvenile Nonfiction / Activity Books / General",
                      "Juvenile Nonfiction / Games & Activities / Puzzles"]
WHAT = {"maze": "<b>{n} mazes</b> in fun shapes, with straight, wavy and round paths, from easy to tricky",
        "wordsearch": "<b>{n} word search puzzles</b> with big, clear letters and {theme} words",
        "hidden": "<b>{n} seek-and-find pages</b>: find the pictures, count them and write the number",
        "dots": "<b>{n} dot-to-dot pictures</b> to join and then color in"}


def keywords(theme, kinds, count=7):
    out = []
    for k in theme["keywords"]:
        if isinstance(k, tuple):
            if k[0] not in kinds:
                continue
            k = k[1]
        out.append(k)
    return out[:count]


def description(book):
    theme, spec = book.theme, book.spec
    name = theme_word(theme)
    total = sum(len(v) for v in book.puzzles.values())
    items = [WHAT[k].format(n=len(book.puzzles[k]), theme=name) for k in book.kinds]
    level = ("Puzzles start easy and get a little harder as you go, so every child can feel like a puzzle champion."
             if spec.difficulty == "progressive" else "")
    parts = [
        f"<p><b>{total} {name} puzzles for kids {spec.ages.lower()}!</b></p>",
        f"<p>Keep little hands busy and minds sharp with this {name} activity book. "
        f"Grab a pencil and some crayons and dive in. {level}</p>",
        "<p><b>Inside you will find:</b></p>",
        "<ul>" + "".join(f"<li>{s}</li>" for s in items) + "</ul>",
        "<p><b>Why kids and parents love it:</b></p>",
        "<ul><li>Large 8.5 x 11 inch pages with plenty of room to draw</li>"
        + ("<li>Answer key at the back of the book</li>" if spec.answers else "")
        + "<li>A certificate of achievement to celebrate at the end</li>"
        "<li>Builds focus, problem solving, spelling and fine motor skills</li></ul>",
        f"<p>Makes {theme['gift']}. Scroll up and click <b>Add to Cart</b> to start the fun!</p>",
    ]
    return "\n".join(parts)


def make_listing(book, paper="white"):
    spec = book.spec
    pages = len(book.pages)
    spine = spine_width(pages, paper)
    lines = [
        f"KDP PAPERBACK LISTING: {book.title}",
        f"Вариант (seed): {spec.seed}, тема: {spec.theme}, страниц: {pages}",
        "",
        "Как пользоваться: на сайте kdp.amazon.com создайте Paperback и копируйте поля отсюда по порядку.",
        "Тексты ниже на английском, потому что книга для американского Amazon.",
        "",
        "=== 1. Paperback Details ===",
        "",
        "Language: English",
        f"Book Title: {book.title}",
        f"Subtitle: {book.subtitle}",
        "Series: (пусто или ваша серия, например Invisible KID Puzzle Books)",
        f"Author: {spec.author}",
        "",
        "Description (вставьте целиком, KDP понимает эти теги):",
        description(book),
        "",
        "Publishing Rights: I own the copyright and I hold the necessary publishing rights.",
        "",
        "Primary Audience: Sexually Explicit Images or Title: No. Reading age: Minimum 6, Maximum 8",
        "",
        "Keywords (7 полей, по одной фразе в каждое поле):",
    ]
    lines += [f"  {i}. {k}" for i, k in enumerate(keywords(book.theme, book.kinds), 1)]
    lines += ["", "Categories (в KDP можно выбрать до трёх, ищите их через поиск категорий):"]
    lines += [f"  - {c}" for c in book.theme["categories"] + GENERAL_CATEGORIES]
    lines += [
        "",
        "=== 2. Paperback Content ===",
        "",
        "Print ISBN: Get a free KDP ISBN (бесплатный ISBN от KDP; штрихкод KDP поставит сам в белый прямоугольник на задней обложке)",
        f"Ink and Paper Type: Black & white interior with {paper} paper",
        "Trim Size: 8.5 x 11 in (21.59 x 27.94 cm)",
        "Bleed Settings: No Bleed",
        "Paperback cover finish: Glossy (для детских книг смотрится ярче)",
        "Manuscript: interior.pdf",
        "Book Cover: Upload a cover you already have -> cover.pdf",
        f"  Размер обложки: {2 * 8.5 + spine + 0.25:.3f} x 11.250 in, корешок {spine:.3f} in ({pages} стр., бумага {paper}).",
        "  Если поменяете тип бумаги или число страниц, обложку нужно собрать заново.",
        "",
        "AI-Generated Content (честный ответ на вопрос KDP про ИИ):",
        "  Images: No. Все головоломки и картинки нарисованы программой по алгоритмам, без ИИ.",
        "  Text: Yes, Some sections, with minimal or no editing (если сами переписали тексты: with extensive editing).",
        "    Шаблоны текстов (описание, инструкции и подписи в книге, задняя обложка) написаны с помощью Claude.",
        "    Tool: Claude (Anthropic).",
        "  Translations: No.",
        "",
        "=== 3. Pricing ===",
        "",
        "Территории: All territories. Цену выбирайте сами: KDP покажет минимальную цену и роялти",
        f"для этого числа страниц ({pages}).",
        "",
        "Шрифты в книге: Andika и Fredoka (SIL Open Font License, коммерческое использование разрешено).",
    ]
    return "\n".join(lines) + "\n"
