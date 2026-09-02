# -*- coding: utf-8 -*-
"""Сверяет вёрстку первого экрана с эталоном из Figma и показывает расхождения."""
import os
from PIL import Image, ImageChops, ImageDraw
Image.MAX_IMAGE_PIXELS = None

REF_FULL = "C:/Users/Acer/Documents/Projects/mzt/figma-export/Главная.png"
MINE     = "C:/tmp/mine_hero.png"
W, H     = 1920, 900

ref = Image.open(REF_FULL).convert("RGB").crop((0, 0, W, H))
ref.save("C:/tmp/ref_hero.png")

mine = Image.open(MINE).convert("RGB")
if mine.size != (W, H):
    mine = mine.crop((0, 0, W, H))

diff = ImageChops.difference(ref, mine).convert("L")

# зоны первого экрана по макету
ZONES = [
    ("шапка",                 80,   30, 1840,  87),
    ("заголовок H1",          80,  207,  953, 359),
    ("подзаголовок",          80,  399,  513, 447),
    ("кнопки",                80,  527,  623, 579),
    ("карточка 8",          1650,  207, 1840, 347),
    ("карточка 25",         1650,  357, 1840, 497),
    ("карточка 105",        1650,  507, 1840, 647),
    ("карточка 7",          1650,  657, 1840, 797),
    ("нижняя панель",       1483,  822, 1840, 874),
]

THRESH = 42          # порог, ниже которого считаем совпадением (сглаживание, jpeg-шум)
print(f"{'зона':<22} {'площадь':>9} {'расхождение':>12}   вывод")
print("-" * 68)

report = []
for name, x0, y0, x1, y1 in ZONES:
    box = diff.crop((x0, y0, x1, y1))
    px = list(box.getdata())
    total = len(px)
    bad = sum(1 for v in px if v > THRESH)
    pct = bad / total * 100
    verdict = "совпадает" if pct < 1.5 else ("小 отличия" if pct < 8 else "РАСХОЖДЕНИЕ")
    verdict = verdict.replace("小 ", "мелкие ")
    print(f"{name:<22} {total:>9} {pct:>10.1f} %   {verdict}")
    report.append((name, pct, (x0, y0, x1, y1)))

# карта различий: эталон + красная подсветка
overlay = ref.copy()
mask = diff.point(lambda v: 255 if v > THRESH else 0).convert("L")
red = Image.new("RGB", ref.size, (255, 0, 0))
overlay.paste(red, (0, 0), mask)
dr = ImageDraw.Draw(overlay)
for name, pct, (x0, y0, x1, y1) in report:
    if pct >= 1.5:
        dr.rectangle([x0, y0, x1, y1], outline=(0, 120, 255), width=3)
overlay.save("C:/tmp/hero_diff.png")

# бок о бок
side = Image.new("RGB", (W, H * 2 + 12), (255, 255, 255))
side.paste(ref, (0, 0)); side.paste(mine, (0, H + 12))
side.save("C:/tmp/hero_side.png")
print("\nкарта различий: C:/tmp/hero_diff.png")
print("эталон / вёрстка: C:/tmp/hero_side.png")
