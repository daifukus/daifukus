#!/usr/bin/env python3
"""Renders assets/header-dark.svg and assets/header-light.svg.

One geometry, two palettes. Edit the palettes or the LABELS below and re-run:

    python3 assets/build-header.py

The output is committed, so the profile has no build step.
Animation is SMIL, not CSS: GitHub serves the file through camo and the
browser paints it as an <img>, where SMIL is the reliably supported half.
"""

from pathlib import Path

PALETTES = {
    "dark": {
        "bg": "#050505",
        "panel": "#0d0d0f",
        "grid": "#ffffff",
        "grid_op": "0.055",
        "line": "#ffffff",
        "line_op": "0.13",
        "ink": "#f4f4f5",
        "ink_dim": "#9aa4b2",
        "ink_faint": "#5b6472",
        "accent": "#3fe0c5",
        "blue": "#2563eb",
    },
    "light": {
        "bg": "#fbfbfc",
        "panel": "#f2f3f5",
        "grid": "#0a0a0a",
        "grid_op": "0.06",
        "line": "#0a0a0a",
        "line_op": "0.14",
        "ink": "#0a0a0a",
        "ink_dim": "#4b5563",
        "ink_faint": "#8b95a3",
        "accent": "#0e9c86",
        "blue": "#2563eb",
    },
}

# The seven surfaces, in the order they light up.
LABELS = ["LABS", "BIRDIO", "QUAKE", "MULE", "STUDIO", "PANELTIR", "RISU"]

W, H = 1200, 300


def corners(p):
    """Viewfinder brackets, drawn on with a stroke-dash reveal."""
    a, m, L = p["accent"], 26, 34
    pairs = [
        (m, m, 1, 1),
        (W - m, m, -1, 1),
        (m, H - m, 1, -1),
        (W - m, H - m, -1, -1),
    ]
    out = []
    for i, (x, y, sx, sy) in enumerate(pairs):
        d = f"M {x} {y + sy * L} L {x} {y} L {x + sx * L} {y}"
        out.append(
            f'<path d="{d}" fill="none" stroke="{a}" stroke-width="2" '
            f'stroke-linecap="square" stroke-dasharray="{2 * L}" stroke-dashoffset="{2 * L}" opacity="0.75">'
            f'<animate attributeName="stroke-dashoffset" values="{2 * L};0" dur="0.8s" '
            f'begin="{0.1 + i * 0.12:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/>'
            f"</path>"
        )
    return "\n    ".join(out)


def ticks(p):
    """One tick per shipping surface, lighting in sequence, forever."""
    out = []
    x0, y = 152, 246
    for i, name in enumerate(LABELS):
        x = x0 + i * 96
        out.append(
            f'<g><rect x="{x}" y="{y}" width="72" height="3" rx="1.5" fill="{p["accent"]}" opacity="0.16">'
            f'<animate attributeName="opacity" values="0.16;0.16;1;0.16" keyTimes="0;0.12;0.22;1" '
            f'dur="5.6s" begin="{2.0 + i * 0.34:.2f}s" repeatCount="indefinite"/></rect>'
            f'<text x="{x}" y="{y + 20}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
            f'font-size="10" letter-spacing="1.6" fill="{p["ink_faint"]}">{name}</text></g>'
        )
    return "\n    ".join(out)


def render(name, p):
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    sans = "system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="DFK Labs — iOS Engineering Unit. Native intelligence, fluid reality.">
  <title>DFK Labs — iOS Engineering Unit</title>
  <defs>
    <linearGradient id="scan-{name}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{p['accent']}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{p['accent']}" stop-opacity="0.17"/>
      <stop offset="100%" stop-color="{p['accent']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="vign-{name}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{p['panel']}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{p['bg']}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="grid-{name}" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0H0V40" fill="none" stroke="{p['grid']}" stroke-width="1" stroke-opacity="{p['grid_op']}"/>
    </pattern>
    <clipPath id="card-{name}"><rect x="0" y="0" width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="wipe-word-{name}">
      <rect x="150" y="70" width="0" height="120">
        <animate attributeName="width" values="0;760" dur="1.1s" begin="0.35s" fill="freeze"
                 calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/>
      </rect>
    </clipPath>
    <clipPath id="wipe-sub-{name}">
      <rect x="150" y="196" width="0" height="40">
        <animate attributeName="width" values="0;620" dur="1.4s" begin="1.05s" fill="freeze"
                 calcMode="spline" keyTimes="0;1" keySplines="0.33 1 0.68 1"/>
      </rect>
    </clipPath>
  </defs>

  <g clip-path="url(#card-{name})">
    <rect width="{W}" height="{H}" fill="{p['bg']}"/>
    <rect width="{W}" height="{H}" fill="url(#vign-{name})"/>

    <g opacity="0">
      <animate attributeName="opacity" values="0;1" dur="1.4s" fill="freeze"/>
      <rect width="{W}" height="{H}" fill="url(#grid-{name})"/>
    </g>

    {corners(p)}

    <!-- the mark: a block sitting behind an outlined box, opening on a slow loop -->
    <g transform="translate(64,104)">
      <rect x="6" y="6" width="56" height="56" rx="7" fill="{p['blue']}" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.25s" fill="freeze"/>
        <animateTransform attributeName="transform" type="translate"
                          values="0,0; 5,5; 0,0" keyTimes="0;0.5;1" dur="4.5s"
                          begin="1.2s" repeatCount="indefinite" calcMode="spline"
                          keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>
      </rect>
      <rect x="0" y="0" width="56" height="56" rx="7" fill="{p['bg']}" stroke="{p['ink']}"
            stroke-width="2" opacity="0">
        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.35s" fill="freeze"/>
      </rect>
      <rect x="20" y="20" width="16" height="16" rx="3" fill="{p['accent']}" opacity="0">
        <animate attributeName="opacity" values="0;1;0.35;1" keyTimes="0;0.25;0.6;1"
                 dur="3s" begin="0.8s" repeatCount="indefinite"/>
      </rect>
    </g>

    <!-- wordmark -->
    <g clip-path="url(#wipe-word-{name})">
      <text x="150" y="152" font-family="{mono}" font-size="62" font-weight="700"
            letter-spacing="6" fill="{p['ink']}">DFK LABS</text>
    </g>
    <rect x="152" y="172" width="0" height="3" rx="1.5" fill="{p['accent']}">
      <animate attributeName="width" values="0;432" dur="0.9s" begin="0.95s" fill="freeze"
               calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/>
    </rect>

    <!-- subtitle, revealed like it is being typed -->
    <g clip-path="url(#wipe-sub-{name})">
      <text x="152" y="212" font-family="{mono}" font-size="15" letter-spacing="5.5"
            fill="{p['ink_dim']}">iOS ENGINEERING UNIT · NATIVE INTELLIGENCE</text>
    </g>
    <rect x="152" y="199" width="9" height="16" fill="{p['accent']}" opacity="0">
      <animate attributeName="x" values="152;618" dur="1.4s" begin="1.05s" fill="freeze"
               calcMode="spline" keyTimes="0;1" keySplines="0.33 1 0.68 1"/>
      <animate attributeName="opacity" values="0;1" dur="0.1s" begin="1.05s" fill="freeze"/>
      <animate attributeName="opacity" values="1;1;0;1" keyTimes="0;0.4;0.5;1" dur="1.1s"
               begin="2.5s" repeatCount="indefinite"/>
    </rect>

    {ticks(p)}

    <!-- status, top right -->
    <g transform="translate({W - 42},52)" opacity="0">
      <animate attributeName="opacity" values="0;1" dur="0.8s" begin="1.6s" fill="freeze"/>
      <text x="-16" y="5" text-anchor="end" font-family="{mono}" font-size="12"
            letter-spacing="2.4" fill="{p['ink_dim']}">SHIPPING</text>
      <circle cx="0" cy="0" r="4.5" fill="{p['accent']}"/>
      <circle cx="0" cy="0" r="4.5" fill="none" stroke="{p['accent']}" stroke-width="1.5">
        <animate attributeName="r" values="4.5;15" dur="2.4s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.7;0" dur="2.4s" repeatCount="indefinite"/>
      </circle>
    </g>

    <text x="{W - 42}" y="{H - 34}" text-anchor="end" font-family="{sans}" font-size="13"
          font-style="italic" fill="{p['ink_faint']}" opacity="0">Engineered in Silence.
      <animate attributeName="opacity" values="0;1" dur="1.2s" begin="2.2s" fill="freeze"/>
    </text>

    <!-- the sweep -->
    <rect x="-190" y="0" width="190" height="{H}" fill="url(#scan-{name})">
      <animate attributeName="x" values="-190;{W}" dur="8s" begin="1.8s" repeatCount="indefinite"/>
    </rect>

    <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="16" fill="none"
          stroke="{p['line']}" stroke-opacity="{p['line_op']}"/>
  </g>
</svg>
"""


def main():
    here = Path(__file__).resolve().parent
    for name, palette in PALETTES.items():
        out = here / f"header-{name}.svg"
        out.write_text(render(name, palette), encoding="utf-8")
        print(f"wrote {out.relative_to(here.parent)}  ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
