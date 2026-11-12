#!/usr/bin/env python3
"""Captures the profile cards straight off dfklabs.com's own markup.

    python3 assets/capture.py /path/to/daifukus/DFK

The README shows exactly the cards the portal shows, in the portal's current
style: serve a checkout of daifukus/DFK, render index.html at 2x and crop each
visible card. Units the portal parks in <template data-dfk-parked> never render,
so they never reach the profile either — the "In the lab" strip stands in for
them here as it does there.

Needs Playwright, Pillow and a Chromium/Chrome build. WebP at q88 keeps
the 2x captures near 80 KB each instead of 1.3 MB as PNG.
"""

import asyncio
import io
import functools
import http.server
import sys
import threading
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parent / "cards"

# README order = portal order.
CARDS = [
    ("birdio", ".birdio-card"),
    ("nitnoi", ".nitnoi-card"),
    ("cue", ".cue-card"),
    ("cooked", ".cooked-card"),
    ("lab", ".lab-strip"),
    ("quake", ".quake-card"),
    ("studio", ".studio-card"),
    ("vibeclaude", ".tool-card"),
]

HIDE = "#chat-launch, #chat-panel { display: none !important; }"


def serve(root):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


async def main(root):
    httpd = serve(root)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/index.html"
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        exe = next((c for c in ("/usr/bin/google-chrome", "/usr/bin/chromium")
                    if Path(c).exists()), None)
        browser = await p.chromium.launch(executable_path=exe,
                                          args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1280, "height": 1000},
                                      device_scale_factor=2)
        await page.goto(url, wait_until="networkidle", timeout=90_000)
        await page.add_style_tag(content=HIDE)
        for name, sel in CARDS:
            el = await page.query_selector(sel)
            if el is None:
                print(f"  {name}: not on the portal, skipped")
                continue
            await el.scroll_into_view_if_needed()
            await page.wait_for_timeout(2500)     # let the entrance settle
            path = OUT / f"{name}.webp"
            shot = await el.screenshot()
            Image.open(io.BytesIO(shot)).save(path, "WEBP", quality=88, method=6)
            print(f"  assets/cards/{path.name:<16} {path.stat().st_size:>9,} bytes")
        await browser.close()
    httpd.shutdown()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    asyncio.run(main(Path(sys.argv[1]).resolve()))
