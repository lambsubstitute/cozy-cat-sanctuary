"""Start over (in Settings) forgets everything and brings back the cat creator.
usage: python3 tests/startover_test.py /absolute/path/to/index.html"""
import sys
from playwright.sync_api import sync_playwright
html = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(); pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"file://{html}"); pg.wait_for_timeout(800)
    assert pg.evaluate("creator.open"), 'the creator should open on a first visit'
    pg.click('[data-originals]'); pg.wait_for_timeout(300)
    pg.evaluate("void 0; stray.coat = KITTEN_COATS[0]; const k = addKittenToFamily('Kitten', 'floor', 70, 178, 'sit_relax'); finishNaming(k, 'Pip'); bonds['0-2'] = 0.95; saveState(); 0;")
    pg.reload(); pg.wait_for_timeout(800)
    before = pg.evaluate("[cats.length, +bonds['0-2'].toFixed(2), creator.open]")
    print('before:', before); assert before == [4, 0.95, False]
    pg.evaluate("void 0; toggleSettings(true); 0;")
    pg.click('#btnStartOver')
    assert pg.evaluate("document.getElementById('startOverLabel').textContent") == 'Sure? Click again'
    pg.wait_for_timeout(5300)
    assert pg.evaluate("document.getElementById('startOverLabel').textContent") == 'Start over', 'it should disarm after 5 seconds'
    pg.click('#btnStartOver'); pg.wait_for_timeout(200)
    with pg.expect_navigation(): pg.click('#btnStartOver')
    pg.wait_for_timeout(800)
    after = pg.evaluate("[creator.open, cats.length, stray.adopted]")
    print('after start over:', after); assert after == [True, 0, False]
    print('errors:', errs); assert not errs
    print('OK')
    b.close()
