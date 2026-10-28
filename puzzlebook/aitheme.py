"""A whole book theme made by the neural network from what the author typed ("динозавры", "Under the Sea"...).

build() asks the text model for the theme (English name, words, maze stories, colours, font) and the image
model for 12 pictures, cleans the pictures and saves everything in a folder. load() reads that folder back
and registers the pictures as icons, maze shapes and dot-to-dot figures, so the rest of the book code uses
them like the built-in ones. "Another variant" of the same book reuses the folder: no new neurons spent.
revise() redraws only the pictures the author complained about, and remembers the author's wishes for later.
"""
import json
import logging
import os
import random
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from . import ai, raster
from .figures import FIGURES
from .icons import RASTER
from .lib import font
from .puzzles.maze import THIN_SHAPES
from .shapes import SHAPE_NAMES, SHAPES

log = logging.getLogger(__name__)

PICTURES = 12
MIN_PICTURES = 8

# title font, font for the small lines, what it suits (shown to the text model)
FONT_LIBRARY = {
    "creepster": ("Creepster-Regular.ttf", "Griffy-Regular.ttf", "spooky: monsters, Halloween, ghosts"),
    "christmas": ("MountainsofChristmas-Bold.ttf", "BerkshireSwash-Regular.ttf", "winter, Christmas, snow, fairy tales"),
    "audiowide": ("Audiowide-Regular.ttf", "Electrolize-Regular.ttf", "space, robots, science, technology"),
    "luckiest": ("LuckiestGuy-Regular.ttf", "Sniglet-Regular.ttf", "animals, farm, zoo, general fun"),
    "bangers": ("Bangers-Regular.ttf", "PatrickHand-Regular.ttf", "superheroes, comics, action, sports"),
    "chewy": ("Chewy-Regular.ttf", "Sniglet-Regular.ttf", "food, candy, sweets, cooking, summer, beach"),
    "hennypenny": ("HennyPenny-Regular.ttf", "BerkshireSwash-Regular.ttf", "magic, fairies, unicorns, princesses, mermaids"),
    "pirata": ("PirataOne-Regular.ttf", "BerkshireSwash-Regular.ttf", "pirates, knights, castles, dragons, medieval"),
    "rye": ("Rye-Regular.ttf", "PatrickHand-Regular.ttf", "wild west, cowboys, horses, desert"),
    "bungee": ("Bungee-Regular.ttf", "Electrolize-Regular.ttf", "cars, trucks, trains, construction, city"),
    "titan": ("TitanOne-Regular.ttf", "Sniglet-Regular.ttf", "dinosaurs, jungle, safari, ocean, adventure"),
    "cherrybomb": ("CherryBombOne-Regular.ttf", "Sniglet-Regular.ttf", "cute pets, kawaii, Easter, Valentine, spring, baby animals"),
}

SYSTEM = ("You design themed activity books for children ages 6-8, sold on Amazon KDP in the USA. "
          "Everything must be friendly, simple and safe for young kids. Reply with one JSON object only.")

ASK = """The author typed this book theme (it may be Russian or English): "{typed}"
{wishes}
Return a JSON object with exactly these fields:
"name": the theme in English, Title Case, 1-3 words, as in the book title "<name> Puzzle Fun!" (e.g. "Dinosaur", "Under the Sea").
"word": the theme as it reads inside a sentence "32 ___ puzzles": lowercase unless it is a proper noun (e.g. "dinosaur", "Easter").
"holiday": true if the theme is a holiday, otherwise false.
"tagline": a short lowercase phrase that ends with "puzzle book", at most 6 words (e.g. "a roaring fun puzzle book").
"pictures": exactly 12 things that fit the theme, each easy to draw as ONE simple coloring-book object (no scenes, no text, no groups). Put the main character first and 3-4 other characters next. Each item: {{"name": "t-rex", "prompt": "a cute smiling T-rex dinosaur standing"}}.
"pairs": 4 maze stories, each {{"from": 1, "to": 5, "story": "Help the T-rex find its egg!"}}: "from" and "to" are picture numbers 1-12, "from" is a character, the story has at most 7 words.
"words": 30 English words about the theme for a word search: easy for kids, 3-10 letters, letters only.
"colors": cover colors as "#rrggbb": {{"bg": a bright main background, "dark": a very dark color in the same family for outlines, "accent": a strong contrasting color, "light": a slightly lighter shade of bg, "highlight": a bright yellow or cream for ribbons and badges}}.
"font": the best title font key from this list: {fonts}.
"keywords": 7 Amazon search phrases parents would type, lowercase, under 50 characters each, most of them with the theme in them.
"gift": a phrase that completes "Makes ___." (e.g. "a great gift for little dinosaur fans").
"""

WISHES = "The author's wishes from earlier tries, follow them strictly: {}\n"

REVISE = """A children's activity book has the theme "{name}". These are its pictures, numbered as the author sees them:
{pictures}
{wishes}The author looked at the pictures and wrote (it may be Russian): "{feedback}"

Return a JSON object with exactly these fields:
"redraw": the numbers of the pictures to draw again: only the ones the author's words are about. If the words are about \
all pictures (the drawing style, "no people" and so on), list every picture that does not follow them.
"pictures": one item for each number in "redraw": {{"n": 2, "name": "rescue helicopter", "prompt": "a cute smiling \
rescue helicopter flying"}}. Follow the author's words exactly. Each picture is still ONE simple coloring-book object \
that fits the theme (no scenes, no text, no groups).
"wish": what the author wants, as one short English instruction for all future pictures of this book \
(e.g. "only helicopters and helicopter things, no people").
"pairs": 4 maze stories for the final pictures, each {{"from": 1, "to": 5, "story": "Help the helicopter find the \
helipad!"}}: picture numbers from the list, "from" is a character or vehicle, the story has at most 7 words.
"""

STYLE = ("Simple cute cartoon coloring book icon, black and white line art, thick clean black outlines, "
         "pure white background, no shading, no gray, no color, no text, one single object, centered, "
         "fully visible with empty space around it")
# Cloudflare's safety filter sometimes refuses a harmless prompt; then the picture is asked for in other words.
PLAIN = ("Black and white line art with thick clean outlines on a plain white background, "
         "one single object in the middle, no text")


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "theme"


# ------------------------------------------------------------------ checks
def _hex(v, default):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(v or "").strip())
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else default


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _mix(c, d, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c, d))


def palette(colors):
    c = colors if isinstance(colors, dict) else {}
    bg = _hex(c.get("bg"), (64, 160, 90))
    dark = _hex(c.get("dark"), (20, 40, 30))
    while _lum(dark) > 70:                          # outlines and the spine must stay dark
        dark = _mix(dark, (0, 0, 0), 0.35)
    if _lum(bg) < 70:
        bg = _mix(bg, (255, 255, 255), 0.25)
    accent = _hex(c.get("accent"), (230, 90, 40))
    light = _hex(c.get("light"), _mix(bg, (255, 255, 255), 0.18))
    highlight = _hex(c.get("highlight"), (255, 214, 70))
    if _lum(highlight) < 170:
        highlight = _mix(highlight, (255, 255, 255), 0.45)
    stickers = [(255, 255, 255), highlight, _mix(accent, (255, 255, 255), 0.35), _mix(bg, (255, 255, 255), 0.5)]
    return {"bg": bg, "dark": dark, "accent": accent, "light": light, "highlight": highlight, "sticker": stickers}


def clean_words(words):
    out = []
    for w in words if isinstance(words, list) else []:
        w = str(w).strip().upper()
        if re.fullmatch(r"[A-Z]{3,10}", w) and w not in out:
            out.append(w)
    return out


def font_k(name):
    """Size factor so that every title font fills about the same width as Luckiest Guy at 0.9."""
    ref = font("LuckiestGuy-Regular.ttf", 20).getlength("MAZE #12 WORD SEARCH")
    w = font(name, 20).getlength("MAZE #12 WORD SEARCH")
    return max(0.72, min(1.15, 0.9 * ref / w))


# ------------------------------------------------------------------- build
def _label(p, n):
    return re.sub(r"\s+", " ", str(p.get("name") or f"picture {n}")).strip()[:24]


def _draw_all(jobs, tmp, name, seed, progress, verb):
    """Draws the pictures jobs = {slot number: {"name", "prompt"}} into tmp as raw/pic/sil_NN files.
    Returns the slot numbers that worked. Stops only for errors that make asking again pointless."""
    done = {"n": 0}

    def draw(n):
        p = jobs[n]
        thing = " ".join(str(p.get("name") or name).split())[:40]
        prompts = [f"{p['prompt']}. {STYLE}",
                   f"A friendly cartoon {thing} from a {name} coloring book. {PLAIN}",
                   f"A simple outline drawing of a {thing}. {PLAIN}"]
        variant = 0
        for attempt in range(4):
            try:
                img = ai.picture(prompts[variant], seed + n * 101 + attempt * 7919)
                icon, sil = raster.clean(img)
            except ai.Fatal:
                raise
            except ai.Refused:
                log.warning("picture %d refused by the filter: %s", n, prompts[variant])
                variant += 1
                if variant == len(prompts):
                    return None
                continue
            except (ai.AIError, raster.BadArt) as e:
                log.warning("picture %d attempt %d: %s", n, attempt + 1, e or type(e).__name__)
                continue
            img.save(os.path.join(tmp, f"raw_{n:02d}.jpg"), quality=85)
            icon.save(os.path.join(tmp, f"pic_{n:02d}.png"))
            sil.save(os.path.join(tmp, f"sil_{n:02d}.png"))
            done["n"] += 1
            progress(f"🎨 {verb}: {done['n']} из {len(jobs)}")
            return n
        return None

    progress(f"🎨 {verb}: 0 из {len(jobs)}")
    try:
        with ThreadPoolExecutor(4) as pool:
            return [n for n in pool.map(draw, sorted(jobs)) if n is not None]
    except ai.AIError:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def _pairs(spec, labels):
    pairs = []
    for p in spec.get("pairs") or []:
        try:
            a, b, story = int(p["from"]), int(p["to"]), str(p.get("story", "")).strip()
        except (KeyError, TypeError, ValueError):
            continue
        if a in labels and b in labels and a != b and 0 < len(story) <= 60:
            pairs.append([a, b, story])
    return pairs


def _save(tmp, folder, data):
    with open(os.path.join(tmp, "theme.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    shutil.rmtree(folder, ignore_errors=True)
    os.replace(tmp, folder)
    theme = load(folder)
    preview_sheet(folder, theme)
    return theme


def wishes(folder):
    """The author's wishes remembered in a theme folder (English), to keep them when drawing the theme anew."""
    try:
        with open(os.path.join(folder, "theme.json"), encoding="utf-8") as f:
            return list(json.load(f).get("wishes") or [])
    except (OSError, ValueError, TypeError):
        return []


def build(typed, themes_dir, progress=lambda text: None, seed=None, wishes=()):
    """Makes the theme with the neural network and saves it in a new folder in themes_dir.
    wishes: what the author asked for on earlier tries. Returns (theme, folder)."""
    seed = random.randint(1, 10 ** 6) if seed is None else seed
    wishes = [str(w) for w in wishes if str(w).strip()][-5:]
    progress("✍️ Придумываю тему: название, слова, сюжеты…")
    fonts = "; ".join(f"{k} ({v[2]})" for k, v in FONT_LIBRARY.items())
    spec = ai.chat_json(SYSTEM, ASK.format(typed=typed.replace('"', "'"), fonts=fonts,
                                           wishes=WISHES.format("; ".join(wishes)) if wishes else ""))
    name = " ".join(str(spec.get("name") or typed).split())[:30]
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 '&-]*", name):
        name = "Fun"
    pics = [p for p in spec.get("pictures") or [] if isinstance(p, dict) and p.get("prompt")][:PICTURES]
    if len(pics) < MIN_PICTURES:
        raise ai.AIError("Нейросеть не придумала картинки для этой темы. Попробуйте написать тему иначе.")

    folder = os.path.join(themes_dir, f"{slug(name)}-{seed}")
    tmp = folder + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    good = _draw_all({i + 1: p for i, p in enumerate(pics)}, tmp, name, seed, progress, "Рисую картинки")
    if len(good) < MIN_PICTURES:
        shutil.rmtree(tmp, ignore_errors=True)
        raise ai.AIError("Не получилось нарисовать достаточно картинок для этой темы. Попробуйте ещё раз "
                         "или напишите тему иначе.")
    labels = {n: _label(pics[n - 1], n) for n in good}
    key = str(spec.get("font", "")).strip().lower()
    data = {
        "typed": typed, "seed": seed, "name": name,
        "word": " ".join(str(spec.get("word") or name.lower()).split())[:30],
        "holiday": bool(spec.get("holiday")),
        "tagline": str(spec.get("tagline") or "a super fun puzzle book").strip().lower()[:40],
        "pictures": [{"n": n, "label": labels[n], "prompt": str(pics[n - 1]["prompt"])[:300]} for n in good],
        "pairs": _pairs(spec, labels), "words": clean_words(spec.get("words")),
        "colors": {k: "#%02x%02x%02x" % v for k, v in palette(spec.get("colors")).items() if k != "sticker"},
        "font": key if key in FONT_LIBRARY else "luckiest",
        "keywords": [str(k).strip().lower()[:50] for k in spec.get("keywords") or [] if str(k).strip()][:7],
        "gift": str(spec.get("gift") or "a fun screen-free gift for kids").strip().rstrip(".")[:90],
        "wishes": wishes,
    }
    return _save(tmp, folder, data), folder


def revise(folder, feedback, themes_dir, progress=lambda text: None, seed=None):
    """Redraws the pictures the author's words (any language) are about and keeps the others.
    Saves the result as a new theme folder. Returns (theme, folder, redrawn, failed): picture numbers as on
    the preview sheet."""
    seed = random.randint(1, 10 ** 6) if seed is None else seed
    with open(os.path.join(folder, "theme.json"), encoding="utf-8") as f:
        data = json.load(f)
    pics = data["pictures"]                                 # position on the sheet = index + 1
    old = data.get("wishes") or []
    progress("✍️ Нейросеть читает ваши правки…")
    listing = "\n".join(f"{i}. {p['label']}: {p.get('prompt') or p['label']}" for i, p in enumerate(pics, 1))
    spec = ai.chat_json(SYSTEM, REVISE.format(
        name=data["name"], pictures=listing, feedback=feedback.replace('"', "'")[:1000],
        wishes=WISHES.format("; ".join(old[-5:])) if old else ""))
    jobs = {}
    for p in spec.get("pictures") or []:
        try:
            pos = int(p["n"])
        except (KeyError, TypeError, ValueError):
            continue
        if 1 <= pos <= len(pics) and str(p.get("prompt") or "").strip():
            jobs[pics[pos - 1]["n"]] = {"name": p.get("name"), "prompt": str(p["prompt"]).strip()}
    if not jobs:
        raise ai.AIError("Не понял, какие картинки перерисовать. Назовите номера картинок с листа, например: "
                         "«2 и 5 замени на вертолёты, людей не рисуй».")
    out = os.path.join(themes_dir, f"{slug(data['name'])}-{seed}")
    tmp = out + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(folder, tmp, ignore=shutil.ignore_patterns("preview.png", "theme.json"))
    good = _draw_all(jobs, tmp, data["name"], seed, progress, "Перерисовываю")
    by_slot = {p["n"]: i for i, p in enumerate(pics, 1)}
    for p in pics:
        if p["n"] in good:
            p["label"] = _label(jobs[p["n"]], p["n"])
            p["prompt"] = jobs[p["n"]]["prompt"][:300]
    labels = {p["n"]: p["label"] for p in pics}
    pairs = _pairs({"pairs": [{**q, "from": pics[int(q["from"]) - 1]["n"], "to": pics[int(q["to"]) - 1]["n"]}
                              for q in spec.get("pairs") or [] if _pos_ok(q, len(pics))]}, labels)
    wish = " ".join(str(spec.get("wish") or "").split())[:200]
    data.update(seed=seed, pairs=pairs or data["pairs"], wishes=(old + [wish])[-5:] if wish else old)
    theme = _save(tmp, out, data)
    return theme, out, sorted(by_slot[n] for n in good), sorted(by_slot[n] for n in jobs if n not in good)


def _pos_ok(q, count):
    try:
        return isinstance(q, dict) and 1 <= int(q["from"]) <= count and 1 <= int(q["to"]) <= count
    except (KeyError, TypeError, ValueError):
        return False


# -------------------------------------------------------------------- load
_loaded = {}


def load(folder):
    """The theme dict from a folder made by build(); registers its pictures for drawing."""
    folder = os.path.abspath(folder)
    if folder in _loaded:
        return _loaded[folder]
    with open(os.path.join(folder, "theme.json"), encoding="utf-8") as f:
        data = json.load(f)
    tag = "ai_" + slug(os.path.basename(folder)).replace("-", "_")
    names, labels, shapes, figures = [], {}, [], []
    for p in data["pictures"]:
        n = p["n"]
        name = f"{tag}_{n}"
        icon = Image.open(os.path.join(folder, f"pic_{n:02d}.png")).convert("RGBA")
        sil = Image.open(os.path.join(folder, f"sil_{n:02d}.png")).convert("L")
        RASTER[name] = icon
        names.append(name)
        labels[n] = name
        label = p["label"]
        try:
            inside, fill = raster.shape_test(sil)
            if fill >= 0.28:
                SHAPES[name] = inside
                SHAPE_NAMES[name] = label[:1].upper() + label[1:]
                if fill < 0.42:
                    THIN_SHAPES.add(name)
                shapes.append((fill, name))
        except raster.BadArt:
            pass
        try:
            fig = raster.figure(icon, sil)
            if len(fig["outline"]) >= 10:
                fig["label"] = label
                FIGURES[name] = fig
                figures.append(name)
        except raster.BadArt:
            pass
    pairs = [(labels[a], labels[b], story) for a, b, story in data["pairs"] if a in labels and b in labels]
    if not pairs:
        first = data["pictures"][0]
        pairs = [(names[0], names[i], f"Help the {first['label']} find the {p['label']}!")
                 for i, p in enumerate(data["pictures"][1:4], 1)]
    colors = palette(data["colors"])
    word = data["word"]
    low = word.lower()
    title_font, sub_font, _ = FONT_LIBRARY[data["font"]]
    keywords = data["keywords"] or [f"{low} activity book for kids ages 6-8"]
    for extra in (f"{low} puzzle book for kids", "activity book for kids ages 6-8", "puzzle books for kids 6-8"):
        if len(keywords) < 7 and extra not in keywords:
            keywords.append(extra)
    theme = {
        "name": data["name"], "word": word, "holiday": data["holiday"], "ai": True, "folder": folder,
        "icons": names,
        "maze_shapes": [n for _, n in sorted(shapes, reverse=True)[:4]] + ["circle"],
        "dots": figures,
        "pairs": pairs,
        "cover": colors,
        "keywords": keywords,
        "gift": data["gift"],
        "categories": [],
        "words": data["words"] if len(data["words"]) >= 8 else ["STAR", "HEART", "SMILE", "HAPPY", "PLAY", "FUN",
                                                                  "GAME", "PUZZLE", "COLOR", "PENCIL"],
        "art": {"font": title_font, "sub_font": sub_font, "font_k": font_k(title_font), "hero": names[0],
                "tagline": data["tagline"], "corners": (names[1 % len(names)], names[2 % len(names)]),
                "scene": names[3:9] or names, "faint": names[:4]},
    }
    _loaded[folder] = theme
    return theme


def preview_sheet(folder, theme):
    """preview.png: all pictures of the theme in one image, for the bot to show."""
    from .icons import draw_raster
    from .lib import Canvas
    names = theme["icons"]
    cols = 4
    rows = (len(names) + cols - 1) // cols
    C = Canvas(cols * 100, rows * 100, "L", 255)
    for i, name in enumerate(names):
        x, y = (i % cols) * 100, C.h - (i // cols) * 100
        draw_raster(C, RASTER[name], x + 50, y - 50, 86)
        C.text(x + 9, y - 15, str(i + 1), name="LuckiestGuy-Regular.ttf", pt=13, anchor="ls",
               outline=2.5, outline_gray=255)
    img = C.final_bytes().convert("RGB")
    img.thumbnail((1200, 1200))
    img.save(os.path.join(folder, "preview.png"))
    return os.path.join(folder, "preview.png")
