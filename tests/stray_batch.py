import sys, json
from playwright.sync_api import sync_playwright
from sim_test import INIT
html = sys.argv[1]; seeds = range(int(sys.argv[2]), int(sys.argv[3]))
JS = r"""([delay]) => {
  stray.next = globalTick + 5;
  let n = 0; while (!(stray.active && stray.phase === 'sit') && n++ < 5000) window.__step();
  for (let i = 0; i < delay; i++) window.__step();
  const before = cats.map(c => c.name + ':' + c.surface + ':' + c.x.toFixed(0) + (c.nav ? '>' + c.nav.goal.surface + '@' + c.nav.goal.x.toFixed(0) + (c.nav.jump ? 'J' : '') : '') + ':' + c.state);
  letStrayIn();
  for (let i = 0; i < 40; i++) window.__step();
  if (nameModalCat) { const k = nameModalCat; nameModalCat = null; finishNaming(k, 'Pip'); }
  const after = cats.map(c => c.name + ':' + c.surface + ':' + c.x.toFixed(1) + ':' + c.state);
  const moved = cats.map(() => 0), onSill = cats.map(() => 0), sx = cats.map(c => c.x), sy = cats.map(c => c.y);
  for (let f = 0; f < 3600; f++) {
    window.__step();
    cats.forEach((c, i) => { if (c.surface === 'sill' || !c.surface) onSill[i]++; if (Math.hypot(c.x - sx[i], c.y - sy[i]) > 30) moved[i] = 1; });
  }
  return { before, after, onSill: onSill.map(v => +(v / 3600).toFixed(2)), moved, end: cats.map(c => c.name + ':' + c.surface + ':' + c.x.toFixed(1) + ':' + c.state + (c.nav ? ' nav ' + c.nav.label + ' w' + c.nav.waiting + ' r' + c.nav.replans : '')) };
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for seed in seeds:
        for delay in (5, 60, 240):
            pg = b.new_page()
            pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.add_init_script(INIT)
            pg.goto(f"file://{html}?seed={seed}&fake=2026-10-15T09:30:00")
            pg.wait_for_function("window.__rafCb !== null")
            r = pg.evaluate(JS, [delay])
            stuck = [i for i in range(len(r['moved'])) if not r['moved'][i] and r['onSill'][i] > 0.95]
            if stuck or errs:
                print('SEED', seed, 'delay', delay, 'stuck', stuck, errs); print('  before', r['before']); print('  after', r['after']); print('  end', r['end'])
            pg.close()
    print('done')
    b.close()
