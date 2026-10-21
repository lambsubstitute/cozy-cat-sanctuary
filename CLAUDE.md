# Cozy Cat Sanctuary

A cosy pixel-art living room where the player's own cats live their lives. It's a hobby browser game, live at https://lambsubstitute.github.io/cozy-cat-sanctuary/ (GitHub Pages, deployed from `main`). `README.md` explains the game itself.

## The shape of it

- **Everything is in `index.html`**: the page at the top, then one big script. There's no build step, no bundler, no package.json, and no image or sound files. Keep it that way: open the file in a browser and it runs.
- The only outside resources are the Tailwind play CDN and two Google fonts (Press Start 2P, VT323), plus Open-Meteo for the optional real weather and GoatCounter (`gc.zgo.at`) for visitor counts and play-time events, at the very end of the page. Don't add others.
- The script is split into commented sections with capitalised banners (TIME OF DAY, ROOM NAVIGATION, THE CAT TUNNEL, 16-BIT ART, MEMORY...). Find your way by those, not by line numbers, which drift:

  ```sh
  grep -nE '^\s*// [A-Z0-9][A-Z0-9 &:,()-]{5,}' index.html
  ```

- The cats are instances of `PixelCat`; behaviour is a state machine (`cat.state`), and `getPose()` turns state into which sprite to draw.

## Rules that keep it working

- **Room pixels.** The room is 320 x 190 room pixels (`W`, `H`) and every position, route and hit box uses them. The canvas is drawn at `RES = 2`, purely for finer art.
- **Never move furniture, ledges or surfaces.** The cats' routes (`NAV_EDGES` and the surfaces in ROOM NAVIGATION) depend on exact positions, and the simulation test checks every jump against them.
- **Saves must keep loading.** Progress lives in `localStorage` under `cozyCatSanctuary.v1` (and `cozyCatSanctuary.weather` for the weather setting). If you add to the save, give old saves a sensible default rather than breaking them; `tests/household_persist.py` checks old saves still load.
- **Phones matter.** There's a touch layout (portrait and landscape). Anything that changes the page around the canvas needs `tests/touch_test.py` and `tests/mobile_shot.py`.
- **Any artwork or animation change: use the `cozy-cat-art` skill** in `.claude/skills/cozy-cat-art/`. It has the style, the drawing toolkit (`painter`, `spriteFX`, `catMap`, `catHeadSide`...), the cat palette rules, the strobe rule for patterns on moving sprites, and how to check art before it ships.

## Testing

The tests drive the page in headless Chromium with Playwright, with a seeded `Math.random`, a fixed clock and manual frame stepping. Full details are in `tests/README.md`.

```sh
pip install playwright pillow --break-system-packages && python3 -m playwright install chromium   # once
export PYTHONPATH=$PWD/tests
GAME=$PWD/index.html                                      # the scripts need an absolute path

EXTRA=1 python3 tests/sim_test.py $GAME 36000 300 1 2 > run.txt   # ten minutes of cat life, two seeds
python3 tests/sum2.py run.txt                             # overlaps, illegal positions, bad jumps, errors: all must be 0
```

- Run the simulation after any change to behaviour, movement, navigation or anything a cat can stand on. It takes a few minutes, so run it in the background.
- Focused checks: `creator_flow.py`, `household_persist.py`, `startover_test.py`, `livewx_test.py`, `moon_click.py`, `stray_batch.py`, `touch_test.py`. Run the ones that touch what you changed.
- For artwork, render it and look: `tests/pose_sheet.py` (every pose, four coats) and `tests/frame_strip.py` (one pose frame by frame), and `tests/symbol_sheet.py` for the hearts, Zs, "!"s and bubbles. Any change to `spriteFX` or the cat drawing also needs `tests/noise_test.py`.
- Beef's browser adds anti-fingerprinting noise to canvas read-backs, and a headless test browser doesn't. If something looks fine in tests but he sees flicker, suspect that first (`FX_NOISY` in the 16-BIT ART section).
- Hooks the tests use, set before the page loads: `window.__skipCreator` (skip choosing cats), `window.__household` (a list of cat looks to move in), `window.__fakeNow` (a fixed time), and an overridden `requestAnimationFrame` so the test steps each frame. (The seed and the time come from `?seed=` and `?fake=` on the page address, read by the tests' own setup script, not by the game.)
- Test output (`*.png`, `*.txt`) is git-ignored; keep scratch files out of the repo.

## Working with Beef

Beef owns the game.

- Show, don't describe: send before and after screenshots (pose sheets, frame strips, phone screenshots) as soon as there's something to see, so he can redirect early. Keep write-ups short and practical.
- **Commit and push only when he says to.** Pushing to `main` deploys to the live site.
- After a push, confirm GitHub Pages has picked up the new version, then remind him to run `git pull` in his own copy (`Documents/projects/cozy-cat-sanctuary` on his Mac).
- Commit messages: a plain-English title saying what changed for the player, then a short body on what and why.
- Keep `README.md` (what's in the room, the "Making changes" section) and `tests/README.md` true when you change what they describe. They're written in plain British English, for a player as much as a programmer.
