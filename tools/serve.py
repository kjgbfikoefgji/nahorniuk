"""Локальний сервер для перевірки сайту ДО деплою на Netlify.

Віддає папку site/ (її публікує Netlify) і відтворює з netlify.toml (через tomllib):
  * усі [[headers]] (for = "/*", "/img/og.jpg", ...) - зокрема Content-Security-Policy,
    тож порушення CSP видно в консолі браузера так само, як на Netlify;
  * [[redirects]] зі status = 404 (force = true), якщо вони там з'являться.

Запуск:  python main.py serve [порт]      (типово 8830)

Тільки для локальної перевірки (на Netlify цього файлу немає):
  * До CSP локально дописується "report-uri /__csp": браузер шле туди звіти про порушення,
    сервер складає їх в пам'ять і віддає на GET /__csp-log (JSON), чистить на POST /__csp-clear.
    Правила CSP від цього не змінюються.
  * Якщо в netlify.toml більше одного правила дає Content-Security-Policy для одного
    шляху - у консоль сервера іде попередження (Netlify комбінує такі політики).
"""
import fnmatch
import gzip  # GZIP_DEV: сжатие як на Netlify
import json
import mimetypes
import os
import re
import sys
import threading
import time
import tomllib
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
TOML = os.path.join(ROOT, 'netlify.toml')

# Реєстр Windows інколи віддає .js як text/plain, а з nosniff такий скрипт не виконається.
for ext, mime in {
    '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.html': 'text/html', '.json': 'application/json', '.woff2': 'font/woff2',
    '.webp': 'image/webp', '.svg': 'image/svg+xml', '.png': 'image/png',
    '.jpg': 'image/jpeg', '.mp4': 'video/mp4', '.webm': 'video/webm',
}.items():
    mimetypes.add_type(mime, ext)

CSP_LOG = []
CSP_LOCK = threading.Lock()


def load_rules():
    """Читає netlify.toml заново на кожен запит: правки видно без перезапуску."""
    with open(TOML, 'rb') as f:
        cfg = tomllib.load(f)
    return cfg.get('headers', []), cfg.get('redirects', [])


def pat_to_re(pattern):
    """Netlify: '*' - splat (будь-які символи, включно з '/' і порожній рядок)."""
    out = ''
    for ch in pattern:
        out += '.*' if ch == '*' else re.escape(ch)
    return re.compile('^' + out + '$')


def match(pattern, path):
    return bool(pat_to_re(pattern).match(path))


class Handler(SimpleHTTPRequestHandler):
    server_version = 'nahorniuk-dev'

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    def guess_type(self, path):
        t = super().guess_type(path)
        # Netlify віддає текстові типи з charset=utf-8
        if t.startswith('text/') or t in ('application/json', 'text/javascript'):
            return t + '; charset=utf-8' if 'charset' not in t else t
        return t

    # ---- шлях запиту без query/hash ----
    def req_path(self):
        return self.path.split('?', 1)[0].split('#', 1)[0]

    # ---- 404-редіректи з netlify.toml ----
    def blocked(self, path):
        _, redirects = load_rules()
        for r in redirects:
            if int(r.get('status', 301)) != 404:
                continue
            if match(r.get('from', ''), path):
                return True
        return False

    def send_blocked(self):
        body = '<!doctype html><meta charset="utf-8"><title>404</title><h1>404 Not Found</h1>'.encode('utf-8')
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    # ---- заголовки з [[headers]] ----
    def end_headers(self):
        path = self.req_path()
        headers, _ = load_rules()
        merged = {}
        for rule in headers:
            if not match(rule.get('for', ''), path):
                continue
            for name, value in (rule.get('values') or {}).items():
                key = name.lower()
                if key in merged:
                    if key == 'content-security-policy':
                        sys.stderr.write('WARN: кілька CSP для %s - Netlify їх скомбінує\n' % path)
                        merged[key] = (name, merged[key][1] + ', ' + value)
                    else:
                        merged[key] = (name, merged[key][1] + ', ' + value)
                else:
                    merged[key] = (name, value)
        if 'content-security-policy' in merged:
            name, value = merged['content-security-policy']
            if 'report-uri' not in value:
                value = value.rstrip().rstrip(';') + '; report-uri /__csp'
            merged['content-security-policy'] = (name, value)
        if 'cache-control' not in merged:
            merged['cache-control'] = ('Cache-Control', 'no-cache')
        for name, value in merged.values():
            self.send_header(name, value)
        super().end_headers()

    # ---- методи ----
    def do_GET(self):
        path = self.req_path()
        if path == '/__csp-log':
            with CSP_LOCK:
                body = json.dumps(CSP_LOG, ensure_ascii=False, indent=1).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.blocked(path):
            self.send_blocked()
            return
        # GZIP_DEV: Netlify віддає html/css/js стиснутими; без цього заміри
        # на повільній мережі показують завантаження 290 КБ замість ~55.
        ae = self.headers.get('Accept-Encoding', '')
        fs = self.translate_path(path)
        if os.path.isdir(fs) and os.path.isfile(os.path.join(fs, 'index.html')):
            fs = os.path.join(fs, 'index.html')
        if 'gzip' in ae and not os.environ.get('NOGZIP') and os.path.isfile(fs) and fs.endswith(('.html', '.css', '.js', '.json')):
            data = gzip.compress(open(fs, 'rb').read(), 6)
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(fs))
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        super().do_GET()

    def do_HEAD(self):
        if self.blocked(self.req_path()):
            self.send_blocked()
            return
        super().do_HEAD()

    def do_POST(self):
        path = self.req_path()
        length = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(length) if length else b''
        if path == '/__csp':
            try:
                data = json.loads(raw.decode('utf-8', 'replace') or '{}')
            except ValueError:
                data = {'raw': raw.decode('utf-8', 'replace')[:500]}
            rep = data.get('csp-report', data) if isinstance(data, dict) else data
            with CSP_LOCK:
                CSP_LOG.append({'t': time.strftime('%H:%M:%S'), 'report': rep})
            sys.stderr.write('CSP-VIOLATION: %s\n' % json.dumps(rep, ensure_ascii=False)[:400])
            self.send_response(204)
            self.end_headers()
            return
        if path == '/__csp-clear':
            with CSP_LOCK:
                CSP_LOG.clear()
            self.send_response(204)
            self.end_headers()
            return
        self.send_response(405)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write('%s - %s\n' % (self.log_date_time_string(), fmt % args))


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    port = int(args[0]) if args else 8830
    srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print('Dev-сервер: http://127.0.0.1:%d/  (корінь: %s)' % (port, SITE), flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == '__main__':
    main()
