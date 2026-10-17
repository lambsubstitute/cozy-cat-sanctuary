"""Playing with a finger on a phone-sized screen: tapping cats (and just missing them),
treats, brushing, the laser, hide and seek, the screensaver and the photo, plus the
pinned room, turning the phone sideways, and the desktop staying as it was.
The layout needs Tailwind and the fonts: see assets.py.

usage: python3 touch_test.py <html>
"""
import json, os, sys
from assets import route_assets
from playwright.sync_api import sync_playwright

html = sys.argv[1]
results = []
def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))

INIT = "window.__skipCreator = true; window.__fakeNow = new Date('2026-10-17T14:00:00').getTime();"

def screen_xy(pg, cat_index, dx=0, dy=0):
    return pg.evaluate("""([i, dx, dy]) => {
        const r = canvas.getBoundingClientRect(), c = cats[i];
        return [r.left + c.x * r.width / W + dx, r.top + (c.y - c.z - 6) * r.height / H + dy];
    }""", [cat_index, dx, dy])

def touch(cdp, kind, x, y):
    pts = [] if kind == "touchEnd" else [{"x": x, "y": y, "id": 1}]
    cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": pts})

def drag(cdp, pg, pts, step_ms=16):
    touch(cdp, "touchStart", *pts[0])
    for p in pts[1:]:
        pg.wait_for_timeout(step_ms)
        touch(cdp, "touchMove", *p)
    pg.wait_for_timeout(step_ms)
    touch(cdp, "touchEnd", 0, 0)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    route_assets(pg, html)
    pg.goto(f"file://{html}")
    pg.wait_for_timeout(1500)
    cdp = ctx.new_cdp_session(pg)

    check("touch screen detected", pg.evaluate("TOUCH_UI"))
    check("hints say tap", pg.evaluate("document.getElementById('toolHint').textContent") == "Tap a cat to pet it",
          pg.evaluate("document.getElementById('toolHint').textContent"))
    check("short phone tagline showing", pg.evaluate("getComputedStyle(document.getElementById('taglineShort')).display") != "none")
    check("no sideways page scroll", pg.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    # Count pets
    pg.evaluate("""() => { window.__petted = []; cats.forEach(c => { const o = c.pet.bind(c); c.pet = (...a) => { __petted.push(c.name); return o(...a); }; }); }""")
    # Hold the cats still while we aim at them
    pg.evaluate("() => { cats.forEach(c => { c.update = () => {}; }); }")

    x, y = screen_xy(pg, 0)
    pg.touchscreen.tap(x, y)
    pg.wait_for_timeout(150)
    check("tap a cat pets it", pg.evaluate("__petted.length") == 1, pg.evaluate("__petted"))

    # A near miss: 14 screen px off the edge of the mouse target still counts for a finger
    scale = pg.evaluate("canvas.getBoundingClientRect().width / W")
    off = 13 * scale + 6
    x, y = screen_xy(pg, 1, off, 0)
    # make sure no other cat is closer to that point
    nearest = pg.evaluate("""([x, y]) => { const r = canvas.getBoundingClientRect(); const mx = (x - r.left) * W / r.width, my = (y - r.top) * H / r.height;
        return cats.map(c => Math.hypot(mx - c.x, my - (c.y - c.z - 6))).map(d => +d.toFixed(1)); }""", [x, y])
    pg.touchscreen.tap(x, y)
    pg.wait_for_timeout(150)
    petted = pg.evaluate("__petted")
    check("a fingertip just off a cat still pets it", len(petted) == 2, f"{petted}, distances {nearest}")

    # The same near miss with a mouse does not
    pg.evaluate("() => { __petted.length = 0; }")
    pg.mouse.click(x, y)
    pg.wait_for_timeout(150)
    check("a mouse click there doesn't (desktop unchanged)", pg.evaluate("__petted.length") == 0, pg.evaluate("__petted"))

    # Treats: tap a cat with the treat bag
    pg.click("#tool-treat")
    pg.wait_for_timeout(100)
    pg.evaluate("cats[2].needs.food = 0.3")
    x, y = screen_xy(pg, 2)
    toast_before = pg.evaluate("document.getElementById('toastBanner').textContent")
    pg.touchscreen.tap(x, y)
    pg.wait_for_timeout(200)
    toast = pg.evaluate("document.getElementById('toastBanner').textContent")
    check("tap a cat with treats gives one", toast != toast_before and ("treat" in toast.lower() or "🐟" in toast), toast)
    pg.click("#tool-treat")    # put the bag down

    # Brush: touch a cat and stroke back and forth
    pg.click("#tool-brush")
    pg.wait_for_timeout(100)
    check("brush hint is for fingers", "Touch a cat" in pg.evaluate("document.getElementById('toolHint').textContent"))
    pg.evaluate("() => { window.__strokes = 0; cats.forEach(c => { const o = c.brushStroke.bind(c); c.brushStroke = (...a) => { __strokes++; return o(...a); }; }); }")
    x, y = screen_xy(pg, 0)
    sy0 = pg.evaluate("scrollY")
    pts = [(x, y)]
    for i in range(24):
        pts.append((x + (6 if i % 2 == 0 else -6), y + (i % 3) - 1))
    drag(cdp, pg, pts, 30)
    pg.wait_for_timeout(200)
    check("stroking a cat with a finger brushes it", pg.evaluate("__strokes") >= 3, f"strokes {pg.evaluate('__strokes')}")
    check("brushing doesn't scroll the page", pg.evaluate("scrollY") == sy0)
    pg.click("#tool-brush")

    # Laser: drag a finger across the room
    pg.click("#btnLaser")
    pg.wait_for_timeout(100)
    r = pg.evaluate("(() => { const r = canvas.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    sy0 = pg.evaluate("scrollY")
    pts = [(r[0] + r[2] * 0.2, r[1] + r[3] * 0.8)] + [(r[0] + r[2] * (0.2 + 0.05 * i), r[1] + r[3] * (0.8 - 0.03 * i)) for i in range(1, 12)]
    drag(cdp, pg, pts, 25)
    pg.wait_for_timeout(150)
    lx, ly = pg.evaluate("[laser.x, laser.y]")
    ex, ey = (pts[-1][0] - r[0]) * 320 / r[2], (pts[-1][1] - r[1]) * 190 / r[3]
    check("the laser dot follows the finger", abs(lx - ex) < 3 and abs(ly - ey) < 3, f"dot {lx},{ly} finger {ex:.0f},{ey:.0f}")
    check("aiming the laser doesn't scroll the page", pg.evaluate("scrollY") == sy0)
    toast = pg.evaluate("document.getElementById('toastBanner').textContent")
    pg.click("#btnLaser")
    pg.wait_for_timeout(100)
    check("laser off again", not pg.evaluate("laser.on"))

    # Hide and seek: pressing it twice gives up (no Esc key on a phone)
    pg.evaluate("() => { cats.forEach(c => { delete c.update; }); }")
    pg.evaluate("triggerHideAndSeek()")
    pg.wait_for_timeout(300)
    started = pg.evaluate("hideGame.active && hideGame.byUser")
    pg.evaluate("triggerHideAndSeek()")
    t1 = pg.evaluate("document.getElementById('toastBanner').textContent")
    pg.evaluate("triggerHideAndSeek()")
    t2 = pg.evaluate("document.getElementById('toastBanner').textContent")
    check("hide and seek: second press explains, third gives up", started and "tap Hide & Seek again" in t1 and "give up" in t2.lower() and not pg.evaluate("hideGame.active"), f"{t1} / {t2}")

    # Pinned room: scroll down to the activities and the room is still on screen
    pg.evaluate("window.scrollTo(0, 700)")
    pg.wait_for_timeout(200)
    top = pg.evaluate("canvas.getBoundingClientRect().top")
    hb = pg.evaluate("document.getElementById('toolBar').getBoundingClientRect().bottom")
    check("room stays pinned at the top when scrolled", 0 <= top <= 12 and hb < 340, f"canvas top {top:.0f}, hand bottom {hb:.0f}")
    # and the activity buttons are still tappable under it
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(100)
    pg.locator("button[onclick='triggerTossYarn()']").tap()
    pg.wait_for_timeout(100)
    check("activity buttons respond to a tap", "yarn" in pg.evaluate("document.getElementById('toastBanner').textContent").lower())

    # Screensaver: a tap brings up the ✕
    pg.evaluate("toggleScreensaver(true)")
    ss_toast = pg.evaluate("document.getElementById('toastBanner').textContent")
    pg.wait_for_timeout(3000)
    asleep = "ss-awake" not in pg.evaluate("document.body.className")
    r = pg.evaluate("(() => { const r = canvas.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
    pg.touchscreen.tap(r[0] + 20, r[1] + r[3] - 20)
    pg.wait_for_timeout(100)
    check("screensaver: a tap shows the way out", asleep and "ss-awake" in pg.evaluate("document.body.className"))
    check("screensaver toast is for fingers", "tap the ✕" in ss_toast, ss_toast)
    pg.locator("#ssExit").tap()
    pg.wait_for_timeout(200)
    check("the ✕ leaves the screensaver", not pg.evaluate("screensaver"))

    # Photo: share button only where the phone can share files (headless can't), save link always
    pg.evaluate("takePhoto()")
    pg.wait_for_timeout(800)
    check("photo opens with a save link", pg.evaluate("!document.getElementById('photoPanel').classList.contains('hidden') && !document.getElementById('photoSave').classList.contains('hidden')"))
    pg.evaluate("togglePhoto(false)")

    # Turn the phone on its side: the room comes up to fill the screen, with your hand beside it
    pg.evaluate("window.scrollTo(0, 0)")
    pg.set_viewport_size({"width": 844, "height": 390})
    pg.wait_for_timeout(1500)
    c = pg.evaluate("(() => { const r = canvas.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })()")
    t = pg.evaluate("(() => { const r = document.getElementById('toolBar').getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; })()")
    check("sideways: the room scrolls up to fill the screen", c[1] >= 0 and c[3] <= 390 and (c[3] - c[1]) > 330, f"canvas {[round(v) for v in c]}")
    check("sideways: your hand sits beside the room", t[0] >= c[2] and t[1] >= 0 and t[3] <= 390, f"hand {[round(v) for v in t]}")
    check("sideways: no sideways page scroll", pg.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    check("no page errors", not errs, errs)
    ctx.close()

    # Desktop: still says click, nothing pinned
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(INIT)
    route_assets(pg, html)
    pg.goto(f"file://{html}")
    pg.wait_for_timeout(1200)
    check("desktop: not a touch screen", not pg.evaluate("TOUCH_UI"))
    check("desktop: hints still say click", pg.evaluate("document.getElementById('toolHint').textContent") == "Click a cat to pet it")
    check("desktop: room not pinned", pg.evaluate("getComputedStyle(document.getElementById('stage')).position") != "sticky")
    check("desktop: full tagline, no phone hints", pg.evaluate("getComputedStyle(document.getElementById('tagline')).display") != "none"
          and pg.evaluate("getComputedStyle(document.getElementById('turnHint')).display") == "none"
          and pg.evaluate("getComputedStyle(document.getElementById('taglineShort')).display") == "none")
    check("desktop: no page errors", not errs, errs)
    ctx.close()
    b.close()

failed = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} passed" + (f"; FAILED: {failed}" if failed else ""))
sys.exit(1 if failed else 0)
