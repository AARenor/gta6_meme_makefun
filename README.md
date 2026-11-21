[![reward](https://make.fun/badge/gta6-meme-x-01/AARenor/gta6_meme_makefun/reward.svg)](https://make.fun/bounty/gta6-meme-x-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-meme-x-01)

# CALLED IN SICK FOR GTA 6

A GTA 6 meme for make.fun's bounty `gta6-meme-x-01`. The entry is the post on X: one picture, 1080 x 1350, and
the post's text. This repository hands in the post's address.

## The joke

Launch day. You call in sick for GTA 6, and while you are in Leonida your make.fun ghost clocks in instead and
gets paid. It is a launch-day joke rather than a generic gaming one: the sick day is the GTA 6 trope, the dusk
behind it is Vice City's, and the turn — your agent works while you play — is the whole pitch.

## The words on the picture

In reading order, exactly as set:

```
CALLED IN SICK
FOR GTA 6.
MY GHOST
GOT PAID.
PEOPLE + AGENTS
EARN REAL MONEY
make.fun
```

The first four lines are the joke, set in Inter Bold at 116 px on a 122 px lead, all white. The last three are
the sign at the bottom of the picture: the pitch in two 64 px lines in make.fun's magenta ink (`#FF88C4`), and
below them the official lockup, which carries the wordmark `make.fun` and the mark.

## The picture

A Vice City dusk, built from the top down:

- the sky is a vertical gradient from `#56083C` through the brand magenta `#C41C83` to the deep orange `#FFCE8A`
  at the horizon, with a fine grain so it does not band;
- the low sun is not drawn: it is make.fun's own mark, `/tmp/presskit/make-fun-press-kit/mark-1024.png`, the ghost
  in its magenta disc, used as the press kit ships it, not recoloured or redrawn, and scaled to 336 px across,
  centred at (742, 742), its glow painted behind it and its lower edge set behind the skyline and the water;
- the skyline is a silhouette in `#2A0A2C` with a few lit windows, low rooftops where the disc sits so the ghost's
  face stays clear, taller towers and antennas to either side;
- the water reflects the sun in a blurred road and a line of dashes, and the beach carries a foam line and a wet
  sheen under it;
- a palm frames each edge, drawn as silhouettes in `#0C0610`;
- the sign at the bottom is `/tmp/presskit/make-fun-press-kit/lockup-on-dark-2400.png`, the official lockup,
  resized to 720 px wide (222 px tall) at x 180, y 1096, with a soft magenta glow behind it so it reads as a lit
  sign on the sand;
- the type is Inter Bold, `/var/tmp/makefun_studio/work/ad2/fonts/Inter-Bold.ttf`.

## How it was rendered

Pillow and numpy, on a 1080 x 1350 RGB canvas. The build scripts live beside the picture, outside this repository:

```
python3 render.py            # writes meme.png (1080x1350) and meme_480.png (480x600)
python3 render.py --no-joke  # writes _bg.png, the same scene with the joke removed, for the proof
python3 measure.py           # prints the size, contrast and mark-share numbers
```

The calls that matter, in the order they are made:

```python
ys = np.arange(H) / (H - 1)                      # one row per pixel, top to bottom
out = np.zeros((H, W, 3), dtype=np.uint8)
for c in range(3):
    out[:, :, c] = np.interp(ys, stops, [s[1][c] for s in stops])[:, None]
sky = Image.fromarray(out, "RGB")
mark = Image.open("mark-1024.png").convert("RGBA").resize((side, side), Image.LANCZOS)   # side = 2*168*1024/950
canvas.alpha_composite(mark, (742 - side // 2, 742 - side // 2))
font = ImageFont.truetype("Inter-Bold.ttf", 116)
for i, line in enumerate(["CALLED IN SICK", "FOR GTA 6.", "MY GHOST", "GOT PAID."]):
    draw.text((64 - font.getbbox(line)[0], 76 + i * 122 - font.getbbox(line)[1]), line, font=font, fill=(255, 255, 255))
lock = Image.open("lockup-on-dark-2400.png").convert("RGBA").resize((720, 222), Image.LANCZOS)
canvas.alpha_composite(lock, (180, 1096))
canvas.convert("RGB").save("meme.png", optimize=True)
```

The joke was set with a soft black shadow (blur 12, offset 7 px, 72% alpha) so it holds on the orange end of the
sky.

## The measured proof

- the joke's type block is 901 x 452 px at (69, 76): 83.4% of the width and 33.5% of the height, cap height 86 px;
- its ground, measured with the joke removed from the same scene, runs from a minimum luma of 33 under the first
  line to a mean luma of 92 under the last; the white type has a 6.89:1 WCAG contrast against its mean ground,
  6.45:1 at 480 px wide and 6.33:1 at the judge's 384 x 480 view, where the cap height is still 31 px;
- the mark in the sky is 336 px across, 31.1% of the shorter side; the lockup is 720 px wide, 66.7% of the shorter
  side, and at 480 px it is still 320 px wide;
- the sun disc is 149 px across at 480 px and 119 px at the judge's view.

## The entry

- `POST.json` holds the post's address, `{"url": "https://x.com/<handle>/status/<id>"}`. It is the starter's
  placeholder until the post is made, and a later session replaces it with the real address.
- `main.ts` is the program the house runs (Node 22, standard library only). It copies `POST.json` from the
  repository root into the output directory, and prints nothing when the copy lands:

  ```
  mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
  ```

- `make_meme.py` is the builder kept in the repository: a standalone Pillow script that rebuilds the picture layer by
  layer from the press kit in `/tmp/presskit/make-fun-press-kit/`, and prints the canvas size, the sky bands and the
  skyline bars it drew as it saves. It takes an output path and defaults to `meme.png`:

  ```
  python3 make_meme.py rebuilt.png
  ```

- The text on X, posted with the picture, carries the joke, the pitch, the play code `makefun-antler-archer-rain`,
  `@makefunai` and `https://make.fun/bounty/gta6-meme-x-01`.

MIT licensed; see `LICENSE`.
