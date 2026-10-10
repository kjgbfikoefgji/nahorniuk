"""Збірка сайту: src/ -> site/.

    python tools/build.py            зібрати site/ і синхронізувати хеш CSP у netlify.toml
    python tools/build.py --check    нічого не писати, лише перевірити, що site/ і
                                     netlify.toml відповідають src/ (код виходу 1, якщо ні)

Мова шаблонів (усе інше в файлах лишається як є):
  * {{ json "data/i18n-en.json" }}  підставляє вміст JSON-файла (словник англійської);
  * маркер на окремому рядку   {{ include "styles/01-fonts.css" }}
    замінюється вмістом файлу з src/ (вкладені include підтримуються);
  * {{ site_url }}, {{ telegram_url }}, {{ instagram_url }}, {{ mono_url }} ...
    підставляються з src/site.json: ключ JSON = назва маркера.

Збираються: src/index.html, src/robots.txt, src/sitemap.xml -> site/.
Після збірки рахується sha256 кожного виконуваного inline-<script>, і хеші
записуються в script-src у netlify.toml: вручну перераховувати їх не треба.

CSP дозволяє лише хеші inline-скриптів (без 'self'), тому JS і CSS не виносяться
в окремі файли на сайті: у src/ вони розділені, а збірка склеює їх назад в
один index.html. Лише стандартна бібліотека Python.
"""
import base64
from html.parser import HTMLParser
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
SITE = os.path.join(ROOT, 'site')
TOML = os.path.join(ROOT, 'netlify.toml')

# шаблон у src/ -> готовий файл у site/
PAGES = ['index.html', 'robots.txt', 'sitemap.xml']

INCLUDE = re.compile(r'^\{\{ include "([^"]+)" \}\}\n', re.M)
JSON = re.compile(r'\{\{ json "([^"]+)" \}\}')
VAR = re.compile(r'\{\{ (\w+) \}\}')
LEFTOVER = re.compile(r'\{\{ *\w+')
MAX_DEPTH = 8


def read(path):
    """Читає UTF-8 текст; CRLF (autocrlf у Windows) зводить до LF: від цього залежить хеш CSP."""
    with open(path, encoding='utf-8', newline='') as f:
        return f.read().replace('\r\n', '\n')


def src_path(rel):
    path = os.path.normpath(os.path.join(SRC, *rel.split('/')))
    if os.path.commonpath([path, SRC]) != SRC:
        sys.exit('шлях виходить за межі src/: %s' % rel)
    if not os.path.isfile(path):
        sys.exit('у src/ немає файла: %s' % rel)
    return path


def render(text, variables, depth=0):
    if depth > MAX_DEPTH:
        sys.exit('include вкладений глибше за %d рівнів (цикл?)' % MAX_DEPTH)

    def include(m):
        part = read(src_path(m.group(1)))
        if not part.endswith('\n'):
            part += '\n'
        return render(part, variables, depth + 1)

    def var(m):
        return variables.get(m.group(1), m.group(0))

    def as_json(m):
        data = json.loads(read(src_path(m.group(1))))
        # </ екранується, щоб рядок не міг закрити <script>
        return json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', r'<\/')

    return VAR.sub(var, JSON.sub(as_json, INCLUDE.sub(include, text)))


def load_variables():
    data = json.loads(read(os.path.join(SRC, 'site.json')))
    data['site_url'] = data['site_url'].rstrip('/')
    return data


def build_pages():
    """Повертає {назва файла в site/: готовий текст}."""
    variables = load_variables()
    pages = {}
    for name in PAGES:
        out = render(read(src_path(name)), variables)
        left = LEFTOVER.search(out)
        if left:
            sys.exit('у %s лишився нерозкритий маркер: %s' % (name, left.group(0)))
        pages[name] = out
    return pages


I18N_ATTRS = ('alt', 'aria-label', 'placeholder', 'title', 'content', 'data-cap')
# ключі, які скрипти ставлять уже в браузері: у розмітці їх немає, але вони потрібні
I18N_RUNTIME = {'Закрити меню', 'Відновити анімацію стрічок', 'Відновити'}


class _Texts(HTMLParser):
    """Видимі тексти й атрибути сторінки: саме їх обходить скрипт перекладу (12-i18n.js)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
            return
        d = dict(attrs)
        for a in I18N_ATTRS:
            v = d.get(a)
            if v and v.strip():
                self.found.append(v.strip())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.found.append(data.strip())


def i18n_report(html):
    """(немає в словнику, застарілі ключі). Текст без кирилиці (числа, бренди) перекладу не потребує."""
    d = json.loads(read(src_path('data/i18n-en.json')))
    p = _Texts()
    p.feed(html)
    found = set(p.found)
    missing = sorted(t for t in found if re.search('[А-Яа-яІіЇїЄєҐґ]', t) and t not in d)
    stale = sorted(k for k in d if k not in found and k not in I18N_RUNTIME)
    return missing, stale


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
    hashes = inline_script_hashes(pages['index.html'])
    if not hashes:
        sys.exit('у зібраному index.html немає жодного inline-скрипта')
    toml_old, toml_new = toml_with_hashes(hashes)
    missing, stale_keys = i18n_report(pages['index.html'])
    for t in missing:
        print('НЕМАЄ ПЕРЕКЛАДУ (src/data/i18n-en.json):', t[:90])
    for t in stale_keys:
        print('застарілий ключ словника:', t[:90])

    stale = [n for n in PAGES if read_current(os.path.join(SITE, n)) != pages[n]]
    toml_stale = toml_old != toml_new

    for h in hashes:
        print('CSP hash:', h)
    if check:
        for n in stale:
            print('site/%s НЕ відповідає src/' % n)
        if toml_stale:
            print('хеш CSP у netlify.toml НЕ відповідає site/index.html')
        if stale or toml_stale or missing:
            print('Запусти: python main.py build')
            return 1
        print('збирання актуальне')
        return 0

    for n in stale:
        write_text(os.path.join(SITE, n), pages[n])
    if toml_stale:
        write_text(TOML, toml_new)
    print('site/: оновлено %d з %d файлів%s' % (
        len(stale), len(PAGES), '; хеш у netlify.toml оновлено' if toml_stale else ''))
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
