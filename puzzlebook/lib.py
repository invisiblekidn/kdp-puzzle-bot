"""Drawing helpers for the activity-book generator.

A page is drawn on a supersampled grayscale canvas in PDF points (1/72 in, y axis up),
then downsampled to 300 DPI and written into a PDF by a tiny built-in writer.
Only Pillow is needed. Fonts (SIL Open Font License) ship in the fonts/ folder.
"""
import math
import os
import zlib

from PIL import Image, ImageDraw, ImageFont

DPI = 300
SS = 2                              # supersampling factor (anti-aliasing)
S = DPI / 72 * SS                   # device pixels per point while drawing
PW, PH = 612.0, 792.0               # 8.5 x 11 in
OUT_W, OUT_H = round(PW * DPI / 72), round(PH * DPI / 72)   # 2550 x 3300 px

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
TITLE_FONT, BOLD, REG = "Fredoka.ttf", "Andika-Bold.ttf", "Andika-Regular.ttf"
VARIATIONS = {TITLE_FONT: [600, 100]}     # Fredoka is a variable font: weight, width
_fonts = {}


def font(name, pt):
    key = (name, pt)
    if key not in _fonts:
        f = ImageFont.truetype(os.path.join(FONT_DIR, name), round(pt * S))
        if name in VARIATIONS:
            f.set_variation_by_axes(VARIATIONS[name])
        _fonts[key] = f
    return _fonts[key]


def wrap(text, name, pt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w points."""
    f = font(name, pt)
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if f.getlength(trial) / S <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- geometry
def ellipse_pts(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=360.0, n=72):
    """Points on an ellipse (angles in degrees, y up). Full ellipses omit the duplicate end point."""
    full = abs(a1 - a0) >= 360
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for i in range(n if full else n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def resample(pts, n, closed=False):
    """n points spaced equally along the polyline (or closed polygon)."""
    P = list(pts) + ([pts[0]] if closed else [])
    cum = [0.0]
    for a, b in zip(P, P[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = cum[-1]
    m = n if closed else n - 1
    out, j = [], 0
    for i in range(n):
        t = total * i / m
        while j < len(cum) - 2 and cum[j + 1] < t:
            j += 1
        seg = cum[j + 1] - cum[j]
        u = (t - cum[j]) / seg if seg else 0.0
        out.append((P[j][0] + (P[j + 1][0] - P[j][0]) * u, P[j][1] + (P[j + 1][1] - P[j][1]) * u))
    return out


def fit_to_box(pts, x0, y0, x1, y1):
    """Uniformly scale + centre points inside the box."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    k = min((x1 - x0) / w, (y1 - y0) / h)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    bx, by = (x0 + x1) / 2, (y0 + y1) / 2
    return [(bx + (x - cx) * k, by + (y - cy) * k) for x, y in pts], k


def star_pts(R, r, points=5, cx=0.0, cy=0.0):
    pts = []
    for i in range(points * 2):
        rad = R if i % 2 == 0 else r
        a = math.radians(90 + 180 * i / points)
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    return pts


def heart_pts(width, n=120, cx=0.0, cy=0.0):
    k = width / 32.0
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * k, cy + (y + 5) * k))
    return pts


def rounded(x0, y0, x1, y1, r, n=10):
    """Rounded rectangle outline points."""
    pts = []
    for (x, y, a0) in ((x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270)):
        pts += [(x + r * math.cos(math.radians(a0 + 90 * i / n)), y + r * math.sin(math.radians(a0 + 90 * i / n)))
                for i in range(n + 1)]
    return pts


# ------------------------------------------------------------------ canvas
class Canvas:
    """Page canvas (w x h points). mode "RGB" is for the colour cover; gray values then map to gray RGB.
    self.colors remaps gray values while drawing (cover: coloured icon fills; pages: faint background icons)."""

    def __init__(self, w=PW, h=PH, mode="L", bg=255):
        self.w, self.h, self.mode = w, h, mode
        self.colors = {}
        self.im = Image.new(mode, (round(w * S), round(h * S)), self.ink(bg))
        self.d = ImageDraw.Draw(self.im)

    def ink(self, v):
        if not isinstance(v, int):
            return v
        v = self.colors.get(v, v)
        return v if self.mode == "L" or not isinstance(v, int) else (v, v, v)

    def _p(self, x, y):
        return (x * S, (self.h - y) * S)

    def poly(self, pts, fill=255, seam=False):
        """seam=True also paints the edge, so polygons that share edges leave no hairline gaps."""
        ink = self.ink(fill)
        self.d.polygon([self._p(*p) for p in pts], fill=ink, outline=ink if seam else None, width=3 if seam else 1)

    def rect(self, x0, y0, x1, y1, fill=0):
        a, b = self._p(min(x0, x1), max(y0, y1)), self._p(max(x0, x1), min(y0, y1))
        self.d.rectangle([a, b], fill=self.ink(fill))

    def dot(self, x, y, r, fill=0):
        px, py = self._p(x, y)
        self.d.ellipse([px - r * S, py - r * S, px + r * S, py + r * S], fill=self.ink(fill))

    def ring(self, x, y, r, w, gray=0):
        px, py = self._p(x, y)
        self.d.ellipse([px - r * S, py - r * S, px + r * S, py + r * S],
                       outline=self.ink(gray), width=max(1, round(w * S)))

    def stroke(self, pts, w, dash=None, closed=False, gray=0):
        """Round-capped stroke of width w (pt). dash=(visible_dash_len, gap) in pt."""
        P = [self._p(*p) for p in pts]
        if closed:
            P.append(P[0])
        r = w * S / 2
        step = max(0.8, r * 0.12)
        if dash:
            period = (dash[0] + dash[1]) * S
            on = max(0.0, dash[0] - w) * S
        d, ink = self.d, self.ink(gray)
        t = 0.0
        for (x0, y0), (x1, y1) in zip(P, P[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            if seg == 0:
                continue
            n = max(1, math.ceil(seg / step))
            for i in range(n + 1):
                if dash and ((t + seg * i / n) % period) > on:
                    continue
                x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
                d.ellipse([x - r, y - r, x + r, y + r], fill=ink)
            t += seg

    def shape(self, pts, w, fill=255, gray=0, dash=None):
        if fill is not None:
            self.poly(pts, fill)
        self.stroke(pts, w, dash=dash, closed=True, gray=gray)

    def arrow(self, x, y, ang_deg, size, gray=0):
        """Filled arrow head with its tip at (x, y) pointing along ang_deg."""
        a = math.radians(ang_deg)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x, y), (x - size * ca + size * 0.55 * sa, y - size * sa - size * 0.55 * ca),
               (x - size * ca - size * 0.55 * sa, y - size * sa + size * 0.55 * ca)]
        self.poly(pts, gray)

    def text(self, x, y, s, name=REG, pt=14, anchor="ms", gray=0, outline=0, outline_gray=0):
        """outline: width in pt of a border drawn around the letters (cover titles)."""
        self.d.text(self._p(x, y), s, font=font(name, pt), fill=self.ink(gray), anchor=anchor,
                    stroke_width=round(outline * S), stroke_fill=self.ink(outline_gray))

    def final_bytes(self):
        return self.im.resize((round(self.w * DPI / 72), round(self.h * DPI / 72)), Image.LANCZOS)


# ------------------------------------------------------------------ PDF
def _pdf_str(s):
    s = s.encode("ascii", "replace").decode("ascii")
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


class PdfWriter:
    """Writes one full-page 8-bit grayscale image per page (Flate, lossless)."""

    def __init__(self, path, title="", author=""):
        self.f = open(path, "wb")
        self.f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self.offs, self.pages = {}, []
        self.next_id = 4                      # 1 catalog, 2 page tree, 3 info
        self.title, self.author = title, author

    def _obj(self, oid, body):
        self.offs[oid] = self.f.tell()
        self.f.write(b"%d 0 obj\n" % oid + body + b"\nendobj\n")

    def add_page(self, img):
        data = zlib.compress(img.tobytes(), 9)
        im_id, ct_id, pg_id = self.next_id, self.next_id + 1, self.next_id + 2
        self.next_id += 3
        self._obj(im_id, b"<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /DeviceGray "
                         b"/BitsPerComponent 8 /Filter /FlateDecode /Length %d >>\nstream\n"
                  % (OUT_W, OUT_H, len(data)) + data + b"\nendstream")
        content = b"q %.2f 0 0 %.2f 0 0 cm /Im0 Do Q" % (PW, PH)
        self._obj(ct_id, b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")
        self._obj(pg_id, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] "
                         b"/Resources << /XObject << /Im0 %d 0 R >> >> /Contents %d 0 R >>"
                  % (PW, PH, im_id, ct_id))
        self.pages.append(pg_id)

    def close(self):
        kids = b" ".join(b"%d 0 R" % p for p in self.pages)
        self._obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
        self._obj(2, b"<< /Type /Pages /Kids [" + kids + b"] /Count %d >>" % len(self.pages))
        info = "<< /Title (%s) /Author (%s) /Producer (Python Pillow) >>" % (
            _pdf_str(self.title), _pdf_str(self.author))
        self._obj(3, info.encode("ascii"))
        xref = self.f.tell()
        n = self.next_id
        self.f.write(b"xref\n0 %d\n0000000000 65535 f \n" % n)
        for i in range(1, n):
            self.f.write(b"%010d 00000 n \n" % self.offs[i])
        self.f.write(b"trailer\n<< /Size %d /Root 1 0 R /Info 3 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (n, xref))
        self.f.close()
