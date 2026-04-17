import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
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

DELAY = 1.2  # seconds between requests


def get_soup(url: str):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def limpiar_precio(texto: str) -> float:
    limpio = re.sub(r"[^\d.]", "", texto.replace(",", ""))
    return float(limpio) if limpio else 0.0


def extraer_montos(tag) -> list[float]:
    """Return all numeric price amounts found inside a BeautifulSoup tag."""
    montos = []
    for bdi in tag.select("bdi"):
        val = limpiar_precio(bdi.get_text())
        if val > 0:
            montos.append(val)
    return montos


def parsear_precios_tag(precio_tag):
    """
    Extract (precio_min, precio_max) from a WooCommerce <span class="price"> tag.
    Handles:
      - Simple price: $279.00
      - Range: $279.00 – $349.00
      - Sale with range: <del>$999</del> <ins>$429 – $499</ins>
    """
    # Prefer <ins> (sale price) over <del> (crossed-out old price)
    ins_tag = precio_tag.find("ins")
    target = ins_tag if ins_tag else precio_tag

    montos = extraer_montos(target)

    if len(montos) >= 2:
        return min(montos), max(montos)
    elif len(montos) == 1:
        return montos[0], montos[0]
    return 0.0, 0.0


def obtener_subcategorias() -> list[dict]:
    """Scrape the main damas page to collect all subcategory URLs and names."""
    soup = get_soup(URL_CATEGORIA)
    subcats = []
    for li in soup.select("li.product-category"):
        a = li.find("a")
        h2 = li.find("h2")
        if not a or not h2:
            continue
        nombre = h2.get_text(" ", strip=True)
        # Remove the "XX productos" count suffix
        nombre = re.sub(r"\s*\d+\s*productos?\s*$", "", nombre, flags=re.IGNORECASE).strip()
        subcats.append({"nombre": nombre, "url": a["href"]})
    return subcats


def extraer_productos_pagina(soup, categoria: str) -> list:
    """Extract individual products from a WooCommerce shop page."""
    productos = []

    # Exclude category list items
    cards = [
        li for li in soup.select("li.product")
        if "product-category" not in li.get("class", [])
    ]

    for card in cards:
        # Nombre
        nombre_tag = card.select_one(
            "h2.woocommerce-loop-product__title, h2.product-title, h2"
        )
        nombre = nombre_tag.get_text(strip=True) if nombre_tag else "Sin nombre"

        # Imagen
        img_tag = card.select_one("img")
        imagen = ""
        if img_tag:
            for attr in ("src", "data-src", "data-lazy-src"):
                val = img_tag.get(attr, "")
                if val and "placeholder" not in val and val.startswith("http"):
                    imagen = val
                    break

        # Precio
        precio_tag = card.select_one("span.price")
        precio_min, precio_max = 0.0, 0.0
        if precio_tag:
            precio_min, precio_max = parsear_precios_tag(precio_tag)

        # URL del producto
        enlace = card.select_one("a.woocommerce-loop-product__link, a.ast-loop-product__link, a[href]")
        url_producto = enlace["href"] if enlace else ""

        # Categoría badge
        cat_tag = card.select_one("span.ast-woo-product-category, .product-category-badge")
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
    """Scrape all pages of one category, recursively following nested subcategories."""
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

        # If this page is a subcategory listing (no products, only category links), recurse
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
                nc_name = re.sub(r"\s*\d+\s*productos?\s*$", "", nc_h2.get_text(" ", strip=True), flags=re.IGNORECASE).strip()
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
    productos = scrape()
    print(f"Total de productos extraídos: {len(productos)}")

    if not productos:
        print("No se extrajeron productos. Revisa la URL o si el sitio bloqueó el scraper.")
        return

    datos = {
        "actualizado": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "total": len(productos),
        "productos": productos,
    }

    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print("productos.json guardado correctamente.")
    print("\n--- Muestra (primeros 5 productos) ---")
    for p in productos[:5]:
        print(f"  {p['nombre']} | ${p['precio_min']} – ${p['precio_max']} | {p['categoria']}")
        print(f"    img: {p['imagen'][:70]}...")


if __name__ == "__main__":
    main()
