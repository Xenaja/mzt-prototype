# -*- coding: utf-8 -*-
"""Достаёт из SVG-эталона все текстовые строки с координатами и параметрами."""
import io, re, html, json

P = "C:/Users/Acer/Documents/Projects/mzt/figma-export/Главная.svg"
s = io.open(P, encoding="utf-8", errors="ignore").read()

blocks = re.findall(r"<text\b([^>]*)>(.*?)</text>", s, re.S)
print(f"текстовых блоков: {len(blocks)}\n")

def attr(a, name):
    m = re.search(name + r'="([^"]*)"', a)
    return m.group(1) if m else ""

rows = []
for a, body in blocks:
    fam = attr(a, "font-family")
    size = attr(a, "font-size")
    weight = attr(a, "font-weight") or "normal"
    ls = attr(a, "letter-spacing")
    for m in re.finditer(r'<tspan[^>]*x="([\d.\-]+)"[^>]*y="([\d.\-]+)"[^>]*>(.*?)</tspan>', body, re.S):
        x, y, txt = float(m.group(1)), float(m.group(2)), html.unescape(m.group(3))
        txt = txt.replace("\u2028", "").strip()
        if txt:
            rows.append({"x": x, "y": y, "text": txt, "font": fam,
                         "size": float(size or 0), "weight": weight, "ls": ls})

rows.sort(key=lambda r: (r["y"], r["x"]))
json.dump(rows, open("C:/tmp/svg_lines.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("=== ПЕРВЫЙ ЭКРАН (y < 900) — строки как их разложила Figma ===\n")
for r in rows:
    if r["y"] < 900:
        print(f"  y={r['y']:>7.1f}  x={r['x']:>7.1f}  {r['size']:>5.1f}px/{r['weight']:<8} "
              f"ls={r['ls']:<7} «{r['text'][:56]}»")
print(f"\nвсего строк в файле: {len(rows)}, сохранено: C:/tmp/svg_lines.json")
