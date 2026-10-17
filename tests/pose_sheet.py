"""Render every cat pose for a few different coats, through the game's real drawing code.
usage: pose_sheet.py <html> <out.png> [pose ...]"""
import sys, json, base64, io
from playwright.sync_api import sync_playwright
from PIL import Image

html, out = sys.argv[1], sys.argv[2]
POSES = sys.argv[3:] or ['sit_relax', 'look_at_you', 'grooming', 'walk', 'eating', 'play_yarn', 'window_watch', 'sleep_curl',
                         'sleep_loaf', 'sleep_belly', 'kneading', 'crouch', 'leap', 'stretching', 'scratching', 'proud']
HOUSE = [
    {"name": "Ginger", "coat": "ginger", "pattern": "tabby", "eyes": "green", "character": "playful", "voice": "mew", "age": "adult"},
    {"name": "Tux", "coat": "black", "pattern": "tuxedo", "eyes": "gold", "character": "lazy", "voice": "deep", "age": "adult"},
    {"name": "Grey", "coat": "grey", "pattern": "tabby", "eyes": "blue", "character": "cuddly", "voice": "chatty", "age": "adult"},
    {"name": "Cali", "coat": "white", "pattern": "calico", "eyes": "copper", "character": "grumpy", "voice": "mew", "age": "kitten"},
]
JS = """(pose) => {
  const out = [];
  cats.forEach((c, i) => {
    c.update = () => {}; c.updateDreams = () => {};
    c.getPose = () => pose === 'walk' ? 'walking' : pose; c.isMoving = pose === 'walk'; c.animTick = 7;
    Object.assign(c, { x: 60 + i * 50, y: 170, z: 0, surface: 'floor', nav: null, facing: 1, state: pose === 'walk' ? 'wander' : pose });
    if (pose === 'walk') { c.isWalking = true; }
  });
  return true;
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 1000})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("window.__skipCreator = true; window.__household = %s; window.__fakeNow = new Date('2026-06-17T13:00:00').getTime();" % json.dumps(HOUSE))
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.goto(f"file://{html}")
    pg.wait_for_timeout(800)
    rows = []
    for pose in POSES:
        pg.evaluate(JS, pose)
        pg.wait_for_timeout(250)
        d = pg.evaluate("document.getElementById('dioramaCanvas').toDataURL('image/png')")
        im = Image.open(io.BytesIO(base64.b64decode(d.split(",")[1]))).convert("RGB")
        rows.append(im.crop((30, 140, 250, 180)))
    sheet = Image.new("RGB", (220 * 4, 40 * 4 * len(rows)))
    for k, r in enumerate(rows):
        sheet.paste(r.resize((880, 160), Image.NEAREST), (0, k * 160))
    sheet.save(out)
    print("poses:", POSES, "errors:", errs[:3])
    b.close()
