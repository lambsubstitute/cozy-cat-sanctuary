---
name: cozy-cat-art
description: Use for any artwork or animation change in Cozy Cat Sanctuary (lambsubstitute/cozy-cat-sanctuary) - cat poses, coats, patterns, furniture, the room, the view outside, props or effects. Keeps new art in the game's 16-bit double-resolution style and checks it with pose sheets and frame strips before pushing.
---

# Cozy Cat Sanctuary art

The game is one file, `index.html`, in `lambsubstitute/cozy-cat-sanctuary` (live on GitHub Pages; Beef keeps a git copy in `Documents/projects/cozy-cat-sanctuary`). Every picture in it is drawn in code. There are no image files, and there must never be any: players design their own cats (8 coats x 6 patterns x 6 eye colours, adult or kitten), so art has to be generated from the cat's palette, not stored.

Clone it and find your way by its section banners rather than line numbers, which drift:

```sh
git clone -q https://github.com/lambsubstitute/cozy-cat-sanctuary.git ccs && cd ccs
grep -nE '^\s*// [A-Z0-9][A-Z0-9 &:,()-]{5,}' index.html     # the sections
```

The art lives mostly in **16-BIT ART** (the toolkit, `spriteFX`, room painting), the cat drawing code just before **DANGLY TOY** (`drawCatBody` and its helpers), **THE VIEW OUTSIDE**, and the section for each feature (box, tunnel, birds, night visitors...).

## The look

Super Nintendo era, drawn at double resolution.

- **Light comes from the top left.** Top edges catch light, undersides and right sides fall into shadow, and things cast soft shadows down and to the right.
- **Shading is hue-shifted, never just darker or lighter.** Use `shade(col, amt)` (-1 deepest shadow, drifting cool and indigo; +1 brightest highlight, drifting warm and golden) and `ramp(col, [amts])` for a material's short ramp. Don't mix towards black or white by hand.
- **Gradients are dithered**, with ordered Bayer dithering (`dith`, `rampAt`, `painter.dither`, `.tint`, `.fade`), not smooth canvas gradients. (Radial canvas gradients are only for soft glows of light laid on top: the lamp and fire, flashes, the UFO.)
- **Textures are repeatable.** Use `hash2(x, y, seed)` or `valueNoise`, never `Math.random()`, in anything drawn, so the room looks the same every visit and every frame. Pick a fresh seed number for each new texture.
- **A fine dark outline** in a deep shade of the neighbouring colour goes round sprites (spriteFX adds it) and round painted pieces (`painter.outline()`).
- **Don't bake in time of day.** Night, dusk and lightning are laid over everything afterwards in `drawLightingAndParticles`; draw everything in daylight colours.

## The grid

- The room is **320 x 190 room pixels** (`W`, `H`). Every position, route, hit box and piece of furniture is in room pixels. **Never move furniture or ledges**: the cats' navigation graph (`NAV_EDGES`) and the tests depend on exact positions.
- The canvas is drawn at **`RES = 2`** (640 x 380), so detail can be half a room pixel across. Positions in art code can be on halves (`x + 0.5`).
- `SNAP` is the grid `pxRect` snaps to: `RES` normally, `1` inside a sprite's low-res pass.

## Two kinds of art

### Things that never move: paint them once

The still room is painted once into `roomBackdrop()` (repainted only when the festive decorations change) with a `painter(w, h)`: an offscreen picture measured in room pixels, painted a fine pixel at a time.

- Whole room pixels: `set`, `rect`, `map(x, y, rows, pal)` (a little bitmap, one character per room pixel).
- Fine pixels: `dot`, `fset`, `fmap` (one character per fine pixel), `line` (one fine pixel thick), `fine(x, y, w, h, (fx, fy) => colour or null)` for anything procedural.
- Textures and light: `dither`, `tint(x, y, w, h, amt, coverage)`, `fade`, `woodFill`, `fuzzFill`, `rampAt(ramp, t, fx, fy)`, `roundLight(u)` for a rounded surface lit from the upper left.
- Finishing: `outline(amt)`, `smooth()` (rounds off stepped edges, EPX style), `toCanvas()`.
- `stamp(dst, src, x, y, [right, down, amt, soft])` copies a painted piece into the room with its cast shadow. `blit(ctx, canvas, x, y)` draws a painted canvas at a room position.

Follow the existing `paintWallpaper`, `paintFloor` and furniture painters, and `paintPortrait` for something detailed and procedural. Anything that changes now and then but isn't animated (a portrait, say) is painted once per look and cached by a key.

### Symbols: hearts, Zs, sparkles, "!", notes, bubbles

The little pictures that float over the cats, and the speech and dream bubbles with their pictures, live in the **SYMBOLS** and **SPEECH BUBBLES** sections. Each is a bitmap of fine pixels (one character per half room pixel), finished once by `symbolArt(key, rows, pal, opt)`: light along open top and left edges, shade along bottom and right ones, then a fine outline (a deep shade of its own colour, or `ink`). Options: `flat` (characters left unshaded: eyes, glints), `late` (painted after the outline: glows), `light`/`dark`/`outline`. The result is cached by `key`; draw it with `drawSymbol(cv, cx, cy)`, which centres it on the fine grid.

- New particle: add its bitmap to `PARTICLE_ART` and a `case` in `drawParticle`. New bubble picture: add it to `BUBBLE_ICONS` (up to 16 x 12 fine pixels, so it fits the bubble and the dream cloud).
- Keep them bold and simple: whole shapes in two or three colours, strokes at least two fine pixels thick, and leave two fine pixels between separate parts or their outlines run together.
- Check them with `tests/symbol_sheet.py` (and `night`).

### Things that move: draw them through spriteFX

```js
spriteFX(target, wx, wy, g => drawThing(g), { /* options */ });
```

`draw(g)` paints in room coordinates. spriteFX draws it twice at once: a low-res copy that's blown up with EPX/Scale2x (rounding every diagonal), and a full-resolution copy whose fine details win. Then it shades every edge, adds fur where coat colours meet and outlines the lot, so every pose gets the same finish without being shaded by hand.

Options: `outline` (cats use `-0.9`, default `-0.8`), `light` (0.3), `dim` (0.34), `fur: true`, `coat: cat` (turns stripes into the cat's real markings), `round: false` (no EPX), `dx`/`dy` (glide by part of a pixel), `cache: 'key'` (draw once and reuse: use it for anything that looks the same every frame).

- **A sprite must fit its scratch box**: within 48 room pixels left or right of `(wx, wy)`, 72 above and 24 below (`FX_BOX`, `FX_OX`, `FX_OY`). Anything outside is silently cut off.
- **spriteFX costs a `getImageData` per sprite per frame**: keep sprites compact, and cache still ones.
- **Read-backs can be noisy.** Browsers with anti-fingerprinting protection (Safari, Brave, Firefox, and Beef's) nudge a few read-back values by a level or two, differently every time. spriteFX compares colours exactly, so that noise made patterned cats shimmer while sitting still. `FX_NOISY` detects it at start-up; when it's on, every solid fill colour painted into a sprite is noted (`fxInks`) and the read-back is snapped to the nearest one (`fxClean`). Paint sprites with solid colour strings through `fillStyle` so they're noted. Never add another `getImageData` without the same treatment, and run `tests/noise_test.py` after any change to spriteFX or the cats.
- Things on the floor go in the `drawables` list with their `y`, so they're drawn back to front.

Inside a sprite, draw with the right tool for each job:

| Tool | Use it for |
| --- | --- |
| `pxRect(c, x, y, w, h, col)` | The basic shape, in whole room pixels. Gets EPX rounding, shading, fur and coat markings. |
| `hd(c, x, y, w, h, col)` / `hdClear(...)` | Fine details at half-pixel steps (eyes, noses, whiskers, ear tips, toes) or notches cut out of the shape. Never use them for the basic shape. |
| `hdFur(c, x, y, w, h, col)` | A fine detail that's really coat, in `pal.base` or `pal.stripe`: a breath swelling the outline, fur closing over an eye on a blink. Like `hd`, but the coat markings and fur reach it, so it takes the colour of the patch it's in. |
| `fineMap(c, x, y, rows, pal)`, `fineTri(...)` | Small fine-pixel bitmaps and triangles. |
| `fineDabs(c, [[x, y, r, col]...])` with `roundShader(col, r, nx, ny)` | Smooth, curved, moving parts: anything that bends or moves half a pixel at a time. |
| `catMap(c, x, y, rows, catCols(cat))` | A body as a shaped bitmap, one letter per room pixel: `B` coat, `S` tabby markings, `W` pale chest and belly, `M` muzzle (white on a tuxedo), `D` ears. This is how the rounded silhouettes are drawn (`SIT_BODY`, `STAND_BODY`, `CURL_BODY`, `LOAF_BODY`, `STRETCH_BODY`, and the window-watching cat). Prefer it to stacking `pxRect` boxes. |
| `catHeadSide(c, cat, hx, hy, { eye, whiskers, flick, earUp })` | The side-on head (`HEAD_SIDE`): sloping forehead, muzzle, chin, ears, eye and nose, all placed for you. Use it for any side-on pose. |
| `catMapSwell(c, x, y, rows, cols, 'top' or 'back', from, to)` | Breathing for a `catMap` body: its outline swells half a pixel on a breath in. |
| `catTail`, `catLeg`, `catShadow`, `eyeHD`, `closedEyeHD`, `noseHD`, `earHD`, `pawHD`, `breathHD` | Cat parts. Reuse them rather than drawing new ones. |

Never call canvas paths (`arc`, `lineTo`, `drawImage`...) in cat drawing code: kittens are drawn through `smallCtx`, which only supports `save`, `restore`, `translate`, `scale`, `fillStyle`, `globalAlpha`, `beginPath`, `rect`, `clip` and `fillRect` (and the helpers above, which know about it).

## Cats

- **Coordinates**: `(0, 0)` is on the ground under the middle of the cat; it faces **right** (+x is forward) and up is **-y**. `drawCatBody` flips it with `c.scale(-1, 1)` when it faces left, so draw every pose facing right. A standing adult's body is about `x -7..6`, head `x 2..9`, ears up to `y -14`.
- **Only ever use the palette**: `cat.pal.base`, `dark`, `stripe`, `light`, `belly`, `paws`, `nose`, `eyes` (built by `lookPalette`). Shade them with `shade` or mix them with `blendColors` / `mixHex`; never hard-code a coat colour. The only fixed colours are the small face details: `LID`, `PUPIL`, `WHISKER`, the white glint, the near-black `'#1e140f'` and the soft dark mouth line.
- **Coat areas must be exactly `pal.base` and markings exactly `pal.stripe`** in `pxRect` (in a `catMap`, the letters `B` and `S`). `coatPattern` works by finding those two colours and turning them into solid, calico or tortoiseshell markings; anything shaded, mixed or drawn with `hd` is left alone (use `hdFur` for fine details that should be coat).
- **Tuxedo**: check `cat.isTuxedo` and draw a white blaze or bib in `pal.belly` instead of stripes, the way every existing pose does. Colourpoint works through the palette (and `catTail`).
- **Kittens** are the same sprites at `KITTEN_SIZE` (0.75). Check every new pose on a kitten.

### The strobe rule

Any noise, hash or pattern on something that moves must be worked out from the **sprite's own coordinates** (the scratch canvas, which moves with the sprite), never from its room position or the clock. Otherwise the markings slide across the body as it walks, and it flickers. (This was the tortoiseshell strobe: coat patches computed from room position. `coatPattern` and the fur use scratch-canvas coordinates; `catTail` uses distance along the tail.)

The same goes for anything that comes and goes, like a breath or a blink: a fine detail drawn in plain `pal.base` or `pal.stripe` with `hd` is skipped by `coatPattern`, so on a calico, tortie or solid cat it flashes plain colour across the patches every time it appears. (This was the sitting-cat shimmer: the breath along the back.) Draw coat-coloured details that appear and disappear with `hdFur`. Check it with a frame-by-frame diff across a breath (`inhale` flips when `Math.sin(t * 2π / 110 + cat.id)` crosses 0.15) on a calico and a tortie.

### Animation

- Drive animation from `cat.animTick` (each cat's own clock), offset by `cat.id` so cats never move in step.
- Move parts half a pixel at a time (`hd`, `fineDabs`, `dx`/`dy`) rather than jumping whole room pixels. Breathing is the back rising half a pixel (`breathHD`, or `catMapSwell` for a `catMap` body), not the cat hopping.
- Walking uses `catGait(cat)` (stride phase and body bob); legs step in order back left, front left, back right, front right, and each paw lifts as it swings forward.
- Existing rhythms: blink every 80 ticks, ear flick (`earFlick`), tail sway from `Math.sin(t * 0.15)`. Match their pace; small and slow reads as cosy.

### Adding a pose

1. A branch in `drawCatBody` (copy the nearest existing pose and change it). Draw the body as a `catMap` bitmap with a rounded silhouette and the head with `catHeadSide`, like sitting, standing, curled up, the loaf, kneading and stretching. (A few older poses are still built from boxes: lying on its back, the crouch, the leap, scratching up on the hind legs and the full gallop.)
2. A route to it in `getPose()` (the state or activity that shows it).
3. Its height in `bubbleAnchor()` if it isn't about 18 room pixels tall.
4. Add it to `POSES` in `tests/pose_sheet.py`, and to `PREVIEW_POSES` if it suits the cat creator's preview.

## Checking the work

Never report art as done from the code alone: render it and look.

```sh
pip install playwright pillow --break-system-packages && python3 -m playwright install chromium   # once, if missing
GAME=$PWD/index.html
python3 tests/pose_sheet.py $GAME before.png <pose> ...   # every pose (or the ones named), four coats incl. a calico kitten
python3 tests/pose_sheet.py $GAME after.png <pose> ...
python3 tests/frame_strip.py $GAME walk.png walk 12 0.5 ginger tortie   # consecutive frames of one cat
```

Look at every image yourself (Read the PNG). Check:

- Light from the top left; outline intact all round; no stray pixels, holes or seams.
- Every coat: ginger tabby, black tuxedo, grey tabby, white calico kitten (pose sheet), plus tortie and solid (frame strip).
- In a frame strip with the cat moving, the markings stay put on the body (no strobe) and nothing pops by a whole pixel unless it should.
- Facing left as well as right (frame strip with `facing -1`), if the pose can face both ways.

If the change touches anything that could shift a position, a route or a hit box, also run the simulation (see `tests/README.md`):

```sh
export PYTHONPATH=$PWD/tests
EXTRA=1 python3 tests/sim_test.py $GAME 36000 300 1 2 > run.txt && python3 tests/sum2.py run.txt
```

All counts (overlaps, illegal positions, bad jumps, errors) must be zero. Run `touch_test.py` too if anything on the page around the canvas changed, and `noise_test.py` (cats sitting still in a browser with noisy canvas read-backs) after any change to spriteFX or the cat drawing.

### frame_strip.py

It lives in `tests/frame_strip.py`. If it's ever missing, write this copy to the scratchpad and run that instead:

```python
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
        d = pg.evaluate("document.getElementById('dioramaCanvas').toDataURL('image/png')")
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
```

## Showing Beef and shipping

- Send before and after images (pose sheets or frame strips) as soon as there's something to see, so he can redirect early. Keep the write-up short and practical.
- Commit and push only when he says to. Then confirm the GitHub Pages deployment finished, and remind him to run `git pull` in `Documents/projects/cozy-cat-sanctuary` to bring his copy up to date.
- Keep the README's "Making changes" section true if the toolkit changes.
