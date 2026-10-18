"""A cat in the corner beside the right-hand end of the tunnel can always get out.

The tunnel lies against the front edge of the floor, so the only way past it is round the back.
Cats used to try sliding round the front, scraping along the edge of the room, and shuffled on the
spot in the corner for as long as 15 seconds (during zoomies, or on their way to the bowls).
This starts a cat in that corner, already set on going round the front, and checks it's well clear
of the corner within two seconds, both with the zoomies and walking across the room.

usage: tunnel_corner.py <html>"""
import sys
from playwright.sync_api import sync_playwright
from sim_test import INIT

html = sys.argv[1]
TRIAL = """([how, sx, sy]) => {
  const [c, ...rest] = cats;
  rest.forEach((o, i) => { o.update = () => {}; Object.assign(o, { surface: i ? 'sofaSeat' : 'treeTop', x: i ? 104 : 42, y: i ? 124 : 0, nav: null, claim: null, state: 'sleep_curl' }); });
  if (!tunnel.out) putOutTunnel(false);
  Object.assign(c, { surface: 'floor', x: sx, y: sy, z: 0, nav: null, claim: null, pounce: null, hunt: null, state: 'idle', stateTimer: 0 });
  if (how === 'zoomies') { c.goZoomies(3); c.zoom.pts = [{ x: 60, y: 162 }, { x: 200, y: 160 }]; }
  else c.goTo({ surface: 'floor', x: 60, y: 165 }, 'sit_relax', 'rest');
  c.detourSide = 1; c.detourT = globalTick;          // already heading 'round the front'
  for (let f = 1; f <= 120; f++) {
    window.__step();
    if (c.x < 280 || c.y < 165) return { out: true, f, x: Math.round(c.x), y: Math.round(c.y) };
  }
  return { out: false, f: 120, x: +c.x.toFixed(1), y: +c.y.toFixed(1) };
}"""
fails = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for how in ("zoomies", "walking"):
        for sx, sy in [(300, 181), (302, 179), (299.5, 177)]:
            pg = b.new_page()
            errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.add_init_script(INIT)
            pg.goto(f"file://{html}?seed=3")
            pg.wait_for_function("window.__rafCb !== null")
            for _ in range(30): pg.evaluate("window.__step()")
            r = pg.evaluate(TRIAL, [how, sx, sy])
            ok = r["out"] and not errs
            print(f"{'PASS' if ok else 'FAIL'}  {how} from ({sx}, {sy}): {'out of the corner after ' + str(r['f']) + ' frames' if r['out'] else 'still at (' + str(r['x']) + ', ' + str(r['y']) + ') after 2 seconds'} {errs[:1]}")
            if not ok: fails.append(how)
            pg.close()
    b.close()
sys.exit(1 if fails else 0)
