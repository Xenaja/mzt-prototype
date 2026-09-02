# -*- coding: utf-8 -*-
"""
Сверка блока главной с эталоном из Figma.

    python compare_block.py 8

Снимает страницу целиком в Chrome (первый экран закрепляется на 900px, иначе
100vh растянется на всю высоту снимка), накладывает на figma-export/Главная.png
и считает долю несовпавших точек. Ищет лучший вертикальный сдвиг: если блок
уехал, это видно сразу и в пикселях.
"""
import os, sys, re, io, subprocess, shutil, json
from PIL import Image, ImageChops, ImageDraw
Image.MAX_IMAGE_PIXELS = None

HERE  = os.path.dirname(os.path.abspath(__file__))
REF   = os.path.join(HERE, "figma-export", "Главная.png")
SRC   = os.path.join(HERE, "prototype")
TMP   = "C:/tmp/mzt-shot"
SHOT  = os.path.join(TMP, "page.png")
W     = 1920
THRESH = 42

# блоки главной: имя -> (y, высота) из макета
BLOCKS = {
    "1": ("Первый экран",   0,  900, ".hero"),       "2": ("Готовые проекты", 1100, 1574, ".projects"),
    "3": ("Утепление",   2874,  800, ".insulation"), "4": ("Каталог",         3874,  802, ".catalog"),
    "5": ("Визуализатор",4876,  655, ".visual"),     "6": ("Почему выбирают", 5731,  484, ".why"),
    "7": ("Производство",6415,  681, ".prod"),       "8": ("Поможем",         7290, 1496, ".services"),
    "9": ("Отзывы",      8986,  776, ".reviews"),   "10": ("Найдите нас",     9962, 1284, ".dealers"),
    "11": ("Футер",     11441,  651, ".footer"),
}

def chrome():
    for p in ("C:/Program Files/Google/Chrome/Application/chrome.exe",
              "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
              os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")):
        if os.path.exists(p): return p
    found = shutil.which("chrome") or shutil.which("msedge")
    if found: return found
    sys.exit("не найден Chrome")

def shoot(total_h, keep, hide_dock=True):
    """Копия сайта с закреплённым первым экраном, снимок всей страницы.

    Изображения вне проверяемого блока прячем: при высоте снимка около
    11 000px Chrome перестаёт отрисовывать часть картинок, и они выходили
    белыми пятнами — то карта дилеров, то последние фотографии услуг.
    Геометрия при этом сохраняется полностью, а сравниваем мы всё равно
    только целевой блок."""
    if os.path.exists(TMP): shutil.rmtree(TMP)
    shutil.copytree(SRC, TMP)
    p = os.path.join(TMP, "index.html")
    s = io.open(p, encoding="utf-8").read()
    # снимаем дев-режим: оранжевые метки незакрытых данных рисуют рамку
    # и подпись, из-за них сверка показывала расхождение там, где его нет
    s = s.replace('<html lang="ru" data-env="dev">', '<html lang="ru">')
    s = re.sub(r'\s*data-pending="[^"]*"', '', s)
    # отложенная загрузка обрезает съёмку: последняя фотография блока
    # не успевала подгрузиться и место оставалось белым
    s = s.replace('loading="lazy"', 'loading="eager"')
    # при окне 900 первый экран даёт padding-top max(56, (900-540)/3) = 120
    s = s.replace("</head>", """<style>
      .hero, .hero__inner { min-height: 900px !important; }
      .hero__body { padding-top: 120px !important; }
      *, *::before, *::after { transition: none !important; animation: none !important; }
      /* плавающая панель перекрывала бы содержимое блока; на первом экране
         она часть макета, там её оставляем */
      %s
      img { visibility: hidden; }
      %s img, %s .dealers__map-shot { visibility: visible; }
    </style></head>""" % (".dock.is-floating { display: none !important; }" if hide_dock else "",
                          keep, keep))
    io.open(p, "w", encoding="utf-8").write(s)
    subprocess.run([chrome(), "--headless=old", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1",
                    f"--window-size={W},{total_h}", "--virtual-time-budget=45000",
                    f"--screenshot={SHOT}", "file:///" + p.replace("\\", "/")],
                   capture_output=True, timeout=180)
    if not os.path.exists(SHOT): sys.exit("снимок не сделан")
    return Image.open(SHOT).convert("RGB")

def score(a, b):
    d = ImageChops.difference(a, b).convert("L")
    px = d.getdata()
    return sum(1 for v in px if v > THRESH) / len(px) * 100, d

def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "8"
    name, y0, h, keep = BLOCKS[key]
    zones = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []

    ref_full = Image.open(REF).convert("RGB")
    # для первого экрана окно ровно 900: при большем панель успевает
    # открепиться и уходит к нижнему краю окна, как ей и положено
    total = h if key == "1" else min(ref_full.height, y0 + h + 400)
    mine = shoot(total, BLOCKS[key][3], key != "1")
    shift = 0

    ref = ref_full.crop((0, y0, W, y0 + h))
    print(f"\nБлок {key} «{name}» — y={y0}, высота {h}\n")

    best = (999, 0)
    for dy in range(-80, 81, 2):
        t = y0 - shift + dy
        if t < 0 or t + h > mine.height: continue
        pct, _ = score(ref, mine.crop((0, t, W, t + h)))
        if pct < best[0]: best = (pct, dy)
    print(f"  при сдвиге 0: {score(ref, mine.crop((0, y0 - shift, W, y0 - shift + h)))[0]:.1f} %")
    print(f"  лучший сдвиг: {best[1]:+d} px -> {best[0]:.1f} %")
    if best[1]:
        # положительный сдвиг: чтобы попасть в эталон, выборку в моём снимке
        # пришлось брать ниже — значит блок стоит ниже нужного и его поднимают
        way = "поднять" if best[1] > 0 else "опустить"
        print(f"  => блок ниже эталона на {best[1]} px" if best[1] > 0
              else f"  => блок выше эталона на {-best[1]} px")
        print(f"     {way} на {abs(best[1])} px: отступ сверху "
              f"{'уменьшить' if best[1] > 0 else 'увеличить'}")

    dy = best[1]
    got = mine.crop((0, y0 - shift + dy, W, y0 - shift + dy + h))
    pct, diff = score(ref, got)

    if zones:
        print(f"\n  {'зона':<24} {'расхождение':>12}")
        print("  " + "-" * 40)
        for zn, zx0, zy0, zx1, zy1 in zones:
            b = diff.crop((zx0, zy0, zx1, zy1))
            bad = sum(1 for v in b.getdata() if v > THRESH)
            zp = bad / max(len(list(b.getdata())), 1) * 100
            mark = "ok" if zp < 3 else ("~" if zp < 8 else "!!")
            print(f"  {zn:<24} {zp:>10.1f} %  {mark}")

    overlay = ref.copy()
    mask = diff.point(lambda v: 255 if v > THRESH else 0).convert("L")
    overlay.paste(Image.new("RGB", ref.size, (255, 0, 0)), (0, 0), mask)
    overlay.save(f"C:/tmp/blk{key}_diff.png")
    side = Image.new("RGB", (W, h * 2 + 20), (255, 255, 255))
    side.paste(ref, (0, 0)); side.paste(got, (0, h + 20))
    side.save(f"C:/tmp/blk{key}_side.png")
    mine.save("C:/tmp/mzt-shot/view.png")        # кадр целиком, для ручной проверки
    io.open("C:/tmp/mzt-shot/view.txt", "w").write(str(shift))
    print(f"\n  карта: C:/tmp/blk{key}_diff.png   рядом: C:/tmp/blk{key}_side.png")

main()
