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
PORTRAIT = 'photo_2026-10-09_12-25-44.jpg'  # портрет тренера (герой, «Про мене», og)

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
    for w in (640, 853):
        im = img if img.width <= w else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        im.save(os.path.join(OUT, 'portrait-%d.webp' % w), 'WEBP', quality=82, method=6)
    print('portrait: %dx%d' % img.size)


def cover(img, w, h):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=(0.5, 0.35))


def og():
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    # правий блок: портрет тренера
    photo = Image.open(os.path.join(OUT, 'portrait-853.webp')).convert('RGB')
    im.paste(cover(photo, 400, 630), (800, 0))
    d.rectangle((0, 0, 14, H), fill=ACCENT)
    d.text((70, 90), 'ОНЛАЙН-ТРЕНЕР', font=font(30), fill=ACCENT)
    d.text((70, 140), 'Влад', font=font(104), fill=TEXT)
    d.text((70, 252), 'Нагорнюк', font=font(104), fill=TEXT)
    d.text((70, 420), '12 років досвіду · 100+ клієнтів', font=font(32, False), fill=MUTED)
    d.text((70, 470), 'Чемпіон світу · «Україна має талант 5»', font=font(28, False), fill=MUTED)
    im.save(os.path.join(SITE, 'img', 'og.jpg'), 'JPEG', quality=86, optimize=True)


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
    og()
    icons()
    print('готово:', OUT)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    main()
