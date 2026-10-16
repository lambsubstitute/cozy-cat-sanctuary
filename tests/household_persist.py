import sys, json
from playwright.sync_api import sync_playwright
html = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    # 1. an old save (from before households) with an adopted kitten
    ctx = b.new_context(); pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"file://{html}"); pg.wait_for_timeout(500)
    pg.evaluate("""void 0; localStorage.setItem(SAVE_KEY, JSON.stringify({ v: 1, savedAt: Date.now(), cats: [{mice: 2, needs: {food: .5, energy: .5, love: .5}}, {mice: 0}, {mice: 1}, {mice: 0}],
        kitten: { name: 'Puddle', coat: 'magpie', sex: 'm', wet: true }, diary: [{t: Date.now(), icon: '🏡', text: 'old entry'}], bonds: {'0-2': 0.8} })); 0;""")
    pg.reload(); pg.wait_for_timeout(800)
    print('legacy:', pg.evaluate("[creator.open, cats.map(c => c.name + (c.small ? '(small)' : '')), cats[0].miceCaught, householdIsOriginal, stray.adopted, document.querySelectorAll('#catCards > div').length, WALL_PORTRAITS.length]"))
    pg.evaluate("void 0; saveState(); 0;")
    pg.reload(); pg.wait_for_timeout(800)
    print('legacy resaved:', pg.evaluate("[cats.map(c => c.name), householdIsOriginal, stray.adopted, Object.keys(JSON.parse(localStorage.getItem(SAVE_KEY))).includes('household')]"))
    ctx.close()
    # 2. a custom pair, then the stray kitten joins as the third
    ctx = b.new_context(); pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"file://{html}"); pg.wait_for_timeout(500)
    pg.click('[data-count="2"]'); pg.click('[data-next]'); pg.click('[data-next]'); pg.wait_for_timeout(300)
    names = pg.evaluate("cats.map(c => c.name)")
    pg.evaluate("void 0; stray.next = globalTick + 5; 0;")
    pg.wait_for_timeout(200)
    # run the page's own loop for a bit by stepping time quickly via the stray timer
    pg.evaluate("void 0; spawnStray(); stray.phase = 'sit'; stray.t = 40; letStrayIn(); 0;")
    pg.wait_for_timeout(1500)
    pg.evaluate("void 0; if (nameModalCat) { document.getElementById('nameInput').value = 'Dot'; confirmKittenName(); } 0;")
    pg.wait_for_timeout(300)
    print('pair + stray:', pg.evaluate("[cats.map(c => c.id + ':' + c.name + (c.small ? '(small)' : '')), document.querySelectorAll('#catCards > div').length, WALL_PORTRAITS.map(w => w.cat + '@' + w.x)]"))
    pg.reload(); pg.wait_for_timeout(800)
    print('after reload:', pg.evaluate("[cats.map(c => c.name + (c.isKitten ? '(kitten)' : '')), stray.adopted, stray.sex, stray.coat && stray.coat.id, householdIsOriginal]"))
    # 3. start over: back to the creator
    pg.click('#btnStartOver'); pg.wait_for_timeout(200)
    with pg.expect_navigation(): pg.click('#btnStartOver')
    pg.wait_for_timeout(800)
    print('start over:', pg.evaluate("[creator.open, cats.length]"))
    print(errs)
    b.close()
