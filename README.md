# Cozy Cat Sanctuary

A cosy pixel-art living room for your own cats. They nap by the fire, chase the laser and the mouse, watch the birds, knock things off the mantelpiece, dream, make friends, and react to the weather outside, which can be the real weather where you live.

**Play it:** https://lambsubstitute.github.io/cozy-cat-sanctuary/

Everything is in one file, `index.html`. There's nothing to install or build: open it in a browser and it runs.

## What's in the room

- **Your own cats.** On your first visit you choose how many cats live here (1 to 4) and design each one: name, coat, pattern, eyes, character, voice, and grown-up or kitten. Or move in with the originals: Moe, Mr Mews and Joe.
- **A life of their own.** Naps, zoomies, grooming, cuddle piles, play-fights, games of chase, knocking things over, asking for food and fuss. Each cat has needs (food, energy, love) and a mood.
- **Your hand.** Pet, give treats, brush, or get the laser pointer out. Release a mouse, toss the yarn, put down a cardboard box, sprinkle catnip, fill the bird feeder, play hide and seek.
- **The crinkly tunnel** by the hearth. Cats dash through it, lurk inside to ambush whoever settles nearby, pop their heads up through the peephole on top (and get bopped by a friend), nap in it with a tail sticking out, and hide in it. In a game of chase, the one being chased will shoot through it, while the chaser follows... or nips round to lie in wait at the other end. Click it for a rustle; put it out or away from the activities panel.
- **The view outside.** Real time of day, seasons (with Halloween, Bonfire Night and Christmas), and either made-up weather or **the real weather where you live** (Settings ⚙️). Birds and squirrels by day; an owl, moths, a fox, shooting stars and the very occasional UFO at night. Thunderstorms and fireworks send the nervous ones under the sofa.
- **Friendships and dreams.** Pairs of cats grow closer and become best friends. Sleeping cats dream about what happened today.
- **A stray kitten** may turn up at the window, soaked if it's raining. Let it in and it joins the family.
- **The diary, photos and screensaver.** Everything memorable is written in the diary; snap a polaroid; or go full screen and just watch.

**On a phone** the room stays pinned to the top of the screen while you scroll through the buttons, so you can always see what the cats make of them. Tap to pet, drag a finger to aim the laser or brush a cat. Turn the phone sideways and the room fills the screen with your hand tools beside it.

Everything is remembered in your browser (local storage) between visits. **Settings ⚙️ → Start over** wipes it and lets you choose your cats again.

## Real local weather

In Settings ⚙️, choose "The real weather where I live" and search for your town (or use your location). The window then shows the real rain, snow, fog, cloud, storms, temperature and sunrise/sunset, checked every 15 minutes. Weather data comes from [Open-Meteo](https://open-meteo.com/) (free, no key needed).

It works on the GitHub Pages link above, or when you open `index.html` straight from your computer. It doesn't work inside a Claude artifact, because those pages aren't allowed to go online.

## Making changes

The whole game is `index.html`: the HTML at the top, then one script holding the room, the cats and everything else, in clearly commented sections. Edit it, open it in a browser, and refresh.

**The look is 16-bit** (think Super Nintendo), drawn at double resolution. The room is measured in 320 × 190 "room pixels" (every position, route and piece of furniture uses those), but the canvas is 640 × 380 (`RES = 2`), so the art can have details half a room pixel across: finer textures, thinner outlines, smoother curves and gradients, and faces with eyes, noses and whiskers. The **16-BIT ART** section holds the toolkit: `painter` (an offscreen picture measured in room pixels but painted a fine pixel at a time), hue-shifted shading ramps (shadows go cool and purple, highlights warm and golden), ordered dithering for gradients, wood, brick, velvet and carpet textures, and outlines. The parts of the room that don't move are painted once into an offscreen picture (`roomBackdrop`). Everything that moves goes through `spriteFX`, which draws each sprite twice at once: at room resolution, blown up with the EPX (Scale2x) pixel-art scaler so its edges come out rounded, and at full resolution for the fine details added with `hd`. It then adds the light along the top, the shadow underneath, furry edges where coat colours meet and a fine dark outline, so every cat pose gets the same treatment without being redrawn by hand. Tails, legs and paws are drawn straight onto the fine grid from round dabs of colour (`fineDabs`, `catTail`, `catLeg`), so they curve and move half a pixel at a time: walking cats step in a proper gait with their paws lifting (`catGait`), tails sway, sleeping cats breathe, and the sprites glide half a pixel at a time. Calico and tortoiseshell coats get their patches from `coatPattern`. Furniture keeps its exact positions, because the cats' routes depend on them.

The house rules for the artwork (the style, the tools, the cat palette, the "strobe rule" for patterns on moving sprites, and how to check new art before it ships) are written up for Claude as a skill in [.claude/skills/cozy-cat-art/SKILL.md](.claude/skills/cozy-cat-art/SKILL.md), which Claude Code picks up whenever it works in this folder.

Libraries are loaded from CDNs: [Tailwind CSS](https://tailwindcss.com/) (play CDN) for the page styling, and the [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P) and [VT323](https://fonts.google.com/specimen/VT323) fonts from Google Fonts.

## Tests

The `tests/` folder has automated checks that run the game headlessly in Chromium with a fixed random seed and fast-forward it frame by frame, checking that cats never overlap, never stand anywhere they shouldn't, only make legal jumps, and never throw errors. See [tests/README.md](tests/README.md).

Built with Claude.
