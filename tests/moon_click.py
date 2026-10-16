import sys
from playwright.sync_api import sync_playwright
from sim_test import INIT
html = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1280, 'height': 900})
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.goto(f"file://{html}?seed=5&fake=2026-10-15T23:00:00"); pg.wait_for_function("window.__rafCb !== null")
    r = pg.evaluate("(() => { const r = canvas.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    at = lambda x, y: (r[0] + (x + 0.5) * r[2] / 320, r[1] + (y + 0.5) * r[3] / 190)
    pg.evaluate("void 0; nextUfo = 1e9; 0;")
    pg.mouse.click(*at(143, 38))
    print('toast:', pg.evaluate("document.getElementById('toastBanner').textContent"))
    pg.evaluate("(() => { for (let i = 0; i < 400; i++) window.__step(); })()")
    print('ufo:', pg.evaluate("[ufo.active, ufo.phase, Math.round(ufo.x), Math.round(ufo.y)]"))
    pg.evaluate("(() => { for (let i = 0; i < 200; i++) window.__step(); })()")
    ux, uy = pg.evaluate("[ufo.x, ufo.y]")
    pg.mouse.click(*at(ux, uy))
    print('after clicking ufo:', pg.evaluate("[ufo.phase, document.getElementById('toastBanner').textContent]"))
    print(errs)
    b.close()
