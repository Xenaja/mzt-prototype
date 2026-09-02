# -*- coding: utf-8 -*-
"""
Скачивает ОРИГИНАЛЫ фотографий из Figma — те файлы, которые дизайнер загрузил
в макет, в их полном разрешении.

Зачем отдельно от export_images.py:
  тот скрипт просит Figma ОТРИСОВАТЬ слой, поэтому размер результата равен
  размеру слоя в макете. Миниатюра 117×80 в двойном масштабе даёт 234×160,
  хотя внутри неё лежит фотография 1672×941. Здесь мы берём саму фотографию.

Важно: эндпоинт /v1/files/{key}/images ничего не рендерит, поэтому квота
на рендер изображений (в которую упирается export_images.py) его не касается.

Запуск:
    Windows PowerShell:  $env:FIGMA_TOKEN="figd_..."
    python fetch_originals.py
"""
import os, sys, json, time, requests

HERE     = os.path.dirname(os.path.abspath(__file__))
OUT_DIR  = os.path.join(HERE, "source", "figma-originals")
MAP_FILE = os.path.join(OUT_DIR, "map.json")
CACHE    = "C:/tmp/mzt_doc.json"

FILE_KEY = "4xhAaa2IkIqUddv23e0i3i"
PAGE     = "Для разработчика (десктоп)"
FRAME    = "Главная"
API      = "https://api.figma.com/v1"
TIMEOUT  = 120

TOKEN = os.environ.get("FIGMA_TOKEN", "").strip()
if not TOKEN:
    sys.exit("Не задан FIGMA_TOKEN — см. шапку файла.")
HEADERS = {"X-Figma-Token": TOKEN}


def load_document():
    """Структура файла: из кэша, иначе запрашиваем и кэшируем."""
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    print("Загружаю структуру файла…")
    r = requests.get(f"{API}/files/{FILE_KEY}", headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(data, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    return data


def size_of(node):
    bb = node.get("absoluteBoundingBox") or {}
    return [round(bb.get("width") or 0), round(bb.get("height") or 0)]


def collect_refs(doc):
    """node_id -> сведения о заливке-изображении, по блокам главной."""
    found = {}
    for page in doc["document"].get("children") or []:
        if page.get("name") != PAGE:
            continue
        for top in page.get("children") or []:
            if top.get("name") != FRAME or size_of(top)[1] < 5000:
                continue
            for block in top.get("children") or []:
                bname = block.get("name", "?")

                def walk(node):
                    for fill in node.get("fills") or []:
                        if fill.get("type") == "IMAGE" and fill.get("imageRef"):
                            found[node["id"]] = {
                                "imageRef":   fill["imageRef"],
                                "scaleMode":  fill.get("scaleMode", ""),
                                "block":      bname,
                                "layer_size": size_of(node),
                            }
                    for child in node.get("children") or []:
                        walk(child)

                walk(block)
    return found


def natural_size(path):
    """Размер картинки по заголовку файла, без полного разбора."""
    import struct
    with open(path, "rb") as f:
        head = f.read(4096)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        return [w, h]
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] == 0xFF and head[i + 1] in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return [w, h]
            i += 1
    return [0, 0]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = load_document()
    refs = collect_refs(doc)
    uniq = sorted({v["imageRef"] for v in refs.values()})
    print(f"Мест с фотографиями: {len(refs)} | уникальных изображений: {len(uniq)}")

    print("Запрашиваю ссылки на оригиналы…")
    r = requests.get(f"{API}/files/{FILE_KEY}/images", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        sys.exit(f"Не удалось получить ссылки: HTTP {r.status_code} {r.text[:200]}")
    links = r.json().get("meta", {}).get("images", {})
    print(f"Ссылок получено: {len(links)}\n")

    ok = skipped = failed = 0
    for i, ref in enumerate(uniq, 1):
        dest = os.path.join(OUT_DIR, ref + ".png")
        if os.path.exists(dest):
            skipped += 1
            continue
        url = links.get(ref)
        if not url:
            print(f"  [{i}/{len(uniq)}] ссылки нет для {ref[:12]}…")
            failed += 1
            continue
        try:
            img = requests.get(url, timeout=TIMEOUT)
        except requests.RequestException as e:
            print(f"  [{i}/{len(uniq)}] сеть: {type(e).__name__}")
            failed += 1
            continue
        if img.status_code != 200:
            print(f"  [{i}/{len(uniq)}] HTTP {img.status_code}")
            failed += 1
            continue
        with open(dest, "wb") as f:
            f.write(img.content)
        ok += 1
        print(f"  [{i}/{len(uniq)}] {ref[:12]}…  {natural_size(dest)}  "
              f"{os.path.getsize(dest)/1024:.0f} КБ")
        time.sleep(0.2)

    # карта: какой ноде какой файл соответствует
    out = {}
    for node_id, info in refs.items():
        path = os.path.join(OUT_DIR, info["imageRef"] + ".png")
        out[node_id] = dict(info,
                            file=info["imageRef"] + ".png",
                            natural_size=natural_size(path) if os.path.exists(path) else [0, 0])
    json.dump(out, open(MAP_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"\nСкачано: {ok}, уже было: {skipped}, не удалось: {failed}")
    print(f"Папка: {OUT_DIR}")
    print(f"Карта: {MAP_FILE}")


if __name__ == "__main__":
    main()
