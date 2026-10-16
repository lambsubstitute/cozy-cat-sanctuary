"""Fast-forward the cat sanctuary headlessly and check movement rules every frame.

usage: python3 sim_test.py <html> <frames> <trigger_every> <seed> [<seed> ...]
"""
import json, sys
from playwright.sync_api import sync_playwright

INIT = r"""
(() => {
  // Seeded random so runs are reproducible
  let s = (window.__seed = Number(new URLSearchParams(location.search).get('seed') || 1)) >>> 0;
  Math.random = function () {
    s |= 0; s = s + 0x6D2B79F5 | 0;
    let t = Math.imul(s ^ s >>> 15, 1 | s);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
  // A fixed moment in time, so the day/night cycle doesn't depend on when the test runs
  window.__fakeNow = Date.parse(new URLSearchParams(location.search).get('fake') || '2026-10-14T15:00:00');
  // Skip choosing cats: move straight in with the originals
  window.__skipCreator = true;
  // Manual frame stepping
  window.__rafCb = null;
  window.requestAnimationFrame = cb => { window.__rafCb = cb; return 1; };
  window.__step = () => { const cb = window.__rafCb; window.__rafCb = null; if (cb) cb(performance.now()); };
})();
"""

RUN = r"""
([frames, triggerEvery]) => {
  const legal = new Set(NAV_EDGES.map(e => e.from + '>' + e.to));
  const st = { overlapFrames: 0, worst: 99, worstInfo: null, illegal: [], teleports: [], noJumpChanges: [],
               badJumps: [], jumps: {}, airSpeedMax: 0, visits: {}, longestSameState: [0,0,0], longestInfo: [null,null,null],
               longestWait: 0, replansGaveUp: 0, triggers: {}, errors: [] };
  const prev = cats.map(c => ({ x: c.x, y: c.y, s: c.surface, nav: !!c.nav }));
  const from = cats.map(c => c.surface);
  const lastChange = cats.map(() => 0);
  const lastState = cats.map(c => c.state + '|' + !!c.nav);
  const trig = { snacks: triggerSnacks, yarn: triggerTossYarn, cuddle: triggerCuddlePile, window: triggerWindowWatch };
  if (window.__extraTriggers && typeof triggerBox === 'function') Object.assign(trig, { box: triggerBox, feeder: triggerFeeder, tidy: triggerTidyUp });
  if (window.__extraTriggers && typeof triggerCatnip === 'function') Object.assign(trig, {
    catnip: triggerCatnip,
    toss: () => tossTreat(80 + Math.random() * 200, 150 + Math.random() * 30),
    treat: () => giveTreat(cats[Math.floor(Math.random() * cats.length)]),
    brush: () => { const c = cats[Math.floor(Math.random() * cats.length)]; if (c.canBeHandled()) { startBrushing(c); for (let k = 0; k < 5; k++) c.brushStroke(); endBrushing(); } },
    bag: () => { setTool('treat'); setTool('pet'); }
  });
  st.boxOverlap = 0; st.boxInfo = null; st.boxes = 0; st.knocks = 0; st.birds = 0;
  let boxWas = false, birdWas = false; const knockWas = {};
  const trigNames = Object.keys(trig);
  for (let f = 0; f < frames; f++) {
    if (triggerEvery && f % triggerEvery === triggerEvery - 1) {
      const n = trigNames[Math.floor(Math.random() * trigNames.length)];
      st.triggers[n] = (st.triggers[n] || 0) + 1;
      trig[n]();
    }
    try { window.__step(); } catch (e) { st.errors.push(f + ': ' + e.message); break; }
    cats.forEach((c, i) => {
      const p = prev[i];
      if (c.surface) {
        const S = SURFACES[c.surface];
        const bad = S.kind === 'area'
          ? (c.y < S.y1 - 1e-6 || c.y > S.y2 + 1e-6 || c.x < S.x1 - 1e-6 || c.x > S.x2 + 1e-6)
          : (Math.abs(c.y - S.y) > 1e-6 || c.x < S.x1 - 1e-6 || c.x > S.x2 + 1e-6);
        if (bad && st.illegal.length < 10) st.illegal.push({ f, cat: c.name, s: c.surface, x: c.x, y: c.y });
      }
      if (p.s && c.surface) {
        const d = Math.hypot(c.x - p.x, c.y - p.y);
        if (d > ((c.pounce || p.pounce) ? 4 : 2.1) && st.teleports.length < 10) st.teleports.push({ f, cat: c.name, d, s: c.surface });
        if (p.s !== c.surface && st.noJumpChanges.length < 10) st.noJumpChanges.push({ f, cat: c.name, from: p.s, to: c.surface });
      }
      if (!c.surface) st.airSpeedMax = Math.max(st.airSpeedMax, Math.hypot(c.x - p.x, c.y - p.y));
      if (p.s && !c.surface) from[i] = p.s;
      if (!p.s && c.surface) {
        const k = from[i] + '>' + c.surface;
        if (!new Set(NAV_EDGES.map(e => e.from + '>' + e.to)).has(k)) st.badJumps.push({ f, cat: c.name, k });
        st.jumps[k] = (st.jumps[k] || 0) + 1;
      }
      if (p.nav && !c.nav && c.surface) {
        const k = c.surface + ':' + c.state;
        st.visits[k] = (st.visits[k] || 0) + 1;
      }
      if (c.nav) st.longestWait = Math.max(st.longestWait, c.nav.waiting);
      const key = c.state + '|' + !!c.nav;
      if (key !== lastState[i]) { lastState[i] = key; lastChange[i] = f; }
      if (f - lastChange[i] > st.longestSameState[i]) { st.longestSameState[i] = f - lastChange[i];
        st.longestInfo[i] = { since: lastChange[i], key, s: c.surface, x: +c.x.toFixed(1), y: +c.y.toFixed(1), label: c.getStateDisplay().label,
          await: c.awaitingPartner ? c.awaitingPartner.name + ':' + (c.awaitingPartner.nav ? c.awaitingPartner.nav.label + '/' + c.awaitingPartner.nav.waiting : 'nonav') : null }; }
      prev[i] = { x: c.x, y: c.y, s: c.surface, nav: !!c.nav, pounce: !!c.pounce };
    });
    if (typeof box !== 'undefined') {
      if (box.active && !boxWas) st.boxes++;
      boxWas = box.active;
      if (bird.active && !birdWas) st.birds++;
      birdWas = bird.active;
      KNOCKABLES.forEach(k => { if (k.state === 'falling' && knockWas[k.id] !== 'falling') st.knocks++; knockWas[k.id] = k.state; });
      if (box.active) cats.forEach(c => {
        if (c.surface === 'floor' && spaceOverlap('floor', c.x, c.y, box.x, box.y) < 1 - 1e-6) {
          st.boxOverlap++;
          if (!st.boxInfo) st.boxInfo = { f, cat: c.name, x: c.x, y: c.y, bx: box.x, by: box.y, state: c.state, nav: !!c.nav };
        }
      });
    }
    for (let i = 0; i < cats.length; i++) for (let j = i + 1; j < cats.length; j++) {
      const a = cats[i], b = cats[j];
      if (!a.surface || a.surface !== b.surface) continue;
      const partners = a.partnerCat === b || b.partnerCat === a;
      const e = spaceOverlap(a.surface, a.x, a.y, b.x, b.y);
      const limit = 1;
      if (e < limit - 1e-6) {
        st.overlapFrames++;
        if (e < st.worst) { st.worst = e; st.worstInfo = { f, a: a.name, b: b.name, s: a.surface,
          ax: +a.x.toFixed(1), ay: +a.y.toFixed(1), bx: +b.x.toFixed(1), by: +b.y.toFixed(1),
          as: a.state, bs: b.state, anav: !!a.nav, bnav: !!b.nav }; }
      }
    }
  }
  st.final = cats.map(c => ({ name: c.name, s: c.surface, x: +c.x.toFixed(1), y: +c.y.toFixed(1), state: c.state }));
  return st;
}
"""

import os
def run(html, frames, every, seed):
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.add_init_script(INIT)
        if os.environ.get("HOUSEHOLD"): pg.add_init_script("window.__household = " + os.environ["HOUSEHOLD"] + ";")
        pg.goto(f"file://{html}?seed={seed}")
        pg.wait_for_function("window.__rafCb !== null")
        pass
        if os.environ.get("EXTRA"): pg.evaluate("window.__extraTriggers = true")
        if os.environ.get("SETUP"): pg.evaluate("void 0;" + os.environ["SETUP"] + "; 0;")
        res = pg.evaluate(RUN, [frames, every])
        res["pageErrors"] = errors
        b.close()
        return res

if __name__ == "__main__":
    html, frames, every = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for seed in sys.argv[4:]:
        r = run(html, frames, every, int(seed))
        print(f"=== seed {seed}: {frames} frames (~{frames/60/60:.1f} min) ===")
        print(json.dumps(r, indent=1))
