#!/usr/bin/env python3
"""Renders every panel in the profile README.

    python3 assets/build.py            # from the committed snapshot
    python3 assets/build.py --live     # refresh Quake from the USGS feed first

One frame, one palette per product — the rule dfklabs.com's own cards follow,
where each `.<slug>-card` is commented "DFK frame · <product> DNA". The frame
is constant: #0f0f0f block, a 10% white hairline, square corners, a 2px top
rule in the product's accent. Only the mark, the accent, the far end of the
gradient and the instrument change.

Nothing here is invented. Colours, marks and wording are read off the portal's
own source (`daifukus/DFK`, index.html) and `daifukus/Studio`'s src/site.json:

    --accent        #2563eb   Engineering Blue, the portal's accent
    --accent-green  #10b981   Terminal Green
    --bg-core       #050505   --block-solid #0f0f0f
    --border-line   rgba(255,255,255,.1)
    --text-main     #ffffff   --text-mute #6b7280

    .dfk-logo       2px white border, 800 weight, -1px tracking,
                    3px 3px hard shadow in --accent
    Risu, Birdio    the app icons, lifted from the portal as assets/logo-*.jpg
    Quake, Studio   the portal's own path glyphs, vector
    Mule            "M" over linear-gradient(140deg,#4E86F0,#1247B8)
    VibeClaude      the GitHub mark, as the portal's tool card shows it

Paneltir is the one mark drawn here rather than copied: it is not on the
portal, so its glyph is a board, in its own Night City yellow.

One deliberate departure: `--text-mute` (#6b7280) measures 3.96:1 on #0f0f0f
and fails AA — Studio's own contrast check already caught it — so body copy
uses #8b94a2, the value Studio moved to. #6b7280 stays on micro-labels that
carry no information alone.

Animation is CSS, not SMIL. SMIL cannot be switched off by a viewer who asks
for less motion; a CSS keyframe can, and the reduced-motion block at the top
of every file resolves each panel to its finished frame. Transforms and
opacity only, so the compositor does the work.

The output is committed, so the profile has no build step.
"""

import argparse
import base64
import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

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
# system sans and weight plus tracking carry the identity instead — which is
# what .risu-wordmark leans on anyway.
ROUND = "'Fredoka'," + SANS

CARD_W, CARD_H = 604, 436
WIDE_W, WIDE_H = 1240, 392
PAD = 26

GITHUB_MARK = (
    "M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111"
    ".793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387"
    "-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839"
    " 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305"
    ".762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236"
    "-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957"
    "-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552"
    " 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911"
    " 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222"
    "v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0"
    "-6.627-5.373-12-12-12z"
)


# ── The products, as the portal names them ───────────────────────────────────

PRODUCTS = [
    dict(
        slug="risu", mark="RISU", face=ROUND, tag="SMART DOCUMENTS",
        platform="iOS", state="SOON", accent="#F59E1B", deep="#1E1408",
        logo=("raster", "logo-risu.jpg"),
        blurb=["The documents that expire — passport, ID, licence,",
               "insurance. The dates are read off the photo, and the",
               "alert lands early enough that renewing is still easy."],
        chips=["OCR", "MRZ", "Alerts", "Vault"],
        url="risu.dfklabs.com", instrument="expiry",
    ),
    dict(
        slug="birdio", mark="BIRDIO", face=ROUND, tag="GOLF & MINIGOLF",
        platform="iOS", state="SOON", accent="#D9B45B", deep="#0A1B12",
        logo=("raster", "logo-birdio.jpg"),
        blurb=["Every round, remembered. A WHS-style index from your",
               "best 8 of the last 20 — and the one statistic that",
               "names where the strokes are actually going."],
        chips=["WHS", "Analytics", "Ladder", "On-Device"],
        url="birdio.dfklabs.com", instrument="handicap",
    ),
    dict(
        slug="mule", mark="MULE", face=ROUND, tag="STRENGTH TRAINING",
        platform="iOS · watchOS", state="SOON", accent="#4E86F0",
        deep="#071A3F",
        logo=("letter", "M", "#4E86F0", "#1247B8"),
        blurb=["Every rep, remembered. Each session scored against your",
               "own baseline, and a coach that cites the study behind",
               "every recommendation — so you can check it."],
        chips=["Sets", "Score", "Strength Index", "On-Device"],
        url="mule.dfklabs.com", instrument="sets",
    ),
    dict(
        slug="quake", mark="QUAKE", face=MONO, tag="SEISMIC MONITOR",
        platform="WEB · PWA", state="LIVE", accent="#E8A33D", deep="#1A1408",
        # the portal's own glyph: a trace, on the amber tile
        logo=("glyph", "M12 50h16l8-30 14 56 12-34 8 8h18", "#1A1408", 11),
        blurb=["Live USGS and EMSC catalogues, alerts only for the places",
               "you pick, and aftershock outlooks stated as statistics.",
               "Every card names what it rests on. Never a prediction."],
        chips=["USGS", "EMSC", "Outlook", "14 languages"],
        url="quake.dfklabs.com", instrument="seismic",
    ),
    dict(
        slug="studio", mark="STUDIO", face=MONO, tag="BROWSER TOOLS",
        platform="WEB", state="LIVE", accent="#3FE0C5", deep="#062A24",
        logo=("glyph", "M30 34h40M30 50h40M30 66h24", "#062A24", 11),
        blurb=["Thirty-odd converters, encoders and image tools. Load one,",
               "switch the network off, and it keeps working — which is",
               "the only proof of “nothing is uploaded” worth anything."],
        chips=["30+ tools", "Offline", "Installable"],
        url="studio.dfklabs.com", instrument="tools",
    ),
    dict(
        slug="paneltir", mark="PANELTIR", face=MONO, tag="UI KIT",
        platform="REACT · TS", state="LIVE", accent="#FCEE0A", deep="#1A0711",
        logo=("glyph", "M26 28v44M50 28v30M74 28v38", "#1A0711", 11),
        blurb=["The admin-panel kit behind every DFK board. It owns",
               "structure and behaviour and never colour: each project",
               "hands it a palette, and that is the whole customisation."],
        chips=["Board", "Pointer drag", "Theming"],
        url="paneltir.dfklabs.com", instrument="board",
    ),
]

OPEN_SOURCE = dict(
    slug="vibeclaude", mark="VIBECLAUDE", face=MONO, tag="CLI TOOL",
    platform="macOS", state="PUBLIC", accent=GREEN, deep="#04140E",
    logo=("github",),
    blurb=["Watch what Claude is doing inside Xcode. The only surface here",
           "you can clone, read and run for yourself."],
    chips=["Swift", "Xcode", "MIT"],
    url="github.com/daifukus/vibeclauded", instrument="ticker",
)


# ── Small parts ──────────────────────────────────────────────────────────────

def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g_, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g_},{b},{alpha})"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def text(x, y, s, *, face=SANS, size=13, fill=BODY, weight=None, track=None,
         anchor=None, cls=None, delay=None):
    a = [f'x="{x}"', f'y="{y}"', f'font-family="{face}"', f'font-size="{size}"',
         f'fill="{fill}"']
    if weight:
        a.append(f'font-weight="{weight}"')
    if track is not None:
        a.append(f'letter-spacing="{track}"')
    if anchor:
        a.append(f'text-anchor="{anchor}"')
    if cls:
        a.append(f'class="{cls}"')
    if delay is not None:
        a.append(f'style="animation-delay:{delay}s"')
    return f'<text {" ".join(a)}>{esc(s)}</text>'


def grp(body, *, cls=None, delay=None):
    a = []
    if cls:
        a.append(f'class="{cls}"')
    if delay is not None:
        a.append(f'style="animation-delay:{delay}s"')
    return f'<g {" ".join(a)}>{body}</g>'


# ── The animation layer ──────────────────────────────────────────────────────
# Transforms and opacity only. Every keyframe ends on the finished frame, so
# the reduced-motion block can switch the animations off and leave the panel
# readable — which is also what a still thumbnail gets.

BASE_CSS = """
  .rise,.pop,.wipe,.grow,.draw{animation-fill-mode:both}
  .rise{opacity:0;animation:rise .62s cubic-bezier(.16,1,.3,1) forwards}
  .pop{opacity:0;transform-box:fill-box;transform-origin:center;
       animation:pop .5s cubic-bezier(.34,1.56,.64,1) forwards}
  .wipe{transform-box:fill-box;transform-origin:left center;
        animation:wipe .9s cubic-bezier(.16,1,.3,1) forwards}
  .grow{transform-box:fill-box;transform-origin:bottom center;
        animation:grow .55s cubic-bezier(.16,1,.3,1) forwards}
  .draw{animation:draw 1.8s cubic-bezier(.16,1,.3,1) forwards}
  .beat{transform-box:fill-box;transform-origin:center;
        animation:beat 2.4s ease-in-out infinite}
  .halo{transform-box:fill-box;transform-origin:center;
        animation:halo 2.4s ease-out infinite}
  .sheen{animation:sheen 9s cubic-bezier(.5,0,.2,1) 1.6s infinite}
  @keyframes rise{from{opacity:0;transform:translateY(9px)}
                  to{opacity:1;transform:none}}
  @keyframes pop{0%{opacity:0;transform:scale(.82)}
                 62%{opacity:1;transform:scale(1.05)}
                 100%{opacity:1;transform:scale(1)}}
  @keyframes wipe{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
  @keyframes draw{to{stroke-dashoffset:0}}
  @keyframes beat{0%,100%{opacity:1}50%{opacity:.28}}
  @keyframes halo{0%{transform:scale(1);opacity:.55}
                  70%,100%{transform:scale(2.7);opacity:0}}
  @keyframes sheen{0%{transform:translateX(-38%)}
                   34%,100%{transform:translateX(150%)}}
  @media (prefers-reduced-motion:reduce){
    *{animation:none!important;opacity:1!important;transform:none!important;
      stroke-dashoffset:0!important}
  }
"""


def stylesheet(extra=""):
    return f"<style>{BASE_CSS}{extra}</style>"


# ── The marks ────────────────────────────────────────────────────────────────

def logo(spec, x, y, size, accent, *, delay=0.3):
    """The product's own mark, on its own tile, at the portal's proportions."""
    kind = spec[0]
    tile = f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="9" '

    if kind == "raster":
        data = base64.b64encode((HERE / spec[1]).read_bytes()).decode()
        cid = "clip-" + spec[1].replace(".", "-")
        return grp(
            f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{size}" '
            f'height="{size}" rx="9"/></clipPath>'
            f'<image x="{x}" y="{y}" width="{size}" height="{size}" '
            f'clip-path="url(#{cid})" preserveAspectRatio="xMidYMid slice" '
            f'href="data:image/jpeg;base64,{data}"/>'
            + tile + f'fill="none" stroke="{rgba("#ffffff", 0.14)}"/>',
            cls="pop", delay=delay)

    if kind == "letter":
        _, ch, c1, c2 = spec
        gid = f"lg-{ch.lower()}"
        return grp(
            f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0.75" y2="1">'
            f'<stop offset="0%" stop-color="{c1}"/>'
            f'<stop offset="100%" stop-color="{c2}"/></linearGradient></defs>'
            + tile + f'fill="url(#{gid})"/>'
            + text(x + size / 2, y + size * 0.71, ch, face=ROUND,
                   size=size * 0.52, fill="#ffffff", weight="600",
                   anchor="middle"),
            cls="pop", delay=delay)

    if kind == "glyph":
        _, d, ink, sw = spec
        s = size / 100
        return grp(
            tile + f'fill="{accent}"/>'
            + f'<g transform="translate({x + size * 0.18},{y + size * 0.18}) '
              f'scale({s * 0.64})"><path d="{d}" fill="none" stroke="{ink}" '
              f'stroke-width="{sw}" stroke-linecap="round" '
              f'stroke-linejoin="round"/></g>',
            cls="pop", delay=delay)

    # the GitHub mark, as the portal's tool card shows it
    s = size / 24
    return grp(
        tile + f'fill="{rgba(accent, 0.12)}" stroke="{rgba(accent, 0.3)}"/>'
        + f'<g transform="translate({x + size * 0.2},{y + size * 0.2}) '
          f'scale({s * 0.6})"><path d="{GITHUB_MARK}" fill="{accent}"/></g>',
        cls="pop", delay=delay)


def dfk_mark(x, y, scale=1.0):
    """.dfk-logo: 2px white border, 800 weight, a 3px hard shadow in --accent."""
    w, h = 54 * scale, 30 * scale
    return grp(
        f'<rect x="{x + 3 * scale}" y="{y + 3 * scale}" width="{w}" '
        f'height="{h}" fill="{BLUE}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}" '
        f'stroke="{INK}" stroke-width="{2 * scale}"/>'
        + text(x + w / 2, y + h * 0.72, "DFK", face=MONO, size=17 * scale,
               fill=INK, weight="800", track=-1, anchor="middle"),
        cls="rise", delay=0.1)


# ── Card furniture ───────────────────────────────────────────────────────────

def pill(x, y, label, accent, delay):
    w = 15 + len(label) * 6.4
    return grp(
        f'<rect x="{x}" y="{y}" width="{w:.0f}" height="20" rx="10" '
        f'fill="{rgba(accent, 0.08)}" stroke="{rgba(accent, 0.2)}"/>'
        + text(x + w / 2, y + 13.5, label, face=SANS, size=10, fill=accent,
               anchor="middle"),
        cls="pop", delay=delay), w


def tag_box(x, y, label, accent, delay):
    w = 16 + len(label) * 6.3
    return grp(
        f'<rect x="{x}" y="{y}" width="{w:.0f}" height="20" fill="none" '
        f'stroke="{rgba(accent, 0.25)}"/>'
        + text(x + w / 2, y + 13.5, label, face=MONO, size=9.5, fill=accent,
               anchor="middle", track=0.6),
        cls="rise", delay=delay), w


def state_dot(x, y, label, accent, delay):
    return grp(
        f'<circle cx="{x}" cy="{y}" r="3.5" fill="{accent}" class="beat"/>'
        f'<circle cx="{x}" cy="{y}" r="3.5" fill="none" stroke="{accent}" '
        f'stroke-width="1.2" class="halo"/>'
        + text(x + 16, y + 4, label, face=MONO, size=10, fill=accent,
               track=1.4),
        cls="rise", delay=delay)


def rule(x, y, w, color=LINE):
    return (f'<line x1="{x}" y1="{y}" x2="{x + w}" y2="{y}" stroke="{color}" '
            f'stroke-width="1"/>')


def path_draw(d, color, length, *, width=1.6, delay=0.7, dur=1.8, opacity=1):
    return (f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{opacity}" class="draw" '
            f'stroke-dasharray="{length}" stroke-dashoffset="{length}" '
            f'style="animation-delay:{delay}s;animation-duration:{dur}s"/>')


# ── The instruments ──────────────────────────────────────────────────────────

def inst_expiry(x, y, w, a):
    """Risu: a document, its expiry ring closing, the date read off it."""
    o = [f'<rect x="{x}" y="{y}" width="66" height="84" rx="3" '
         f'fill="{rgba(a, 0.07)}" stroke="{rgba(a, 0.22)}"/>']
    for i, ln in enumerate((30, 44, 22, 38)):
        o.append(f'<rect x="{x + 10}" y="{y + 16 + i * 12}" width="{ln}" '
                 f'height="3" rx="1.5" fill="{rgba(a, 0.35)}" class="wipe" '
                 f'style="animation-delay:{0.9 + i * 0.13:.2f}s;'
                 f'animation-duration:.45s"/>')
    cx, cy, r = x + 132, y + 42, 30
    circ = 2 * math.pi * r
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
             f'stroke="{rgba(a, 0.14)}" stroke-width="5"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{a}" '
             f'stroke-width="5" stroke-linecap="round" class="draw" '
             f'stroke-dasharray="{circ:.0f}" '
             f'stroke-dashoffset="{circ * 0.22:.0f}" '
             f'transform="rotate(-90 {cx} {cy})" '
             f'style="animation-name:ring;animation-delay:1.2s;'
             f'animation-duration:1.5s"/>')
    o.append(text(cx, cy + 5, "78d", face=MONO, size=15, fill=a, weight="700",
                  anchor="middle", cls="rise", delay=2.2))
    lx = x + 186
    o.append(text(lx, y + 26, "EXPIRES", face=MONO, size=9, fill=MUTE,
                  track=1.6, cls="rise", delay=1.5))
    o.append(text(lx, y + 46, "2027-01-14", face=MONO, size=15, fill=INK,
                  weight="700", cls="rise", delay=1.65))
    o.append(text(lx, y + 68, "read from the photo", face=SANS, size=11,
                  fill=MUTE, cls="rise", delay=1.8))
    css = (f"\n  @keyframes ring{{from{{stroke-dashoffset:{circ:.0f}}}"
           f"to{{stroke-dashoffset:{circ * 0.22:.0f}}}}}")
    return "".join(o), css


def inst_handicap(x, y, w, a):
    """Birdio: the index falling, and the ladder it climbs as it does."""
    pts = [(0, 12), (46, 26), (92, 20), (138, 40), (184, 34),
           (230, 52), (276, 47), (322, 64), (368, 72)]
    d = "M " + " L ".join(f"{x + px} {y + py}" for px, py in pts)
    o = [f'<rect x="{x}" y="{y + 4}" width="374" height="74" fill="none" '
         f'stroke="{HAIR}"/>']
    for gy in (22, 44, 66):
        o.append(rule(x, y + gy, 374, HAIR))
    area = d + f" L {x + 368} {y + 78} L {x} {y + 78} Z"
    o.append(f'<path d="{area}" fill="{rgba(a, 0.09)}" class="rise" '
             f'style="animation-delay:1.9s"/>')
    o.append(path_draw(d, a, 560, width=2, delay=0.8, dur=2.0))
    ex_, ey_ = x + pts[-1][0], y + pts[-1][1]
    o.append(f'<circle cx="{ex_}" cy="{ey_}" r="4" fill="{a}" class="pop" '
             f'style="animation-delay:2.5s"/>')
    o.append(f'<circle cx="{ex_}" cy="{ey_}" r="4" fill="none" stroke="{a}" '
             f'class="halo" style="animation-delay:2.9s"/>')
    o.append(text(x, y - 2, "INDEX 24.1 → 11.6", face=MONO, size=9, fill=MUTE,
                  track=1.4, cls="rise", delay=0.6))
    lx = x + 396
    for i, (name, on) in enumerate((("CONDOR", 0), ("EAGLE", 1),
                                    ("OWL", 0), ("FLAMINGO", 0))):
        c = a if on else rgba(a, 0.28)
        o.append(grp(f'<rect x="{lx}" y="{y + 6 + i * 19}" width="7" '
                     f'height="7" fill="{c}"/>'
                     + text(lx + 15, y + 13 + i * 19, name, face=MONO, size=9,
                            fill=INK if on else MUTE, track=1.2),
                     cls="rise", delay=1.9 + i * 0.09))
    return "".join(o), ""


def inst_sets(x, y, w, a):
    """Mule: the session, bar by bar, against the baseline it is scored on."""
    o = []
    bars = [30, 44, 38, 56, 62, 50, 71, 66, 78, 58, 84, 74]
    base = 52
    o.append(f'<line x1="{x}" y1="{y + 84 - base}" x2="{x + 300}" '
             f'y2="{y + 84 - base}" stroke="{rgba(a, 0.45)}" '
             f'stroke-dasharray="3 3" class="wipe" '
             f'style="animation-delay:.6s"/>')
    o.append(text(x + 306, y + 88 - base, "BASELINE", face=MONO, size=8.5,
                  fill=MUTE, track=1.2, cls="rise", delay=1.5))
    for i, hh in enumerate(bars):
        col = a if hh >= base else rgba(a, 0.4)
        o.append(f'<rect x="{x + i * 25}" y="{y + 84 - hh}" width="14" '
                 f'height="{hh}" fill="{col}" class="grow" '
                 f'style="animation-delay:{0.7 + i * 0.06:.2f}s"/>')
    lx = x + 396
    o.append(text(lx, y + 18, "SESSION", face=MONO, size=9, fill=MUTE,
                  track=1.6, cls="rise", delay=1.6))
    o.append(text(lx, y + 46, "+14%", face=MONO, size=24, fill=a,
                  weight="700", cls="pop", delay=1.75))
    o.append(text(lx, y + 68, "above your normal", face=SANS, size=11,
                  fill=MUTE, cls="rise", delay=1.9))
    return "".join(o), ""


def inst_seismic(x, y, w, a, *, live=None):
    """Quake: the trace, and the per-hour bars the portal's own mock shows."""
    events = live["events"] if live else {58: 1.0, 150: 0.55, 268: 0.85,
                                          392: 0.4, 470: 0.7}
    bars = live["bars"] if live else [34, 52, 41, 70, 88, 60, 46, 74, 38, 57,
                                      100, 44]
    stamp = live["stamp"] if live else "M 2.5+ · LAST 24 H · USGS ⊕ EMSC"
    bval = live["b"] if live else "b = 0.98"

    pts = []
    for px in range(0, 400, 2):
        v = math.sin(px * 0.28) * 1.6 + math.sin(px * 0.11) * 1.2
        for ex, amp in events.items():
            exx = ex * 400 / 520
            dx = px - exx
            v += math.sin(dx * 0.75) * 28 * amp * math.exp(-(dx * dx) / 200.0)
        pts.append((px, max(-36, min(36, v))))
    d = "M " + " L ".join(f"{x + px} {y + 42 - pv:.1f}" for px, pv in pts)

    o = [f'<rect x="{x}" y="{y}" width="400" height="84" fill="none" '
         f'stroke="{HAIR}"/>', rule(x, y + 42, 400, rgba(a, 0.16))]
    o.append(path_draw(d, a, 1200, width=1.5, delay=0.6, dur=2.4))
    for ex, amp in events.items():
        px = x + ex * 400 / 520
        r = 3 + amp * 3
        o.append(f'<circle cx="{px:.0f}" cy="{y + 42}" r="{r:.1f}" '
                 f'fill="none" stroke="{a}" stroke-width="1.2" class="halo" '
                 f'style="animation-delay:{2.6 + ex / 520 * 1.3:.2f}s"/>')
    o.append(text(x + 2, y - 2, stamp, face=MONO, size=9, fill=MUTE, track=1.2,
                  cls="rise", delay=0.5))
    # the portal's .qk-bars, same amber gradient
    bx = x + 418
    o.append('<defs><linearGradient id="qkb" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0%" stop-color="#E8A33D"/>'
             '<stop offset="100%" stop-color="#B87A1E"/></linearGradient>'
             '</defs>')
    for i, hpc in enumerate(bars[:12]):
        bh = max(3, hpc * 0.62)
        o.append(f'<rect x="{bx + i * 10}" y="{y + 84 - bh:.0f}" width="7" '
                 f'height="{bh:.0f}" rx="2" fill="url(#qkb)" class="grow" '
                 f'style="animation-delay:{1.0 + i * 0.05:.2f}s"/>')
    o.append(text(bx, y - 2, "PER 2 H", face=MONO, size=9, fill=MUTE,
                  track=1.2, cls="rise", delay=1.0))
    o.append(text(x + 400, y - 2, bval, face=MONO, size=9, fill=a, track=1.2,
                  anchor="end", cls="rise", delay=1.4))
    return "".join(o), ""


def inst_tools(x, y, w, a):
    """Studio: the portal's own browser window, with the portal's own tiles."""
    tiles = [("JPG → PNG", "IMAGE"), ("Resize", "IMAGE"), ("JSON", "DATA"),
             ("CSV ⇄ JSON", "DATA"), ("Markdown", "TEXT"), ("QR code", "WEB")]
    ww = 344
    o = [f'<rect x="{x}" y="{y - 4}" width="{ww}" height="96" rx="8" '
         f'fill="#101315" stroke="{rgba("#ffffff", 0.12)}"/>',
         f'<rect x="{x}" y="{y - 4}" width="{ww}" height="22" rx="8" '
         f'fill="#161A1D"/>',
         f'<rect x="{x}" y="{y + 10}" width="{ww}" height="4" fill="#161A1D"/>',
         rule(x, y + 14, ww, rgba("#ffffff", 0.07))]
    for i, c in enumerate(("#E07A6B", "#E0B45B", "#3FE0C5")):
        o.append(f'<circle cx="{x + 12 + i * 12}" cy="{y + 7}" r="3.5" '
                 f'fill="{c}"/>')
    o.append(text(x + 56, y + 10.5, "studio.dfklabs.com/tools", face=MONO,
                  size=8.5, fill="#7F8A86"))
    for i, (name, kind) in enumerate(tiles):
        tx = x + 10 + (i % 3) * 110
        ty = y + 20 + (i // 3) * 31
        o.append(grp(f'<rect x="{tx}" y="{ty}" width="104" height="25" rx="4" '
                     f'fill="{rgba(a, 0.07)}" stroke="{rgba(a, 0.16)}"/>'
                     + text(tx + 9, ty + 12, name, face=SANS, size=9.5,
                            fill=INK, weight="600")
                     + text(tx + 9, ty + 22, kind, face=MONO, size=7.5,
                            fill=MUTE, track=1),
                     cls="pop", delay=0.9 + i * 0.08))
    o.append(text(x + 10, y + 84, "● ALL PROCESSING HAPPENS IN YOUR BROWSER",
                  face=MONO, size=7.5, fill=rgba(a, 0.75), track=1,
                  cls="rise", delay=1.6))
    lx = x + ww + 18
    o.append(text(lx, y + 18, "OFFLINE", face=MONO, size=9, fill=MUTE,
                  track=1.6, cls="rise", delay=1.5))
    o.append(text(lx, y + 46, "31", face=MONO, size=26, fill=a, weight="700",
                  cls="pop", delay=1.65))
    o.append(text(lx, y + 68, "installable tools", face=SANS, size=11,
                  fill=MUTE, cls="rise", delay=1.8))
    return "".join(o), ""


def inst_board(x, y, w, a):
    """Paneltir: a card crossing columns — the drag the kit exists for."""
    o = []
    for i, name in enumerate(("IDEAS", "NEXT", "DOING", "DONE")):
        cx = x + i * 96
        o.append(grp(f'<rect x="{cx}" y="{y + 12}" width="84" height="72" '
                     f'fill="{rgba(a, 0.04)}" stroke="{rgba(a, 0.16)}"/>'
                     + text(cx + 4, y + 6, name, face=MONO, size=8.5,
                            fill=MUTE, track=1.4),
                     cls="rise", delay=0.7 + i * 0.08))
        for j in range(2 if i != 2 else 1):
            o.append(f'<rect x="{cx + 8}" y="{y + 22 + j * 20}" width="68" '
                     f'height="13" fill="{rgba(a, 0.13)}" class="rise" '
                     f'style="animation-delay:{1.0 + i * 0.08 + j * 0.05:.2f}s"'
                     f'/>')
    o.append(f'<rect x="{x + 8}" y="{y + 22}" width="68" height="13" '
             f'fill="{a}" opacity="0.92" class="travel"/>')
    lx = x + 4 * 96 + 14
    o.append(text(lx, y + 26, "POINTER EVENTS", face=MONO, size=9, fill=MUTE,
                  track=1.4, cls="rise", delay=1.6))
    o.append(text(lx, y + 48, "drag that works", face=SANS, size=12.5,
                  fill=INK, cls="rise", delay=1.72))
    o.append(text(lx, y + 66, "on iOS touch", face=SANS, size=12.5, fill=MUTE,
                  cls="rise", delay=1.84))
    css = ("\n  .travel{animation:travel 9s cubic-bezier(.5,0,.2,1) 1.6s "
           "infinite}"
           "\n  @keyframes travel{0%{transform:none}"
           "22%{transform:translate(96px,20px)}"
           "48%{transform:translate(192px,0)}"
           "72%{transform:translate(288px,20px)}"
           "96%,100%{transform:none}}")
    return "".join(o), css


def inst_ticker(x, y, w, a):
    """VibeClaude: the monitor line, showing what Xcode is being told."""
    rows = [("14:02:11", "build", "succeeded · 0 warnings"),
            ("14:02:44", "edit", "ContentView.swift +18 −11"),
            ("14:03:09", "test", "42 passed"),
            ("14:03:31", "wait", "your call")]
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="86" rx="4" '
         f'fill="{rgba(a, 0.04)}" stroke="{rgba(a, 0.14)}"/>']
    for i, (t, kind, msg) in enumerate(rows):
        ry = y + 20 + i * 18
        o.append(grp(text(x + 14, ry, t, face=MONO, size=10, fill=MUTE)
                     + text(x + 76, ry, kind, face=MONO, size=10, fill=a,
                            track=0.8)
                     + text(x + 132, ry, msg, face=MONO, size=10, fill=BODY),
                     cls="rise", delay=0.8 + i * 0.3))
    o.append(f'<rect x="{x + 236}" y="{y + 20 + 3 * 18 - 9}" width="7" '
             f'height="11" fill="{a}" class="beat" '
             f'style="animation-delay:2.2s"/>')
    return "".join(o), ""


INSTRUMENTS = {
    "expiry": inst_expiry, "handicap": inst_handicap, "sets": inst_sets,
    "seismic": inst_seismic, "tools": inst_tools, "board": inst_board,
    "ticker": inst_ticker,
}


# ── The card ─────────────────────────────────────────────────────────────────

def card(p, *, wide=False, live=None):
    w, h = (WIDE_W, WIDE_H) if wide else (CARD_W, CARD_H)
    a, slug = p["accent"], p["slug"]
    o = []

    o.append(f'<rect width="{w}" height="{h}" fill="url(#g-{slug})"/>')
    o.append(f'<rect x="0" y="0" width="{w}" height="2" fill="url(#r-{slug})" '
             f'class="wipe" style="animation-delay:.15s"/>')

    tag, tw = tag_box(PAD, 40, p["tag"], a, 0.5)
    o.append(tag)
    o.append(text(PAD + tw + 12, 53.5, p["platform"], face=MONO, size=9.5,
                  fill=MUTE, track=1.2, cls="rise", delay=0.58))
    o.append(state_dot(w - PAD - 63, 50, p["state"], a, 0.66))

    o.append(logo(p["logo"], PAD, 78, 52, a))
    o.append(text(PAD + 68, 112, p["mark"], face=p["face"], size=27, fill=INK,
                  weight="700", track=6, cls="rise", delay=0.42))
    o.append(f'<rect x="{PAD + 70}" y="124" width="26" height="3" rx="1.5" '
             f'fill="{a}" class="wipe" style="animation-delay:.62s"/>')

    for i, ln in enumerate(p["blurb"]):
        o.append(text(PAD, 170 + i * 19, ln, face=SANS, size=12.5, fill=BODY,
                      cls="rise", delay=0.7 + i * 0.08))

    cy = 170 + len(p["blurb"]) * 19 + 12
    cx = PAD
    for i, label in enumerate(p["chips"]):
        ch, cw = pill(cx, cy, label, a, 0.95 + i * 0.07)
        o.append(ch)
        cx += cw + 7

    iy = cy + 44
    fn = INSTRUMENTS[p["instrument"]]
    body, css = (fn(PAD, iy, w - PAD * 2, a, live=live)
                 if p["instrument"] == "seismic" else
                 fn(PAD, iy, w - PAD * 2, a))
    o.append(body)

    o.append(rule(PAD, h - 40, w - PAD * 2))
    o.append(text(PAD, h - 20, p["url"], face=MONO, size=10.5, fill=a,
                  track=0.4, cls="rise", delay=1.9))
    o.append(text(w - PAD, h - 20, "DFK LABS", face=MONO, size=9.5, fill=MUTE,
                  track=2, anchor="end", cls="rise", delay=2.0))

    # the sheen the portal shows on hover, run once on a long loop instead
    o.append(f'<g clip-path="url(#c-{slug})"><rect x="{-w * 0.38:.0f}" y="0" '
             f'width="{w * 0.34:.0f}" height="{h}" fill="url(#s-{slug})" '
             f'class="sheen"/></g>')
    o.append(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" '
             f'fill="none" stroke="{LINE}"/>')

    label = (f"{p['mark']} — {p['tag']}, {p['platform']}, {p['state']}. "
             f"{' '.join(p['blurb'])} {p['url']}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img" aria-label="{esc(label)}">
  <title>{esc(p['mark'] + ' — ' + p['tag'])}</title>
  {stylesheet(css)}
  <defs>
    <linearGradient id="g-{slug}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="35%" stop-color="{BLOCK}"/>
      <stop offset="100%" stop-color="{p['deep']}"/>
    </linearGradient>
    <linearGradient id="r-{slug}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{a}"/>
      <stop offset="100%" stop-color="{a}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="s-{slug}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{a}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{a}" stop-opacity="0.07"/>
      <stop offset="100%" stop-color="{a}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="c-{slug}"><rect width="{w}" height="{h}"/></clipPath>
  </defs>
  {''.join(o)}
</svg>
"""


# ── The header ───────────────────────────────────────────────────────────────

def header():
    w, h = 1240, 420
    o = [f'<rect width="{w}" height="{h}" fill="{BG}"/>']

    # the portal's particle grid: three layers drifting at different rates
    for layer, (count, op, r) in enumerate(
            ((46, 0.10, 1.6), (58, 0.07, 1.1), (70, 0.05, 0.8))):
        dots = []
        for i in range(count):
            px = (i * 173 + layer * 61) % w
            py = 64 + ((i * 97 + layer * 37) % (h - 120))
            dots.append(
                f'<circle cx="{px}" cy="{py}" r="{r}" fill="{BLUE_LT}"/>')
        o.append(f'<g opacity="{op}" class="drift{layer}">'
                 f'{"".join(dots)}</g>')
    for i in range(7):
        x1 = (i * 211) % w
        o.append(f'<line x1="{x1}" y1="60" x2="{(x1 + 180) % w}" y2="{h - 46}" '
                 f'stroke="{BLUE}" stroke-opacity="0.05"/>')

    # nav
    o.append(f'<rect width="{w}" height="60" fill="{rgba("#050505", 0.92)}"/>')
    o.append(rule(0, 60, w, HAIR))
    o.append(dfk_mark(32, 15))
    o.append(text(102, 36, "iOS ENGINEERING UNIT", face=MONO, size=9.5,
                  fill=MUTE, track=2.6, cls="rise", delay=0.22))
    for i, item in enumerate(("iOS", "WEB", "TOOLS", "PROJECTS")):
        o.append(text(w - 470 + i * 62, 36, item, face=MONO, size=9.5,
                      fill=MUTE, track=1.6, anchor="middle", cls="rise",
                      delay=0.3 + i * 0.05))
    o.append(grp(text(w - 32, 36, "SYSTEM: ACTIVE", face=MONO, size=9.5,
                      fill=BLUE_LT, track=1.6, anchor="end"),
                 cls="beat", delay=1.4))

    ex, ew = w / 2 - 84, 168
    o.append(grp(f'<rect x="{ex}" y="118" width="{ew}" height="28" '
                 f'fill="{rgba("#ffffff", 0.05)}" stroke="{LINE}"/>'
                 + text(w / 2, 136, "/// AI-DRIVEN FLOW", face=MONO, size=11,
                        fill=BLUE_LT, anchor="middle", track=1.4),
                 cls="rise", delay=0.45))

    for i, line in enumerate(("NATIVE", "INTELLIGENCE.")):
        o.append(text(w / 2, 224 + i * 70, line, face=SANS, size=74, fill=INK,
                      weight="900", track=-3, anchor="middle", cls="rise",
                      delay=0.6 + i * 0.13))

    o.append(text(w / 2, 336, "We build iOS apps and tools that replace "
                  "friction with flow.", face=SANS, size=17, fill=MUTE,
                  anchor="middle", cls="rise", delay=0.92))

    o.append(rule(0, h - 46, w, HAIR))
    o.append(text(32, h - 20, "SEVEN SURFACES · ONE FRAME", face=MONO,
                  size=9.5, fill=MUTE, track=2, cls="rise", delay=1.1))
    o.append(text(w - 32, h - 20, "ENGINEERED IN SILENCE.", face=MONO,
                  size=9.5, fill=MUTE, track=2, anchor="end", cls="rise",
                  delay=1.2))

    css = "".join(
        f"\n  .drift{i}{{animation:drift{i} {d}s ease-in-out infinite "
        f"alternate}}"
        f"\n  @keyframes drift{i}{{to{{transform:translate({dx}px,{dy}px)}}}}"
        for i, (d, dx, dy) in enumerate(((26, 18, -9), (34, -14, 7),
                                         (44, 9, -5))))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img"
     aria-label="DFK Labs, iOS Engineering Unit. Native Intelligence. We build iOS apps and tools that replace friction with flow.">
  <title>DFK Labs — Native Intelligence</title>
  {stylesheet(css)}
  {''.join(o)}
</svg>
"""


# ── The closing strip ────────────────────────────────────────────────────────

def footer():
    w, h = 1240, 116
    o = [f'<rect width="{w}" height="{h}" fill="{BG}"/>', rule(0, 0, w, LINE)]
    marks = [(p["mark"], p["accent"]) for p in PRODUCTS]
    marks.append((OPEN_SOURCE["mark"], OPEN_SOURCE["accent"]))
    x = 32
    for i, (name, a) in enumerate(marks):
        o.append(f'<rect x="{x}" y="40" width="58" height="3" fill="{a}" '
                 f'class="tick" style="animation-delay:{i * 0.42:.2f}s"/>')
        o.append(text(x, 64, name, face=MONO, size=8.5, fill=MUTE, track=1.2))
        x += 72
    o.append(text(w - 32, 46, "ENGINEERED IN SILENCE.", face=MONO, size=11,
                  fill=INK, track=2.4, anchor="end"))
    o.append(text(w - 32, 64, "© 2026 DFK Labs", face=MONO, size=9.5,
                  fill=MUTE, track=1.2, anchor="end"))
    css = ("\n  .tick{opacity:.22;animation:tick 6.3s ease-in-out infinite}"
           "\n  @keyframes tick{0%,8%{opacity:.22}14%{opacity:1}"
           "24%,100%{opacity:.22}}")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"
     width="{w}" height="{h}" role="img"
     aria-label="Engineered in Silence. © 2026 DFK Labs.">
  <title>Engineered in Silence</title>
  {stylesheet(css)}
  {''.join(o)}
</svg>
"""


# ── Live seismic data ────────────────────────────────────────────────────────

FEED_DAY = ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/"
            "2.5_day.geojson")
FEED_MONTH = ("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/"
              "2.5_month.geojson")
SNAPSHOT = HERE / "quake-snapshot.json"


def _get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "daifukus-profile/1.0 (+https://github.com/daifukus)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _mags(doc):
    return [f["properties"]["mag"] for f in doc.get("features", [])
            if (f.get("properties") or {}).get("mag") is not None]


def completeness(mags):
    """Mc by maximum curvature (Wiemer & Wyss, 2000), the same method the app
    uses. The M2.5+ feed is complete at 2.5 only over the United States; over
    the whole globe it is complete somewhere above M4, so taking 2.5 as Mc
    understates b badly — the first live run of this workflow reported 0.38.
    The mode of the 0.1-wide magnitude bins, plus the usual 0.2 correction, is
    what the estimator actually needs."""
    if len(mags) < 50:
        return None
    bins = {}
    for m in mags:
        bins[round(m, 1)] = bins.get(round(m, 1), 0) + 1
    return max(bins.items(), key=lambda kv: (kv[1], -kv[0]))[0] + 0.2


def b_value(mags):
    """Aki (1965) maximum likelihood above Mc, with the 0.05 bin correction.

    Returns (label, mc, n) or (None, ...) when the sample is too small to say
    anything — in which case the panel shows the count instead of a number
    nobody should trust."""
    mc = completeness(mags)
    if mc is None:
        return None, None, len(mags)
    above = [m for m in mags if m >= mc - 0.001]
    if len(above) < 50:
        return None, mc, len(above)
    mean = sum(above) / len(above)
    denom = mean - (mc - 0.05)
    if denom <= 0.05:
        return None, mc, len(above)
    return math.log10(math.e) / denom, mc, len(above)


def fetch_quake():
    """The real catalogue, reduced to what the panel draws.

    Two feeds, because they answer different questions — the same split the
    app itself makes. The day feed is the trace and the per-2 h bars. The month
    feed is the only one with enough events to fit a b-value on.

    Refreshed by .github/workflows/refresh-quake.yml. On any failure the caller
    keeps the committed snapshot: a profile showing yesterday's numbers beats
    one showing a stack trace.
    """
    day = _get(FEED_DAY)
    feats = [f for f in day.get("features", [])
             if (f.get("properties") or {}).get("mag") is not None
             and (f.get("properties") or {}).get("time") is not None]
    now = datetime.now(timezone.utc)
    now_ms = now.timestamp() * 1000

    buckets = [0] * 12
    for f in feats:
        age_h = (now_ms - f["properties"]["time"]) / 3_600_000
        if 0 <= age_h < 24:
            buckets[int(age_h / 2)] += 1
    peak = max(buckets) or 1
    bars = [max(6, round(c / peak * 100)) for c in reversed(buckets)]

    top = sorted(feats, key=lambda f: -f["properties"]["mag"])[:5]
    events, span = {}, 520
    for i, f in enumerate(top):
        m = f["properties"]["mag"]
        pos = int(40 + i * (span - 90) / max(1, len(top) - 1))
        events[pos] = max(0.28, min(1.0, (m - 2.5) / 4.0))

    # The b-value comes off the 30-day feed: a single day carries a few dozen
    # events, which is not a sample you can fit a slope to.
    try:
        month = _mags(_get(FEED_MONTH))
    except Exception:                                  # noqa: BLE001
        month = []
    b, mc, n = b_value(month)
    if b is not None:
        bval = f"b = {b:.2f} · Mc {mc:.1f} · 30 d"
    else:
        bval = f"n = {n} · 30 d"

    return {
        "events": events or {58: 1.0},
        "bars": bars,
        "b": bval,
        "stamp": (f"M 2.5+ · {len(feats)} EVENTS · 24 H · "
                  f"{now.strftime('%Y-%m-%d %H:%MZ')} · USGS"),
    }


def load_live(refresh):
    if refresh:
        try:
            live = fetch_quake()
            SNAPSHOT.write_text(json.dumps(live, indent=2) + "\n",
                                encoding="utf-8")
            print(f"  quake: {live['stamp']}")
            return live
        except Exception as exc:                       # noqa: BLE001
            print(f"  quake: feed unavailable ({exc}); keeping the snapshot")
    if SNAPSHOT.exists():
        raw = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        raw["events"] = {int(k): v for k, v in raw["events"].items()}
        return raw
    return None


# ── Build ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Render the profile README's panels.")
    ap.add_argument("--live", action="store_true",
                    help="refresh the Quake panel from the USGS feed first")
    args = ap.parse_args()

    live = load_live(args.live)
    written = []

    def put(name, body):
        p = HERE / name
        p.write_text(body, encoding="utf-8")
        written.append((name, p.stat().st_size))

    put("header.svg", header())
    for prod in PRODUCTS:
        put(f"card-{prod['slug']}.svg", card(prod, live=live))
    put("card-vibeclaude.svg", card(OPEN_SOURCE, wide=True))
    put("footer.svg", footer())

    for name, size in written:
        print(f"  assets/{name:<24} {size:>8,} bytes")
    print(f"{len(written)} files, {sum(s for _, s in written):,} bytes total")


if __name__ == "__main__":
    main()
