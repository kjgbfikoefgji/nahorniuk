"""Оптимізація зображень: images/ -> site/img/out, плюс брендові файли.

    python main.py images

Потрібен Pillow (pip install pillow). Лише для розробки: на Netlify не запускається.
Портрет: portrait-640.webp, portrait-853.webp. Результати before/after: res-N-640.webp і res-N-1200.webp. Також генеруються
og.jpg (1200x630), favicon.ico та icon-180.png.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

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
            os.path.join(OUT, 'portrait-%d.webp' % w), 'WEBP', quality=82, method=6)
    # круглий аватар у шапці: обличчя з нового фото
    r = round(img.height * 0.084)
    cx, cy = round(img.width * 0.512), round(img.height * 0.312)
    face = img.crop((cx - r, cy - r, cx + r, cy + r)).resize((112, 112), Image.LANCZOS)
    face.save(os.path.join(OUT, 'avatar-112.webp'), 'WEBP', quality=86, method=6)
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


def og(lang='uk'):  # lang лишився на випадок окремого зображення для іншої мови
    W, H = 1200, 630
    t = {
        'uk': ('ОНЛАЙН-ТРЕНЕР', 'Владислав', 'Нагорнюк', '12 років досвіду · 100+ клієнтів', 'Чемпіон світу · «Україна має талант 5»', 'og.jpg'),
    }[lang]
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    # правий блок: портрет тренера
    photo = Image.open(os.path.join(OUT, 'portrait-853.webp')).convert('RGB')
    im.paste(cover(photo, 400, 630), (800, 0))
    d.rectangle((0, 0, 14, H), fill=ACCENT)
    d.text((70, 90), t[0], font=font(30), fill=ACCENT)
    d.text((70, 140), t[1], font=font(104), fill=TEXT)
    d.text((70, 252), t[2], font=font(104), fill=TEXT)
    d.text((70, 420), t[3], font=font(32, False), fill=MUTED)
    d.text((70, 470), t[4], font=font(28, False), fill=MUTED)
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
