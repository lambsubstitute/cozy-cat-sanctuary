"""Find cats jittering on the spot: lots of facing flips / movement with no real progress.
usage: dither.py html frames seed [fake] [setup_js]"""
import sys, json
from playwright.sync_api import sync_playwright
from sim_test import INIT
html, frames, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
fake = sys.argv[4] if len(sys.argv) > 4 else '2026-10-14T18:30:00'
setup = sys.argv[5] if len(sys.argv) > 5 else ''
JS = r"""([frames]) => {
  const out = { flipEvents: [], stuckEvents: [], flipFrames: 0, stuckFrames: 0 };
  const hist = cats.map(() => []);
  const lastFace = cats.map(c => c.facing);
  const busyUntil = cats.map(() => 0), stuckUntil = cats.map(() => 0);
  for (let f = 0; f < frames; f++) {
    if (window.__trig && f % window.__trig.every === window.__trig.every - 1) window.__trig.fn();
    window.__step();
    cats.forEach((c, i) => {
      const flipped = c.facing !== lastFace[i];
      lastFace[i] = c.facing;
      const h = hist[i];
      h.push({ x: c.x, y: c.y, flip: flipped && c.surface === 'floor', moving: c.isMoving && c.surface === 'floor' && !c.pounce && !(c.nav && c.nav.jump) });
      if (h.length > 60) h.shift();
      if (h.length < 60) return;
      const flips = h.slice(-30).filter(e => e.flip).length;
      const label = () => ({ f, cat: c.name, state: c.state, nav: c.nav ? c.nav.purpose : null, x: +c.x.toFixed(1), y: +c.y.toFixed(1), role: c.playRole });
      if (flips >= 6) { out.flipFrames++; if (f > busyUntil[i]) { out.flipEvents.push(Object.assign(label(), { flips })); busyUntil[i] = f + 120; } }
      const allMoving = h.every(e => e.moving);
      const disp = Math.hypot(h[59].x - h[0].x, h[59].y - h[0].y);
      if (allMoving && disp < 4) { out.stuckFrames++; if (f > stuckUntil[i]) { out.stuckEvents.push(Object.assign(label(), { disp: +disp.toFixed(1) })); stuckUntil[i] = f + 120; } }
    });
  }
  return out;
}"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.goto(f"file://{html}?seed={seed}&fake={fake}")
    pg.wait_for_function("window.__rafCb !== null")
    if setup: pg.evaluate("void 0;" + setup + "; 0;")
    r = pg.evaluate(JS, [frames])
    print(f"seed {seed}: flipFrames {r['flipFrames']} stuckFrames {r['stuckFrames']} events {len(r['flipEvents'])}/{len(r['stuckEvents'])} errors {errs}")
    for e in (r['flipEvents'] + r['stuckEvents'])[:12]: print('   ', e)
    b.close()
