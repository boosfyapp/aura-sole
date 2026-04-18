import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from urllib.parse import urlparse
from config import URL_CATEGORIA, aplicar_precio

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DELAY = 1.5  # seconds between requests


def get_soup(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def limpiar_precio(texto: str) -> float:
    limpio = re.sub(r"[^\d.]", "", texto.replace(",", ""))
    return float(limpio) if limpio else 0.0


def extraer_montos(tag) -> list[float]:
    montos = []
    for bdi in tag.select("bdi"):
        val = limpiar_precio(bdi.get_text())
        if val > 0:
            montos.append(val)
    return montos


def parsear_precios_tag(precio_tag):
    ins_tag = precio_tag.find("ins")
    target = ins_tag if ins_tag else precio_tag
    montos = extraer_montos(target)
    if len(montos) >= 2:
        return min(montos), max(montos)
    elif len(montos) == 1:
        return montos[0], montos[0]
    return 0.0, 0.0


def id_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else ""


def extraer_sku(soup) -> str:
    tag = soup.select_one(".sku, [itemprop='sku']")
    return tag.get_text(strip=True) if tag else ""


def extraer_imagenes(soup) -> list[str]:
    imagenes = []
    seen = set()

    # Try gallery anchor links first (full resolution)
    for a in soup.select(".woocommerce-product-gallery__image a"):
        url = a.get("href", "")
        if url and url.startswith("http") and "placeholder" not in url and url not in seen:
            seen.add(url)
            imagenes.append(url)

    if not imagenes:
        # Fall back to img data-large_image or src
        for img in soup.select(
            ".woocommerce-product-gallery__image img, "
            ".flex-viewport img, "
            ".product-gallery img"
        ):
            url = (
                img.get("data-large_image")
                or img.get("data-src")
                or img.get("src")
                or ""
            )
            if url and url.startswith("http") and "placeholder" not in url and url not in seen:
                seen.add(url)
                full = re.sub(r"-\d+x\d+(\.[a-zA-Z]+)$", r"\1", url)
                imagenes.append(full)

    if not imagenes:
        img = soup.select_one(".wp-post-image")
        if img:
            url = img.get("data-large_image") or img.get("src") or ""
            if url and url.startswith("http"):
                full = re.sub(r"-\d+x\d+(\.[a-zA-Z]+)$", r"\1", url)
                imagenes.append(full)

    return imagenes


def extraer_tallas(soup) -> list[dict]:
    select = None

    # Look for the row labeled "Talla" in the variations table
    for row in soup.select("table.variations tr, .variations tr"):
        label_el = row.find("th") or row.find("td", class_="label")
        if label_el and "talla" in label_el.get_text(strip=True).lower():
            select = row.find("select")
            break

    if not select:
        for s in soup.find_all("select"):
            name_id = (s.get("name", "") + s.get("id", "")).lower()
            if "talla" in name_id:
                select = s
                break

    if not select:
        return []

    # Parse WooCommerce variations JSON for stock info
    form = soup.select_one("form.variations_form")
    variations = []
    if form:
        raw = form.get("data-product_variations", "[]")
        try:
            variations = json.loads(raw)
        except Exception:
            pass

    tallas = []
    for option in select.find_all("option"):
        val = option.get("value", "").strip()
        if not val:
            continue

        disabled = option.has_attr("disabled")
        texto = option.get_text(strip=True).lower()
        agotado = "agotado" in texto or "out of stock" in texto

        disponible = not disabled and not agotado

        # Cross-check against variations stock data when available
        if variations and disponible:
            matching = [
                v for v in variations
                if any(
                    v_val == val
                    for v_key, v_val in v.get("attributes", {}).items()
                    if "talla" in v_key.lower()
                )
            ]
            if matching:
                disponible = any(v.get("is_in_stock", False) for v in matching)

        tallas.append({"numero": val, "disponible": disponible})

    return tallas


def scrape_producto_detalle(url: str, base: dict) -> dict | None:
    try:
        soup = get_soup(url)
    except Exception as e:
        print(f"    ERROR al cargar {url}: {e}")
        return None

    prod_id = id_from_url(url)
    sku = extraer_sku(soup)
    imagenes = extraer_imagenes(soup)
    if not imagenes and base.get("imagen"):
        imagenes = [base["imagen"]]
    tallas = extraer_tallas(soup)

    return {
        "id": prod_id,
        "nombre": base["nombre"],
        "sku": sku,
        "categoria": base["categoria"],
        "precio": base.get("precio_min", 0),
        "url": url,
        "imagenes": imagenes,
        "tallas": tallas,
    }


def obtener_subcategorias() -> list[dict]:
    soup = get_soup(URL_CATEGORIA)
    subcats = []
    for li in soup.select("li.product-category"):
        a = li.find("a")
        h2 = li.find("h2")
        if not a or not h2:
            continue
        nombre = h2.get_text(" ", strip=True)
        nombre = re.sub(r"\s*\d+\s*productos?\s*$", "", nombre, flags=re.IGNORECASE).strip()
        subcats.append({"nombre": nombre, "url": a["href"]})
    return subcats


def extraer_productos_pagina(soup, categoria: str) -> list:
    productos = []
    cards = [
        li for li in soup.select("li.product")
        if "product-category" not in li.get("class", [])
    ]

    for card in cards:
        nombre_tag = card.select_one(
            "h2.woocommerce-loop-product__title, h2.product-title, h2"
        )
        nombre = nombre_tag.get_text(strip=True) if nombre_tag else "Sin nombre"

        img_tag = card.select_one("img")
        imagen = ""
        if img_tag:
            for attr in ("src", "data-src", "data-lazy-src"):
                val = img_tag.get(attr, "")
                if val and "placeholder" not in val and val.startswith("http"):
                    imagen = val
                    break

        precio_tag = card.select_one("span.price")
        precio_min, precio_max = 0.0, 0.0
        if precio_tag:
            precio_min, precio_max = parsear_precios_tag(precio_tag)

        enlace = card.select_one(
            "a.woocommerce-loop-product__link, a.ast-loop-product__link, a[href]"
        )
        url_producto = enlace["href"] if enlace else ""

        cat_tag = card.select_one(
            "span.ast-woo-product-category, .product-category-badge"
        )
        cat = cat_tag.get_text(strip=True).upper() if cat_tag else categoria.upper()

        if precio_min == 0.0:
            continue

        productos.append({
            "nombre": nombre,
            "imagen": imagen,
            "precio_min": aplicar_precio(precio_min),
            "precio_max": aplicar_precio(precio_max),
            "url": url_producto,
            "categoria": cat,
        })

    return productos


def scrape_categoria(url_cat: str, nombre_cat: str, depth: int = 0) -> list:
    productos = []
    url_actual = url_cat
    pagina = 1

    while url_actual:
        indent = "    " + "  " * depth
        print(f"{indent}Página {pagina}: {url_actual}")
        try:
            soup = get_soup(url_actual)
        except Exception as e:
            print(f"{indent}ERROR: {e}")
            break

        nuevos = extraer_productos_pagina(soup, nombre_cat)

        nested_cats = [
            li for li in soup.select("li.product-category")
            if li.find("a") and li.find("h2")
        ]
        if not nuevos and nested_cats and depth < 3:
            print(f"{indent}→ Página con subcategorías ({len(nested_cats)}), recursando...")
            time.sleep(DELAY)
            for nc in nested_cats:
                nc_a = nc.find("a")
                nc_h2 = nc.find("h2")
                nc_url = nc_a["href"]
                nc_name = re.sub(
                    r"\s*\d+\s*productos?\s*$", "",
                    nc_h2.get_text(" ", strip=True),
                    flags=re.IGNORECASE
                ).strip()
                sub_prods = scrape_categoria(nc_url, nc_name or nombre_cat, depth + 1)
                productos.extend(sub_prods)
                time.sleep(DELAY)
            break

        print(f"{indent}→ {len(nuevos)} productos")
        productos.extend(nuevos)

        next_link = soup.select_one("a.next.page-numbers")
        if next_link and next_link["href"] != url_actual:
            url_actual = next_link["href"]
            pagina += 1
            time.sleep(DELAY)
        else:
            break

    return productos


def scrape() -> list:
    todos = []

    print(f"Obteniendo subcategorías de: {URL_CATEGORIA}")
    subcats = obtener_subcategorias()
    print(f"  {len(subcats)} subcategorías encontradas: {[s['nombre'] for s in subcats]}\n")

    for sc in subcats:
        print(f"  ▶ {sc['nombre']} ({sc['url']})")
        prods = scrape_categoria(sc["url"], sc["nombre"])
        todos.extend(prods)
        print(f"  Subtotal {sc['nombre']}: {len(prods)} productos\n")
        time.sleep(DELAY)

    return todos


def main():
    # Phase 1: scrape listing pages
    productos_base = scrape()
    print(f"\nTotal en listados: {len(productos_base)}")

    if not productos_base:
        print("No se extrajeron productos. Revisa la URL o si el sitio bloqueó el scraper.")
        return

    # Phase 2: deep scrape each product page
    print("Iniciando scraping profundo por producto...\n")
    productos = []
    total = len(productos_base)

    for i, base in enumerate(productos_base, 1):
        print(f"  [{i}/{total}] {base['nombre'][:55]}")
        if not base.get("url"):
            print("    Sin URL, omitiendo detalle")
            productos.append({
                "id": f"producto-{i}",
                "nombre": base["nombre"],
                "sku": "",
                "categoria": base["categoria"],
                "precio": base.get("precio_min", 0),
                "url": "",
                "imagenes": [base["imagen"]] if base.get("imagen") else [],
                "tallas": [],
            })
            continue

        detalle = scrape_producto_detalle(base["url"], base)
        if detalle:
            productos.append(detalle)
        else:
            productos.append({
                "id": id_from_url(base["url"]),
                "nombre": base["nombre"],
                "sku": "",
                "categoria": base["categoria"],
                "precio": base.get("precio_min", 0),
                "url": base["url"],
                "imagenes": [base["imagen"]] if base.get("imagen") else [],
                "tallas": [],
            })
        time.sleep(DELAY)

    datos = {
        "actualizado": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "total": len(productos),
        "productos": productos,
    }

    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"\nproductos.json guardado con {len(productos)} productos.")
    print("\n--- Muestra (primeros 3) ---")
    for p in productos[:3]:
        tallas_disp = [t["numero"] for t in p.get("tallas", []) if t["disponible"]]
        print(f"  {p['nombre'][:45]} | ${p['precio']} | Tallas disp: {tallas_disp[:6]}")


if __name__ == "__main__":
    main()
