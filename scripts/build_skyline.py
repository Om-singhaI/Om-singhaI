#!/usr/bin/env python3
"""Build the open source skyline SVGs (light and dark) from scripts/merged.json.

One isometric building per repository, one floor per merged pull request,
grouped into company districts. Districts are sorted by their pull request
count, buildings by theirs. The street wraps into more rows as the data
grows, so it keeps its proportions from a handful of repos to about thirty.
Pure Python, no dependencies.

    python3 scripts/build_skyline.py                     # scripts/merged.json -> assets/skyline/
    python3 scripts/build_skyline.py --in data.json --out some/dir
    python3 scripts/build_skyline.py --static            # also write non-animated copies
"""
import html
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- palette
# company -> (base, deep: light mode ink, bright: dark mode ink)
PALETTE = {
    "Microsoft": ("#4f8ff7", "#1f5fd1", "#7fb0ff"),
    "Meta": ("#8a6cff", "#5a3fdc", "#b09cff"),
    "Cloudflare": ("#f48a33", "#b9540a", "#ffae6e"),
    "Apple": ("#98a2b0", "#525c6b", "#c5ccd6"),
    "AWS": ("#f2b233", "#9a6500", "#ffd06e"),
    "Google": ("#3fae5f", "#1f7a3a", "#72d38e"),
    "NVIDIA": ("#76b900", "#4a7600", "#a6e04a"),
    "Hugging Face": ("#ffcc33", "#8f6a00", "#ffe07a"),
    "Vercel": ("#6b7584", "#343b46", "#aab3c0"),
    "Tesla": ("#e5484d", "#b0262b", "#ff8a8e"),
    "NASA": ("#3a64c8", "#1d3f94", "#8aa8f0"),
    "OpenAI": ("#10a37f", "#08705a", "#5fd4b3"),
    "Anthropic": ("#d97757", "#a24a2c", "#f0a488"),
}
FALLBACK = ["#5b9bd5", "#c774e8", "#44b5a8", "#e07b39", "#8e9aaf", "#d4a72c"]

# ---------------------------------------------------------------- geometry
W = 900           # canvas width; the height follows the layout
KMAX = 34.0       # half width of one grid cell on screen (2:1 projection), at most
KMIN = 27.0       # below this the street wraps into another row
CAP = 3.0         # roof parapet
T = 15.0          # slab thickness
D = 1.2           # slab depth (gx)
FD = 0.62         # building depth (gx)
FS = 0.50         # building width along the street (gy)
PAD = 0.4         # slab padding before the first and after the last lot
SINGLE = 2.2      # slab length for a one building district
GAP = 0.5         # street between districts
MARGIN_L, MARGIN_R = 26.0, 26.0
ROW_GAP = 16.0    # clear space between one row's labels and the next row's roofs
TOP = 22.0        # clear space above the tallest roof

SANS = ("-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',"
        "Helvetica,Arial,sans-serif")
MONO = ("ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,"
        "'Liberation Mono',monospace")

LABEL_PX = 12.5
CHAR = 0.61 * LABEL_PX
NARROW = 560      # rendered px below which the phone layout takes over
NL_PX = 28        # phone layout: district label size
MAX_LABEL = 22    # longest repo label before it is shortened with an ellipsis

TITLE = "Where my pull requests landed"

# solved by layout()
K = KMAX
FH = 12.0
OX = 0.0
H = 0


def P(gx, gy, z=0.0, oy=0.0):
    return (OX + (gx - gy) * K, oy + (gx + gy) * K / 2.0 - z)


def pts(*ps):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """t=0 -> a, t=1 -> b"""
    ra, rb = hx(a), hx(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ra, rb))


def esc(s):
    return html.escape(str(s), quote=True)


def text_w(s, px, k=0.56):
    return len(s) * k * px


def short(name):
    return name if len(name) <= MAX_LABEL else name[:MAX_LABEL - 1] + "…"


def nice_date(iso):
    if not iso:
        return ""
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    y, m, d = (int(x) for x in iso[:10].split("-"))
    return f"{months[m - 1]} {d}, {y}"


# ---------------------------------------------------------------- data
def load(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    dists = []
    fb = 0
    for c in doc.get("companies", []):
        repos = [(r["name"], int(r["count"])) for r in c.get("repos", []) if int(r["count"]) > 0]
        if not repos:
            continue
        repos.sort(key=lambda r: (-r[1], r[0].lower()))
        name = c["company"]
        if name in PALETTE:
            base, deep, bright = PALETTE[name]
        else:
            base = FALLBACK[fb % len(FALLBACK)]
            fb += 1
            deep, bright = mix(base, "#0b1526", 0.4), mix(base, "#ffffff", 0.35)
        dists.append(dict(name=name, base=base, deep=deep, bright=bright,
                          repos=repos, total=sum(n for _, n in repos)))
    dists.sort(key=lambda d: (-d["total"], -len(d["repos"]), d["name"].lower()))
    return doc, dists


# ---------------------------------------------------------------- layout
def sign_len(d):
    """Street length the district needs so its sign fits on the slab face."""
    return (len(d["name"]) * (0.66 * 7.6 + 1.1) + 16) / 30.0


def district_len(d):
    if len(d["repos"]) == 1:
        return max(SINGLE, sign_len(d))
    return max(PAD + len(d["repos"]) + PAD, sign_len(d))


def plan_row(dists):
    cursor, out = 0.0, []
    for d in dists:
        n = len(d["repos"])
        L = district_len(d)
        start, end = cursor, cursor + L
        if n == 1:
            centers = [start + L / 2.0]
            trees = [start + 0.38, end - 0.38]
        else:
            off = (L - (2 * PAD + n)) / 2.0
            centers = [start + off + PAD + 0.5 + j for j in range(n)]
            trees = []
        out.append(dict(d, start=start, end=end, centers=centers, trees=trees))
        cursor = end + GAP
    return out, cursor - GAP


def partition(dists, rows):
    """Split the sorted districts into contiguous rows, minimising the longest row."""
    lens = [district_len(d) for d in dists]
    n = len(lens)

    def seg(i, j):
        return sum(lens[i:j]) + GAP * (j - i - 1)

    memo = {}

    def f(i, r):
        if (i, r) in memo:
            return memo[(i, r)]
        if r == 1:
            res = (seg(i, n), (n,))
        else:
            res = None
            for j in range(i + 1, n - r + 2):
                m, cuts = f(j, r - 1)
                v = max(seg(i, j), m)
                if res is None or v < res[0] - 1e-9:
                    res = (v, (j,) + cuts)
        memo[(i, r)] = res
        return res

    _, cuts = f(0, rows)
    out, i = [], 0
    for j in cuts:
        out.append(dists[i:j])
        i = j
    return out


def label_width(name, n):
    return (len(str(n)) + 1 + len(short(name))) * CHAR


def extents(plans, k):
    """Screen extent of the rows left and right of OX at a given K."""
    right = D * k
    left = 0.0
    for plan, length in plans:
        left = max(left, length * k)
        for d in plan:
            for (name, n), c in zip(d["repos"], d["centers"]):
                right = max(right, (D - c) * k + 8 + label_width(name, n))
    return left, right


def solve_k(plans):
    lo, hi = 10.0, KMAX
    for _ in range(50):
        mid = (lo + hi) / 2
        l, r = extents(plans, mid)
        if MARGIN_L + l + r + MARGIN_R <= W:
            lo = mid
        else:
            hi = mid
    return round(lo, 2)


def extra_top(n):
    return 30.0 if n >= 10 else (5.0 if n >= 4 else 0.0)


def phone_label(d, oy):
    ax, ay = P(D, (d["start"] + d["end"]) / 2.0, -T, oy)
    txt = f"{d['name']} {d['total']}"
    x = ax + 6
    # shrink a label that would run off the right edge rather than sliding it
    # left onto the neighbouring district's roofs; clamp only as a last resort
    fs = max(18.0, min(float(NL_PX), (W - 26 - x) / (0.6 * len(txt))))
    wdt = text_w(txt, fs, 0.6)
    x = min(x, W - 26 - wdt)
    return x, ay + fs + 6, wdt, fs


def row_boxes(plan, oy):
    """Axis aligned boxes covering everything a row draws (both layouts)."""
    boxes = []
    for d in plan:
        s, e = d["start"], d["end"]
        g = s
        while g < e - 1e-9:
            g2 = min(g + 0.5, e)
            boxes.append((P(0, g2)[0], P(0, g, 0, oy)[1], P(D, g)[0], P(D, g2, -T, oy)[1]))
            g = g2
        for (name, n), c in zip(d["repos"], d["centers"]):
            gx0, gx1 = (D - FD) / 2.0, (D + FD) / 2.0
            gy0, gy1 = c - FS / 2.0, c + FS / 2.0
            h = n * FH + CAP
            top = P(gx0, gy0, h, oy)[1] - extra_top(n) - 3
            boxes.append((P(gx0, gy1)[0], top, P(gx1, gy0)[0], P(gx1, gy1, 0, oy)[1]))
            ax, ay = P(D, c, -T, oy)
            boxes.append((ax - 3, ay - 3, ax + 8 + label_width(name, n), ay + 16))
        for tg in d["trees"]:
            tx, ty = P(D / 2.0, tg, 0, oy)
            boxes.append((tx - 7, ty - 19, tx + 11, ty + 5))
        x, y, wdt, fs = phone_label(d, oy)
        boxes.append((x, y - fs + 2, x + wdt, y + 8))
    return boxes


def overlap_x(a, b, pad=6.0):
    return a[0] < b[2] + pad and b[0] < a[2] + pad


def title_lines(n_keys):
    """Boxes for the title block (wide and phone layouts), line by line."""
    tx = 34
    kw = key_col_w()
    boxes = [
        (tx, 34, tx + text_w("OPEN SOURCE SKYLINE", 11, 0.8), 50),
        (tx, 60, tx + text_w("Where my pull", 26, 0.6), 88),
        (tx, 90, tx + text_w("requests landed", 26, 0.6), 118),
        (tx, 124, tx + text_w("merged since September 30, 2026", 14, 0.53), 142),
    ]
    ky = KEY_Y
    for r in range((n_keys + 1) // 2):
        cols = 2 if 2 * r + 1 < n_keys else 1
        boxes.append((tx, ky + r * 23 - 13, tx + cols * kw, ky + r * 23 + 5))
    # phone headline
    boxes += [
        (tx, 50, tx + text_w("Where my pull", 42, 0.6), 96),
        (tx, 100, tx + text_w("requests landed", 42, 0.6), 146),
        (tx, 152, tx + text_w("since September 30, 2026", 24, 0.53), 184),
    ]
    return boxes


KEY_Y = 172
KEY_NAMES = []


def key_col_w():
    return max([126.0] + [18 + text_w(f"{n} {t}", 13.5, 0.55) + 10 for n, t in KEY_NAMES])


def layout(dists):
    global K, FH, OX, H
    max_n = max(n for d in dists for _, n in d["repos"])
    FH = min(12.0, 190.0 / max_n)   # keep the tallest tower under ~190 px
    KEY_NAMES[:] = [(d["name"], d["total"]) for d in dists]

    best = None
    for rows in range(1, len(dists) + 1):
        plans = [plan_row(p) for p in partition(dists, rows)]
        k = solve_k(plans)
        best = (plans, k)
        if k >= KMIN:
            break
    plans, K = best
    left, right = extents(plans, K)
    # hug the right margin; the title block lives in the empty corner on the left
    OX = W - MARGIN_R - right

    obstacles = list(title_lines(len(dists)))
    rows = []
    oy0 = None
    for plan, length in plans:
        rel = row_boxes(plan, 0.0)
        oy = TOP - min(b[1] for b in rel)
        for b in rel:
            for o in obstacles:
                if overlap_x(b, o):
                    oy = max(oy, o[3] + ROW_GAP - b[1])
        if oy0 is None:
            oy0 = oy
        else:
            # snap to the isometric grid so every row sits on the dot lattice
            oy = oy0 + math.ceil((oy - oy0) / K - 1e-6) * K
        abs_boxes = [(b[0], b[1] + oy, b[2], b[3] + oy) for b in rel]
        obstacles += abs_boxes
        rows.append(dict(plan=plan, oy=oy, boxes=abs_boxes))

    city = [b for r in rows for b in r["boxes"]]
    H = max(b[3] for b in city) + 26
    # the floor key sits in the bottom right corner; push the canvas down if a row reaches it
    for b in city:
        if b[2] > W - 250 and b[3] > H - 70:
            H = b[3] + 70
    H = int(math.ceil(H))
    return rows


# ---------------------------------------------------------------- themes
THEMES = {
    "light": dict(
        bg0="#ffffff", bg1="#f4f7fb", border="#d8dee4", dot="#c9d3df",
        fg="#1f2328", muted="#59636e", faint="#8c959f",
        slab_top=lambda b: mix(b, "#ffffff", 0.88),
        slab_face=lambda d: d["deep"],
        slab_end=lambda d: mix(d["deep"], "#ffffff", 0.28),
        slab_ink="#ffffff",
        top=lambda b: mix(b, "#ffffff", 0.62),
        left=lambda b: mix(b, "#ffffff", 0.22),
        right=lambda b: mix(b, "#10223f", 0.10),
        edge=lambda b: mix(b, "#0b1526", 0.45),
        edge_op=0.55,
        floor_line=lambda b: mix(b, "#0b1526", 0.30),
        win_l="#ffffff", win_l_op=0.62, win_r="#eaf2ff", win_r_op=0.42,
        lit=None,
        shadow="#1b2b44", shadow_op=0.13,
        count=lambda d: d["deep"],
        trunk="#8a6a4f", leaf="#56b36b", leaf2="#3f9a55",
        sweep_op=0.55, star=None, beacon="#e5484d",
    ),
    "dark": dict(
        bg0="#0d1117", bg1="#0f1830", border="#30363d", dot="#1f2a3d",
        fg="#e6edf3", muted="#9198a1", faint="#6e7781",
        slab_top=lambda b: mix(b, "#0d1117", 0.84),
        slab_face=lambda d: mix(d["deep"], "#0d1117", 0.18),
        slab_end=lambda d: mix(d["base"], "#0d1117", 0.30),
        slab_ink="#ffffff",
        top=lambda b: mix(b, "#0d1117", 0.30),
        left=lambda b: mix(b, "#0d1117", 0.58),
        right=lambda b: mix(b, "#0d1117", 0.74),
        edge=lambda b: mix(b, "#ffffff", 0.10),
        edge_op=0.50,
        floor_line=lambda b: mix(b, "#0d1117", 0.86),
        win_l="#0a0f1a", win_l_op=0.55, win_r="#0a0f1a", win_r_op=0.55,
        lit="#ffd27a",
        shadow="#000000", shadow_op=0.35,
        count=lambda d: d["bright"],
        trunk="#6b5440", leaf="#2f7d4a", leaf2="#256a3d",
        sweep_op=0.16, star="#c9d6ff", beacon="#ff5a5f",
    ),
}


def lcg(seed):
    s = [seed]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return r


def rise(n):
    return n * FH + CAP + extra_top(n) + (FD + FS) * K / 2 + 6


# ---------------------------------------------------------------- builder
def build(theme_name, rows, since, animate=True):
    th = THEMES[theme_name]
    out = []
    a = out.append
    rnd = lcg(7 if theme_name == "dark" else 3)
    dists = [d for r in rows for d in r["plan"]]
    since_txt = nice_date(since)

    desc = ("An isometric city with one building per repository and one "
            "floor per merged pull request, grouped into company districts. "
            + "; ".join(
                f"{d['name']}: " + ", ".join(f"{r} {n}" for r, n in d["repos"])
                for d in dists) + ".")

    a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
      f'width="{W}" height="{H}" role="img" aria-labelledby="t d">')
    a(f'<title id="t">{esc(TITLE)}</title>')
    a(f'<desc id="d">{esc(desc)}</desc>')

    # ------------------------------------------------------------ styles
    css = [
        f".sans{{font-family:{SANS}}}",
        f".mono{{font-family:{MONO}}}",
        # phone layout: repo labels and the legend drop out, district names and the headline grow
        ".n{display:none}",
        f"@media (max-width:{NARROW}px){{.w{{display:none}}.n{{display:inline}}}}",
    ]
    if animate:
        for n in sorted({n for d in dists for _, n in d["repos"]}):
            css.append(f"@keyframes r{n}{{from{{transform:translateY({rise(n):.0f}px)}}"
                       f"to{{transform:translateY(0)}}}}")
        css += [
            ".b{animation-duration:1.15s;animation-timing-function:"
            "cubic-bezier(.16,.84,.3,1);animation-fill-mode:both}",
            "@keyframes fade{from{opacity:0}to{opacity:1}}",
            ".f{animation:fade .9s ease-out both}",
            "@keyframes sweep{0%{transform:translateX(0)}"
            "30%{transform:translateX(1080px)}100%{transform:translateX(1080px)}}",
            ".sw{animation:sweep 10s cubic-bezier(.45,0,.35,1) 2.8s infinite both}",
            "@keyframes blink{0%,62%{opacity:1}72%,92%{opacity:.18}100%{opacity:1}}",
            ".bl{animation:blink 2.6s ease-in-out 1.6s infinite}",
            "@keyframes tw{0%,100%{opacity:1}50%{opacity:.2}}",
            ".tw{animation:tw 7s ease-in-out infinite}",
            "@media (prefers-reduced-motion:reduce){.b,.f,.sw,.bl,.tw"
            "{animation:none!important}}",
        ]
    a("<style>" + "".join(css) + "</style>")

    # ------------------------------------------------------------ defs
    OY0 = rows[0]["oy"]
    a("<defs>")
    a(f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0" stop-color="{th["bg0"]}"/>'
      f'<stop offset="1" stop-color="{th["bg1"]}"/></linearGradient>')
    a('<linearGradient id="sg" x1="0" y1="0" x2="1" y2="0">'
      '<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
      f'<stop offset=".5" stop-color="#fff" stop-opacity="{th["sweep_op"]}"/>'
      '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    # isometric dot grid aligned with the city
    px, py = OX % (2 * K), OY0 % K
    a(f'<pattern id="grid" width="{2 * K:.2f}" height="{K:.2f}" '
      f'patternUnits="userSpaceOnUse" x="{px:.1f}" y="{py:.1f}">'
      f'<circle cx="0" cy="0" r="1.1" fill="{th["dot"]}"/>'
      f'<circle cx="{2 * K:.2f}" cy="0" r="1.1" fill="{th["dot"]}"/>'
      f'<circle cx="0" cy="{K:.2f}" r="1.1" fill="{th["dot"]}"/>'
      f'<circle cx="{2 * K:.2f}" cy="{K:.2f}" r="1.1" fill="{th["dot"]}"/>'
      f'<circle cx="{K:.2f}" cy="{K / 2:.2f}" r="1.1" fill="{th["dot"]}"/>'
      '</pattern>')
    a('<radialGradient id="gm" cx=".62" cy=".42" r=".62">'
      '<stop offset="0" stop-color="#fff" stop-opacity="1"/>'
      '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
    a(f'<mask id="gmask"><rect width="{W}" height="{H}" fill="url(#gm)"/></mask>')

    silhouettes = []
    clips = []
    bodies = []   # (sort key, svg)
    building_index = 0

    for ri, row in enumerate(rows):
        oy = row["oy"]
        for d in row["plan"]:
            base = d["base"]
            s, e = d["start"], d["end"]
            slab = []
            slab.append(f'<polygon points="{pts(P(0, s, 0, oy), P(D, s, 0, oy), P(D, e, 0, oy), P(0, e, 0, oy))}" '
                        f'fill="{th["slab_top"](base)}"/>')
            slab.append(f'<polygon points="{pts(P(D, s, 0, oy), P(D, e, 0, oy), P(D, e, -T, oy), P(D, s, -T, oy))}" '
                        f'fill="{th["slab_face"](d)}"/>')
            slab.append(f'<polygon points="{pts(P(0, e, 0, oy), P(D, e, 0, oy), P(D, e, -T, oy), P(0, e, -T, oy))}" '
                        f'fill="{th["slab_end"](d)}"/>')
            slab.append(f'<polyline points="{pts(P(D, s, 0, oy), P(D, e, 0, oy), P(0, e, 0, oy))}" fill="none" '
                        f'stroke="#ffffff" stroke-opacity="{0.7 if theme_name == "light" else 0.14}" '
                        f'stroke-width="1"/>')
            # signage on the long face, reading up and to the right; shrink to fit
            cx, cy = P(D, (s + e) / 2.0, -T / 2.0, oy)
            sign = d["name"].upper()
            fs = 8.6 if len(d["repos"]) == 1 else 9.4
            fit = (((e - s) * K - 14) / max(1, len(sign)) - 1.1) / 0.66
            fs = max(6.0, min(fs, fit))
            slab.append(f'<text class="sans" transform="matrix(1 -0.5 0 1 {cx:.1f} {cy:.1f})" '
                        f'y="{fs * 0.33:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="700" '
                        f'letter-spacing="1.1" fill="{th["slab_ink"]}">{esc(sign)}</text>')
            bodies.append(((ri, s - 0.01), "".join(slab)))

            for tg in d["trees"]:
                tx, ty = P(D / 2.0, tg, 0, oy)
                tr = []
                tr.append(f'<ellipse cx="{tx + 3:.1f}" cy="{ty + 1.5:.1f}" rx="8" ry="3.4" '
                          f'fill="{th["shadow"]}" fill-opacity="{th["shadow_op"]}"/>')
                tr.append(f'<rect x="{tx - 1:.1f}" y="{ty - 7:.1f}" width="2" height="7" '
                          f'fill="{th["trunk"]}"/>')
                tr.append(f'<circle cx="{tx:.1f}" cy="{ty - 12:.1f}" r="6.4" fill="{th["leaf2"]}"/>')
                tr.append(f'<circle cx="{tx - 1.4:.1f}" cy="{ty - 13.4:.1f}" r="4.6" fill="{th["leaf"]}"/>')
                bodies.append(((ri, tg), "".join(tr)))

            for (repo, n), c in zip(d["repos"], d["centers"]):
                def Pb(gx, gy, z=0.0):
                    return P(gx, gy, z, oy)
                gx0, gx1 = (D - FD) / 2.0, (D + FD) / 2.0
                gy0, gy1 = c - FS / 2.0, c + FS / 2.0
                h = n * FH + CAP
                delay = 0.15 + building_index * 0.085
                building_index += 1

                b = []
                b.append(f'<polygon points="{pts(Pb(gx0, gy1), Pb(gx1, gy1), Pb(gx1, gy1, h), Pb(gx0, gy1, h))}" '
                         f'fill="{th["left"](base)}"/>')
                b.append(f'<polygon points="{pts(Pb(gx1, gy0), Pb(gx1, gy1), Pb(gx1, gy1, h), Pb(gx1, gy0, h))}" '
                         f'fill="{th["right"](base)}"/>')
                fl = []
                for k in range(1, n):
                    z = k * FH
                    fl.append(f"M{pts(Pb(gx0, gy1, z))}L{pts(Pb(gx1, gy1, z))}L{pts(Pb(gx1, gy0, z))}")
                if fl:
                    b.append(f'<path d="{"".join(fl)}" fill="none" stroke="{th["floor_line"](base)}" '
                             f'stroke-width="0.8" stroke-opacity="0.75"/>')
                # windows
                sc = FH / 12.0
                wl, wr, lit, tw = [], [], [], []
                for k in range(n):
                    z0, z1 = k * FH + 3.4 * sc, k * FH + 9.0 * sc
                    for fa, fb in ((0.16, 0.42), (0.58, 0.84)):
                        ga, gb = gx0 + fa * FD, gx0 + fb * FD
                        poly = pts(Pb(ga, gy1, z0), Pb(gb, gy1, z0), Pb(gb, gy1, z1), Pb(ga, gy1, z1))
                        if th["lit"] and rnd() < 0.5:
                            (tw if rnd() < 0.12 else lit).append(poly)
                        else:
                            wl.append(poly)
                    for fa, fb in ((0.16, 0.42), (0.58, 0.84)):
                        ga, gb = gy0 + fa * FS, gy0 + fb * FS
                        poly = pts(Pb(gx1, ga, z0), Pb(gx1, gb, z0), Pb(gx1, gb, z1), Pb(gx1, ga, z1))
                        if th["lit"] and rnd() < 0.38:
                            (tw if rnd() < 0.12 else lit).append(poly)
                        else:
                            wr.append(poly)
                if wl:
                    b.append(f'<path d="{"".join("M" + p.replace(" ", "L") + "Z" for p in wl)}" '
                             f'fill="{th["win_l"]}" fill-opacity="{th["win_l_op"]}"/>')
                if wr:
                    b.append(f'<path d="{"".join("M" + p.replace(" ", "L") + "Z" for p in wr)}" '
                             f'fill="{th["win_r"]}" fill-opacity="{th["win_r_op"]}"/>')
                if lit:
                    b.append(f'<path d="{"".join("M" + p.replace(" ", "L") + "Z" for p in lit)}" '
                             f'fill="{th["lit"]}" fill-opacity="0.92"/>')
                for i, p in enumerate(tw):
                    cls = ' class="tw"' if animate else ""
                    sty = f' style="animation-delay:{1.5 + (building_index * 1.7 + i * 2.3) % 6:.1f}s"' if animate else ""
                    b.append(f'<polygon{cls}{sty} points="{p}" fill="{th["lit"]}" fill-opacity="0.92"/>')
                # roof
                b.append(f'<polygon points="{pts(Pb(gx0, gy0, h), Pb(gx1, gy0, h), Pb(gx1, gy1, h), Pb(gx0, gy1, h))}" '
                         f'fill="{th["top"](base)}"/>')
                ins = 0.07
                b.append(f'<polygon points="{pts(Pb(gx0 + ins, gy0 + ins, h), Pb(gx1 - ins, gy0 + ins, h), Pb(gx1 - ins, gy1 - ins, h), Pb(gx0 + ins, gy1 - ins, h))}" '
                         f'fill="{th["right"](base)}" fill-opacity="0.22"/>')
                b.append(f'<path d="M{pts(Pb(gx0, gy1))}L{pts(Pb(gx1, gy1))}L{pts(Pb(gx1, gy0))}'
                         f'L{pts(Pb(gx1, gy0, h))}L{pts(Pb(gx0, gy0, h))}L{pts(Pb(gx0, gy1, h))}Z'
                         f'M{pts(Pb(gx1, gy1))}L{pts(Pb(gx1, gy1, h))}L{pts(Pb(gx0, gy1, h))}'
                         f'M{pts(Pb(gx1, gy1, h))}L{pts(Pb(gx1, gy0, h))}" fill="none" '
                         f'stroke="{th["edge"](base)}" stroke-opacity="{th["edge_op"]}" '
                         f'stroke-width="0.8" stroke-linejoin="round"/>')
                # rooftop unit on the mid height towers
                if 4 <= n < 10:
                    ux0, ux1 = gx0 + 0.12, gx0 + 0.34
                    uy0, uy1 = gy0 + 0.10, gy0 + 0.28
                    uh = 5.0
                    b.append(f'<polygon points="{pts(Pb(ux0, uy1, h), Pb(ux1, uy1, h), Pb(ux1, uy1, h + uh), Pb(ux0, uy1, h + uh))}" fill="{th["left"](base)}"/>')
                    b.append(f'<polygon points="{pts(Pb(ux1, uy0, h), Pb(ux1, uy1, h), Pb(ux1, uy1, h + uh), Pb(ux1, uy0, h + uh))}" fill="{th["right"](base)}"/>')
                    b.append(f'<polygon points="{pts(Pb(ux0, uy0, h + uh), Pb(ux1, uy0, h + uh), Pb(ux1, uy1, h + uh), Pb(ux0, uy1, h + uh))}" fill="{th["top"](base)}" '
                             f'stroke="{th["edge"](base)}" stroke-opacity="{th["edge_op"]}" stroke-width="0.6"/>')
                # antenna and beacon on the tall towers
                if n >= 10:
                    ax_, ay_ = Pb((gx0 + gx1) / 2.0, (gy0 + gy1) / 2.0, h)
                    b.append(f'<path d="M{ax_:.1f},{ay_:.1f}v-22M{ax_ - 3:.1f},{ay_ - 8:.1f}h6M{ax_ - 2:.1f},{ay_ - 14:.1f}h4" '
                             f'stroke="{th["edge"](base)}" stroke-width="1.2" stroke-linecap="round" fill="none"/>')
                    cls = ' class="bl"' if animate else ""
                    b.append(f'<circle cx="{ax_:.1f}" cy="{ay_ - 23:.1f}" r="2.3" fill="{th["beacon"]}"{cls}/>')
                    b.append(f'<circle cx="{ax_:.1f}" cy="{ay_ - 23:.1f}" r="5" fill="{th["beacon"]}" fill-opacity=".18"{cls}/>')

                # ground shadow cast toward the lower right
                sh_shift = min(0.22 + 0.012 * n, 0.55)
                shadow = (f'<polygon points="{pts(Pb(gx1, gy0), Pb(min(gx1 + sh_shift, D - 0.02), gy0 + 0.08), Pb(min(gx1 + sh_shift, D - 0.02), gy1 + 0.1), Pb(gx1, gy1))}" '
                          f'fill="{th["shadow"]}" fill-opacity="{th["shadow_op"]}"')
                shadow += (f' class="f" style="animation-delay:{delay + 0.5:.2f}s"/>' if animate else "/>")

                # clip region: everything above the footprint's front edges
                L0, F0, R0 = Pb(gx0, gy1), Pb(gx1, gy1), Pb(gx1, gy0)
                top_y = -200
                cid = f"c{building_index}"
                clips.append(f'<clipPath id="{cid}"><polygon points="{pts(L0, F0, R0, (R0[0], top_y), (L0[0], top_y))}"/></clipPath>')
                silhouettes.append(pts(L0, F0, R0, Pb(gx1, gy0, h), Pb(gx0, gy0, h), Pb(gx0, gy1, h)))

                if animate:
                    inner = (f'<g class="b" style="animation-name:r{n};animation-delay:{delay:.2f}s">'
                             + "".join(b) + "</g>")
                    body = shadow + f'<g clip-path="url(#{cid})">{inner}</g>'
                else:
                    body = shadow + "<g>" + "".join(b) + "</g>"
                bodies.append(((ri, c), body))

    a("".join(clips))
    a('<clipPath id="sil">' + "".join(f'<polygon points="{s}"/>' for s in silhouettes) + "</clipPath>")
    a("</defs>")

    # ------------------------------------------------------------ backdrop
    a(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="url(#bg)" '
      f'stroke="{th["border"]}"/>')
    a(f'<rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gmask)" opacity=".9"/>')
    if th["star"]:
        srnd = lcg(11)
        keep_out = [b for r in rows for b in r["boxes"]] + title_lines(len(dists)) + [
            (W - 250, H - 72, W, H)]
        stars = []
        tries = 0
        want = int(46 * H / 540)
        while len(stars) < want and tries < 4000:
            tries += 1
            x, y = 20 + srnd() * (W - 40), 16 + srnd() * (H - 40)
            r = 0.5 + srnd() * 0.8
            if any(b[0] - 8 < x < b[2] + 8 and b[1] - 8 < y < b[3] + 8 for b in keep_out):
                continue
            stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}"/>')
        a(f'<g fill="{th["star"]}" fill-opacity=".45">' + "".join(stars) + "</g>")

    # ------------------------------------------------------------ city
    a('<g id="city">')
    for _, svg in sorted(bodies, key=lambda t: t[0]):
        a(svg)
    a("</g>")
    if animate:
        a('<g clip-path="url(#sil)"><g class="sw">'
          f'<polygon points="-150,{H} -90,{H} -10,0 -70,0" fill="url(#sg)"/></g></g>')

    # ------------------------------------------------------------ labels
    lab = []
    nl = []
    for row in rows:
        oy = row["oy"]
        for d in row["plan"]:
            for (repo, n), c in zip(d["repos"], d["centers"]):
                ax, ay = P(D, c, -T, oy)
                lab.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="1.9" fill="{th["count"](d)}"/>')
                lab.append(f'<path d="M{ax:.1f},{ay:.1f}l5,4.5" stroke="{th["count"](d)}" stroke-width="1"/>')
                lab.append(f'<text class="mono" x="{ax + 8:.1f}" y="{ay + 11.5:.1f}" font-size="{LABEL_PX}">'
                           f'<tspan font-weight="700" fill="{th["count"](d)}">{n}</tspan>'
                           f'<tspan fill="{th["fg"]}" dx="{CHAR * 0.7:.1f}">{esc(short(repo))}</tspan></text>')
            x, y, _, fs = phone_label(d, oy)
            nl.append(f'<text class="sans" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" '
                      f'font-weight="700" fill="{th["fg"]}">{esc(d["name"])}'
                      f'<tspan fill="{th["count"](d)}" dx="7">{d["total"]}</tspan></text>')
    a('<g class="w">' + "".join(lab) + "</g>")
    a('<g class="n">' + "".join(nl) + "</g>")

    # ------------------------------------------------------------ title block
    tx = 34
    sub = f"merged since {since_txt}" if since_txt else "merged into company repos"
    a('<g class="w">')
    a(f'<text class="sans" x="{tx}" y="46" font-size="11" font-weight="700" letter-spacing="2.2" '
      f'fill="{th["muted"]}">OPEN SOURCE SKYLINE</text>')
    a(f'<text class="sans" x="{tx - 1}" y="84" font-size="26" font-weight="800" fill="{th["fg"]}" '
      f'letter-spacing="-.5">Where my pull</text>')
    a(f'<text class="sans" x="{tx - 1}" y="114" font-size="26" font-weight="800" fill="{th["fg"]}" '
      f'letter-spacing="-.5">requests landed</text>')
    a(f'<text class="sans" x="{tx}" y="139" font-size="14" fill="{th["muted"]}">{esc(sub)}</text>')
    col_w = key_col_w()
    for i, d in enumerate(dists):
        cx = tx + (i % 2) * col_w
        cy = KEY_Y + (i // 2) * 23
        a(f'<rect x="{cx:.1f}" y="{cy - 10}" width="11" height="11" rx="2.5" fill="{d["base"]}"/>')
        a(f'<text class="sans" x="{cx + 18:.1f}" y="{cy}" font-size="13.5" fill="{th["fg"]}">{esc(d["name"])}'
          f'<tspan font-weight="700" fill="{th["count"](d)}" dx="5">{d["total"]}</tspan></text>')
    a('</g>')
    # phone layout headline
    a('<g class="n">')
    a(f'<text class="sans" x="{tx - 2}" y="90" font-size="42" font-weight="800" fill="{th["fg"]}" '
      f'letter-spacing="-1">Where my pull</text>')
    a(f'<text class="sans" x="{tx - 2}" y="140" font-size="42" font-weight="800" fill="{th["fg"]}" '
      f'letter-spacing="-1">requests landed</text>')
    if since_txt:
        a(f'<text class="sans" x="{tx}" y="178" font-size="24" fill="{th["muted"]}">since {esc(since_txt)}</text>')
    a('</g>')

    # ------------------------------------------------------------ floor key
    kx, kyy = W - 222, H - 44
    base = "#8c959f" if theme_name == "light" else "#6e7781"

    def Q(gx, gy, z=0.0, s=15.0):
        return (kx + (gx - gy) * s, kyy + (gx + gy) * s / 2.0 - z)
    g0, g1 = 0.0, 0.8
    hh = 12.0
    a('<g class="w">')
    a(f'<polygon points="{pts(Q(g0, g1), Q(g1, g1), Q(g1, g1, hh), Q(g0, g1, hh))}" fill="{mix(base, th["bg1"], 0.25)}"/>')
    a(f'<polygon points="{pts(Q(g1, g0), Q(g1, g1), Q(g1, g1, hh), Q(g1, g0, hh))}" fill="{mix(base, th["bg1"], 0.45)}"/>')
    a(f'<polygon points="{pts(Q(g0, g0, hh), Q(g1, g0, hh), Q(g1, g1, hh), Q(g0, g1, hh))}" fill="{mix(base, th["bg1"], 0.05 if theme_name == "dark" else 0.55)}"/>')
    a(f'<text class="sans" x="{kx + 22}" y="{kyy + 8}" font-size="13" fill="{th["muted"]}">'
      f'1 floor = 1 merged pull request</text>')
    a('</g>')
    a(f'<text class="sans n" x="{W - 30}" y="{H - 26}" text-anchor="end" font-size="24" fill="{th["muted"]}">'
      f'1 floor = 1 merged PR</text>')

    a("</svg>")
    return "\n".join(out)


def arg(flag, default):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


def main():
    src = arg("--in", os.path.join(HERE, "merged.json"))
    out_dir = arg("--out", os.path.join(ROOT, "assets", "skyline"))
    doc, dists = load(src)
    if not dists:
        sys.exit(f"{src}: no companies with merged pull requests; leaving the SVGs alone")
    rows = layout(dists)
    os.makedirs(out_dir, exist_ok=True)
    for name in ("light", "dark"):
        svg = build(name, rows, doc.get("since"), animate=True)
        path = os.path.join(out_dir, f"oss-skyline-{name}.svg")
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = f.read()
        if svg != old:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
        print(path, len(svg.encode()), "bytes", "(unchanged)" if svg == old else "")
        if "--static" in sys.argv:
            spath = os.path.join(out_dir, f"oss-skyline-{name}-static.svg")
            with open(spath, "w", encoding="utf-8") as f:
                f.write(build(name, rows, doc.get("since"), animate=False))
    print(f"rows {len(rows)}  K {K}  FH {FH:.1f}  W {W}  H {H}  repos "
          f"{sum(len(d['repos']) for d in dists)}  companies {len(dists)}")


if __name__ == "__main__":
    main()
