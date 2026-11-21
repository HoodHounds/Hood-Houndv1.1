#!/usr/bin/env python3
"""Generate the Juiced in-game art (murals, tags, billboards, intro poster, bandana).

Run from the repo root:  python3 tools/juiced_art.py
Edit the TEXT dict below to change slogans, then re-run and reload the game.
Needs Pillow (pip install pillow). Source billboards are read from tools/src/.
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, 'tools')
SRC = os.path.join(T, 'src')
OUT = os.path.join(ROOT, 'art')

TEXT = {
    'slogan': 'STAY JUICED',
    'handle': '@JUICED009',
    'site': 'HOODHOUND.SITE',
    'drop': 'NEW DROP',
    'drop_sub': 'OUT NOW',
}

# Juiced palette: juice orange, hot pink, lime, grape, gold (matches the game's HUD gold).
ORANGE = (255, 140, 26)
PINK = (255, 61, 127)
LIME = (166, 230, 41)
GRAPE = (123, 63, 228)
GOLD = (247, 183, 51)
INK = (14, 12, 16)

random.seed(9)


def font(name, size):
    return ImageFont.truetype(os.path.join(T, 'fonts', name + '.woff'), size)


def logo(width, color=(255, 255, 255)):
    src = Image.open(os.path.join(T, 'juiced_logo_src.png'))
    h = round(src.height * width / src.width)
    a = src.getchannel('A').resize((width, h), Image.LANCZOS)
    out = Image.new('RGBA', (width, h), color + (0,))
    out.putalpha(a)
    return out


def brick(w=1024, h=1024, base=(122, 58, 44)):
    im = Image.new('RGB', (w, h), (70, 62, 58))
    d = ImageDraw.Draw(im)
    bw, bh = 96, 40
    for row in range(h // bh + 1):
        off = (bw // 2) if row % 2 else 0
        for col in range(-1, w // bw + 2):
            x = col * bw + off
            y = row * bh
            j = random.randint(-22, 22)
            c = tuple(max(0, min(255, base[i] + j + random.randint(-6, 6))) for i in range(3))
            d.rectangle([x + 3, y + 3, x + bw - 3, y + bh - 3], fill=c)
    noise = Image.effect_noise((w, h), 28).convert('RGB')
    im = ImageChops.multiply(im, Image.blend(Image.new('RGB', (w, h), (255, 255, 255)), noise, 0.35))
    return im.filter(ImageFilter.GaussianBlur(0.6))


def spray_glow(base, layer, color, radius=18, strength=0.85):
    """Soft overspray halo around a layer's alpha, like real spray paint."""
    a = layer.getchannel('A').filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: int(v * strength))
    glow = Image.new('RGBA', layer.size, color + (0,))
    glow.putalpha(a)
    base.alpha_composite(glow)


def drips(d, box, color, n=14, max_len=120):
    x0, y0, x1, y1 = box
    for _ in range(n):
        x = random.randint(x0, x1)
        ln = random.randint(20, max_len)
        wdt = random.randint(4, 9)
        d.rounded_rectangle([x, y1 - 10, x + wdt, y1 + ln], radius=wdt // 2, fill=color)
        d.ellipse([x - 2, y1 + ln - 4, x + wdt + 2, y1 + ln + wdt + 2], fill=color)


def text_layer(size, txt, fnt, fill, outline=INK, stroke=10, rot=0):
    w, h = size
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    bb = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
    x = (w - (bb[2] - bb[0])) // 2 - bb[0]
    y = (h - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((x, y), txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=outline)
    if rot:
        lay = lay.rotate(rot, resample=Image.BICUBIC)
    return lay


def fit_font(name, txt, max_w, start=300):
    s = start
    while s > 10:
        f = font(name, s)
        bb = f.getbbox(txt)
        if bb[2] - bb[0] <= max_w:
            return f
        s -= 4
    return font(name, 10)


def paste_center(base, lay, cx, cy):
    base.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))


def save(im, name, q=86):
    os.makedirs(OUT, exist_ok=True)
    im.save(os.path.join(OUT, name), 'WEBP', quality=q, method=6)


# ---------------------------------------------------------------- murals (full-wall, opaque)

def mural_logo():
    """Giant white JUICED brush logo on orange-glow brick."""
    im = brick(base=(110, 52, 40)).convert('RGBA')
    lg = logo(860)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    lay.alpha_composite(lg, ((1024 - lg.width) // 2, 330))
    spray_glow(im, lay, ORANGE, 26, 1.0)
    spray_glow(im, lay, PINK, 60, 0.55)
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    drips(d, (140, 330, 880, 330 + lg.height - 40), (255, 255, 255, 255), 10, 90)
    sub = text_layer((1024, 200), TEXT['slogan'], font('PermanentMarker', 110), GOLD, INK, 8, 4)
    paste_center(im, sub, 512, 700)
    tag = text_layer((1024, 120), TEXT['handle'], font('PermanentMarker', 54), LIME, INK, 5, -3)
    paste_center(im, tag, 700, 860)
    save(im.convert('RGB'), 'juiced_mural_logo.webp')


def mural_stay():
    """STAY JUICED wildstyle-ish, stacked."""
    im = brick(base=(96, 70, 64)).convert('RGBA')
    words = TEXT['slogan'].split(' ', 1)
    cols = [PINK, ORANGE]
    for i, wd in enumerate(words):
        f = fit_font('Bungee', wd, 900, 330)
        lay = text_layer((1024, 420), wd, f, cols[i % 2], INK, 16, (-5 if i == 0 else 3))
        cy = 330 + i * 330
        tmp = Image.new('RGBA', im.size, (0, 0, 0, 0))
        tmp.alpha_composite(lay, (0, int(cy - 210)))
        spray_glow(im, tmp, (255, 255, 255), 14, 0.5)
        im.alpha_composite(tmp)
    d = ImageDraw.Draw(im)
    drips(d, (120, 360, 900, 420), PINK + (255,), 12, 110)
    for _ in range(7):
        x, y = random.randint(60, 960), random.randint(60, 960)
        r = random.randint(10, 26)
        d.polygon([(x, y - r), (x + r // 4, y - r // 4), (x + r, y), (x + r // 4, y + r // 4),
                   (x, y + r), (x - r // 4, y + r // 4), (x - r, y), (x - r // 4, y - r // 4)],
                  fill=(255, 255, 255, 230))
    save(im.convert('RGB'), 'juiced_mural_stay.webp')


def mural_biscuit():
    """Wheat-paste Biscuit poster on brick with a JUICED throw-up over it."""
    im = brick(base=(84, 74, 70)).convert('RGBA')
    poster = Image.open(os.path.join(OUT, 'hood_hound_intro.webp')).convert('RGBA').resize((640, 640), Image.LANCZOS)
    frame = Image.new('RGBA', (664, 664), (236, 230, 214, 255))
    frame.alpha_composite(poster, (12, 12))
    frame = frame.rotate(-3, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    sh.putalpha(frame.getchannel('A').filter(ImageFilter.GaussianBlur(14)).point(lambda v: v * 0.6))
    im.alpha_composite(sh, (196, 146))
    im.alpha_composite(frame, (180, 130))
    lg = logo(560, PINK)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    lay.alpha_composite(lg.rotate(8, resample=Image.BICUBIC, expand=True), (420, 740))
    spray_glow(im, lay, (255, 255, 255), 10, 0.9)
    im.alpha_composite(lay)
    tag = text_layer((500, 120), 'x BISCUIT', font('PermanentMarker', 60), GOLD, INK, 6, 6)
    im.alpha_composite(tag, (30, 820))
    save(im.convert('RGB'), 'juiced_mural_biscuit.webp')


def mural_drop():
    """NEW DROP announcement wall."""
    im = brick(base=(60, 56, 70)).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([90, 150, 934, 874], radius=40, fill=GRAPE + (235,), outline=INK, width=14)
    f = fit_font('Bungee', TEXT['drop'], 740, 220)
    paste_center(im, text_layer((1024, 300), TEXT['drop'], f, LIME, INK, 12, -2), 512, 330)
    lg = logo(600)
    paste_center(im, lg, 512, 560)
    paste_center(im, text_layer((1024, 160), TEXT['drop_sub'], font('PermanentMarker', 100), GOLD, INK, 8, 2), 512, 760)
    drips(ImageDraw.Draw(im), (140, 860, 880, 874), GRAPE + (255,), 12, 80)
    save(im.convert('RGB'), 'juiced_mural_drop.webp')


def mural_dawgs():
    """DAWGS ONLY crew wall with bones."""
    im = brick(base=(118, 64, 46)).convert('RGBA')
    paste_center(im, text_layer((1024, 320), 'DAWGS', fit_font('Bungee', 'DAWGS', 880, 300), GOLD, INK, 16, -4), 512, 300)
    paste_center(im, text_layer((1024, 320), 'ONLY', fit_font('Bungee', 'ONLY', 700, 300), PINK, INK, 16, 3), 512, 560)
    lg = logo(420)
    paste_center(im, lg, 512, 800)
    d = ImageDraw.Draw(im)
    for (x, y, r) in [(120, 120, 0), (880, 140, 30), (130, 880, -20), (900, 860, 15)]:
        b = Image.new('RGBA', (200, 80), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.rounded_rectangle([30, 28, 170, 52], radius=12, fill='white', outline=INK, width=4)
        for cx in (30, 170):
            for cy in (24, 56):
                bd.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill='white', outline=INK, width=4)
        bd.rounded_rectangle([30, 30, 170, 50], radius=10, fill='white')
        b = b.rotate(r, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(b, (x - b.width // 2, y - b.height // 2))
    save(im.convert('RGB'), 'juiced_mural_dawgs.webp')


# ---------------------------------------------------------------- tags (transparent stickers on walls)

def tag(name, txt, fill, glow, rot):
    im = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    f = fit_font('PermanentMarker', txt, 860, 260)
    lay = text_layer((1024, 1024), txt, f, fill, INK, 14, rot)
    spray_glow(im, lay, glow, 22, 0.9)
    im.alpha_composite(lay)
    save(im, name)


def tag_logo():
    im = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    lg = logo(880, ORANGE)
    ol = logo(880, INK)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    for dx in range(-10, 11, 5):
        for dy in range(-10, 11, 5):
            lay.alpha_composite(ol, (72 + dx, 400 + dy))
    lay.alpha_composite(lg, (72, 400))
    lay = lay.rotate(-6, resample=Image.BICUBIC)
    spray_glow(im, lay, LIME, 26, 0.9)
    im.alpha_composite(lay)
    save(im, 'juiced_tag_logo.webp')


# ---------------------------------------------------------------- billboards & poster edits

def cover(im, box, blur=28):
    """Hide original text by heavily blurring the region (keeps the scene colours)."""
    reg = im.crop(box).filter(ImageFilter.GaussianBlur(blur)).filter(ImageFilter.GaussianBlur(blur))
    im.paste(reg, box)


def billboard_juiced():
    im = Image.open(os.path.join(SRC, 'billboard_biscuit_gamer.webp')).convert('RGBA')
    cover(im, (150, 262, 884, 412))
    cover(im, (146, 696, 884, 742), 14)
    d = ImageDraw.Draw(im)
    d.rectangle([146, 696, 884, 742], fill=(40, 18, 70, 255))
    lg = logo(440)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    lay.alpha_composite(lg, (512 - lg.width // 2, 268))
    spray_glow(im, lay, PINK, 16, 1.0)
    im.alpha_composite(lay)
    paste_center(im, text_layer((740, 70), TEXT['slogan'] + '  •  ' + TEXT['handle'], font('Bungee', 30), GOLD, INK, 0), 515, 720)
    save(im.convert('RGB'), 'juiced_billboard.webp', 90)


def billboard_out_now():
    """Biscuit billboard: replace the fake console line with the real site."""
    im = Image.open(os.path.join(SRC, 'billboard_biscuit_out_now.webp')).convert('RGBA')
    d = ImageDraw.Draw(im)
    box = BISCUIT_BB_TEXT_BOX
    d.rectangle(box, fill=(8, 8, 10, 255))
    cw = box[2] - box[0]
    paste_center(im, text_layer((cw, 70), 'PLAY FREE NOW', fit_font('Bungee', 'PLAY FREE NOW', cw - 40, 60), (255, 255, 255), INK, 0),
                 (box[0] + box[2]) // 2, box[1] + 52)
    paste_center(im, text_layer((cw, 50), TEXT['site'] + '  •  JUICED', font('Bungee', 34), GOLD, INK, 0),
                 (box[0] + box[2]) // 2, box[1] + 112)
    save(im.convert('RGB'), 'Biscuit_game_billboard.webp', 90)


def intro_poster():
    im = Image.open(os.path.join(SRC, 'intro_poster.webp')).convert('RGBA')
    d = ImageDraw.Draw(im)
    d.rectangle(INTRO_JAM_BOX, fill=(0, 0, 0, 255))
    lg = logo(270)
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    cx = (INTRO_JAM_BOX[0] + INTRO_JAM_BOX[2]) // 2
    cy = (INTRO_JAM_BOX[1] + INTRO_JAM_BOX[3]) // 2
    lay.alpha_composite(lg.rotate(-6, resample=Image.BICUBIC, expand=True), (cx - 140, cy - 60))
    spray_glow(im, lay, LIME, 14, 0.9)
    im.alpha_composite(lay)
    save(im.convert('RGB'), 'hood_hound_intro.webp', 90)


def windows_wall():
    im = Image.open(os.path.join(SRC, 'wall_windows.png')).convert('RGBA')
    for box in WINDOW_TAG_BOXES:
        cover(im, box, 10)
        w = box[2] - box[0]
        txt = random.choice(['JUICED', 'STAY JUICED', 'J009'])
        lay = text_layer((w, box[3] - box[1]), txt, fit_font('PermanentMarker', txt, w - 10, 70),
                         random.choice([PINK, LIME, ORANGE, GOLD]), INK, 4, random.randint(-12, 12))
        im.alpha_composite(lay, (box[0], box[1]))
    save(im.convert('RGB'), 'wall_windows.webp', 88)


def bandana_texture(name, bg, fg=(255, 255, 255)):
    """Bandana print: bones + small JUICED logos, tiles horizontally (used on Biscuit's bandana)."""
    im = Image.new('RGBA', (512, 512), bg + (255,))
    d = ImageDraw.Draw(im)
    lg = logo(150, fg)
    for row in range(5):
        for col in range(3):
            x = col * 170 + (85 if row % 2 else 0) - 40
            y = row * 104 + 18
            if (row + col) % 2:
                im.alpha_composite(lg, (x, y + 6)) if x >= 0 else None
            else:
                d.rounded_rectangle([x + 40, y + 26, x + 120, y + 40], radius=7, fill=fg)
                for cx in (40, 120):
                    for cy in (22, 44):
                        d.ellipse([x + cx - 10, y + cy - 10, x + cx + 10, y + cy + 10], fill=fg)
    save(im.convert('RGB'), name, 90)


def bandana_flap(name, bg, fg=(255, 255, 255)):
    """Front triangle of the bandana: logo centred in the wide top part, bones toward the tip."""
    im = Image.new('RGBA', (512, 512), bg + (255,))
    d = ImageDraw.Draw(im)
    lg = logo(330, fg)
    im.alpha_composite(lg, ((512 - lg.width) // 2, 70))
    def bone(x, y, w=70):
        d.rounded_rectangle([x, y - 6, x + w, y + 6], radius=6, fill=fg)
        for cx in (x, x + w):
            for cy in (y - 8, y + 8):
                d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=fg)
    for x, y in [(60, 40), (380, 40), (150, 300), (290, 300), (220, 400)]:
        bone(x, y)
    save(im.convert('RGB'), name, 90)


def road_texture():
    """Seamless asphalt (tiles in both directions) for the streets: grain, soft patches, a few cracks."""
    n = 512
    base = Image.new('RGB', (n, n), (66, 60, 70))
    grain = Image.effect_noise((n, n), 40).convert('RGB')
    im = Image.blend(base, ImageChops.multiply(base, grain).point(lambda v: min(255, int(v * 2.2))), 0.45)
    blot = Image.new('L', (n, n), 128)
    d = ImageDraw.Draw(blot)
    for _ in range(26):
        x, y, r = random.randint(0, n), random.randint(0, n), random.randint(20, 80)
        v = random.randint(95, 165)
        for ox in (-n, 0, n):
            for oy in (-n, 0, n):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=v)
    big = Image.new('L', (n * 3, n * 3))
    for ox in range(3):
        for oy in range(3):
            big.paste(blot, (ox * n, oy * n))
    blot = big.filter(ImageFilter.GaussianBlur(30)).crop((n, n, 2 * n, 2 * n))
    im = Image.merge('RGB', [ImageChops.multiply(c, blot.point(lambda v: min(255, v * 2))) for c in im.split()])
    d = ImageDraw.Draw(im)
    for _ in range(5):
        x, y = random.randint(40, n - 40), random.randint(40, n - 40)
        pts = [(x, y)]
        for _ in range(6):
            x += random.randint(-14, 14); y += random.randint(6, 18); pts.append((x, y))
        d.line(pts, fill=(38, 34, 40), width=2)
    im.save(os.path.join(ROOT, 'road02.jpg'), 'JPEG', quality=84)


def og_image():
    """1200x630 link-preview image (Open Graph / X cards)."""
    im = Image.new('RGBA', (1200, 630), (11, 10, 13, 255))
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([-40, -80, 720, 700], fill=PINK + (120,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(90)))
    poster = Image.open(os.path.join(OUT, 'hood_hound_intro.webp')).convert('RGBA').resize((570, 570), Image.LANCZOS)
    im.alpha_composite(poster, (30, 30))
    lg = logo(470)
    im.alpha_composite(lg, (660, 120))
    d = ImageDraw.Draw(im)
    d.text((895, 330), 'x HOOD HOUND', font=font('Bungee', 46), fill=GOLD, anchor='mm')
    d.text((895, 410), 'PLAY FREE IN YOUR BROWSER', font=font('Bungee', 28), fill=(255, 255, 255), anchor='mm')
    d.rounded_rectangle([700, 455, 1090, 525], radius=18, fill=ORANGE)
    d.text((895, 490), TEXT['site'], font=font('Bungee', 30), fill=INK, anchor='mm')
    im.convert('RGB').save(os.path.join(OUT, 'og.jpg'), 'JPEG', quality=88)


# Regions measured on the source images (1024x1024).
BISCUIT_BB_TEXT_BOX = (148, 592, 882, 738)
INTRO_JAM_BOX = (700, 820, 962, 962)
WINDOW_TAG_BOXES = [(18, 62, 182, 242), (18, 588, 168, 742), (894, 572, 1022, 728)]

if __name__ == '__main__':
    intro_poster()
    billboard_juiced()
    billboard_out_now()
    windows_wall()
    mural_logo()
    mural_stay()
    mural_biscuit()
    mural_drop()
    mural_dawgs()
    tag('juiced_tag_stay.webp', TEXT['slogan'], PINK, ORANGE, 8)
    tag('juiced_tag_handle.webp', TEXT['handle'], LIME, GRAPE, -5)
    tag_logo()
    bandana_texture('juiced_bandana.webp', (16, 16, 18))
    bandana_texture('juiced_bandana_drop.webp', ORANGE)
    bandana_flap('juiced_flap.webp', (16, 16, 18))
    bandana_flap('juiced_flap_drop.webp', ORANGE)
    road_texture()
    og_image()
    print('wrote art to', OUT)
