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

`sim_test.py <html> <frames> <trigger_every> <seed> [<seed>...]` fast-forwards the game (60 frames = 1 second) and checks every frame that no two cats overlap, nobody stands off their surface, every jump follows the navigation graph, and nothing teleports. With `EXTRA=1` it also fires random room events (box, feeder, catnip, treats, brushing, yarn and so on) every `trigger_every` frames.

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
| `overlap_sep.py <html>` | Two cats squashed together on a ledge can walk apart |
| `household_persist.py <html>` | Old saves still load; a stray can join a custom household; Start over brings back the creator |
| `creator_flow.py <html>` | Designing two cats in the creator, then saving and reloading |
| `startover_test.py <html>` | Settings → Start over forgets everything |
| `moon_click.py <html>` | Clicking the moon at night summons the UFO; clicking the UFO sends it off |
| `livewx_test.py <html>` | Real local weather, with the weather service mocked: town search, every kind of weather, going offline, and reloading |
