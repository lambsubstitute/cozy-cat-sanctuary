"""Patterned cats must sit still even in browsers that add noise to canvas read-backs.

Some browsers guard against fingerprinting (Safari, Brave and Firefox can all do this) by nudging a
few of the values a page reads back from a canvas by a level or two, differently every time. The
sprite shading reads every sprite back, so without care that noise makes tabby stripes and tortie
patches shimmer on a cat that's sitting perfectly still. This test fakes that noise, sits a tabby, a
tortie and a calico down, and checks that nothing on their bodies changes from one frame to the next
(the tail is allowed to sway). It also checks the game noticed the noise.

The noise is random but seeded, so a failure can be run again exactly: each run picks a seed and
prints it, and passing that seed back repeats the same noise.

usage: noise_test.py <html> [seed]"""
import sys, json, base64, io, random
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

html = sys.argv[1]
seed = int(sys.argv[2]) if len(sys.argv) > 2 else random.randrange(1 << 30)
NOISE = """(() => {
  // seeded random numbers (mulberry32): one stream for the game, and one for the noise that starts
  // afresh every frame, so the same seed gives the same noise however many read-backs came before
  const stream = s => () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const seed = %d;
  Math.random = stream(seed);
  let rnd = stream(seed ^ 0x5bd1e995);
  window.__noiseFrame = t => { rnd = stream((seed * 1009 + t) ^ 0x5bd1e995); };
  const orig = CanvasRenderingContext2D.prototype.getImageData;
  CanvasRenderingContext2D.prototype.getImageData = function (...a) {
    const im = orig.apply(this, a), d = im.data;
    for (let k = 0; k < d.length; k += 4) if (rnd() < 0.2) {
      const ch = k + Math.floor(rnd() * 4), dv = 1 + Math.floor(rnd() * 2);
      d[ch] = Math.max(0, Math.min(255, d[ch] + (rnd() < 0.5 ? -dv : dv)));
    }
    return im;
  };
})();"""
FRAME = """([t]) => {
  const c = cats[0];
  window.__noiseFrame(t);
  c.update = () => {}; c.updateDreams = () => {}; c.purrTimer = 0; c.getPose = () => 'sit_relax';
  Object.assign(c, { isMoving: false, animTick: t, x: 120, y: 170, z: 0, surface: 'floor', nav: null, facing: 1, state: 'sit_relax' });
  window.__step();
  return Math.sin(t * Math.PI * 2 / 110 + c.id) > 0.15;
}"""
fails = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for i, (coat, pattern) in enumerate([("brown", "tabby"), ("ginger", "tortie"), ("white", "calico")]):
        house = [{"name": "T", "coat": coat, "pattern": pattern, "eyes": "green", "character": "lazy", "voice": "mew", "age": "adult"}]
        pg = b.new_page()
        pg.add_init_script("window.__skipCreator = true; window.__household = %s; window.__fakeNow = Date.parse('2026-06-17T13:00:00');"
                           "window.requestAnimationFrame = cb => { window.__rafCb = cb; return 1; };"
                           "window.__step = () => { const cb = window.__rafCb; window.__rafCb = null; if (cb) cb(performance.now()); };" % json.dumps(house))
        pg.add_init_script(NOISE % (seed + i))
        pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        pg.goto(f"file://{html}")
        pg.wait_for_timeout(500)
        pg.evaluate("drawDustMotes = () => {}")          # (the sunbeam's dust motes drift across the cat, which isn't noise)
        noticed = pg.evaluate("typeof FX_NOISY !== 'undefined' && FX_NOISY")
        prev, prev_in, worst = None, None, 0
        for t in range(100, 124):
            inhale = pg.evaluate(FRAME, [t])
            d = pg.evaluate("roomCanvas.toDataURL('image/png')")
            im = Image.open(io.BytesIO(base64.b64decode(d.split(",")[1]))).convert("RGB")
            r = im.width // 320
            body = im.crop(((120 - 6) * r, (170 - 22) * r, (120 + 14) * r, (170 + 2) * r))   # the cat, without its tail behind
            if prev is not None and inhale == prev_in:
                n = sum(1 for px in ImageChops.difference(body, prev).getdata() if max(px) > 6)
                worst = max(worst, n)
            prev, prev_in = body, inhale
        ok = noticed and worst == 0
        print(f"{'PASS' if ok else 'FAIL'}  {coat} {pattern}: noise noticed {noticed}, most body pixels changed between frames {worst}")
        if not ok: fails.append(pattern)
        pg.close()
    b.close()
print(f"noise seed {seed}" + (f" (run again with: noise_test.py <html> {seed})" if fails else ""))
sys.exit(1 if fails else 0)
