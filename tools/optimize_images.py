"""Оптимізація зображень: images/ -> site/img/out, плюс брендові файли.

    python main.py images

Потрібен Pillow (pip install pillow). Лише для розробки: на Netlify не запускається.
Заглавне фото: hero-640.webp, hero-853.webp. Результати before/after: res-N-640.webp і res-N-1200.webp. Також генеруються
og.jpg (1200x630), favicon.ico та icon-180.png.
"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

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


def cover(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=(0.5, 0.35))


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
    W, H = 1200, 630
    t = {
        'uk': ('НАГОРНЮК', 'ОНЛАЙН-ТРЕНЕР', 'ТРЕНУВАННЯ, ЩО', 'ДАЮТЬ РЕЗУЛЬТАТ',
               'ЧЕМПІОН СВІТУ  •  12 РОКІВ ДОСВІДУ  •  100+ КЛІЄНТІВ', 'og.jpg'),
    }[lang]
    im = Image.new('RGB', (W, H), BG)
    # фото тренера праворуч, кадр від маківки до пояса, приглушене під темну тему
    src = ImageOps.exif_transpose(Image.open(os.path.join(SRC, PORTRAIT))).convert('RGB')
    pw = 760
    side = round(src.height * 0.56)
    cw = round(side * pw / H)
    # тренер на 3/4 ширини фото, щоб обличчя не опинилось під заголовком
    left = min(max(round(src.width * PORTRAIT_CENTER - cw * 0.72), 0), src.width - cw)
    top = round(src.height * 0.04)
    photo = src.crop((left, top, left + cw, top + side))
    photo = Image.blend(photo.resize((pw, H), Image.LANCZOS), Image.new('RGB', (pw, H), BG), 0.42)
    im.paste(photo, (W - pw, 0))
    # градієнти: зліва в тло (текст), знизу в тло (рядок регалій)
    x0 = W - pw
    side_shade = Image.linear_gradient('L').rotate(-90).resize((360, H))  # 255 зліва -> 0 справа
    left_mask = Image.new('L', (W, H), 0)
    left_mask.paste(255, (0, 0, x0, H))
    left_mask.paste(side_shade, (x0, 0))
    bottom_mask = Image.new('L', (W, H), 0)
    bottom_mask.paste(Image.linear_gradient('L').resize((W, 220)).point(lambda v: v * 235 // 255), (0, H - 220))
    im.paste(Image.new('RGB', (W, H), BG), (0, 0), ImageChops.lighter(left_mask, bottom_mask))
    d = ImageDraw.Draw(im)
    # аватар і ім'я
    av = Image.open(os.path.join(OUT, 'avatar-cap-112.webp')).convert('RGB').resize((76, 76), Image.LANCZOS)
    mask = Image.new('L', (76, 76), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 75, 75), fill=255)
    d.ellipse((60, 52, 140, 132), fill=ACCENT)
    im.paste(av, (62, 54), mask)
    brand = site_font('unbounded', 30, 800)
    w = draw_mixed(d, (162, 72), t[0], brand, TEXT)
    draw_mixed(d, (162 + w + 14, 72), t[1], brand, ACCENT)
    # заголовок
    big = site_font('unbounded', 62, 900)
    draw_mixed(d, (60, 300), t[2], big, TEXT)
    draw_mixed(d, (60, 384), t[3], big, ACCENT)
    draw_mixed(d, (62, 520), t[4], site_font('onest', 26, 800), TEXT)
    im.save(os.path.join(SITE, 'img', t[5]), 'JPEG', quality=86, optimize=True)


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
