#!/usr/bin/env python3
"""Renders every panel in the profile README.

    python3 assets/build.py

One frame, one palette per product — the same rule dfklabs.com's cards follow,
where each `.<slug>-card` is described in the source as "DFK frame · <product>
DNA". The frame is constant: #0f0f0f block, a 10% white hairline, square
corners, a 2px top rule in the product's accent. Only the accent, the far end
of the gradient and the instrument at the bottom change.

Colours are not invented here. They are read off the portal's own stylesheet
(`daifukus/DFK`, index.html) and `daifukus/Studio`'s `src/site.json`:

    --accent        #2563eb   Engineering Blue, the portal's own accent
    --accent-green  #10b981   Terminal Green
    --bg-core       #050505   --block-solid #0f0f0f
    --border-line   rgba(255,255,255,.1)
    --text-main     #ffffff   --text-mute #6b7280

One deliberate departure: `--text-mute` (#6b7280) measures 3.96:1 on #0f0f0f
and fails WCAG AA, which Studio's own contrast check already caught. Body copy
here uses #8b94a2 — the value Studio moved to, two steps up the same ramp.
#6b7280 is kept for micro-labels that carry no information on their own.

Animation is SMIL, not CSS. GitHub serves these through camo and the browser
paints them as <img>, where SMIL is the half that reliably runs.

The output is committed, so the profile has no build step.
"""

from pathlib import Path

# ── The frame ────────────────────────────────────────────────────────────────

BG = "#050505"
BLOCK = "#0f0f0f"
LINE = "rgba(255,255,255,0.1)"
HAIR = "rgba(255,255,255,0.05)"
INK = "#ffffff"
BODY = "#8b94a2"
MUTE = "#6b7280"
BLUE = "#2563eb"
BLUE_LT = "#60a5fa"
GREEN = "#10b981"

MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SANS = "'Inter',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
# Fredoka is the portal's wordmark face for the three iOS apps. A webfont
# cannot load inside an SVG served through camo, so the stack degrades to the
# system sans and the identity is carried by weight and tracking instead —
# which is what the portal's own .risu-wordmark rule does anyway.
ROUND = "'Fredoka'," + SANS

CARD_W, CARD_H = 604, 424
WIDE_W, WIDE_H = 1240, 380
PAD = 26


# ── The products, as the portal names them ───────────────────────────────────

PRODUCTS = [
    dict(
        slug="risu", mark="RISU", face=ROUND, tag="SMART DOCUMENTS",
        platform="iOS", status="SOON", accent="#F59E1B", deep="#1E1408",
        blurb=["The documents that expire — passport, ID, licence,",
               "insurance. The dates are read off the photo, and the",
               "alert lands early enough that renewing is still easy."],
        chips=["OCR", "MRZ", "Alerts", "Vault"],
        url="risu.dfklabs.com", instrument="expiry",
    ),
    dict(
        slug="birdio", mark="BIRDIO", face=ROUND, tag="GOLF & MINIGOLF",
        platform="iOS", status="SOON", accent="#D9B45B", deep="#0A1B12",
        blurb=["Every round, remembered. A WHS-style index from your",
               "best 8 of the last 20 — and the one statistic that",
               "names where the strokes are actually going."],
        chips=["WHS", "Analytics", "Ladder", "On-Device"],
        url="birdio.dfklabs.com", instrument="handicap",
    ),
    dict(
        slug="mule", mark="MULE", face=ROUND, tag="STRENGTH TRAINING",
        platform="iOS · watchOS", status="SOON", accent="#4E86F0",
        deep="#071A3F",
        blurb=["Every rep, remembered. Each session scored against your",
               "own baseline, and a coach that cites the study behind",
               "every recommendation — so you can check it."],
        chips=["Sets", "Score", "Strength Index", "On-Device"],
        url="mule.dfklabs.com", instrument="sets",
    ),
    dict(
        slug="quake", mark="QUAKE", face=MONO, tag="SEISMIC MONITOR",
        platform="WEB · PWA", status="LIVE", accent="#E8A33D", deep="#1A1408",
        blurb=["Live USGS and EMSC catalogues, alerts only for the places",
               "you pick, and aftershock outlooks stated as statistics.",
               "Every card names what it rests on. Never a prediction."],
        chips=["USGS", "EMSC", "Outlook", "14 languages"],
        url="quake.dfklabs.com", instrument="seismic",
    ),
    dict(
        slug="studio", mark="STUDIO", face=MONO, tag="BROWSER TOOLS",
        platform="WEB", status="LIVE", accent="#3FE0C5", deep="#062A24",
        blurb=["Thirty-odd converters, encoders and image tools. Load one,",
               "switch the network off, and it keeps working — which is",
               "the only proof of “nothing is uploaded” worth anything."],
        chips=["30+ tools", "Offline", "Installable"],
        url="studio.dfklabs.com", instrument="tools",
    ),
    dict(
        slug="paneltir", mark="PANELTIR", face=MONO, tag="UI KIT",
        platform="REACT · TS", status="LIVE", accent="#FCEE0A", deep="#1A0711",
        blurb=["The admin-panel kit behind every DFK board. It owns",
               "structure and behaviour and never colour: each project",
               "hands it a palette, and that is the whole customisation."],
        chips=["Board", "Pointer drag", "Theming"],
        url="paneltir.dfklabs.com", instrument="board",
    ),
]

OPEN_SOURCE = dict(
    slug="vibeclaude", mark="VIBECLAUDE", face=MONO, tag="XCODE MONITOR",
    platform="OPEN SOURCE", status="PUBLIC", accent=GREEN, deep="#04140E",
    blurb=["Watch what Claude is doing inside Xcode. The only surface here",
           "you can clone, read and run for yourself."],
    chips=["Swift", "Xcode", "MIT"],
    url="github.com/daifukus/vibeclauded", instrument="ticker",
)


# ── Small parts ──────────────────────────────────────────────────────────────

def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def text(x, y, s, *, face=SANS, size=13, fill=BODY, weight=None,
         track=None, anchor=None, extra=""):
    a = [f'x="{x}"', f'y="{y}"', f'font-family="{face}"', f'font-size="{size}"',
         f'fill="{fill}"']
    if weight:
        a.append(f'font-weight="{weight}"')
    if track is not None:
        a.append(f'letter-spacing="{track}"')
    if anchor:
        a.append(f'text-anchor="{anchor}"')
    return f'<text {" ".join(a)}>{esc(s)}{extra}</text>'


def pill(x, y, label, accent, *, w=None, filled=True):
    """The portal's .<slug>-chip: 8% ground, 20% border, accent ink."""
    w = w if w else 15 + len(label) * 6.4
    bg = f'fill="{rgba(accent, 0.08)}"' if filled else 'fill="none"'
    return (
        f'<g><rect x="{x}" y="{y}" width="{w:.0f}" height="20" rx="10" {bg} '
        f'stroke="{rgba(accent, 0.2)}"/>'
        + text(x + w / 2, y + 13.5, label, face=SANS, size=10, fill=accent,
               anchor="middle")
        + "</g>"
    ), w


def tag_box(x, y, label, accent):
    """The portal's .<slug>-tag: square, accent ink, 25% border."""
    w = 16 + len(label) * 6.3
    return (
        f'<g><rect x="{x}" y="{y}" width="{w:.0f}" height="20" fill="none" '
        f'stroke="{rgba(accent, 0.25)}"/>'
        + text(x + w / 2, y + 13.5, label, face=MONO, size=9.5, fill=accent,
               anchor="middle", track=0.6)
        + "</g>"
    ), w


def status(x, y, label, accent, *, delay=1.2):
    """Status dot + word, the pulse the portal puts on every card."""
    return (
        f'<g>'
        f'<circle cx="{x}" cy="{y}" r="3.5" fill="{accent}">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="2.2s" '
        f'begin="{delay}s" repeatCount="indefinite"/></circle>'
        f'<circle cx="{x}" cy="{y}" r="3.5" fill="none" stroke="{accent}" '
        f'stroke-width="1.2"><animate attributeName="r" values="3.5;11" '
        f'dur="2.2s" begin="{delay}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.6;0" dur="2.2s" '
        f'begin="{delay}s" repeatCount="indefinite"/></circle>'
        + text(x + 11, y + 4, label, face=MONO, size=10, fill=accent, track=1.4)
        + "</g>"
    )


def dashline(x, y, w, color=LINE):
    return (f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{color}" '
            f'stroke-width="1"/>')


def draw(d, color, *, width=1.6, dash=None, dur="1.4s", begin="0.5s",
         fill="none", opacity=1, cap="round"):
    """A path that draws itself once, then stays."""
    if dash is None:
        return (f'<path d="{d}" fill="{fill}" stroke="{color}" '
                f'stroke-width="{width}" stroke-linecap="{cap}" '
                f'opacity="{opacity}"/>')
    return (
        f'<path d="{d}" fill="{fill}" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="{cap}" stroke-linejoin="round" opacity="{opacity}" '
        f'stroke-dasharray="{dash}" stroke-dashoffset="{dash}">'
        f'<animate attributeName="stroke-dashoffset" values="{dash};0" '
        f'dur="{dur}" begin="{begin}" fill="freeze" calcMode="spline" '
        f'keyTimes="0;1" keySplines="0.16 1 0.3 1"/></path>'
    )


# ── The instruments ──────────────────────────────────────────────────────────
# One per product, drawn from that product's own subject matter. Each gets the
# strip between y and y+86, inset by PAD.

def inst_expiry(x, y, w, a):
    """Risu: a document, its expiry ring closing, the date read off it."""
    out = [f'<rect x="{x}" y="{y}" width="66" height="84" rx="3" '
           f'fill="{rgba(a, 0.07)}" stroke="{rgba(a, 0.22)}"/>']
    for i, ln in enumerate((30, 44, 22, 38)):
        out.append(f'<rect x="{x + 10}" y="{y + 16 + i * 12}" width="{ln}" '
                   f'height="3" rx="1.5" fill="{rgba(a, 0.35)}">'
                   f'<animate attributeName="width" values="0;{ln}" dur="0.5s" '
                   f'begin="{0.8 + i * 0.16:.2f}s" fill="freeze"/></rect>')
    cx, cy, r = x + 132, y + 42, 30
    circ = 2 * 3.14159 * r
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
               f'stroke="{rgba(a, 0.14)}" stroke-width="5"/>')
    out.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{a}" '
        f'stroke-width="5" stroke-linecap="round" stroke-dasharray="{circ:.0f}" '
        f'stroke-dashoffset="{circ:.0f}" transform="rotate(-90 {cx} {cy})">'
        f'<animate attributeName="stroke-dashoffset" '
        f'values="{circ:.0f};{circ * 0.22:.0f}" dur="1.6s" begin="1.1s" '
        f'fill="freeze" calcMode="spline" keyTimes="0;1" '
        f'keySplines="0.16 1 0.3 1"/></circle>')
    out.append(text(cx, cy + 4, "78d", face=MONO, size=15, fill=a,
                    weight="700", anchor="middle"))
    lx = x + 186
    out.append(text(lx, y + 26, "EXPIRES", face=MONO, size=9, fill=MUTE,
                    track=1.6))
    out.append(text(lx, y + 46, "2027-01-14", face=MONO, size=15, fill=INK,
                    weight="700"))
    out.append(text(lx, y + 68, "read from the photo", face=SANS, size=11,
                    fill=MUTE))
    return "".join(out)


def inst_handicap(x, y, w, a):
    """Birdio: the index falling, and the ladder it climbs as it does."""
    pts = [(0, 12), (46, 26), (92, 20), (138, 40), (184, 34),
           (230, 52), (276, 47), (322, 64), (368, 72)]
    d = "M " + " L ".join(f"{x + px} {y + py}" for px, py in pts)
    out = [f'<rect x="{x}" y="{y + 4}" width="374" height="74" fill="none" '
           f'stroke="{HAIR}"/>']
    for gy in (22, 44, 66):
        out.append(dashline(x, y + gy, 374, HAIR))
    out.append(draw(d, a, width=2, dash=560, dur="2s", begin="0.7s"))
    last = pts[-1]
    out.append(f'<circle cx="{x + last[0]}" cy="{y + last[1]}" r="4" '
               f'fill="{a}" opacity="0"><animate attributeName="opacity" '
               f'values="0;1" dur="0.3s" begin="2.5s" fill="freeze"/></circle>')
    out.append(text(x, y - 2, "INDEX 24.1 → 11.6", face=MONO, size=9,
                    fill=MUTE, track=1.4))
    lx = x + 396
    for i, (name, on) in enumerate((("CONDOR", 0), ("EAGLE", 1),
                                    ("OWL", 0), ("FLAMINGO", 0))):
        c = a if on else rgba(a, 0.28)
        out.append(f'<rect x="{lx}" y="{y + 6 + i * 19}" width="7" height="7" '
                   f'fill="{c}"/>')
        out.append(text(lx + 15, y + 13 + i * 19, name, face=MONO, size=9,
                        fill=INK if on else MUTE, track=1.2))
    return "".join(out)


def inst_sets(x, y, w, a):
    """Mule: the session, bar by bar, against the baseline it is scored on."""
    out = []
    bars = [30, 44, 38, 56, 62, 50, 71, 66, 78, 58, 84, 74]
    base = 52
    out.append(f'<line x1="{x}" y1="{y + 84 - base}" x2="{x + 300}" '
               f'y2="{y + 84 - base}" stroke="{rgba(a, 0.45)}" '
               f'stroke-dasharray="3 3"/>')
    out.append(text(x + 306, y + 88 - base, "BASELINE", face=MONO, size=8.5,
                    fill=MUTE, track=1.2))
    for i, h in enumerate(bars):
        bx = x + i * 25
        col = a if h >= base else rgba(a, 0.4)
        out.append(f'<rect x="{bx}" y="{y + 84}" width="14" height="0" '
                   f'fill="{col}"><animate attributeName="height" '
                   f'values="0;{h}" dur="0.5s" begin="{0.6 + i * 0.07:.2f}s" '
                   f'fill="freeze" calcMode="spline" keyTimes="0;1" '
                   f'keySplines="0.16 1 0.3 1"/>'
                   f'<animate attributeName="y" values="{y + 84};{y + 84 - h}" '
                   f'dur="0.5s" begin="{0.6 + i * 0.07:.2f}s" fill="freeze" '
                   f'calcMode="spline" keyTimes="0;1" '
                   f'keySplines="0.16 1 0.3 1"/></rect>')
    lx = x + 396
    out.append(text(lx, y + 18, "SESSION", face=MONO, size=9, fill=MUTE,
                    track=1.6))
    out.append(text(lx, y + 46, "+14%", face=MONO, size=24, fill=a,
                    weight="700"))
    out.append(text(lx, y + 68, "above your normal", face=SANS, size=11,
                    fill=MUTE))
    return "".join(out)


def inst_seismic(x, y, w, a):
    """Quake: the trace, running, with the events it is made of."""
    import math
    pts = []
    events = {58: 1.0, 150: 0.55, 268: 0.85, 392: 0.4, 470: 0.7}
    for px in range(0, 520, 2):
        v = math.sin(px * 0.28) * 1.6 + math.sin(px * 0.11) * 1.2
        for ex, amp in events.items():
            dx = px - ex
            v += math.sin(dx * 0.75) * 30 * amp * math.exp(-(dx * dx) / 240.0)
        pts.append((px, max(-38, min(38, v))))
    d = "M " + " L ".join(f"{x + px} {y + 42 - pv:.1f}" for px, pv in pts)
    out = [f'<rect x="{x}" y="{y}" width="520" height="84" fill="none" '
           f'stroke="{HAIR}"/>',
           dashline(x, y + 42, 520, rgba(a, 0.16))]
    out.append(draw(d, a, width=1.5, dash=1400, dur="2.6s", begin="0.5s"))
    for ex, amp in events.items():
        r = 3 + amp * 3
        out.append(
            f'<circle cx="{x + ex}" cy="{y + 42}" r="{r:.1f}" fill="none" '
            f'stroke="{a}" stroke-width="1.2" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.55;0" dur="2.4s" '
            f'begin="{2.6 + ex / 520 * 1.4:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="r" values="{r:.1f};{r * 2.4:.1f}" '
            f'dur="2.4s" begin="{2.6 + ex / 520 * 1.4:.2f}s" '
            f'repeatCount="indefinite"/></circle>')
    out.append(text(x + 4, y - 2, "M 2.5+ · LAST 24 H · USGS ⊕ EMSC",
                    face=MONO, size=9, fill=MUTE, track=1.4))
    out.append(text(x + 516, y - 2, "b = 0.98", face=MONO, size=9, fill=a,
                    track=1.2, anchor="end"))
    return "".join(out)


def inst_tools(x, y, w, a):
    """Studio: the tool grid, lighting one at a time — each its own install."""
    out = []
    cols, rows, cell, gap = 8, 3, 30, 6
    n = 0
    for r in range(rows):
        for c in range(cols):
            gx, gy = x + c * (cell + gap), y + 6 + r * (cell - 4 + gap)
            out.append(
                f'<rect x="{gx}" y="{gy}" width="{cell}" height="{cell - 4}" '
                f'fill="{rgba(a, 0.06)}" stroke="{rgba(a, 0.18)}">'
                f'<animate attributeName="fill" '
                f'values="{rgba(a, 0.06)};{rgba(a, 0.06)};{rgba(a, 0.34)};'
                f'{rgba(a, 0.06)}" keyTimes="0;0.86;0.92;1" dur="7s" '
                f'begin="{0.9 + n * 0.11:.2f}s" repeatCount="indefinite"/>'
                f'</rect>')
            n += 1
    lx = x + cols * (cell + gap) + 14
    out.append(text(lx, y + 20, "OFFLINE", face=MONO, size=9, fill=MUTE,
                    track=1.6))
    out.append(text(lx, y + 46, "31", face=MONO, size=26, fill=a, weight="700"))
    out.append(text(lx, y + 68, "installable tools", face=SANS, size=11,
                    fill=MUTE))
    return "".join(out)


def inst_board(x, y, w, a):
    """Paneltir: a card crossing columns — the drag the kit exists for."""
    out = []
    names = ("IDEAS", "NEXT", "DOING", "DONE")
    for i, name in enumerate(names):
        cx = x + i * 96
        out.append(f'<rect x="{cx}" y="{y + 12}" width="84" height="72" '
                   f'fill="{rgba(a, 0.04)}" stroke="{rgba(a, 0.16)}"/>')
        out.append(text(cx + 4, y + 6, name, face=MONO, size=8.5, fill=MUTE,
                        track=1.4))
        for j in range(2 if i != 2 else 1):
            out.append(f'<rect x="{cx + 8}" y="{y + 22 + j * 20}" width="68" '
                       f'height="13" fill="{rgba(a, 0.13)}"/>')
    # the travelling card
    out.append(
        f'<g><rect x="{x + 8}" y="{y + 22}" width="68" height="13" '
        f'fill="{a}" opacity="0.9">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0,0; 96,20; 192,0; 288,20; 0,0" keyTimes="0;0.25;0.5;0.75;1" '
        f'dur="9s" begin="1.4s" repeatCount="indefinite" calcMode="spline" '
        f'keySplines="0.5 0 0.2 1;0.5 0 0.2 1;0.5 0 0.2 1;0.5 0 0.2 1"/>'
        f'</rect></g>')
    lx = x + 4 * 96 + 14
    out.append(text(lx, y + 26, "POINTER EVENTS", face=MONO, size=9, fill=MUTE,
                    track=1.4))
    out.append(text(lx, y + 48, "drag that works", face=SANS, size=12.5,
                    fill=INK))
    out.append(text(lx, y + 66, "on iOS touch", face=SANS, size=12.5,
                    fill=MUTE))
    return "".join(out)


def inst_ticker(x, y, w, a):
    """VibeClaude: the monitor line, scrolling what Xcode is being told."""
    rows = [("14:02:11", "build", "succeeded · 0 warnings"),
            ("14:02:44", "edit", "ContentView.swift +18 −11"),
            ("14:03:09", "test", "42 passed"),
            ("14:03:31", "wait", "your call")]
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="86" '
           f'fill="{rgba(a, 0.04)}" stroke="{rgba(a, 0.14)}"/>']
    for i, (t, kind, msg) in enumerate(rows):
        ry = y + 20 + i * 18
        out.append(f'<g opacity="0"><animate attributeName="opacity" '
                   f'values="0;1" dur="0.4s" begin="{0.7 + i * 0.35:.2f}s" '
                   f'fill="freeze"/>'
                   + text(x + 14, ry, t, face=MONO, size=10, fill=MUTE)
                   + text(x + 76, ry, kind, face=MONO, size=10, fill=a,
                          track=0.8)
                   + text(x + 132, ry, msg, face=MONO, size=10, fill=BODY)
                   + "</g>")
    return "".join(out)


INSTRUMENTS = {
    "expiry": inst_expiry, "handicap": inst_handicap, "sets": inst_sets,
    "seismic": inst_seismic, "tools": inst_tools, "board": inst_board,
    "ticker": inst_ticker,
}


# ── The card ─────────────────────────────────────────────────────────────────

def card(p, *, wide=False):
    w, h = (WIDE_W, WIDE_H) if wide else (CARD_W, CARD_H)
    a, slug = p["accent"], p["slug"]
    o = []

    o.append(f'<rect width="{w}" height="{h}" fill="url(#g-{slug})"/>')
    # the 2px top rule the portal reveals on hover, drawn on instead
    o.append(f'<rect x="0" y="0" width="0" height="2" fill="url(#r-{slug})">'
             f'<animate attributeName="width" values="0;{w}" dur="1.1s" '
             f'begin="0.2s" fill="freeze" calcMode="spline" keyTimes="0;1" '
             f'keySplines="0.16 1 0.3 1"/></rect>')

    tag, tw = tag_box(PAD, 40, p["tag"], a)
    o.append(tag)
    o.append(text(PAD + tw + 12, 53.5, p["platform"], face=MONO, size=9.5,
                  fill=MUTE, track=1.2))
    o.append(status(w - PAD - 58, 50, p["status"], a))

    o.append(text(PAD, 112, p["mark"], face=p["face"], size=27, fill=INK,
                  weight="700", track=6))
    o.append(f'<rect x="{PAD + 2}" y="124" width="0" height="3" rx="1.5" '
             f'fill="{a}"><animate attributeName="width" values="0;26" '
             f'dur="0.5s" begin="0.9s" fill="freeze"/></rect>')

    for i, ln in enumerate(p["blurb"]):
        o.append(text(PAD, 158 + i * 19, ln, face=SANS, size=12.5, fill=BODY))

    cy = 158 + len(p["blurb"]) * 19 + 12
    cx = PAD
    for label in p["chips"]:
        ch, cw = pill(cx, cy, label, a)
        o.append(ch)
        cx += cw + 7

    iy = cy + 42
    o.append(INSTRUMENTS[p["instrument"]](PAD, iy, w - PAD * 2, a))

    o.append(dashline(PAD, h - 40, w - PAD * 2))
    o.append(text(PAD, h - 20, p["url"], face=MONO, size=10.5, fill=a,
                  track=0.4))
    o.append(text(w - PAD, h - 20, "DFK LABS", face=MONO, size=9.5, fill=MUTE,
                  track=2, anchor="end"))

    o.append(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" '
             f'fill="none" stroke="{LINE}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img"
     aria-label="{esc(p['mark'] + ' — ' + p['tag'] + ', ' + p['platform'] + ', ' + p['status'] + '. ' + ' '.join(p['blurb']) + ' ' + p['url'])}">
  <title>{esc(p['mark'] + ' — ' + p['tag'])}</title>
  <defs>
    <linearGradient id="g-{slug}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="35%" stop-color="{BLOCK}"/>
      <stop offset="100%" stop-color="{p['deep']}"/>
    </linearGradient>
    <linearGradient id="r-{slug}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{a}"/>
      <stop offset="100%" stop-color="{a}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  {''.join(o)}
</svg>
"""


# ── The header ───────────────────────────────────────────────────────────────

def header():
    w, h = 1240, 400
    o = []
    o.append(f'<rect width="{w}" height="{h}" fill="{BG}"/>')

    # the portal's particle grid, as a field that settles rather than a canvas
    import math
    for i in range(120):
        px = (i * 137) % w
        py = 56 + ((i * 89) % (h - 110))
        r = 1 + (i % 3) * 0.5
        dur = 3 + (i % 7) * 0.6
        op = 0.05 + (i % 5) * 0.035
        o.append(
            f'<circle cx="{px}" cy="{py}" r="{r}" fill="{BLUE_LT}" '
            f'opacity="0"><animate attributeName="opacity" '
            f'values="0;{op:.3f};{op * 0.3:.3f};{op:.3f}" dur="{dur:.1f}s" '
            f'begin="{(i % 11) * 0.19:.2f}s" repeatCount="indefinite"/>'
            f'</circle>')
    for i in range(9):
        x1 = (i * 211) % w
        o.append(f'<line x1="{x1}" y1="56" x2="{(x1 + 180) % w}" y2="{h - 40}" '
                 f'stroke="{BLUE}" stroke-opacity="0.05"/>')

    # nav
    o.append(f'<rect width="{w}" height="56" fill="{rgba("#050505", 0.9)}"/>')
    o.append(dashline(0, 56, w, HAIR))
    o.append(text(32, 36, "DFK", face=MONO, size=18, fill=INK, weight="700",
                  track=1))
    o.append(text(80, 35, "iOS ENGINEERING UNIT", face=MONO, size=9.5,
                  fill=MUTE, track=2.6))
    for i, item in enumerate(("iOS", "WEB", "TOOLS", "PROJECTS")):
        o.append(text(w - 470 + i * 62, 35, item, face=MONO, size=9.5,
                      fill=MUTE, track=1.6, anchor="middle"))
    o.append(f'<g><text x="{w - 32}" y="35" font-family="{MONO}" '
             f'font-size="9.5" fill="{BLUE_LT}" letter-spacing="1.6" '
             f'text-anchor="end">SYSTEM: ACTIVE'
             f'<animate attributeName="opacity" values="1;0.45;1" dur="2.4s" '
             f'repeatCount="indefinite"/></text></g>')

    # eyebrow
    ex, ew = w / 2 - 84, 168
    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
             f'dur="0.6s" begin="0.3s" fill="freeze"/>'
             f'<rect x="{ex}" y="112" width="{ew}" height="28" '
             f'fill="{rgba("#ffffff", 0.05)}" stroke="{LINE}"/>'
             + text(w / 2, 130, "/// AI-DRIVEN FLOW", face=MONO, size=11,
                    fill=BLUE_LT, anchor="middle", track=1.4)
             + "</g>")

    # the headline, two lines, revealed by a wipe like the portal's reveal
    for i, line in enumerate(("NATIVE", "INTELLIGENCE.")):
        o.append(
            f'<g clip-path="url(#wipe{i})">'
            + text(w / 2, 216 + i * 68, line, face=SANS, size=72, fill=INK,
                   weight="900", track=-3, anchor="middle")
            + "</g>")

    o.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
             f'dur="0.8s" begin="1.5s" fill="freeze"/>'
             + text(w / 2, 322, "We build iOS apps and tools that replace "
                    "friction with flow.", face=SANS, size=17, fill=MUTE,
                    anchor="middle")
             + "</g>")

    o.append(dashline(0, h - 44, w, HAIR))
    o.append(text(32, h - 18, "SEVEN SURFACES · ONE FRAME",
                  face=MONO, size=9.5, fill=MUTE, track=2))
    o.append(text(w - 32, h - 18, "ENGINEERED IN SILENCE.", face=MONO,
                  size=9.5, fill=MUTE, track=2, anchor="end"))

    clips = "".join(
        f'<clipPath id="wipe{i}"><rect x="0" y="{160 + i * 68}" width="0" '
        f'height="76"><animate attributeName="width" values="0;{w}" '
        f'dur="1s" begin="{0.5 + i * 0.22:.2f}s" fill="freeze" '
        f'calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/>'
        f'</rect></clipPath>' for i in range(2))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img"
     aria-label="DFK Labs, iOS Engineering Unit. Native Intelligence. We build iOS apps and tools that replace friction with flow.">
  <title>DFK Labs — Native Intelligence</title>
  <defs>{clips}</defs>
  {''.join(o)}
</svg>
"""


# ── The closing strip ────────────────────────────────────────────────────────

def footer():
    w, h = 1240, 112
    o = [f'<rect width="{w}" height="{h}" fill="{BG}"/>',
         dashline(0, 0, w, LINE)]
    marks = [(p["mark"], p["accent"]) for p in PRODUCTS]
    marks.append((OPEN_SOURCE["mark"], OPEN_SOURCE["accent"]))
    x = 32
    for i, (name, a) in enumerate(marks):
        o.append(f'<rect x="{x}" y="38" width="58" height="3" fill="{a}" '
                 f'opacity="0.22"><animate attributeName="opacity" '
                 f'values="0.22;0.22;1;0.22" keyTimes="0;0.1;0.18;1" '
                 f'dur="6.3s" begin="{i * 0.4:.2f}s" '
                 f'repeatCount="indefinite"/></rect>')
        o.append(text(x, 62, name, face=MONO, size=8.5, fill=MUTE, track=1.2))
        x += 72
    o.append(text(w - 32, 44, "ENGINEERED IN SILENCE.", face=MONO, size=11,
                  fill=INK, track=2.4, anchor="end"))
    o.append(text(w - 32, 62, "© 2026 DFK Labs", face=MONO, size=9.5,
                  fill=MUTE, track=1.2, anchor="end"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img"
     aria-label="Engineered in Silence. © 2026 DFK Labs.">
  <title>Engineered in Silence</title>
  {''.join(o)}
</svg>
"""


def main():
    here = Path(__file__).resolve().parent
    written = []

    def put(name, body):
        p = here / name
        p.write_text(body, encoding="utf-8")
        written.append((name, p.stat().st_size))

    put("header.svg", header())
    for prod in PRODUCTS:
        put(f"card-{prod['slug']}.svg", card(prod))
    put("card-vibeclaude.svg", card(OPEN_SOURCE, wide=True))
    put("footer.svg", footer())

    for name, size in written:
        print(f"  assets/{name:<24} {size:>7,} bytes")
    print(f"{len(written)} files, {sum(s for _, s in written):,} bytes total")


if __name__ == "__main__":
    main()
