#!/usr/bin/env python3
"""Проверка статического сайта перед публикацией на GitHub Pages.

Скрипт не требует сторонних библиотек и выполняет базовый линтинг:
- наличие обязательных файлов проекта;
- корректность базовой HTML-разметки и закрытие тегов;
- наличие обязательных мета-тегов;
- существование локальных файлов, на которые ссылаются страницы;
- баланс фигурных скобок в CSS.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
STYLE = ROOT / "css" / "style.css"

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

SKIP_PREFIXES = ("#", "http://", "https://", "mailto:", "tel:", "data:", "javascript:")


class PageParser(HTMLParser):
    """Собирает ссылки, идентификаторы и проверяет вложенность тегов."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.ids: list[str] = []
        self.refs: list[str] = []

    def _collect(self, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        for name in ("src", "href"):
            value = data.get(name)
            if value:
                self.refs.append(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(attrs)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._collect(attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"лишний закрывающий тег </{tag}>")
            return
        if self.stack[-1] != tag:
            self.errors.append(
                f"нарушен порядок тегов: ожидался </{self.stack[-1]}>, найден </{tag}>"
            )
            return
        self.stack.pop()


def check_file(path: Path, label: str, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"не найден файл {label}: {path.relative_to(ROOT)}")
        return ""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        errors.append(f"файл {label} пустой")
    return text


def check_html(html: str, errors: list[str]) -> None:
    parser = PageParser()
    parser.feed(html)
    parser.close()

    if not html.lstrip().lower().startswith("<!doctype html>"):
        errors.append("в начале index.html отсутствует <!DOCTYPE html>")
    if not re.search(r"<html\b[^>]*\blang\s*=", html, re.IGNORECASE):
        errors.append("у тега <html> не указан атрибут lang")
    if not re.search(r"<meta\b[^>]*charset\s*=\s*[\"']?utf-8", html, re.IGNORECASE):
        errors.append("не указана кодировка UTF-8")
    if not re.search(r"<meta\b[^>]*name\s*=\s*[\"']viewport", html, re.IGNORECASE):
        errors.append("отсутствует meta viewport для мобильных устройств")
    if not re.search(r"<title>\s*\S+.*?</title>", html, re.IGNORECASE | re.DOTALL):
        errors.append("не заполнен тег <title>")
    if not re.search(r"<link\b[^>]*rel\s*=\s*[\"']stylesheet", html, re.IGNORECASE):
        errors.append("не подключён файл стилей")

    errors.extend(parser.errors)
    if parser.stack:
        errors.append("не закрыты теги: " + ", ".join(parser.stack))

    duplicates = {item for item in parser.ids if parser.ids.count(item) > 1}
    if duplicates:
        errors.append("повторяются id: " + ", ".join(sorted(duplicates)))

    for ref in parser.refs:
        value = ref.strip()
        if not value or value.lower().startswith(SKIP_PREFIXES):
            continue
        local = value.split("?", 1)[0].split("#", 1)[0]
        if not local:
            continue
        target = (ROOT / local).resolve()
        if ROOT not in target.parents and target != ROOT:
            errors.append(f"ссылка выходит за пределы проекта: {value}")
        elif not target.exists():
            errors.append(f"файл по ссылке не найден: {value}")


def check_css(css: str, errors: list[str]) -> None:
    clean = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    clean = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", "", clean)
    opens, closes = clean.count("{"), clean.count("}")
    if opens != closes:
        errors.append(f"в style.css нарушен баланс скобок: {{ = {opens}, }} = {closes}")
    if "{" not in clean:
        errors.append("style.css не содержит ни одного правила")


def main() -> int:
    errors: list[str] = []

    html = check_file(INDEX, "index.html", errors)
    css = check_file(STYLE, "css/style.css", errors)

    if html:
        check_html(html, errors)
    if css:
        check_css(css, errors)

    print("Проверка статического сайта")
    print(f"  index.html  — {len(html.splitlines())} строк")
    print(f"  style.css   — {len(css.splitlines())} строк")

    if errors:
        print("\nНайдены проблемы:")
        for error in errors:
            print(f"  ✗ {error}")
        return 1

    print("\n✓ Проверка пройдена: разметка и стили корректны.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
