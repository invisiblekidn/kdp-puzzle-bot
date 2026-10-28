"""Turns a generated black-and-white picture into book art: a clean icon, a maze shape and a dot-to-dot outline.

The pictures come from the image model as line art on a white background. Here they are cleaned up
(specks and frames removed, light shading dropped), cut out along their silhouette and checked, so that
a bad picture can be thrown away and made again.
"""
import math
from collections import deque

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

WORK = 512                  # processing size in pixels


class BadArt(ValueError):
    """The picture is not usable (empty, a frame, a photo-like fill...)."""


def _components(mask, min_px=1):
    """Connected pieces of a 1-bit-ish L mask (255 = set) as lists of (x, y), largest first."""
    w, h = mask.size
    px = mask.load()
    seen = bytearray(w * h)
    out = []
    for y in range(h):
        for x in range(w):
            if px[x, y] < 128 or seen[y * w + x]:
                continue
            seen[y * w + x] = 1
            q, piece = deque([(x, y)]), []
            while q:
                cx, cy = q.popleft()
                piece.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny] >= 128:
                        seen[ny * w + nx] = 1
                        q.append((nx, ny))
            if len(piece) >= min_px:
                out.append(piece)
    out.sort(key=len, reverse=True)
    return out


def _mask_of(pieces, size):
    m = Image.new("L", size, 0)
    px = m.load()
    for piece in pieces:
        for x, y in piece:
            px[x, y] = 255
    return m


def _bbox(piece):
    xs = [p[0] for p in piece]
    ys = [p[1] for p in piece]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _fill_outside(walls):
    """Mask (255) of everything that can be reached from the picture edge without crossing walls."""
    w, h = walls.size
    free = ImageOps.invert(walls)                 # 255 where there is no wall
    canvas = free.copy()
    for x in range(w):
        for y in (0, h - 1):
            if canvas.getpixel((x, y)) == 255:
                ImageDraw.floodfill(canvas, (x, y), 128)
    for y in range(h):
        for x in (0, w - 1):
            if canvas.getpixel((x, y)) == 255:
                ImageDraw.floodfill(canvas, (x, y), 128)
    return canvas.point(lambda v: 255 if v == 128 else 0)


def clean(img):
    """Returns (icon RGBA, silhouette L) cropped to the picture; raises BadArt if it is not usable."""
    g = ImageOps.autocontrast(img.convert("L").resize((WORK, WORK), Image.LANCZOS), cutoff=1)
    ink = g.point(lambda v: 255 if v < 150 else 0).filter(ImageFilter.MedianFilter(3))
    # drop frames and borders: big thin pieces that span the picture
    small = ink.resize((WORK // 2, WORK // 2), Image.BOX).point(lambda v: 255 if v >= 64 else 0)
    pieces = _components(small, 4)
    if not pieces:
        raise BadArt("empty picture")
    keep = []
    for piece in pieces:
        x0, y0, x1, y1 = _bbox(piece)
        if (x1 - x0) > 0.92 * small.width and (y1 - y0) > 0.92 * small.height and len(piece) < 0.2 * small.width * small.height:
            continue                               # a frame around the picture
        keep.append(piece)
    if not keep:
        raise BadArt("only a frame")
    ink = ImageChops.multiply(ink, _mask_of(keep, small.size).resize(ink.size, Image.NEAREST).filter(ImageFilter.MaxFilter(3)))
    # silhouette: everything the outside cannot reach (small gaps in the outline are closed first)
    walls = ink.filter(ImageFilter.MaxFilter(5))
    sil = ImageOps.invert(_fill_outside(walls)).filter(ImageFilter.MinFilter(5))
    sil = ImageChops.lighter(sil, ink)
    # one object: keep the biggest piece of the silhouette
    small = sil.resize((WORK // 2, WORK // 2), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
    pieces = _components(small, 16)
    if not pieces:
        raise BadArt("no shape")
    big = pieces[0]
    near = [p for p in pieces[1:] if len(p) > 0.25 * len(big)]
    obj = _mask_of([big] + near, small.size).resize(sil.size, Image.NEAREST).filter(ImageFilter.MaxFilter(3))
    sil = ImageChops.multiply(sil, obj)
    ink = ImageChops.multiply(ink, obj)
    area = sum(1 for v in sil.getdata() if v >= 128) / (WORK * WORK)
    if area < 0.03:
        raise BadArt("picture too small")
    if area > 0.85:
        raise BadArt("picture fills the whole square")
    dark = sum(1 for a, b in zip(ink.getdata(), sil.getdata()) if a >= 128 and b >= 128)
    if dark / (area * WORK * WORK) > 0.5:
        raise BadArt("too much solid black to colour in")
    box = sil.getbbox()
    bw, bh = box[2] - box[0], box[3] - box[1]
    if max(bw, bh) > 4 * min(bw, bh):
        raise BadArt("too long and thin")
    # line art keeps its soft edges; light shading becomes white
    lines = g.point(lambda v: 0 if v < 90 else 255 if v > 200 else int((v - 90) * 255 / 110))
    lines = ImageChops.lighter(lines, ImageOps.invert(ink.filter(ImageFilter.MaxFilter(3))))
    pad = max(4, round(max(bw, bh) * 0.03))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(WORK, box[2] + pad), min(WORK, box[3] + pad))
    icon = Image.merge("RGBA", [lines, lines, lines, sil]).crop(box)
    return icon, sil.crop(box)


# ------------------------------------------------------------- maze shape
def shape_test(sil, grid=96, thin=0.08):
    """inside(u, v) on -1..1 (y up) for a maze in the shape of the silhouette; thin parts are left out."""
    side = max(sil.size)
    sq = Image.new("L", (side, side), 0)
    sq.paste(sil, ((side - sil.width) // 2, (side - sil.height) // 2))
    m = sq.resize((grid, grid), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
    k = max(3, round(grid * thin) | 1)
    m = m.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    pieces = _components(m)
    if not pieces:
        raise BadArt("shape vanished")
    m = _mask_of(pieces[:1], m.size)
    px = m.load()

    def inside(u, v):
        x = int((u + 1) / 2 * grid)
        y = int((1 - v) / 2 * grid)
        return 0 <= x < grid and 0 <= y < grid and px[x, y] >= 128

    fill = len(pieces[0]) / (grid * grid)
    return inside, fill


# ---------------------------------------------------------- dot-to-dot art
def _trace(mask):
    """Outer boundary of the biggest piece as a list of pixel points (Moore neighbour tracing)."""
    w, h = mask.size
    px = mask.load()
    on = lambda x, y: 0 <= x < w and 0 <= y < h and px[x, y] >= 128
    start = next(((x, y) for y in range(h) for x in range(w) if on(x, y)), None)
    if start is None:
        return []
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
    out = [start]
    cur, back = start, 4                          # we came from the left
    for _ in range(w * h * 2):
        for i in range(8):
            d = (back + 1 + i) % 8
            nx, ny = cur[0] + dirs[d][0], cur[1] + dirs[d][1]
            if on(nx, ny):
                back = (d + 4) % 8
                cur = (nx, ny)
                break
        else:
            break
        if cur == start:
            break
        out.append(cur)
    return out


def _rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    L = math.hypot(bx - ax, by - ay) or 1e-9
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs((bx - ax) * (ay - y) - (ax - x) * (by - ay)) / L
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return _rdp(pts[:idx + 1], eps)[:-1] + _rdp(pts[idx:], eps)


def figure(icon, sil, grid=160):
    """A dot-to-dot figure (as in figures.py) from the icon: outline points and the inner lines as a picture."""
    side = max(sil.size)
    sq = Image.new("L", (side, side), 0)
    off = ((side - sil.width) // 2, (side - sil.height) // 2)
    sq.paste(sil, off)
    m = sq.resize((grid, grid), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
    m = m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    m = _mask_of(_components(m)[:1], m.size)
    ring = _trace(m)
    if len(ring) < 20:
        raise BadArt("outline too small")
    pts = None
    for eps in (1.0, 1.5, 2.2, 3.0, 4.0):
        start = max(range(len(ring)), key=lambda i: ring[i][1])        # lowest point
        loop = ring[start:] + ring[:start]
        far = max(range(len(loop)), key=lambda i: math.dist(loop[0], loop[i]))
        pts = _rdp(loop[:far + 1], eps)[:-1] + _rdp(loop[far:] + loop[:1], eps)[:-1]
        if len(pts) <= 40:
            break
    if len(pts) < 6:
        raise BadArt("outline too simple")
    to_fig = lambda x, y: (x / grid * 100, (1 - y / grid) * 100)
    outline = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        v1 = (x - a[0], y - a[1])
        v2 = (b[0] - x, b[1] - y)
        ang = abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1])))
        fx, fy = to_fig(x, y)
        outline.append((fx, fy, 1) if ang > 55 else (fx, fy))
    # inner lines (eyes, spots...): the line art minus a band along the outside edge
    full = Image.new("L", (side, side), 0)
    full.paste(sil, off)
    inner_zone = full.filter(ImageFilter.MinFilter(max(3, round(side * 0.065) | 1)))
    lines = Image.new("L", (side, side), 255)
    lines.paste(icon.getchannel("R"), off)
    dark = ImageOps.invert(lines)
    inner = ImageChops.multiply(dark, inner_zone)
    detail = Image.merge("RGBA", [Image.new("L", (side, side), 0)] * 3 + [inner])
    probe = inner.resize((50, 50), Image.BOX).load()
    detail_pts = [(x * 2 + 1, 100 - y * 2 - 1) for y in range(50) for x in range(50) if probe[x, y] > 40]
    return dict(outline=outline, details=[], raster=(detail, (0, 0, 100, 100)), detail_pts=detail_pts)
