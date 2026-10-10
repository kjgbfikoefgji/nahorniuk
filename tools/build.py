"""Збірка сайту: src/ -> site/.

    python tools/build.py            зібрати site/ і синхронізувати хеш CSP у netlify.toml
    python tools/build.py --check    нічого не писати, лише перевірити, що site/ і
                                     netlify.toml відповідають src/ (код виходу 1, якщо ні)

Мова шаблонів (усе інше в файлах лишається як є):
  * маркер на окремому рядку   {{ include "styles/01-fonts.css" }}
    замінюється вмістом файлу з src/ (вкладені include підтримуються);
  * {{ site_url }}, {{ telegram_url }}, {{ instagram_url }}, {{ mono_url }} ...
    підставляються з src/site.json: ключ JSON = назва маркера.

Збираються: src/index.html (дві мови: site/index.html і site/en/index.html), src/robots.txt, src/sitemap.xml -> site/.
Переклади англійської версії лежать у src/en/ з тими самими відносними шляхами, що й українські файли.
Після збірки рахується sha256 кожного виконуваного inline-<script>, і хеші
записуються в script-src у netlify.toml: вручну перераховувати їх не треба.

CSP дозволяє лише хеші inline-скриптів (без 'self'), тому JS і CSS не виносяться
в окремі файли на сайті: у src/ вони розділені, а збірка склеює їх назад в
один index.html. Лише стандартна бібліотека Python.
"""
import base64
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
SITE = os.path.join(ROOT, 'site')
TOML = os.path.join(ROOT, 'netlify.toml')

# (готовий файл у site/, шаблон у src/, мова). Англійська версія збирається з того самого
# index.html, але кожен include спершу шукається в src/en/ (там лежать переклади), а якщо
# файла там немає, береться український із src/. Так CSS і більшість JS спільні.
PAGES = [
    ('index.html', 'index.html', 'uk'),
    ('en/index.html', 'index.html', 'en'),
    ('robots.txt', 'robots.txt', 'uk'),
    ('sitemap.xml', 'sitemap.xml', 'uk'),
]

INCLUDE = re.compile(r'^\{\{ include "([^"]+)" \}\}\n', re.M)
VAR = re.compile(r'\{\{ (\w+) \}\}')
LEFTOVER = re.compile(r'\{\{ *\w+')
MAX_DEPTH = 8


def read(path):
    """Читає UTF-8 текст; CRLF (autocrlf у Windows) зводить до LF: від цього залежить хеш CSP."""
    with open(path, encoding='utf-8', newline='') as f:
        return f.read().replace('\r\n', '\n')


def src_path(rel, lang='uk'):
    path = os.path.normpath(os.path.join(SRC, *rel.split('/')))
    if os.path.commonpath([path, SRC]) != SRC:
        sys.exit('шлях виходить за межі src/: %s' % rel)
    if lang != 'uk':
        loc = os.path.normpath(os.path.join(SRC, lang, *rel.split('/')))
        if os.path.isfile(loc):
            return loc
    if not os.path.isfile(path):
        sys.exit('у src/ немає файла: %s' % rel)
    return path


def render(text, variables, depth=0, lang='uk'):
    if depth > MAX_DEPTH:
        sys.exit('include вкладений глибше за %d рівнів (цикл?)' % MAX_DEPTH)

    def include(m):
        part = read(src_path(m.group(1), lang))
        if not part.endswith('\n'):
            part += '\n'
        return render(part, variables, depth + 1, lang)

    def var(m):
        return variables.get(m.group(1), m.group(0))

    return VAR.sub(var, INCLUDE.sub(include, text))


def load_variables():
    data = json.loads(read(os.path.join(SRC, 'site.json')))
    data['site_url'] = data['site_url'].rstrip('/')
    data['url_uk'] = data['site_url'] + '/'
    data['url_en'] = data['site_url'] + '/en/'
    return data


def build_pages():
    """Повертає {назва файла в site/: готовий текст}."""
    variables = load_variables()
    pages = {}
    for name, tpl, lang in PAGES:
        v = dict(variables, html_lang=lang, url_self=variables['url_en'] if lang == 'en' else variables['url_uk'])
        out = render(read(src_path(tpl)), v, lang=lang)
        left = LEFTOVER.search(out)
        if left:
            sys.exit('у %s лишився нерозкритий маркер: %s' % (name, left.group(0)))
        pages[name] = out
    return pages


def inline_script_hashes(html):
    """sha256 усіх inline-скриптів, які виконує браузер.

    <script src=...> пропускається; блоки даних на кшталт application/ld+json
    браузер не виконує, CSP на них не діє.
    """
    hashes = []
    for m in re.finditer(r'<script\b([^>]*)>(.*?)</script>', html, re.S | re.I):
        attrs, body = m.group(1), m.group(2)
        if re.search(r'\bsrc\s*=', attrs, re.I):
            continue
        t = re.search(r'\btype\s*=\s*["\']?([^"\'\s>]+)', attrs, re.I)
        if t and t.group(1).lower() not in ('text/javascript', 'application/javascript', 'module'):
            continue
        digest = hashlib.sha256(body.encode('utf-8')).digest()
        hashes.append('sha256-' + base64.b64encode(digest).decode())
    return hashes


def toml_with_hashes(hashes):
    """Текст netlify.toml із актуальними хешами в script-src (інші джерела лишаються)."""
    toml = read(TOML)
    quoted = ' '.join("'%s'" % h for h in hashes)

    def fix(mo):
        keep = [x for x in mo.group(1).split()
                if not x.startswith("'sha256-") and x != "'none'"]
        return 'script-src ' + ' '.join(keep + [quoted]) + ';'

    new, n = re.subn(r'script-src ([^;]*);', fix, toml)
    if n != 1:
        sys.exit('у netlify.toml має бути рівно один script-src, знайшов %d' % n)
    return toml, new


def read_current(path):
    return read(path) if os.path.isfile(path) else None


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main(argv):
    check = '--check' in argv
    pages = build_pages()
    hashes = []
    for html in ('index.html', 'en/index.html'):
        for h in inline_script_hashes(pages[html]):
            if h not in hashes:
                hashes.append(h)
    if not hashes:
        sys.exit('у зібраному index.html немає жодного inline-скрипта')
    toml_old, toml_new = toml_with_hashes(hashes)

    stale = [n for n in pages if read_current(os.path.join(SITE, *n.split('/'))) != pages[n]]
    toml_stale = toml_old != toml_new

    for h in hashes:
        print('CSP hash:', h)
    if check:
        for n in stale:
            print('site/%s НЕ відповідає src/' % n)
        if toml_stale:
            print('хеш CSP у netlify.toml НЕ відповідає site/index.html')
        if stale or toml_stale:
            print('Запусти: python main.py build')
            return 1
        print('збирання актуальне')
        return 0

    for n in stale:
        write_text(os.path.join(SITE, *n.split('/')), pages[n])
    if toml_stale:
        write_text(TOML, toml_new)
    print('site/: оновлено %d з %d файлів%s' % (
        len(stale), len(pages), '; хеш у netlify.toml оновлено' if toml_stale else ''))
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
