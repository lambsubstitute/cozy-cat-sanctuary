import sys
from playwright.sync_api import sync_playwright
from sim_test import INIT
html, seed, fake, start, ci, n = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
setup = sys.argv[7] if len(sys.argv) > 7 else ''
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.add_init_script(INIT)
    pg.goto(f"file://{html}?seed={seed}&fake={fake}")
    pg.wait_for_function("window.__rafCb !== null")
    if setup: pg.evaluate("void 0;" + setup + "; 0;")
    # replicate dither.py's trigger loop exactly
    pg.evaluate(f"""(() => {{ for (let f = 0; f < {start}; f++) {{ if (window.__trig && f % window.__trig.every === window.__trig.every - 1) window.__trig.fn(); window.__step(); }} }})()""")
    for k in range(n):
        f = start + k
        pg.evaluate(f"(() => {{ const f = {f}; if (window.__trig && f % window.__trig.every === window.__trig.every - 1) window.__trig.fn(); window.__step(); }})()")
        print(pg.evaluate(f"""(() => {{ const c = cats[{ci}]; const st = c.nav && c.nav.steps[c.nav.i];
            return [globalTick, c.x.toFixed(2), c.y.toFixed(2), c.facing, c.detourSide, c.state, c.nav ? c.nav.purpose + ' i' + c.nav.i + ' stall' + c.nav.stall + ' w' + c.nav.waiting : '-', st ? st.type + '(' + (+st.x).toFixed(1) + ',' + (+st.y).toFixed(1) + ')' : '-',
              box.active ? 'box ' + box.x + ',' + box.y : 'nobox', cats.filter(o => o !== c && o.surface === 'floor').map(o => o.name[0] + ':' + o.x.toFixed(0) + ',' + o.y.toFixed(0)).join(' ')]; }})()"""))
    b.close()
