import sys, os, json
sys.argv = sys.argv
from sim_test import run
html, frames, every, seed, fake = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
import sim_test
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(sim_test.INIT)
    if os.environ.get("HOUSEHOLD"): pg.add_init_script("window.__household = " + os.environ["HOUSEHOLD"] + ";")
    pg.goto(f"file://{html}?seed={seed}&fake={fake}")
    pg.wait_for_function("window.__rafCb !== null")
    if os.environ.get("EXTRA"): pg.evaluate("window.__extraTriggers = true")
    if os.environ.get("SETUP"): pg.evaluate("void 0;" + os.environ["SETUP"] + "; 0;")
    res = pg.evaluate(sim_test.RUN, [frames, every]); res["pageErrors"] = errs
    res["baubleKnocks"] = pg.evaluate("KNOCKABLES.filter(k => k.hang && k.state !== 'home').length")
    b.close()
print(f"=== seed {seed} {fake}: {frames} frames ===")
print(json.dumps(res, indent=1))
