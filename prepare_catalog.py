# -*- coding: utf-8 -*-
"""
Разбирает выгрузку товаров Тильды в данные для прототипа.

Из выгрузки: 20 товаров, у каждого 15 вариантов (толщина × плотность),
характеристики, три вкладки текста и 11-12 фотографий.
Результат: prototype/data/catalog.json + сжатые фотографии.
"""
import csv, io, os, json, re, shutil, sys
from PIL import Image

HERE   = os.path.dirname(os.path.abspath(__file__))
CSV    = os.path.join(HERE, "source/tilda-export/Выгрузка_товаров.csv")
IMGDIR = os.path.join(HERE, "source/tilda-export/images")
OUTDIR = os.path.join(HERE, "prototype/assets/catalog-products")
DATA   = os.path.join(HERE, "prototype/data")

PHOTOS_PER_PRODUCT = 4      # главное фото и три дополнительных
PHOTO_W = 900               # для карточки товара
THUMB_W = 520               # для плитки каталога
QUALITY = 78


def strip_tags(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def parse_specs(text):
    """«Размеры термопанели: 1020х455 мм» → пары ключ-значение."""
    out = []
    for line in strip_tags(text).split("\n"):
        line = line.strip()
        if not line: continue
        if ":" in line:
            k, v = line.split(":", 1)
            out.append([k.strip(), v.strip()])
    return out


def parse_tab(raw):
    """template|#|Ярлык|#|Заголовок|#|Текст"""
    parts = (raw or "").split("|#|")
    if len(parts) < 3: return None
    return {"label": parts[1].strip(), "title": parts[2].strip(),
            "text": strip_tags(parts[3] if len(parts) > 3 else "")}


def num(v):
    v = (v or "").replace(",", ".").strip()
    try: return float(v)
    except ValueError: return None


def main():
    text = open(CSV, "rb").read().decode("utf-8-sig")
    delim = ";" if text.count(";") > text.count(",") else ","
    rows = list(csv.DictReader(io.StringIO(text), delimiter=delim))
    parents = [r for r in rows if not r["Parent UID"].strip()]
    kids    = [r for r in rows if r["Parent UID"].strip()]

    photo_dirs = sorted(os.listdir(IMGDIR))
    if os.path.exists(OUTDIR): shutil.rmtree(OUTDIR)
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)

    option_names, option_values = [], {}
    products, saved_bytes = [], 0

    for idx, p in enumerate(parents):
        mine = [k for k in kids if k["Parent UID"] == p["Tilda UID"]]
        variants = []
        for k in mine:
            opts = {}
            for part in k["Editions"].split(";"):
                if ":" in part:
                    name, val = part.split(":", 1)
                    name, val = name.strip(), val.strip()
                    opts[name] = val
                    if name not in option_names: option_names.append(name); option_values[name] = []
                    if val not in option_values[name]: option_values[name].append(val)
            variants.append({"sku": k["SKU"].strip(), "options": opts,
                             "price": num(k["Price"]), "price_old": num(k["Price Old"])})
        prices = [v["price"] for v in variants if v["price"]]

        # фотографии: папка соответствует порядковому номеру товара
        folder = next((d for d in photo_dirs if d.startswith(f"{idx+1:03d}_")), None)
        photos, thumb = [], None
        if folder:
            files = sorted(os.listdir(os.path.join(IMGDIR, folder)))[:PHOTOS_PER_PRODUCT]
            sub = os.path.join(OUTDIR, f"{idx+1:03d}")
            os.makedirs(sub, exist_ok=True)
            for n, f in enumerate(files, 1):
                src = os.path.join(IMGDIR, folder, f)
                with Image.open(src) as im:
                    im = im.convert("RGB")
                    w = PHOTO_W
                    im2 = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS) if im.width > w else im
                    dst = os.path.join(sub, f"{n:02d}.webp")
                    im2.save(dst, "WEBP", quality=QUALITY, method=6)
                    saved_bytes += os.path.getsize(dst)
                    photos.append(f"assets/catalog-products/{idx+1:03d}/{n:02d}.webp")
                    if n == 1:
                        t = im.resize((THUMB_W, round(im.height * THUMB_W / im.width)), Image.LANCZOS)
                        tp = os.path.join(sub, "thumb.webp")
                        t.save(tp, "WEBP", quality=QUALITY, method=6)
                        saved_bytes += os.path.getsize(tp)
                        thumb = f"assets/catalog-products/{idx+1:03d}/thumb.webp"

        cats = [c.strip() for c in p["Category"].split(";") if c.strip() and ">>>" not in c]
        sub_cats = [c.split(">>>")[-1].strip() for c in p["Category"].split(";") if ">>>" in c]

        products.append({
            "id": p["Tilda UID"].strip(),
            "title": p["Title"].strip(),
            "brand": p["Brand"].strip(),
            "mark": p["Mark"].strip(),
            "category": cats[0] if cats else "",
            "subcategory": sub_cats[0] if sub_cats else "",
            "color": p.get("Characteristics:Цвет", "").strip(),
            "design": p.get("Characteristics:Дизайн", "").strip(),
            "unit": "м²" if p.get("Unit") == "MTK" else p.get("Unit", "").strip(),
            "specs": parse_specs(p["Text"]),
            "seo_descr": strip_tags(p.get("SEO descr", "")),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "price_old": num(mine[0]["Price Old"]) if mine else None,
            "variants": variants,
            "tabs": [t for t in (parse_tab(p.get(f"Tabs:{i}")) for i in (1, 2, 3)) if t],
            "thumb": thumb,
            "photos": photos,
        })

    catalog = {
        "_note": "Собрано из выгрузки Тильды скриптом prepare_catalog.py. Вручную не править.",
        "options": [{"name": n, "values": option_values[n]} for n in option_names],
        "brands": sorted({p["brand"] for p in products if p["brand"]}),
        "colors": sorted({p["color"] for p in products if p["color"]}),
        "products": products,
    }
    out = os.path.join(DATA, "catalog.json")
    body = json.dumps(catalog, ensure_ascii=False, indent=1)
    io.open(out, "w", encoding="utf-8").write(body)

    # Прототип открывают с диска двойным щелчком, а по file:// браузер
    # запрещает fetch к локальным файлам. Поэтому те же данные кладём
    # обычным скриптом — он подключается тегом <script> и работает везде.
    js = os.path.join(DATA, "catalog.js")
    io.open(js, "w", encoding="utf-8").write(
        "/* Собрано prepare_catalog.py из выгрузки Тильды. Вручную не править. */\n"
        "window.MZT_CATALOG = " + body + ";\n")

    print(f"товаров: {len(products)}, вариантов у каждого: {len(products[0]['variants'])}")
    print(f"фотографий: {sum(len(p['photos']) for p in products)} + {len(products)} миниатюр, "
          f"{saved_bytes/1048576:.1f} МБ (было 77 МБ)")
    print(f"данные: {os.path.relpath(out, HERE)}, {os.path.getsize(out)/1024:.0f} КБ")
    print(f"        {os.path.relpath(js, HERE)}, {os.path.getsize(js)/1024:.0f} КБ (для открытия с диска)")


if __name__ == "__main__":
    main()
