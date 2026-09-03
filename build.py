# -*- coding: utf-8 -*-
"""
Сборка прототипа для показа заказчику.

Что делает:
  1. копирует prototype/ в release/build/;
  2. выбрасывает служебные файлы разработки (PENDING, DECISIONS, content.json);
  3. проверяет, что не осталось тяжёлых PNG (рабочие файлы уже в WebP);
  4. снимает dev-режим и оранжевые метки незакрытых данных;
  5. кладёт записку «КАК ОТКРЫТЬ.txt» и собирает zip в release/.

Запуск:  python build.py
"""
import os, re, io, shutil, zipfile
from PIL import Image

HERE  = os.path.dirname(os.path.abspath(__file__))
SRC   = os.path.join(HERE, "prototype")
BUILD = os.path.join(HERE, "release", "build")
ZIP   = os.path.join(HERE, "release", "mzt-prototip.zip")
DOCS  = os.path.join(HERE, "docs")   # то же самое для GitHub Pages

DEV_ONLY = ("PENDING.md", "DECISIONS.md", "content.json",
            "BLOCK-CHECKLIST.md", "figma-comments.json",
            "data/catalog.json",   # дублирует catalog.js, который и подключается
            "partials")            # источник для assemble_shared.py, в самих
                                    # страницах уже расставлено — заказчику эти
                                    # заготовки с {{плейсхолдерами}} не нужны
HERO_W   = 2560     # первый экран
PHOTO_W  = 1750     # снимки в карточках
FULL_W   = 1920     # оригиналы для просмотра на весь экран
QUALITY  = 82

NOTE = """МЗТ — прототип

КАК ОТКРЫТЬ
Распакуйте папку целиком и откройте файл index.html двойным щелчком.
Откроется в браузере. Шрифт лежит внутри папки, интернет нужен только
для визуализатора и живой карты дилеров.

ЧТО МОЖНО ПОСМОТРЕТЬ
Главная страница собрана целиком по утверждённому макету — от первого экрана
до подвала. Открывать на компьютере, ширина окна от 1280 пикселей.

- Кнопка «Рассчитать стоимость» и «Калькулятор» внизу справа открывают
  расчёт фасада. Расчёт работает: измените площадь, материал, доставку и
  монтаж — состав и сумма пересчитаются.
  Заявка НЕ отправляется: это прототип, подтверждение показывается для примера.
- Кнопка «Визуализатор» открывает отдельную страницу с подбором отделки.
- Блок «Готовые проекты»: три объекта с описанием и фотографиями.
  Нажмите на любой снимок — он раскроется на весь экран, между фотографиями
  можно листать стрелками на экране или клавишами влево-вправо.

- Блок «Утепление и отделка одновременно»: фотография панели в разрезе
  и четыре преимущества термопанелей.

- Блок «Каталог фасадных решений»: группы термопанелей и категории товаров.
  При наведении на плитку фотография приближается.

- Блок «Визуализатор»: описание и вид интерфейса. Нажатие открывает
  страницу визуализатора.

- Блок «Почему выбирают нас»: четыре преимущества завода.

- Блок «Производство МЗТ»: раскрывающийся список — нажмите на любой пункт.

- Блок «Поможем реализовать проект»: шесть услуг с ценами — расчёт, монтаж,
  замер, шеф-монтаж, 3d визуализация и доставка.

- Блок «Отзывы о работе с нами»: три отзыва со снимками готовых объектов.

- КАТАЛОГ (кнопка «Каталог» в меню): 20 термопанелей из вашей выгрузки.
  Подбор по бренду, цвету, толщине и плотности; сортировка по цене и названию.
  Выбор толщины и плотности пересчитывает цену прямо в списке.
- КАРТОЧКА ТОВАРА (нажмите на любую панель): снимки с увеличением по нажатию,
  выбор толщины и плотности — цена и артикул меняются, характеристики,
  разделы «Описание», «Применение», «Монтаж» и похожие товары.

- Блок «Найдите нас в своём городе»: карта дилеров и форма заявки.
  Нажмите на карту — откроется живая карта Яндекса.
  Форму можно заполнить и отправить: поля проверяются, показывается
  подтверждение. Заявка НЕ отправляется, это прототип.

ЧЕГО ПОКА НЕТ
- Каталог и карточка собраны без макета, по стилю главной: макетов этих
  страниц в Figma не оказалось.
- Точек дилеров на карте — ждём адреса, тогда появятся метки.
- Ссылки «Читать больше отзывов», «Выбрать город», «Стать дилером»
  пока никуда не ведут: этих страниц в макете нет.
- Ссылки «Политика конфиденциальности», «Согласие на обработку данных»,
  «Сертификаты» и иконки соцсетей пока никуда не ведут — ждём адреса страниц.
- Мобильная версия в этот этап не входит. Открывать на компьютере.
"""


def main():
    if os.path.exists(BUILD):
        shutil.rmtree(BUILD)
    shutil.copytree(SRC, BUILD)

    for f in DEV_ONLY:
        p = os.path.join(BUILD, *f.split("/"))
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)

    # рабочие файлы переведены в WebP ещё в prototype/, поэтому здесь только
    # проверка: если PNG появился снова, его надо перевести, а не тащить в сборку
    heavy = []
    for root, _, files in os.walk(os.path.join(BUILD, "assets")):
        for fn in files:
            if fn.lower().endswith(".png"):
                p = os.path.join(root, fn)
                heavy.append((os.path.relpath(p, BUILD), os.path.getsize(p)))
    if heavy:
        print("ВНИМАНИЕ: в сборке остались PNG — перевести в WebP:")
        for rel, size in heavy:
            print(f"  {rel} — {size/1024:.0f} КБ")

    total = sum(os.path.getsize(os.path.join(r, f))
                for r, _, fs in os.walk(os.path.join(BUILD, "assets")) for f in fs)
    print(f"изображения и графика: {total/1048576:.1f} МБ")

    # dev-режим и метки
    for name in ("index.html", "catalog.html", "product.html", "visualizer.html"):
        p = os.path.join(BUILD, name)
        if not os.path.exists(p):
            continue
        s = io.open(p, encoding="utf-8").read()
        s = s.replace('<html lang="ru" data-env="dev">', '<html lang="ru">')
        s = re.sub(r'\s*data-pending="[^"]*"', '', s)
        io.open(p, "w", encoding="utf-8").write(s)
        ok = 'data-pending' not in s and 'data-env' not in s
        print(f"{name}: {'очищен' if ok else 'ПРОВЕРИТЬ — что-то осталось'}")

    io.open(os.path.join(BUILD, "КАК ОТКРЫТЬ.txt"), "w", encoding="utf-8").write(NOTE)

    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(BUILD):
            for fn in sorted(files):
                full = os.path.join(root, fn)
                z.write(full, os.path.join("mzt-prototip", os.path.relpath(full, BUILD)))

    # та же сборка идёт в docs/ — с неё работает онлайн-версия на GitHub Pages
    if os.path.exists(DOCS):
        shutil.rmtree(DOCS)
    shutil.copytree(BUILD, DOCS)
    io.open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8").write("")
    print(f"онлайн-версия: docs/ ({sum(len(f) for _, _, f in os.walk(DOCS))} файлов)")

    print(f"\nАрхив: {ZIP}")
    print(f"Размер: {os.path.getsize(ZIP)/1024:.0f} КБ")


if __name__ == "__main__":
    main()
