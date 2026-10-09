"""Точка входу сайту Влада Нагорнюка.

    python main.py build              зібрати site/ із src/ (і синхронізувати хеш CSP у netlify.toml)
    python main.py check              перевірити, що site/ і хеш CSP актуальні (код виходу 1, якщо ні)
    python main.py serve [порт]       локальний сервер із заголовками Netlify (типово 8830)
    python main.py serve --lan        те саме, але доступний у локальній мережі (для перегляду на телефоні)
    python main.py images             оптимізувати фото з images/ у site/img/out і згенерувати og.jpg, favicon

Без аргументів запускається сервер. Правити треба src/, а site/index.html
збирається автоматично: після правки виконай build і закоміть обидві папки.
"""
import runpy
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent / "tools"

COMMANDS = {
    "build": ("build.py", []),
    "check": ("build.py", ["--check"]),
    "serve": ("serve.py", []),
    "images": ("optimize_images.py", []),
}


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    command = args[0] if args else "serve"
    if command not in COMMANDS:
        sys.exit("невідома команда %r. Доступні: %s" % (command, ", ".join(COMMANDS)))
    script, fixed = COMMANDS[command]
    sys.argv = [script] + fixed + args[1:]
    runpy.run_path(str(TOOLS / script), run_name="__main__")


if __name__ == "__main__":
    main()
