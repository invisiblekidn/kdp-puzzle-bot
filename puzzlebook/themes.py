"""Book themes: title words, icons for pictures, and word lists for word search.

To add a theme, copy one block and change it. Words: capital letters only, no spaces.
Icons must be names from icons.py (ICONS).
Cover colours are RGB: bg (background), dark (outlines, spine), accent, light (pattern on the background),
sticker (fill colours for the pictures). Keywords tagged with a puzzle type are used only when the book has it.
"""

THEMES = {
    "christmas": {
        "name": "Christmas",
        "holiday": True,
        "icons": ["tree", "star", "gift", "snowman", "heart", "moon", "house", "balloon", "ball", "cloud"],
        "maze_shapes": ["tree", "star", "snowman", "gift", "heart", "circle"],
        "dots": ["tree", "snowman", "gingerbread", "bell", "star", "owl", "bunny"],
        "pairs": [("snowman", "house", "Help the snowman get home!"), ("star", "tree", "Put the star on the tree!"),
                  ("gift", "house", "Take the gift to the house!"), ("snowman", "gift", "Help the snowman find the gift!")],
        "cover": {"bg": (200, 34, 52), "dark": (92, 8, 24), "accent": (24, 128, 76), "light": (222, 74, 88),
                  "highlight": (255, 206, 64), "sticker": [(255, 206, 64), (120, 200, 120), (255, 255, 255), (130, 190, 255)]},
        "keywords": ["christmas activity book for kids ages 6-8", ("maze", "christmas mazes for kids"),
                     ("wordsearch", "christmas word search for kids"), ("dots", "christmas dot to dot for kids"),
                     ("hidden", "christmas seek and find book"), "stocking stuffers for kids 6-8",
                     "christmas gifts for boys and girls", "holiday puzzle book for children", "xmas activity book"],
        "gift": "a fun stocking stuffer and a screen-free gift for the holidays",
        "categories": ["Juvenile Nonfiction / Holidays & Celebrations / Christmas & Advent"],
        "words": ["SANTA", "ELF", "GIFT", "TREE", "STAR", "SNOW", "BELL", "SLED", "TOYS", "CANDY", "REINDEER",
                  "STOCKING", "COOKIE", "WREATH", "ANGEL", "MERRY", "JOLLY", "SNOWMAN", "MITTENS", "CAROL",
                  "ORNAMENT", "RIBBON", "WINTER", "CHIMNEY", "NORTH", "POLE", "LIGHTS", "FROST"],
    },
    "halloween": {
        "name": "Halloween",
        "holiday": True,
        "icons": ["pumpkin", "ghost", "moon", "star", "house", "tree", "cloud", "apple", "balloon", "heart"],
        "maze_shapes": ["pumpkin", "ghost", "moon", "circle", "star"],
        "dots": ["pumpkin", "ghost", "bat", "cat", "owl", "star"],
        "pairs": [("ghost", "house", "Help the ghost find the spooky house!"),
                  ("pumpkin", "moon", "Roll the pumpkin to the moon!"),
                  ("ghost", "pumpkin", "Help the ghost find the pumpkin!")],
        "cover": {"bg": (250, 128, 20), "dark": (52, 18, 72), "accent": (112, 52, 160), "light": (255, 158, 60),
                  "highlight": (255, 226, 80), "sticker": [(255, 255, 255), (170, 120, 230), (255, 226, 80), (140, 220, 120)]},
        "keywords": ["halloween activity book for kids ages 6-8", ("maze", "halloween mazes for kids"),
                     ("wordsearch", "halloween word search for kids"), ("dots", "halloween dot to dot for kids"),
                     ("hidden", "halloween seek and find book"), "halloween gifts for kids",
                     "spooky puzzle book for children", "trick or treat basket stuffers", "boo basket gifts for kids"],
        "gift": "a Halloween treat without the sugar and a great boo basket stuffer",
        "categories": ["Juvenile Nonfiction / Holidays & Celebrations / Halloween"],
        "words": ["GHOST", "BAT", "WITCH", "CANDY", "PUMPKIN", "SPIDER", "WEB", "BROOM", "MOON", "OWL", "CAT",
                  "SKULL", "TREAT", "TRICK", "COSTUME", "MASK", "MUMMY", "SPOOKY", "CAULDRON", "NIGHT",
                  "LANTERN", "HAUNTED", "MONSTER", "BOO", "FANGS", "CAPE"],
    },
    "space": {
        "name": "Space",
        "icons": ["rocket", "planet", "star", "moon", "sun", "cloud", "flag", "ball", "balloon", "heart"],
        "maze_shapes": ["rocket", "star", "moon", "circle", "diamond"],
        "dots": ["rocket", "ufo", "star", "bird", "fish"],
        "pairs": [("rocket", "moon", "Fly the rocket to the moon!"), ("rocket", "planet", "Find the way to the planet!"),
                  ("rocket", "star", "Zoom to the bright star!")],
        "cover": {"bg": (24, 36, 104), "dark": (8, 10, 44), "accent": (130, 76, 210), "light": (52, 70, 150),
                  "highlight": (255, 212, 64), "sticker": [(255, 212, 64), (255, 120, 120), (120, 210, 255), (170, 240, 140)]},
        "keywords": ["space activity book for kids ages 6-8", ("maze", "space mazes for kids"),
                     ("wordsearch", "space word search for kids"), ("dots", "space dot to dot for kids"),
                     ("hidden", "outer space seek and find"), "planets and rockets puzzle book",
                     "astronaut gifts for kids", "solar system activity book", "space gifts for boys and girls"],
        "gift": "a great gift for little astronauts and space fans",
        "categories": ["Juvenile Nonfiction / Science & Nature / Astronomy"],
        "words": ["ROCKET", "PLANET", "STAR", "MOON", "SUN", "COMET", "ORBIT", "ALIEN", "MARS", "EARTH", "SPACE",
                  "GALAXY", "SATURN", "JUPITER", "VENUS", "CRATER", "ASTRONAUT", "LAUNCH", "GRAVITY", "METEOR",
                  "UFO", "SHUTTLE", "NEPTUNE", "TELESCOPE", "SKY"],
    },
    "animals": {
        "name": "Animal",
        "icons": ["bunny", "mouse", "bee", "fish", "carrot", "cheese", "flower", "apple", "tree", "sun", "star"],
        "maze_shapes": ["fish", "apple", "heart", "cloud", "star", "circle"],
        "dots": ["fish", "cat", "bunny", "owl", "butterfly", "turtle", "whale", "snail", "bird"],
        "pairs": [("bunny", "carrot"), ("mouse", "cheese"), ("bee", "flower"), ("fish", "boat", "Help the fish swim to the boat!")],
        "cover": {"bg": (82, 176, 84), "dark": (24, 78, 40), "accent": (250, 140, 40), "light": (112, 196, 110),
                  "highlight": (255, 226, 80), "sticker": [(255, 226, 80), (255, 160, 190), (140, 200, 255), (255, 255, 255)]},
        "keywords": ["animal activity book for kids ages 6-8", ("maze", "animal mazes for kids"),
                     ("wordsearch", "animal word search for kids"), ("dots", "animal dot to dot for kids"),
                     ("hidden", "animal seek and find book"), "puzzle book for kids 6-8",
                     "gifts for animal lovers kids", "cute animals activity book", "brain games for kids"],
        "gift": "a great gift for animal lovers and a screen-free boredom buster",
        "categories": ["Juvenile Nonfiction / Animals / General"],
        "words": ["CAT", "DOG", "LION", "TIGER", "BEAR", "ZEBRA", "HORSE", "MOUSE", "BUNNY", "FROG", "DUCK", "OWL",
                  "FOX", "PANDA", "KOALA", "MONKEY", "GIRAFFE", "TURTLE", "RABBIT", "PENGUIN", "SHEEP", "COW",
                  "PIG", "GOAT", "EAGLE", "SNAKE"],
    },
}

DEFAULT_THEME = "animals"


def get_theme(name):
    key = (name or DEFAULT_THEME).strip().lower()
    if key not in THEMES:
        raise ValueError(f"Unknown theme '{name}'. Available: {', '.join(sorted(THEMES))}")
    return THEMES[key]


def theme_word(theme):
    """Holiday names stay capitalised in running text ("Christmas puzzles"), others don't ("space puzzles").
    A theme the author typed is used as typed."""
    if theme.get("word"):
        return theme["word"]
    return theme["name"] if theme.get("holiday") else theme["name"].lower()


def custom_theme(base, name, words=None):
    """A theme the author typed (e.g. "Dinosaurs"), drawn in the style of a built-in theme.

    Pictures, fonts and cover colours come from the base theme; the name goes into the title, the cover and
    the KDP texts; words (if given) replace the word search list.
    """
    theme = dict(base)
    word = " ".join(name.split()) or base["name"]
    low = word.lower()
    theme.update(name=" ".join(w[:1].upper() + w[1:] for w in word.split()), word=word, holiday=False,
                 keywords=[f"{low} activity book for kids ages 6-8", ("maze", f"{low} mazes for kids"),
                           ("wordsearch", f"{low} word search for kids"), ("dots", f"{low} dot to dot for kids"),
                           ("hidden", f"{low} seek and find book"), f"{low} puzzle book for kids",
                           "activity book for kids ages 6-8", "puzzle books for kids 6-8",
                           "screen free gifts for boys and girls"],
                 categories=[], gift="a fun screen-free gift for birthdays, holidays and road trips")
    if words:
        theme["words"] = list(words)
    return theme
