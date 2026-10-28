"""Draw one cat in one pose over consecutive frames, side by side, through the game's real code.
usage: frame_strip.py <html> <out.png> <pose> [frames=12] [step=0.5] [coat] [pattern] [facing=1]
step: room pixels the cat moves per frame (walk uses it; 0 keeps it still). facing -1 faces left.
The crop follows the cat, so coat markings should sit still on its body from frame to frame:
if they crawl, it strobes."""
import sys, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image

html, out, pose = sys.argv[1], sys.argv[2], sys.argv[3]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 12
step = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
coat = sys.argv[6] if len(sys.argv) > 6 else "ginger"
pattern = sys.argv[7] if len(sys.argv) > 7 else "tortie"
facing = int(sys.argv[8]) if len(sys.argv) > 8 else 1
HOUSE = [{"name": "Test", "coat": coat, "pattern": pattern, "eyes": "green", "character": "lazy", "voice": "mew", "age": "adult"}]
INIT = ("window.__skipCreator = true; window.__household = %s; window.__fakeNow = Date.parse('2026-06-17T13:00:00');"
        "window.requestAnimationFrame = cb => { window.__rafCb = cb; return 1; };"
        "window.__step = () => { const cb = window.__rafCb; window.__rafCb = null; if (cb) cb(performance.now()); };") % json.dumps(HOUSE)
FRAME = """([pose, k, step, facing]) => {
  const c = cats[0], walk = pose === 'walk';
  c.update = () => {}; c.updateDreams = () => {};
  c.getPose = () => walk ? 'walking' : pose;
  Object.assign(c, { isMoving: walk, animTick: 100 + k, x: 120 + k * step * facing, y: 170, z: 0, surface: 'floor', nav: null, facing,
                     state: walk ? 'wander' : pose });
  window.__step();
  return c.x;
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.goto(f"file://{html}")
    pg.wait_for_timeout(600)
    for _ in range(3): pg.evaluate("window.__step()")
    frames = []
    for k in range(n):
        x = pg.evaluate(FRAME, [pose, k, step, facing])
        d = pg.evaluate("roomCanvas.toDataURL('image/png')")
        im = Image.open(io.BytesIO(base64.b64decode(d.split(",")[1]))).convert("RGB")
        r = im.width // 320                                   # canvas pixels per room pixel
        x0 = round((x - 20) * r)                              # follow the cat, to the canvas pixel
        frames.append(im.crop((x0, 140 * r, x0 + 40 * r, 176 * r)))
    w, h = frames[0].size
    sheet = Image.new("RGB", (w * 4 * n, h * 4))
    for k, f in enumerate(frames):
        sheet.paste(f.resize((w * 4, h * 4), Image.NEAREST), (k * w * 4, 0))
    sheet.save(out)
    print(f"{pose}: {n} frames, step {step}, {coat} {pattern}, facing {facing}, errors: {errs[:3]}")
    b.close()
