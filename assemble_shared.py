# -*- coding: utf-8 -*-
"""
Единый источник для трёх блоков, которые были скопированы руками
в index.html, catalog.html, product.html и visualizer.html — и успели
разойтись (см. DECISIONS.md, 2026-09-03): перенос в подписи разработчика
чинился только на главной, попап калькулятора на странице визуализатора
отформатирован иначе, а у product.html активный пункт навигации остался
без aria-current.

Правки шапки/подвала/попапа калькулятора теперь вносятся один раз —
в prototype/partials/topbar.html, footer.html, calc-modal.html — а этот
скрипт расставляет их по всем четырём страницам. Раздел «шапка» ещё и
параметризован (какая ссылка ведёт на себя саму, какой пункт активен),
поэтому для неё правится не сама разметка, а таблица PAGES/NAV ниже.

Запуск:  python assemble_shared.py
Раздел prototype/partials/*.html можно менять свободно — эти файлы и есть
источник правды. Сами prototype/*.html — уже нет: правки внутри меток
PARTIAL:* при следующем запуске будут затёрты содержимым партиала.
"""
import io, os, re

HERE  = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "prototype")
PARTS = os.path.join(PROTO, "partials")

PAGES = {
    "index.html":      {"home": True,  "current": None},
    "catalog.html":     {"home": False, "current": "catalog"},
    "product.html":     {"home": False, "current": "catalog"},
    "visualizer.html":  {"home": False, "current": "visualizer"},
}

# порядок и подписи пунктов меню — единственное место, где их менять
NAV = [
    ("catalog",     "Каталог",      "catalog.html"),
    ("services",    "Услуги",       "#services"),
    ("projects",    "Проекты",      "#projects"),
    ("about",       "О заводе",     "#about"),
    ("contacts",    "Контакты",     "#contacts"),
    ("visualizer",  "Визуализатор", "visualizer.html"),
]


def href_for(href, home):
    """На главной якоря ведут прямо на блок; с внутренних страниц —
    сначала на главную, потом на блок."""
    return href if (home or not href.startswith("#")) else "index.html" + href


def render_topbar(home, current):
    tpl = io.open(os.path.join(PARTS, "topbar.html"), encoding="utf-8").read()
    items = []
    for key, label, href in NAV:
        cur = key == current
        cls = "navchip is-current" if cur else "navchip"
        attrs = ' aria-current="page"' if cur else ""
        items.append(f'<li><a class="{cls}" href="{href_for(href, home)}"{attrs}>{label}</a></li>')
    return (tpl
            .replace("{{LOGO_HREF}}", "#main" if home else "index.html")
            .replace("{{NAV_ITEMS}}", "\n        ".join(items)))


def render_footer(home):
    tpl = io.open(os.path.join(PARTS, "footer.html"), encoding="utf-8").read()
    for anchor in ("#services", "#projects", "#about", "#contacts"):
        tpl = tpl.replace(f'href="{anchor}"', f'href="{href_for(anchor, home)}"')
    return tpl


def render_calc_modal():
    return io.open(os.path.join(PARTS, "calc-modal.html"), encoding="utf-8").read()


def extract_balanced(html, open_tag_pattern):
    """Находит блок от открывающего тега до его же парного закрывающего,
    считая вложенность — обычный non-greedy regex здесь не подходит,
    внутри попапа калькулятора десятки своих <div>."""
    m = re.search(open_tag_pattern, html)
    if not m:
        return None
    start = m.start()
    depth = 0
    i = m.end() - 1  # встать на конец открывающего тега (после '>')
    tag_rx = re.compile(r"<(/?)div\b[^>]*>")
    pos = m.end()
    depth = 1
    while depth > 0:
        tm = tag_rx.search(html, pos)
        if not tm:
            raise ValueError("не нашёл парный </div> — разметка повреждена")
        depth += -1 if tm.group(1) else 1
        pos = tm.end()
    return start, pos


def replace_block(html, open_tag_pattern, is_balanced_div, new_content):
    if is_balanced_div:
        span = extract_balanced(html, open_tag_pattern)
        if not span:
            return html, False
        start, end = span
        return html[:start] + new_content + html[end:], True
    else:
        m = re.search(open_tag_pattern, html, re.S)
        if not m:
            return html, False
        return html[:m.start()] + new_content + html[m.end():], True


def main():
    calc_modal = render_calc_modal()
    changed_files = 0

    for name, ctx in PAGES.items():
        path = os.path.join(PROTO, name)
        if not os.path.exists(path):
            print(f"  {name}: файла нет, пропущено")
            continue
        html = io.open(path, encoding="utf-8").read()
        original = html
        touched = []

        html, ok = replace_block(html, r"<header class=\"topbar\">.*?</header>",
                                  False, render_topbar(ctx["home"], ctx["current"]))
        if ok: touched.append("шапка")

        html, ok = replace_block(html, r"<footer class=\"footer\" id=\"contacts\">.*?</footer>",
                                  False, render_footer(ctx["home"]))
        if ok: touched.append("подвал")

        html, ok = replace_block(html, r"<div class=\"ef-calc-modal\"[^>]*>",
                                  True, calc_modal)
        if ok: touched.append("попап калькулятора")

        if html != original:
            io.open(path, "w", encoding="utf-8").write(html)
            changed_files += 1
            print(f"  {name}: обновлено ({', '.join(touched)})")
        else:
            print(f"  {name}: без изменений")

    print(f"\nготово, файлов изменено: {changed_files}")


if __name__ == "__main__":
    main()
