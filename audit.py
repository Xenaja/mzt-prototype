# -*- coding: utf-8 -*-
"""
Проверка прототипа перед показом: доступность, клавиатура, поведение окна.
Запуск: python audit.py
"""
import subprocess, os, io, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "prototype")
TMP  = "C:/tmp/mzt-audit"

def chrome():
    for p in ("C:/Program Files/Google/Chrome/Application/chrome.exe",
              "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"):
        if os.path.exists(p): return p
    sys.exit("не найден Chrome")

PROBE = """<script>
window.addEventListener('load', function () {
  var R = [];
  function say(k, v) { R.push(k + ' :: ' + v); }
  try {
    var de = document.documentElement;

    var noAlt = [];
    document.querySelectorAll('img').forEach(function (i) {
      if (!i.hasAttribute('alt')) noAlt.push(i.getAttribute('src') || '?');
    });
    say('картинки без alt', noAlt.length ? noAlt.join(', ') : 'нет');

    var noName = [];
    document.querySelectorAll('a, button').forEach(function (e) {
      var n = (e.textContent || '').trim() || e.getAttribute('aria-label') || e.getAttribute('title') || '';
      if (!n) noName.push((e.className || e.tagName).toString().slice(0, 30));
    });
    say('без доступного имени', noName.length ? noName.join(' | ') : 'нет');

    var list = document.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select, [tabindex]:not([tabindex="-1"])');
    var hidden = 0, noRing = [];
    list.forEach(function (e) {
      var was = getComputedStyle(e);
      if (was.display === 'none' || was.visibility === 'hidden') { hidden++; return; }
      var before = [was.outlineWidth, was.boxShadow, was.borderBottomColor, was.backgroundColor].join('|');
      try { e.focus(); } catch (x) { return; }
      var now = getComputedStyle(e);
      var after = [now.outlineWidth, now.boxShadow, now.borderBottomColor, now.backgroundColor].join('|');
      var ring = (now.outlineStyle !== 'none' && parseFloat(now.outlineWidth) > 0);
      if (!ring && before === after) {
        noRing.push(((e.textContent || '').trim() || e.className.toString()).slice(0, 20));
      }
    });
    say('элементов для клавиатуры', list.length + ', скрытых ' + hidden);
    say('без заметного фокуса', noRing.length ? (noRing.length + ': ' + noRing.slice(0, 6).join(' | ')) : 'нет');

    var dead = 0;
    document.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (h === '#' || h === '') dead++;
    });
    say('ссылок-заглушек', dead);

    var lv = [];
    document.querySelectorAll('h1,h2,h3,h4').forEach(function (h) { lv.push(+h.tagName[1]); });
    var jumps = [];
    for (var i = 1; i < lv.length; i++) { if (lv[i] - lv[i-1] > 1) jumps.push(lv[i-1] + '-' + lv[i]); }
    var ones = lv.filter(function (l) { return l === 1; }).length;
    say('заголовки', 'h1: ' + ones + ', всего ' + lv.length + (jumps.length ? ', пропуски ' + jumps.join(',') : ', без пропусков'));

    say('горизонтальная прокрутка', (de.scrollWidth - de.clientWidth) + ' px');

    var over = [];
    document.querySelectorAll('section, footer, header, .dock, .footer__inner').forEach(function (e) {
      var r = e.getBoundingClientRect();
      if (r.width > 0 && (r.right > de.clientWidth + 1 || r.left < -1)) {
        over.push((e.className || e.tagName).toString().slice(0, 24));
      }
    });
    say('вылезает за окно', over.length ? over.slice(0, 5).join(' | ') : 'ничего');

    var dock = document.querySelector('.dock');
    if (dock) {
      var dr = dock.getBoundingClientRect();
      say('панель кнопок', 'снизу ' + Math.round(de.clientHeight - dr.bottom) + ' px, справа ' +
          Math.round(de.clientWidth - dr.right) + ' px');
    }
  } catch (err) {
    say('сбой проверки', err.message);
  }
  document.title = 'AUDIT|' + R.join(' // ');
});
</script>"""

def run(width, height, page="index.html", query=""):
    p = os.path.join(TMP, page)
    r = subprocess.run([chrome(), "--headless=old", "--disable-gpu", "--force-device-scale-factor=1",
                        f"--window-size={width},{height}", "--virtual-time-budget=20000", "--dump-dom",
                        "file:///" + p.replace("\\", "/") + query], capture_output=True, timeout=240)
    dom = r.stdout.decode("utf-8", "ignore")
    m = re.search(r"<title>AUDIT\|([^<]*)</title>", dom)
    return m.group(1) if m else None

PAGES = [("index.html",      "",                  "главная"),
         ("catalog.html",    "",                  "каталог"),
         ("product.html",    "?id=508818845952",  "карточка товара"),
         ("visualizer.html", "",                  "визуализатор")]


def main():
    if os.path.exists(TMP): shutil.rmtree(TMP)
    shutil.copytree(SRC, TMP)

    for page, _, _ in PAGES:
        p = os.path.join(TMP, page)
        if not os.path.exists(p): continue
        s = io.open(p, encoding="utf-8").read()
        s = s.replace('<html lang="ru" data-env="dev">', '<html lang="ru">')
        s = re.sub(r'\s*data-pending="[^"]*"', '', s)
        s = s.replace("</body>", PROBE + "</body>")
        io.open(p, "w", encoding="utf-8").write(s)

    for page, query, label in PAGES:
        if not os.path.exists(os.path.join(TMP, page)): continue
        for w, h in ((1920, 1080), (1280, 800)):
            out = run(w, h, page, query)
            print(f"\n=== {label} · {w}x{h} ===")
            if not out:
                print("  проверка не ответила"); continue
            for line in out.split(" // "):
                if " :: " in line:
                    k, v = line.split(" :: ", 1)
                    print(f"  {k:<26} {v}")


main()
