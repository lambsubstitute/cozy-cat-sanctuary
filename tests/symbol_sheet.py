"""Not a check: draws every symbol the cats use (the floating hearts, Zs, sparkles, stars, "!" and
music notes, every speech-bubble icon, and dream bubbles) through the game's real drawing code,
on the real room, and saves them blown up for looking over.
usage: symbol_sheet.py <html> <out.png> [night]"""
import sys, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image

html, out = sys.argv[1], sys.argv[2]
night = len(sys.argv) > 3 and sys.argv[3] == "night"
HOUSE = [
    {"name": "Moe", "coat": "ginger", "pattern": "tabby", "eyes": "green", "character": "playful", "voice": "mew", "age": "adult"},
    {"name": "Tux", "coat": "black", "pattern": "tuxedo", "eyes": "gold", "character": "lazy", "voice": "deep", "age": "adult"},
]
INIT = ("(() => { let s = 3; Math.random = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; })();"
        "window.__skipCreator = true; window.__household = %s; window.__fakeNow = Date.parse('2026-06-17T%s');"
        "window.requestAnimationFrame = cb => { window.__rafCb = cb; return 1; };"
        "window.__step = () => { const cb = window.__rafCb; window.__rafCb = null; if (cb) cb(performance.now()); };") % (json.dumps(HOUSE), "23:30:00" if night else "13:00:00")
JS = r"""() => {
  // keep the cats out of the way, asleep at the back
  cats.forEach((c, i) => { c.update = () => {}; c.updateDreams = () => {}; c.getPose = () => 'sleep_curl'; Object.assign(c, { x: 40 + i * 30, y: 186, z: 0, surface: 'floor', nav: null, facing: 1, state: 'sleep_curl', bubble: null, dream: null }); });
  particles.length = 0;
  const types = ['heart', 'zzz', 'sparkle', 'star', 'alert', 'note', 'crumb', 'splash', 'fluff', 'dust', 'steam'];
  // each particle at three ages (just born, halfway, nearly gone), standing still
  types.forEach((t, i) => [0.1, 0.5, 0.85].forEach((f, k) => {
    spawnParticle(t, 22 + i * 26, 30 + k * 16);
    const p = particles[particles.length - 1]; p.vx = 0; p.vy = 0; p.age = Math.round(p.maxAge * f) - 1;
  }));
  window.__step();
  // speech bubbles: every icon, then a friend's face
  const icons = Object.keys(BUBBLE_ICONS);
  icons.forEach((ic, i) => drawBubble(14 + (i % 13) * 23, 106 + Math.floor(i / 13) * 24, ic));
  // dream bubbles: a few icons, a friend, and a nightmare
  const c = cats[0];
  const dreams = [{ icon: 'fish' }, { icon: 'mouse', chase: true }, { icon: 'heart', kind: 'love' }, { kind: 'friend', friend: cats[1] }, { icon: 'storm', nightmare: true }];
  const realAnchor = c.bubbleAnchor;
  dreams.forEach((d, i) => {
    c.dream = Object.assign({ start: globalTick - 60, until: globalTick + 200, kind: 'thing' }, d);
    c.bubbleAnchor = () => ({ x: 30 + i * 62, y: 180 });
    c.facing = -1; c.surface = 'floor';
    drawDreamBubble(c);
  });
  c.bubbleAnchor = realAnchor; c.dream = null;
  return roomCanvas.toDataURL('image/png');
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.goto(f"file://{html}")
    pg.wait_for_timeout(500)
    for _ in range(3): pg.evaluate("window.__step()")
    d = pg.evaluate(JS)
    im = Image.open(io.BytesIO(base64.b64decode(d.split(",")[1]))).convert("RGB")
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(out)
    print("saved", out, "errors:", errs[:3])
    b.close()
