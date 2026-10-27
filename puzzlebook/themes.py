"""Book themes: title words, icons for pictures, and word lists for word search.

To add a theme, copy one block and change it. Words: capital letters only, no spaces.
Icons must be names from icons.py (ICONS).
"""

THEMES = {
    "christmas": {
        "name": "Christmas",
        "icons": ["tree", "star", "gift", "snowman", "heart", "moon", "house", "balloon", "ball", "cloud"],
        "pairs": [("snowman", "house", "Help the snowman get home!"), ("star", "tree", "Put the star on the tree!"),
                  ("gift", "house", "Take the gift to the house!"), ("snowman", "gift", "Help the snowman find the gift!")],
        "words": ["SANTA", "ELF", "GIFT", "TREE", "STAR", "SNOW", "BELL", "SLED", "TOYS", "CANDY", "REINDEER",
                  "STOCKING", "COOKIE", "WREATH", "ANGEL", "MERRY", "JOLLY", "SNOWMAN", "MITTENS", "CAROL",
                  "ORNAMENT", "RIBBON", "WINTER", "CHIMNEY", "NORTH", "POLE", "LIGHTS", "FROST"],
    },
    "halloween": {
        "name": "Halloween",
        "icons": ["pumpkin", "ghost", "moon", "star", "house", "tree", "cloud", "apple", "balloon", "heart"],
        "pairs": [("ghost", "house", "Help the ghost find the spooky house!"),
                  ("pumpkin", "moon", "Roll the pumpkin to the moon!"),
                  ("ghost", "pumpkin", "Help the ghost find the pumpkin!")],
        "words": ["GHOST", "BAT", "WITCH", "CANDY", "PUMPKIN", "SPIDER", "WEB", "BROOM", "MOON", "OWL", "CAT",
                  "SKULL", "TREAT", "TRICK", "COSTUME", "MASK", "MUMMY", "SPOOKY", "CAULDRON", "NIGHT",
                  "LANTERN", "HAUNTED", "MONSTER", "BOO", "FANGS", "CAPE"],
    },
    "space": {
        "name": "Space",
        "icons": ["rocket", "planet", "star", "moon", "sun", "cloud", "flag", "ball", "balloon", "heart"],
        "pairs": [("rocket", "moon", "Fly the rocket to the moon!"), ("rocket", "planet", "Find the way to the planet!"),
                  ("rocket", "star", "Zoom to the bright star!")],
        "words": ["ROCKET", "PLANET", "STAR", "MOON", "SUN", "COMET", "ORBIT", "ALIEN", "MARS", "EARTH", "SPACE",
                  "GALAXY", "SATURN", "JUPITER", "VENUS", "CRATER", "ASTRONAUT", "LAUNCH", "GRAVITY", "METEOR",
                  "UFO", "SHUTTLE", "NEPTUNE", "TELESCOPE", "SKY"],
    },
    "animals": {
        "name": "Animal",
        "icons": ["bunny", "mouse", "bee", "fish", "carrot", "cheese", "flower", "apple", "tree", "sun", "star"],
        "pairs": [("bunny", "carrot"), ("mouse", "cheese"), ("bee", "flower"), ("fish", "boat", "Help the fish swim to the boat!")],
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
