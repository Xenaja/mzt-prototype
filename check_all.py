# -*- coding: utf-8 -*-
"""Сводка по всем блокам главной: прогоняет compare_block и собирает таблицу."""
import subprocess, sys, re
BLOCKS = ["2","3","4","5","6","7","8","9","10"]
print(f"{'блок':<6} {'расхождение':>12}  {'сдвиг':>8}")
print("-"*32)
worst=[]
for b in BLOCKS:
    r = subprocess.run([sys.executable, "compare_block.py", b],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=900)
    out = r.stdout or ""
    m0 = re.search(r"при сдвиге 0: ([\d.]+) %", out)
    m1 = re.search(r"лучший сдвиг: ([+-]?\d+) px -> ([\d.]+) %", out)
    if not m0:
        print(f"{b:<6} {'ошибка':>12}"); continue
    pct = float(m0.group(1)); dy = m1.group(1) if m1 else "?"
    mark = "ok" if pct < 5 else ("~" if pct < 9 else "!!")
    print(f"{b:<6} {pct:>10.1f} %  {dy:>8}  {mark}")
    worst.append((pct,b))
worst.sort(reverse=True)
print(f"\nхуже всего: " + ", ".join(f"блок {b} ({p:.1f} %)" for p,b in worst[:3]))
