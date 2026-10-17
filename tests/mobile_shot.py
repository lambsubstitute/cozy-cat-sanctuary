"""Full-page screenshots on phone-sized screens (Tailwind and the fonts: see assets.py).

usage: python3 mobile_shot.py <html> <out_prefix> <setup_js> [WxH ...]
  setup_js runs after load ('' for none). Set CREATOR=1 to keep the first-visit cat creator.
  SEL=<css> screenshots just that element; VIEW=1 takes only the visible screen (no full page).
Prints layout facts for each size: page overflow, canvas size and the room's scale.
"""
import json, os, sys
from assets import route_assets
from playwright.sync_api import sync_playwright

html, out, setup = sys.argv[1], sys.argv[2], sys.argv[3]
sizes = [tuple(int(v) for v in s.split("x")) for s in sys.argv[4:]] or [(390, 844)]

INIT = "" if os.environ.get("CREATOR") else "window.__skipCreator = true;"
INIT += "window.__fakeNow = new Date(%s).getTime();" % json.dumps(os.environ.get("FAKE", "2026-10-17T14:00:00"))

FACTS = """() => {
  const c = document.getElementById('dioramaCanvas').getBoundingClientRect();
  const over = [...document.querySelectorAll('body *')].filter(e => {
    const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1);
  }).slice(0, 6).map(e => (e.id ? '#' + e.id : e.tagName.toLowerCase() + '.' + [...e.classList].slice(0, 3).join('.')) + ' ' + Math.round(e.getBoundingClientRect().left) + '..' + Math.round(e.getBoundingClientRect().right));
  return { scrollW: document.documentElement.scrollWidth, innerW: innerWidth, pageH: document.documentElement.scrollHeight,
           canvas: [Math.round(c.left), Math.round(c.top), Math.round(c.width), Math.round(c.height)],
           scale: +(c.width / 320).toFixed(2), canvasBottom: Math.round(c.bottom), overflowing: over };
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for (w, h) in sizes:
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2, is_mobile=w < 1024, has_touch=True)
        pg = ctx.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(INIT)
        route_assets(pg, html)
        pg.goto(f"file://{html}")
        pg.wait_for_timeout(1200)
        if setup: pg.evaluate(setup)
        pg.wait_for_timeout(700)
        facts = pg.evaluate(FACTS)
        sel = os.environ.get("SEL")
        path = f"{out}_{w}x{h}.png"
        if sel: pg.locator(sel).first.screenshot(path=path)
        else: pg.screenshot(path=path, full_page=not os.environ.get("VIEW"))
        print(f"{w}x{h}", json.dumps(facts), "errors:", errs)
        ctx.close()
    b.close()
