# -*- coding: utf-8 -*-
"""Достаёт фоновую графику футера из эталонного SVG страницы.
Разбор координат грубый, но устойчивый: команды V/H дают одну координату,
поэтому чётность чисел в пути не гарантирована. Отбираем по попаданию
чисел в вертикальный диапазон футера."""
import io, re, os

SRC = "C:/Users/Acer/Documents/Projects/mzt/figma-export/Главная.svg"
OUT = "C:/Users/Acer/Documents/Projects/mzt/prototype/assets/patterns/footer-bg.svg"

Y0, Y1 = 11400, 12500      # футер начинается на 11441, графика 1033 высотой
XMAX = 1920

s = io.open(SRC, encoding="utf-8", errors="ignore").read()
paths = re.findall(r'<path\b[^>]*?d="([^"]+)"[^>]*?fill="([^"]*)"[^>]*?/>', s)
print(f"path с заливкой всего: {len(paths)}")

keep, xs, ys = [], [], []
for d, fill in paths:
    if fill.lower() not in ("white", "#fff", "#ffffff"):
        continue
    nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', d)]
    in_footer = [n for n in nums if Y0 <= n <= Y1]
    if not in_footer:
        continue
    maybe_x = [n for n in nums if 0 <= n <= XMAX]
    if not maybe_x:
        continue
    keep.append(d)
    xs += maybe_x
    ys += in_footer

print(f"элементов фоновой графики: {len(keep)}")
if not keep:
    raise SystemExit("не нашлось")

bx0, bx1 = min(xs), max(xs)
by0, by1 = min(ys), max(ys)
w, h = bx1 - bx0, by1 - by0
print(f"область: x {bx0:.0f}..{bx1:.0f}   y {by0:.0f}..{by1:.0f}   {w:.0f}×{h:.0f}")

body = "\n".join(f'<path d="{d}" fill="white"/>' for d in keep)
svg = (f'<svg width="{w:.0f}" height="{h:.0f}" '
       f'viewBox="{bx0:.2f} {by0:.2f} {w:.2f} {h:.2f}" '
       f'fill="none" xmlns="http://www.w3.org/2000/svg">\n'
       f'<g opacity="0.5">\n{body}\n</g>\n</svg>\n')
io.open(OUT, "w", encoding="utf-8").write(svg)
print(f"записано: footer-bg.svg  ({os.path.getsize(OUT)/1024:.0f} КБ)")
