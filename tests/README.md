# Tests

These scripts drive `index.html` in headless Chromium with [Playwright](https://playwright.dev/python/). They seed `Math.random`, fix the clock, and step the animation frame by frame, so a run is repeatable and ten minutes of cat life takes a minute or two.

## Setup

```sh
pip install playwright pillow
playwright install chromium
```

Run them from the repo root, passing the **absolute** path to `index.html`:

```sh
export PYTHONPATH=$PWD/tests
GAME=$PWD/index.html
```

## The main simulation

`sim_test.py <html> <frames> <trigger_every> <seed> [<seed>...]` fast-forwards the game (60 frames = 1 second) and checks every frame that no two cats overlap, nobody stands off their surface, every jump follows the navigation graph, and nothing teleports. It also checks nobody on the floor stands in the tunnel's way, and counts trips through the tunnel and what the cats got up to inside it. With `EXTRA=1` it also fires random room events (box, tunnel, feeder, catnip, treats, brushing, yarn and so on) every `trigger_every` frames.

```sh
EXTRA=1 python3 tests/sim_test.py $GAME 36000 300 1 2 > run.txt
python3 tests/sum2.py run.txt          # one line per seed: overlaps, illegal positions, bad jumps, errors
```

Options, as environment variables:

- `HOUSEHOLD='[{"name":"Solo","coat":"black","pattern":"solid","eyes":"gold","character":"lazy","voice":"deep","age":"adult"}]'` runs a custom household instead of Moe, Mr Mews and Joe.
- `SETUP='currentWeatherIdx = 5; updateOutside(true);'` runs any JavaScript first (here: a thunderstorm).

`run_fake.py <html> <frames> <trigger_every> <seed> <ISO time>` is the same at a chosen date and time, for example Bonfire Night: `2026-11-05T19:30:00`.

## Focused checks

| Script | Checks |
| --- | --- |
| `dither.py <html> <frames> <seed> [time] [setup]` | Cats flickering or shuffling on the spot (zoomies laps can show up as harmless "stuck" events) |
| `trace_stuck.py <html> <seed> <time> <frame> <cat> <n>` | Prints one cat's position and plan frame by frame, to investigate a dither event |
| `stray_batch.py <html> <first seed> <last seed>` | Lets the stray kitten in at different moments; reports any cat stuck on the windowsill |
| `tunnel_corner.py <html>` | A cat in the corner beside the right-hand end of the tunnel gets out within a second or two, with the zoomies and walking across the room (it used to try going round the front of the tunnel and shuffle on the spot there) |
| `overlap_sep.py <html>` | Two cats squashed together on a ledge can walk apart |
| `household_persist.py <html>` | Old saves still load; a stray can join a custom household; Start over brings back the creator |
| `creator_flow.py <html>` | Designing two cats in the creator, then saving and reloading |
| `startover_test.py <html>` | Settings → Start over forgets everything |
| `moon_click.py <html>` | Clicking the moon at night summons the UFO; clicking the UFO sends it off |
| `livewx_test.py <html>` | Real local weather, with the weather service mocked: town search, every kind of weather, going offline, and reloading |
| `pose_sheet.py <html> <out.png> [pose ...]` | Not a check: draws every cat pose (or the ones you name) for four different coats through the game's real drawing code, side by side, for looking over the artwork (at whatever resolution the canvas is drawn) |
| `symbol_sheet.py <html> <out.png> [night]` | Not a check: draws every floating symbol (hearts, Zs, sparkles, stars, "!", notes and the little bits) at three ages, every speech-bubble picture, and a few dream bubbles, on the real room, by day or by night, for looking over |
| `noise_test.py <html> [seed]` | Patterned cats sit still in browsers that add anti-fingerprinting noise to canvas read-backs (Safari, Brave and Firefox can): fakes the noise, sits a tabby, a tortie and a calico down, and checks nothing on their bodies changes from frame to frame. The noise is seeded and the seed printed, so a failure can be run again exactly by passing it back |
| `frame_strip.py <html> <out.png> <pose> [frames] [step] [coat] [pattern] [facing]` | Not a check: one cat in one pose over consecutive frames, side by side, following the cat as it moves (`walk` with a step of 0.5, say). For looking over animations: the markings should stay put on its body, or it strobes |
| `touch_test.py <html>` | Phones: tapping cats (and just missing them), treats, brushing and the laser with a finger, hide and seek, the screensaver, the room staying pinned while you scroll, turning the phone sideways, and the desktop layout unchanged |

## Phone layout

`touch_test.py` and `mobile_shot.py` need the real page styling, so they let Tailwind and the Google fonts load from the internet (and block everything else). To run them offline, see `assets.py`.

`mobile_shot.py <html> <out_prefix> <setup_js> [WxH ...]` takes full-page screenshots at phone sizes and reports any sideways overflow, for example `python3 tests/mobile_shot.py $GAME shot '' 390x844 844x390`.
