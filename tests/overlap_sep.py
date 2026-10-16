import sys
from playwright.sync_api import sync_playwright
from sim_test import INIT
html = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    for surf, xs in [('sill', [125, 126]), ('sill', [158, 160]), ('mantel', [280, 284]), ('sofaSeat', [124, 130])]:
        pg = b.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        pg.add_init_script(INIT)
        pg.goto(f"file://{html}?seed=3&fake=2026-10-15T09:30:00"); pg.wait_for_function("window.__rafCb !== null")
        r = pg.evaluate(f"""(() => {{
          stray.coat = KITTEN_COATS[0]; const k = addKittenToFamily('Pip', '{surf}', {xs[1]}, null, 'sit_relax'); finishNaming(k, 'Pip');
          const m = cats[0]; m.nav = null; m.surface = '{surf}'; m.x = {xs[0]}; m.y = surfacePointY('{surf}'); m.settleHere('sit_relax', 30); k.settleHere('sit_relax', 30);
          let sep = -1;
          for (let f = 0; f < 3600; f++) {{ window.__step(); if (sep < 0 && (m.surface !== '{surf}' || k.surface !== '{surf}' || Math.abs(m.x - k.x) >= 16)) sep = f; }}
          return [sep, m.surface + ':' + m.x.toFixed(0) + ':' + m.state, k.surface + ':' + k.x.toFixed(0) + ':' + k.state];
        }})()""")
        print(surf, xs, 'separated at frame', r[0], r[1:], errs)
        pg.close()
    b.close()
