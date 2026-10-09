# Влад Нагорнюк — сайт онлайн-тренера

Односторінковий статичний сайт (українською): послуги й ціни, результати клієнтів «до/після», відгуки, досягнення, FAQ, умови. Без фреймворків; Python потрібен лише для збірки й локального сервера.

## Швидкий старт

```
python main.py serve          # http://127.0.0.1:8830/ (з тими самими заголовками й CSP, що на Netlify)
python main.py build          # зібрати site/ із src/ і оновити хеші CSP у netlify.toml
python main.py check          # перевірити, що site/ і CSP актуальні
python main.py images         # оптимізувати фото з images/ (потрібен Pillow)
```

Потрібен Python 3.11+.

## Як вносити зміни

1. Правити **тільки `src/`** (розмітка, стилі, скрипти, `site.json`).
2. `python main.py build`.
3. Закомітити `src/`, `site/` і `netlify.toml` разом.

`site/index.html` згенерований, руками його не правити.

## Структура

```
src/        джерело: index.html-каркас, head/, partials/, sections/, styles/ (NN-*.css), scripts/ (NN-*.js), site.json
site/       те, що публікується: згенерований index.html, fonts/, img/, favicon.ico
tools/      build.py, serve.py, optimize_images.py
images/     сирі фото клієнтів (не в git)
Notes/      скріншоти відгуків (не в git)
```

## Налаштування

- Контакти, домен і посилання на оплату: `src/site.json`.
- Приватні значення: `.env` (шаблон `.env.example`), у git не потрапляє.
- Деплой на Netlify поки не налаштований: `NETLIFY_AUTH_TOKEN` і `NETLIFY_SITE_ID` чекають на новий проєкт. Налаштування публікації: `netlify.toml` (`publish = "site"`, build-команди немає, `site/` лежить у git уже зібраним).

## CSP

`netlify.toml` дозволяє виконувати лише inline-скрипти за sha256-хешем (без `'self'`), тому CSS і JS не виносяться в окремі файли. Після будь-якої правки скриптів обов'язково `python main.py build`, інакше браузер заблокує JS.
