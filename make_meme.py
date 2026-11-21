#!/usr/bin/env python3
"""make_meme.py — rebuild the CALLED IN SICK picture for make.fun's `gta6-meme-x-01`.

The joke the picture carries: on GTA 6 launch day you call in sick, and while you
are away in Leonida your make.fun ghost clocks in instead and gets paid.  The
posted meme sets that joke over a Vice City dusk — four heavy white lines, a
magenta sun, a low skyline, two palms and the pitch signed along the sand.

This script rebuilds the posted 1080 x 1350 meme (meme.png) from scratch with
Pillow.  It draws the picture in layers, top of the stack last: the dusk sky and
its sun, the water and the skyline, the joke, the pitch, and finally the press
kit's own mark and lockup, pasted at the sizes the posted picture gives them and
never recoloured or stretched.

Usage:
    python3 make_meme.py [output.png]        # default: meme.png
"""

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# --- the board -------------------------------------------------------------

CANVAS = (1080, 1350)           # the size the post is made at
WIDTH, HEIGHT = CANVAS

# --- brand colours ---------------------------------------------------------

MAGENTA = (196, 28, 131)        # make.fun magenta, #C41C83
TEXT_WHITE = (255, 255, 255)    # the joke
TEXT_PINK = (255, 136, 196)     # #FF88C4, the pitch
PLUM_TOP = (86, 8, 60)          # #56083C, the top of the dusk
HORIZON_GOLD = (255, 206, 138)  # #FFCE8A, the deep orange at the horizon
SUN_CORE = (255, 240, 208)      # the bright disc the mark sits on
SUN_GLOW = (255, 156, 96)       # the warm halo around it
SILHOUETTE = (42, 10, 44)       # #2A0A2C, the skyline
PALM_INK = (12, 6, 16)          # #0C0610, the palms
WINDOW_LIGHT = (255, 214, 160)  # the lit windows
WATER_STOPS = ((0.0, (122, 21, 80)), (1.0, (32, 8, 30)))
SAND_STOPS = ((0.0, (61, 11, 41)), (1.0, (20, 5, 22)))
FOAM = (255, 217, 174)
REFLECTION = (255, 216, 170)

# --- the picture's measurements, as the posted meme holds them -------------

HORIZON = 918                   # where the sky meets the water
SHORE = 1090                    # where the water meets the sand
SUN_X, SUN_Y = 742, 742         # the centre of the mark in the sky
SUN_RADIUS = 168                # a 336 px disc across
SUN_HALO = 430                  # how far the warm glow reaches

JOKE_X, JOKE_Y = 64, 76         # the joke's left edge and first cap line
JOKE_SIZE, JOKE_LEAD = 116, 122  # Inter Bold, tight leading
JOKE_LINES = ("CALLED IN SICK", "FOR GTA 6.", "MY GHOST", "GOT PAID.")

PITCH_Y = 936                   # the first pitch line, under the skyline
PITCH_SIZE, PITCH_LEAD = 64, 70
PITCH_LINES = ("PEOPLE + AGENTS", "EARN REAL MONEY")

MARK_WIDTH = 336                # the press kit mark, as pasted in the sky
LOCKUP_X, LOCKUP_Y = 180, 1096  # the lockup, 720 x 222, on the sand
LOCKUP_WIDTH, LOCKUP_HEIGHT = 720, 222

FONT_PATH = Path("/var/tmp/makefun_studio/work/ad2/fonts/Inter-Bold.ttf")
PRESS_KIT = Path("/tmp/presskit/make-fun-press-kit/")
MARK_FILE = "mark-on-dark-1024.png"
LOCKUP_FILE = "lockup-on-dark-2400.png"

SEED = 20261121                 # the same skyline on every run


# --- small tools -----------------------------------------------------------


def _sample(stops, t):
    """The colour at position ``t`` (0..1) along a list of colour stops."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (pos_a, colour_a), (pos_b, colour_b) in zip(stops, stops[1:]):
        if t <= pos_b:
            span = (t - pos_a) / (pos_b - pos_a) if pos_b > pos_a else 0.0
            return tuple(
                round(start + (end - start) * span)
                for start, end in zip(colour_a, colour_b)
            )
    return stops[-1][1]


def _vertical_fill(size, stops):
    """One horizontal band per row, so a gradient never bands harder than 1 px."""
    width, height = size
    image = Image.new("RGB", size)
    pen = ImageDraw.Draw(image)
    last = max(height - 1, 1)
    for y in range(height):
        pen.line([(0, y), (width, y)], fill=_sample(stops, y / last))
    return image


def _radial(radius, colour, peak=255, falloff=2.0):
    """A soft round glow of ``colour`` that fades to nothing at ``radius``."""
    core = 160
    mask = Image.new("L", (core, core), 0)
    pen = ImageDraw.Draw(mask)
    half = core / 2.0
    for step in range(96, 0, -1):
        frac = step / 96.0
        pen.ellipse(
            (
                half - half * frac,
                half - half * frac,
                half + half * frac,
                half + half * frac,
            ),
            fill=int(peak * (1.0 - frac) ** falloff),
        )
    mask = mask.resize((radius * 2, radius * 2), Image.LANCZOS)
    glow = Image.new("RGBA", mask.size, colour + (0,))
    glow.putalpha(mask)
    return glow


@lru_cache(maxsize=None)
def _font(size):
    """Inter Bold, loaded once per size."""
    return ImageFont.truetype(str(FONT_PATH), size)


def _set_lines(lines, font, lead, top, fill, left=None, centre=None):
    """Set stacked lines on a transparent layer, caps sitting on ``lead``."""
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    pen = ImageDraw.Draw(layer)
    for index, line in enumerate(lines):
        box = pen.textbbox((0, 0), line, font=font)
        width = box[2] - box[0]
        x = left if left is not None else centre - width / 2.0
        pen.text(
            (x - box[0], top + index * lead - box[1]),
            line,
            font=font,
            fill=fill,
        )
    return layer


def _drop_shadow(layer, blur, offset, opacity):
    """A blurred black copy of the type, so it holds on the bright end of the sky."""
    mask = layer.getchannel("A").point(lambda value: round(value * opacity))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(mask)
    return shadow.filter(ImageFilter.GaussianBlur(blur)), offset


# --- the layers ------------------------------------------------------------


def dusk_sky():
    """Magenta at the top, deep orange at the horizon, and the sun disc.

    Returns the canvas and the number of gradient bands drawn.
    """
    canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 255))
    sky = _vertical_fill(
        (WIDTH, HORIZON),
        ((0.0, PLUM_TOP), (0.55, MAGENTA), (1.0, HORIZON_GOLD)),
    )
    canvas.paste(sky, (0, 0))

    halo = _radial(SUN_HALO, SUN_GLOW, peak=140, falloff=2.0)
    canvas.alpha_composite(halo, (SUN_X - SUN_HALO, SUN_Y - SUN_HALO))

    disc = _radial(SUN_RADIUS + 6, SUN_CORE, peak=255, falloff=0.18)
    canvas.alpha_composite(disc, (SUN_X - SUN_RADIUS - 6, SUN_Y - SUN_RADIUS - 6))

    # a fine grain, so the long gradient does not band on a phone screen
    noise = Image.effect_noise(CANVAS, 14).convert("RGBA")
    canvas = ImageChops.blend(canvas, noise, 0.035)

    return canvas, HORIZON


def _sun_road():
    """The sun's reflection: a blurred road of light with brighter dashes on it."""
    height = SHORE - HORIZON
    road = Image.new("RGBA", (WIDTH, height), (0, 0, 0, 0))
    pen = ImageDraw.Draw(road)

    for step in range(64):
        t = step / 63.0
        y = 6 + t * (height - 22)
        half = SUN_RADIUS * (1.0 - t) + 18
        alpha = int(150 * (1.0 - t) ** 1.5) + 16
        pen.line(
            [(SUN_X - half, y), (SUN_X + half, y)],
            fill=REFLECTION + (alpha,),
            width=2,
        )

    rng = random.Random(SEED + 1)
    for step in range(46):
        t = step / 45.0
        y = 10 + t * (height - 30)
        half = (150 * (1.0 - t) + 12) * rng.uniform(0.35, 0.9)
        alpha = int(190 * (1.0 - t) ** 1.3) + 30
        pen.line(
            [(SUN_X - half, y), (SUN_X + half, y)],
            fill=(255, 228, 186, alpha),
            width=3,
        )

    return road.filter(ImageFilter.GaussianBlur(3))


def _foam_line():
    """The surf where the water meets the sand, with a wet sheen under it."""
    band = Image.new("RGBA", (WIDTH, 52), (0, 0, 0, 0))
    pen = ImageDraw.Draw(band)
    points = [
        (x, 22 + 6 * math.sin(x / 57.0) + 3 * math.sin(x / 19.0))
        for x in range(0, WIDTH + 8, 8)
    ]
    pen.line(points, fill=FOAM + (150,), width=4)
    pen.line([(x, y + 9) for x, y in points], fill=FOAM + (46,), width=7)
    return band.filter(ImageFilter.GaussianBlur(2))


def _palm(pen, root, crown, bend, colour):
    """One palm silhouette: a curved tapered trunk and seven drooping fronds."""
    x0, y0 = root
    x1, y1 = crown
    steps = 36
    left, right = [], []
    for index in range(steps + 1):
        t = index / steps
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * (x0 + bend) + t**2 * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ((y0 + y1) / 2.0) + t**2 * y1
        half = 16.0 * (1.0 - 0.55 * t)
        left.append((x - half, y))
        right.append((x + half, y))
    pen.polygon(left + right[::-1], fill=colour)

    for index, angle in enumerate((-2.85, -2.45, -2.0, -1.25, -0.6, -0.15, 0.35)):
        length = 178 + 22 * ((index * 37) % 5)
        control = (
            x1 + math.cos(angle) * length * 0.55,
            y1 + math.sin(angle) * length * 0.55 - 28,
        )
        tip = (
            x1 + math.cos(angle) * length,
            y1 + math.sin(angle) * length + 66,
        )
        blade_left, blade_right = [], []
        for step in range(15):
            t = step / 14.0
            px = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * control[0] + t**2 * tip[0]
            py = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * control[1] + t**2 * tip[1]
            half = 9.0 * (1.0 - t) + 1.0
            normal_x, normal_y = -math.sin(angle), math.cos(angle)
            blade_left.append((px + normal_x * half, py + normal_y * half))
            blade_right.append((px - normal_x * half, py - normal_y * half))
        pen.polygon(blade_left + blade_right[::-1], fill=colour)

    pen.ellipse([x1 - 7, y1 - 7, x1 + 7, y1 + 7], fill=colour)


def skyline(canvas):
    """The water, the silhouette skyline with its lit windows, and two palms.

    Returns the canvas and the number of bars drawn.
    """
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    layer.paste(_vertical_fill((WIDTH, SHORE - HORIZON), WATER_STOPS), (0, HORIZON))
    layer.paste(_vertical_fill((WIDTH, HEIGHT - SHORE), SAND_STOPS), (0, SHORE))
    layer.alpha_composite(_sun_road(), (0, HORIZON))
    layer.alpha_composite(_foam_line(), (0, SHORE - 22))

    pen = ImageDraw.Draw(layer)
    rng = random.Random(SEED)
    x = -30
    bars = 0
    while x < WIDTH:
        width = rng.randint(36, 76)
        centre = x + width / 2.0
        under_sun = abs(centre - SUN_X) < SUN_RADIUS + 90
        if under_sun:
            height = rng.randint(12, 44)       # low rooftops keep the ghost's face clear
        elif rng.random() < 0.16:
            height = rng.randint(200, 300)     # a taller tower to either side
        else:
            height = rng.randint(64, 196)
        top = HORIZON - height

        pen.rectangle([x, top, x + width, HORIZON + 2], fill=SILHOUETTE)
        if height > 200:
            pen.line([(centre, top), (centre, top - 54)], fill=SILHOUETTE, width=3)
            pen.line(
                [(centre - 12, top - 34), (centre + 12, top - 34)],
                fill=SILHOUETTE,
                width=2,
            )
        if height > 60:
            for window_x in range(int(x) + 9, int(x + width) - 8, 13):
                for window_y in range(int(top) + 12, HORIZON - 12, 19):
                    if rng.random() < 0.18:
                        pen.rectangle(
                            [window_x, window_y, window_x + 5, window_y + 8],
                            fill=WINDOW_LIGHT + (200,),
                        )

        bars += 1
        x += width + rng.randint(2, 8)

    _palm(pen, (24, SHORE + 18), (96, 604), 44, PALM_INK)
    _palm(pen, (1052, SHORE + 18), (988, 556), -40, PALM_INK)

    canvas.alpha_composite(layer)
    return canvas, bars


def joke_text(canvas):
    """The four joke lines, heavy white type with a soft black shadow."""
    font = _font(JOKE_SIZE)
    layer = _set_lines(
        JOKE_LINES,
        font,
        JOKE_LEAD,
        JOKE_Y,
        fill=TEXT_WHITE + (255,),
        left=JOKE_X,
    )
    shadow, offset = _drop_shadow(layer, blur=12, offset=(7, 7), opacity=0.72)
    canvas.alpha_composite(shadow, offset)
    canvas.alpha_composite(layer)
    return canvas


def pitch(canvas):
    """PEOPLE + AGENTS / EARN REAL MONEY, centred in the pale pink."""
    font = _font(PITCH_SIZE)
    layer = _set_lines(
        PITCH_LINES,
        font,
        PITCH_LEAD,
        PITCH_Y,
        fill=TEXT_PINK + (255,),
        centre=WIDTH / 2.0,
    )
    shadow, offset = _drop_shadow(layer, blur=9, offset=(4, 5), opacity=0.55)
    canvas.alpha_composite(shadow, offset)
    canvas.alpha_composite(layer)
    return canvas


def brand(canvas):
    """The press kit's mark as the sun, and its lockup as the lit sign on the sand.

    Both are resized by width to the sizes the posted picture gives them, keeping
    their own aspect, and composited as the kit ships them — no recolouring.

    Returns the canvas and the two pasted sizes.
    """
    mark = Image.open(PRESS_KIT / MARK_FILE).convert("RGBA")
    mark_height = round(MARK_WIDTH * mark.height / mark.width)
    mark = mark.resize((MARK_WIDTH, mark_height), Image.LANCZOS)
    canvas.alpha_composite(
        mark,
        (SUN_X - MARK_WIDTH // 2, SUN_Y - mark_height // 2),
    )

    # a soft magenta glow, so the lockup reads as a lit sign on the sand
    glow = _radial(210, MAGENTA, peak=104, falloff=2.2)
    glow = glow.resize((LOCKUP_WIDTH + 260, LOCKUP_HEIGHT + 200), Image.LANCZOS)
    canvas.alpha_composite(
        glow,
        (
            LOCKUP_X - 130,
            LOCKUP_Y + LOCKUP_HEIGHT // 2 - (LOCKUP_HEIGHT + 200) // 2,
        ),
    )

    lockup = Image.open(PRESS_KIT / LOCKUP_FILE).convert("RGBA")
    lockup_height = round(LOCKUP_WIDTH * lockup.height / lockup.width)
    lockup = lockup.resize((LOCKUP_WIDTH, lockup_height), Image.LANCZOS)
    canvas.alpha_composite(
        lockup,
        (LOCKUP_X, LOCKUP_Y + (LOCKUP_HEIGHT - lockup_height) // 2),
    )

    return canvas, (MARK_WIDTH, mark_height), (LOCKUP_WIDTH, lockup_height)


def main(argv):
    """Compose the picture in order, save it and print what was drawn."""
    output = Path(argv[1]) if len(argv) > 1 else Path("meme.png")

    canvas, bands = dusk_sky()
    canvas, bars = skyline(canvas)
    canvas = joke_text(canvas)
    canvas = pitch(canvas)
    canvas, mark_size, lockup_size = brand(canvas)

    canvas = canvas.convert("RGB")
    canvas.save(output, optimize=True)

    print("make_meme.py — rebuilding the CALLED IN SICK meme")
    print(f"  canvas    {canvas.width} x {canvas.height}")
    print(f"  sky       {bands} bands, magenta to #FFCE8A, sun at ({SUN_X}, {SUN_Y})")
    print(f"  skyline   {bars} bars, lit windows, two palms")
    print(f"  joke      {len(JOKE_LINES)} lines, {JOKE_SIZE} px on a {JOKE_LEAD} px lead")
    print(f"  pitch     {len(PITCH_LINES)} lines, {PITCH_SIZE} px, #FF88C4")
    print(f"  mark      {mark_size[0]} x {mark_size[1]} at ({SUN_X}, {SUN_Y})")
    print(f"  lockup    {lockup_size[0]} x {lockup_size[1]} at ({LOCKUP_X}, {LOCKUP_Y})")
    print(f"  wrote     {output} ({output.stat().st_size} bytes)")
    return canvas


if __name__ == "__main__":
    main(sys.argv)
