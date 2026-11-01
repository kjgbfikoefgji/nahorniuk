"""Оптимізація зображень: images/ -> site/img/out, плюс брендові файли.

    python main.py images

Потрібен Pillow (pip install pillow). Лише для розробки: на Netlify не запускається.
Заглавне фото: hero-640.webp, hero-853.webp. Результати before/after: res-N-640.webp і res-N-1200.webp. Також генеруються
og-N.jpg (1200x630), favicon.ico та icon-180.png.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'images')
OUT = os.path.join(ROOT, 'site', 'img', 'out')
SITE = os.path.join(ROOT, 'site')

# порядок на сайті -> файл у images/
RESULTS = [
    'photo_2026-10-09_11-35-14.jpg',  # місяць тренувань, +5 кг
    'photo_2026-10-09_11-37-35.jpg',  # 4 місяці, -5 кг
    'photo_2026-10-09_11-39-04.jpg',  # 4 місяці, -3 кг
    'photo_2026-10-09_11-39-56.jpg',  # 3 роки тренувань
    'photo_2026-10-09_11-40-38.jpg',  # 4 роки, перевтілення
    'photo_2026-10-09_11-41-11.jpg',  # 4 місяці, +4 кг м'язів
    'photo_2026-10-09_11-41-40.jpg',  # 2 місяці, +6 кг
]
WIDTHS = (640, 1200)
PORTRAIT = 'Останню на заглавну фото можна.JPG'  # заглавне фото з торсом (герой, og, аватар у шапці)
PORTRAIT_CENTER = 0.52  # де по горизонталі стоїть тренер (частка ширини): за нею кадруємо 2:3
ABOUT = 'photo_2026-10-09_12-25-44.jpg'  # портрет для «Про мене»
# фото в картках послуг: файл -> ім'я виходу
SERVICES = {
    'Програми тренувань.JPG': 'svc-plan',
    'Онлайн-тренування.JPG': 'svc-online',
    'Консультація.JPG': 'svc-consult',
    'Харчування.JPG': 'svc-meal',
}

BG = (14, 18, 24)
ACCENT = (255, 122, 26)
TEXT = (244, 246, 249)
MUTED = (170, 180, 195)


def font(size, bold=True):
    for name in ('arialbd.ttf' if bold else 'arial.ttf', 'DejaVuSans-Bold.ttf', 'DejaVuSans.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def results():
    for i, name in enumerate(RESULTS, 1):
        img = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name))).convert('RGB')
        for w in WIDTHS:
            im = img if img.width <= w else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
            im.save(os.path.join(OUT, 'res-%d-%d.webp' % (i, w)), 'WEBP', quality=80, method=6)
        print('res-%d: %dx%d' % (i, img.width, img.height))


def portrait():
    img = ImageOps.exif_transpose(Image.open(os.path.join(SRC, PORTRAIT))).convert('RGB')
    # кадр 2:3 по висоті знімка, зсунутий до тренера
    cw = round(img.height * 2 / 3)
    left = min(max(round(img.width * PORTRAIT_CENTER - cw / 2), 0), img.width - cw)
    crop = img.crop((left, 0, left + cw, img.height))
    for w in (640, 853):
        crop.resize((w, round(w * 3 / 2)), Image.LANCZOS).save(
            os.path.join(OUT, 'hero-%d.webp' % w), 'WEBP', quality=82, method=6)
    # круглий аватар у шапці: обличчя з фото в кепці (те саме, що в «Про мене»)
    cap = ImageOps.exif_transpose(Image.open(os.path.join(SRC, ABOUT))).convert('RGB')
    side = min(cap.width, round(cap.height * 0.56))
    left = cap.width - side  # обличчя праворуч у кадрі
    top = round(cap.height * 0.13)
    face = cap.crop((left, top, left + side, top + side)).resize((112, 112), Image.LANCZOS)
    face.save(os.path.join(OUT, 'avatar-cap-112.webp'), 'WEBP', quality=86, method=6)
    print('portrait: %dx%d' % img.size)
    about = ImageOps.exif_transpose(Image.open(os.path.join(SRC, ABOUT))).convert('RGB')
    for w in (640, 853):
        im = about if about.width <= w else about.resize((w, round(about.height * w / about.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, 'about-%d.webp' % w), 'WEBP', quality=82, method=6)


def services():
    for name, out in SERVICES.items():
        img = ImageOps.exif_transpose(Image.open(os.path.join(SRC, name))).convert('RGB')
        im = img if img.width <= 800 else img.resize((800, round(img.height * 800 / img.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, out + '.webp'), 'WEBP', quality=78, method=6)
        print('%s: %dx%d' % (out, im.width, im.height))


def site_font(family, size, weight):
    """Шрифт сайту з site/fonts: пара (кирилиця, латиниця), бо woff2 розбиті на підмножини."""
    pair = []
    for sub in ('cyrillic', 'latin'):
        f = ImageFont.truetype(os.path.join(SITE, 'fonts', '%s-%s-wght-normal.woff2' % (family, sub)), size)
        f.set_variation_by_axes([weight])
        pair.append(f)
    return pair


def draw_mixed(d, xy, text, fonts, fill):
    """Малює рядок, беручи для кожного символу кириличну чи латинську підмножину. Повертає ширину."""
    x, y = xy
    for ch in text:
        f = fonts[0] if 0x400 <= ord(ch) < 0x530 else fonts[1]
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch)
    return x - xy[0]


def og(lang='uk'):  # lang лишився на випадок окремого зображення для іншої мови
    """Прев'ю посилання у світлій темі героя: текст ліворуч, праворуч фото в рамці з нахиленою карткою й печаткою."""
    S = 2  # малюємо вдвічі більше й зменшуємо: гладкі краї рамки, картки й печатки
    W, H = 1200 * S, 630 * S
    t = {
        'uk': ('ОНЛАЙН-ТРЕНЕР', ('ВЛАДИСЛАВ', 'НАГОРНЮК'), ('ЧЕМПІОН СВІТУ', 'З ПІДТЯГУВАНЬ'),
               (('12', 'років у тренерстві'), ('100+', 'задоволених клієнтів')),
               'ЧЕМПІОН СВІТУ 2017 • ПІДТЯГУВАННЯ +32 КГ • ',
               'og-4.jpg'),  # нова назва = нове прев'ю: Telegram кешує картинку за адресою
    }[lang]
    INK, CREAM, HOT = (23, 18, 13), (247, 243, 236), (224, 86, 10)
    im = Image.new('RGB', (W, H), CREAM)
    d = ImageDraw.Draw(im)
    # крапкова фактура тла, як на сайті
    for y in range(14 * S, H, 26 * S):
        for x in range(14 * S, W, 26 * S):
            d.ellipse((x - S, y - S, x + S, y + S), fill=(226, 218, 205))
    # рамка з фото
    fx, fy, fw, fh, r = 770 * S, 48 * S, 370 * S, 534 * S, 30 * S

    def layer(draw_fn, angle=0, blur=0):
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_fn(ImageDraw.Draw(lay))
        if angle:
            lay = lay.rotate(angle, Image.BICUBIC, center=(fx + fw // 2, fy + fh // 2))
        if blur:
            lay = lay.filter(ImageFilter.GaussianBlur(blur))
        im.paste(lay, (0, 0), lay)

    box = (fx, fy, fx + fw, fy + fh)
    shadow = (fx + 6 * S, fy + 26 * S, fx + fw + 6 * S, fy + fh + 26 * S)
    layer(lambda dr: dr.rounded_rectangle(shadow, r, fill=(150, 60, 0, 90)), -4, 22 * S)
    # нахилена помаранчева картка з крапками
    grad = Image.new('RGBA', (fw, fh))
    gd = ImageDraw.Draw(grad)
    for y in range(fh):  # #ffa04a -> #ff7a1a -> #f05a00
        k = y / fh
        c = (255, round(160 - 38 * k / .46), round(74 - 48 * k / .46)) if k < .46 else             (round(255 - 15 * (k - .46) / .54), round(122 - 32 * (k - .46) / .54), round(26 - 26 * (k - .46) / .54))
        gd.line((0, y, fw, y), fill=c + (255,))
    for y in range(10 * S, fh, 20 * S):
        for x in range(10 * S, fw, 20 * S):
            gd.ellipse((x - 2 * S, y - 2 * S, x + 2 * S, y + 2 * S), fill=(23, 18, 13, 50))
    cmask = Image.new('L', (fw, fh), 0)
    ImageDraw.Draw(cmask).rounded_rectangle((0, 0, fw - 1, fh - 1), r, fill=255)
    tilted = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    tilted.paste(grad, (fx, fy), cmask)
    tilted = tilted.rotate(-4, Image.BICUBIC, center=(fx + fw // 2, fy + fh // 2)).resize((round(W * 1.05), round(H * 1.05)), Image.LANCZOS)
    c0 = (round((fx + fw / 2) * 1.05 - (fx + fw / 2)), round((fy + fh / 2) * 1.05 - (fy + fh / 2)))
    tilted = tilted.crop((c0[0], c0[1], c0[0] + W, c0[1] + H))
    im.paste(tilted, (0, 0), tilted)
    # фото: кадр від маківки до пояса
    src = ImageOps.exif_transpose(Image.open(os.path.join(SRC, PORTRAIT))).convert('RGB')
    side = round(src.height * 0.74)
    cw = round(side * fw / fh)
    left = min(max(round(src.width * PORTRAIT_CENTER - cw / 2), 0), src.width - cw)
    top = round(src.height * 0.03)
    photo = src.crop((left, top, left + cw, top + side)).resize((fw, fh), Image.LANCZOS)
    pmask = Image.new('L', (fw, fh), 0)
    ImageDraw.Draw(pmask).rounded_rectangle((0, 0, fw - 1, fh - 1), r, fill=255)
    im.paste(photo, (fx, fy), pmask)
    d.rounded_rectangle(box, r, outline=INK, width=3 * S)
    # печатка «Чемпіон світу» на лівому краї рамки
    cx, cy, R = fx, fy + fh - 110 * S, 78 * S
    layer(lambda dr: dr.ellipse((cx - R, cy - R + 18 * S, cx + R, cy + R + 18 * S), fill=(110, 40, 0, 110)), 0, 16 * S)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(255, 255, 255), outline=INK, width=3 * S)
    d.ellipse((cx - 30 * S, cy - 30 * S, cx + 30 * S, cy + 30 * S), fill=ACCENT)
    trophy(d, cx, cy, 40 * S, INK)
    ring = site_font('unbounded', 12 * S, 800)
    adv = [(ring[0] if 0x400 <= ord(ch) < 0x530 else ring[1]).getlength(ch) for ch in t[4]]
    for i, ch in enumerate(t[4]):  # кут літери пропорційний її ширині
        ang = math.radians(-90 + 360 * (sum(adv[:i]) + adv[i] / 2) / sum(adv))
        f = ring[0] if 0x400 <= ord(ch) < 0x530 else ring[1]
        g = Image.new('RGBA', (30 * S, 30 * S), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((15 * S, 15 * S), ch, font=f, fill=INK, anchor='mm')
        g = g.rotate(-math.degrees(ang) - 90, Image.BICUBIC)
        rr = R - 21 * S
        im.paste(g, (round(cx + rr * math.cos(ang)) - 15 * S, round(cy + rr * math.sin(ang)) - 15 * S), g)
    # текст
    lab = site_font('unbounded', 19 * S, 800)
    w = draw_mixed(ImageDraw.Draw(Image.new('L', (1, 1))), (0, 0), t[0], lab, 0)
    d.rectangle((60 * S, 62 * S, 60 * S + w + 32 * S, 104 * S), fill=HOT)
    draw_mixed(d, (76 * S, 70 * S), t[0], lab, (255, 255, 255))
    big = site_font('unbounded', 70 * S, 900)
    draw_mixed(d, (56 * S, 140 * S), t[1][0], big, INK)
    draw_mixed(d, (56 * S, 228 * S), t[1][1], big, INK)
    mid = site_font('unbounded', 36 * S, 900)
    draw_mixed(d, (60 * S, 336 * S), t[2][0], mid, HOT)
    draw_mixed(d, (60 * S, 384 * S), t[2][1], mid, HOT)
    # великі цифри з підписами, як рядок досягнень у героєві
    num, cap = site_font('unbounded', 50 * S, 900), site_font('onest', 20 * S, 600)
    x = 60 * S
    for i, (n, c) in enumerate(t[3]):
        if i:
            d.line((x - 26 * S, 486 * S, x - 26 * S, 572 * S), fill=(205, 194, 178), width=2 * S)
        wn = draw_mixed(d, (x, 474 * S), n, num, INK)
        wc = draw_mixed(d, (x + 2 * S, 546 * S), c, cap, (90, 81, 72))
        x += max(wn, wc) + 52 * S
    im = im.resize((W // S, H // S), Image.LANCZOS)
    im.save(os.path.join(SITE, 'img', t[5]), 'JPEG', quality=88, optimize=True)


def trophy(d, cx, cy, size, fill):
    """Кубок зі спрайта (i-trophy, сітка 24x24) лініями Pillow."""
    k = size / 24
    w = max(1, round(2 * k))
    P = lambda x, y: (cx + (x - 12) * k, cy + (y - 12) * k)
    box = lambda x, y, r: (*P(x - r, y - r), *P(x + r, y + r))
    d.line([P(6, 9), P(6, 2), P(18, 2), P(18, 9)], fill=fill, width=w, joint='curve')
    d.arc(box(12, 9, 6), 0, 180, fill=fill, width=w)
    d.arc(box(4.5, 6.5, 2.5), 90, 270, fill=fill, width=w)
    d.arc(box(19.5, 6.5, 2.5), 270, 90, fill=fill, width=w)
    for a, b in (((4.5, 4), (6, 4)), ((4.5, 9), (6, 9)), ((18, 4), (19.5, 4)), ((18, 9), (19.5, 9)), ((4, 22), (20, 22))):
        d.line([P(*a), P(*b)], fill=fill, width=w)
    d.line([P(10, 14.7), P(10, 17.3), P(7.6, 19.2), P(7, 22)], fill=fill, width=w, joint='curve')
    d.line([P(14, 14.7), P(14, 17.3), P(16.4, 19.2), P(17, 22)], fill=fill, width=w, joint='curve')


def icon_image(size):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=round(size * 0.22), fill=ACCENT)
    f = font(round(size * 0.66))
    box = d.textbbox((0, 0), 'Н', font=f)
    d.text(((size - (box[2] - box[0])) / 2 - box[0], (size - (box[3] - box[1])) / 2 - box[1]),
           'Н', font=f, fill=(19, 10, 2))
    return im


def icons():
    icon_image(180).save(os.path.join(OUT, 'icon-180.png'), optimize=True)
    icon_image(256).save(os.path.join(SITE, 'favicon.ico'), sizes=[(16, 16), (32, 32), (48, 48)])


def main():
    os.makedirs(OUT, exist_ok=True)
    results()
    portrait()
    services()
    og('uk')
    icons()
    print('готово:', OUT)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    main()
