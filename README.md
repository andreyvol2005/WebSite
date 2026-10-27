# WebSite

[![Deploy static site](https://github.com/andreyvol2005/WebSite/actions/workflows/deploy.yml/badge.svg)](https://github.com/andreyvol2005/WebSite/actions/workflows/deploy.yml)

Личный сайт-портфолио студента ГУАП. Статическая вёрстка на HTML и CSS, которая автоматически публикуется на GitHub Pages.

**Сайт:** https://andreyvol2005.github.io/WebSite/

## Как устроена публикация

При каждом push в ветку `main` запускается workflow `.github/workflows/deploy.yml`:

1. `lint` — проверяет HTML и CSS скриптом `scripts/check_site.py`;
2. `deploy` — собирает артефакт и публикует сайт на GitHub Pages.

Если проверка не проходит, деплой не запускается — на сайте остаётся предыдущая версия.

## Структура проекта

- `index.html` — страница сайта;
- `css/style.css` — стили;
- `scripts/check_site.py` — линтер разметки и стилей;
- `.github/workflows/deploy.yml` — CI/CD-пайплайн.
