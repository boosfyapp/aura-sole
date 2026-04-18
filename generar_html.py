import json
import re
from datetime import datetime
from urllib.parse import urlparse
from config import NOMBRE_TIENDA, WHATSAPP_NUMBER


def cargar_productos() -> tuple[list, str]:
    try:
        with open("productos.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos.get("productos", []), datos.get("actualizado", "")
    except FileNotFoundError:
        print("AVISO: productos.json no encontrado. Generando HTML con catálogo vacío.")
        return [], datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def get_product_id(p: dict, i: int) -> str:
    if p.get("id"):
        return p["id"]
    if p.get("url"):
        path = urlparse(p["url"]).path.strip("/")
        slug = path.split("/")[-1]
        if slug:
            return slug
    nombre = p.get("nombre", str(i)).lower()
    nombre = re.sub(r"[áàäâ]", "a", nombre)
    nombre = re.sub(r"[éèëê]", "e", nombre)
    nombre = re.sub(r"[íìïî]", "i", nombre)
    nombre = re.sub(r"[óòöô]", "o", nombre)
    nombre = re.sub(r"[úùüû]", "u", nombre)
    nombre = re.sub(r"[^a-z0-9\s-]", "", nombre)
    nombre = re.sub(r"\s+", "-", nombre.strip())
    return nombre[:60]


def generar_cards(productos: list) -> str:
    if not productos:
        return '<p class="empty-catalog">No hay productos disponibles en este momento.</p>'

    cards = []
    for i, p in enumerate(productos):
        nombre_esc = p["nombre"].replace('"', "&quot;").replace("'", "&#39;")
        prod_id = get_product_id(p, i)

        # Support both new (imagenes list) and old (imagen string) format
        imagenes = p.get("imagenes", [])
        imagen = imagenes[0] if imagenes else p.get("imagen", "")

        precio = p.get("precio", p.get("precio_min", 0))
        precio_max = p.get("precio_max", precio)
        precio_display = (
            f"${precio:,} – ${precio_max:,}"
            if precio != precio_max
            else f"${precio:,}"
        )

        cat = p.get("categoria", "DAMAS")

        card = f"""
        <div class="product-card" data-nombre="{nombre_esc.lower()}" data-id="{prod_id}" onclick="abrirProducto('{prod_id}')">
          <div class="card-img-wrap">
            <img
              src="{imagen}"
              alt="{nombre_esc}"
              loading="lazy"
              onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22%3E%3Crect width=%22300%22 height=%22300%22 fill=%22%23f5f5f5%22/%3E%3Ctext x=%22150%22 y=%22155%22 text-anchor=%22middle%22 fill=%22%23bbb%22 font-size=%2214%22%3ESin imagen%3C/text%3E%3C/svg%3E'"
            />
          </div>
          <div class="card-body">
            <p class="card-categoria">{cat}</p>
            <h3 class="card-nombre">{p['nombre']}</h3>
            <p class="card-precio">{precio_display}</p>
            <button class="btn-agregar" onclick="event.stopPropagation(); abrirProducto('{prod_id}')">
              Ver tallas
            </button>
          </div>
        </div>"""
        cards.append(card)

    return "\n".join(cards)


def generar_html(productos: list, actualizado: str) -> str:
    cards_html = generar_cards(productos)
    total_productos = len(productos)
    fecha_display = actualizado or datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{NOMBRE_TIENDA}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --gold: #C9A84C;
      --gold-light: #e8c97a;
      --black: #111111;
      --gray: #6b6b6b;
      --gray-light: #f5f5f5;
      --white: #ffffff;
      --shadow: 0 2px 12px rgba(0,0,0,0.09);
      --shadow-hover: 0 8px 28px rgba(0,0,0,0.16);
      --radius: 12px;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--white);
      color: var(--black);
      min-height: 100vh;
    }}

    /* ── HEADER ── */
    header {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: var(--white);
      border-bottom: 1px solid #e8e8e8;
      padding: 0 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 64px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}

    .logo {{
      font-family: 'Playfair Display', serif;
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--black);
      letter-spacing: 0.02em;
    }}

    .logo span {{ color: var(--gold); }}

    .cart-btn {{
      background: none;
      border: 2px solid var(--black);
      border-radius: 50px;
      padding: 0.4rem 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-family: 'Inter', sans-serif;
      font-weight: 600;
      font-size: 0.9rem;
      transition: background 0.2s, color 0.2s;
    }}

    .cart-btn:hover {{ background: var(--black); color: var(--white); }}

    .cart-count {{
      background: var(--gold);
      color: var(--white);
      border-radius: 50%;
      min-width: 20px;
      height: 20px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0 4px;
    }}

    /* ── HERO ── */
    .hero {{
      background: linear-gradient(135deg, var(--black) 0%, #2c2c2c 100%);
      color: var(--white);
      text-align: center;
      padding: 3rem 1.5rem 2.5rem;
    }}

    .hero h1 {{
      font-family: 'Playfair Display', serif;
      font-size: clamp(1.8rem, 5vw, 3rem);
      margin-bottom: 0.5rem;
    }}

    .hero h1 span {{ color: var(--gold); }}

    .hero p {{
      color: #ccc;
      margin-bottom: 1.5rem;
      font-size: 0.95rem;
    }}

    .search-wrap {{
      max-width: 500px;
      margin: 0 auto;
      position: relative;
    }}

    #buscador {{
      width: 100%;
      padding: 0.75rem 1.2rem;
      border-radius: 50px;
      border: none;
      font-size: 1rem;
      font-family: 'Inter', sans-serif;
      outline: none;
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }}

    /* ── MAIN GRID ── */
    main {{
      max-width: 1300px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
    }}

    .section-title {{
      font-family: 'Playfair Display', serif;
      font-size: 1.5rem;
      margin-bottom: 1.5rem;
      color: var(--black);
    }}

    .section-title span {{
      font-family: 'Inter', sans-serif;
      font-size: 0.85rem;
      font-weight: 400;
      color: var(--gray);
      margin-left: 0.5rem;
    }}

    #catalogo {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }}

    @media (min-width: 600px) {{
      #catalogo {{ grid-template-columns: repeat(3, 1fr); }}
    }}

    @media (min-width: 1024px) {{
      #catalogo {{ grid-template-columns: repeat(4, 1fr); gap: 1.4rem; }}
    }}

    /* ── PRODUCT CARD ── */
    .product-card {{
      background: var(--white);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
      transition: transform 0.2s, box-shadow 0.2s;
      display: flex;
      flex-direction: column;
      cursor: pointer;
    }}

    .product-card:hover {{
      transform: translateY(-4px);
      box-shadow: var(--shadow-hover);
    }}

    .card-img-wrap {{
      width: 100%;
      aspect-ratio: 1 / 1;
      overflow: hidden;
      background: var(--gray-light);
    }}

    .card-img-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }}

    .product-card:hover .card-img-wrap img {{
      transform: scale(1.05);
    }}

    .card-body {{
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      flex: 1;
    }}

    .card-categoria {{
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      color: var(--gold);
      text-transform: uppercase;
      margin-bottom: 0.3rem;
    }}

    .card-nombre {{
      font-size: 0.82rem;
      font-weight: 600;
      line-height: 1.35;
      margin-bottom: 0.5rem;
      flex: 1;
    }}

    .card-precio {{
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      font-weight: 700;
      color: var(--gold);
      margin-bottom: 0.75rem;
    }}

    .btn-agregar {{
      width: 100%;
      padding: 0.55rem;
      background: var(--black);
      color: var(--white);
      border: none;
      border-radius: 8px;
      font-family: 'Inter', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }}

    .btn-agregar:hover {{ background: var(--gold); }}

    .empty-catalog {{
      grid-column: 1/-1;
      text-align: center;
      padding: 3rem;
      color: var(--gray);
      font-size: 1.1rem;
    }}

    /* ── PRODUCT MODAL ── */
    #product-modal {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.65);
      z-index: 200;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }}

    #product-modal.open {{ display: flex; }}

    #product-panel {{
      background: var(--white);
      border-radius: var(--radius);
      width: min(880px, 100%);
      max-height: 90vh;
      overflow-y: auto;
      display: grid;
      grid-template-columns: 1fr 1fr;
      position: relative;
      animation: fadeUp 0.25s ease;
    }}

    @media (max-width: 640px) {{
      #product-panel {{
        grid-template-columns: 1fr;
        max-height: 95vh;
      }}
    }}

    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}

    .close-modal {{
      position: absolute;
      top: 0.85rem;
      right: 0.85rem;
      background: var(--white);
      border: none;
      border-radius: 50%;
      width: 34px;
      height: 34px;
      font-size: 1.3rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10;
      box-shadow: var(--shadow);
      color: var(--gray);
      line-height: 1;
      transition: color 0.2s;
    }}

    .close-modal:hover {{ color: var(--black); }}

    .modal-gallery {{
      background: var(--gray-light);
      border-radius: var(--radius) 0 0 var(--radius);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 320px;
    }}

    @media (max-width: 640px) {{
      .modal-gallery {{
        border-radius: var(--radius) var(--radius) 0 0;
        min-height: 260px;
      }}
    }}

    .modal-main-img-wrap {{
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 1.25rem;
    }}

    .modal-main-img-wrap img {{
      max-width: 100%;
      max-height: 360px;
      object-fit: contain;
      border-radius: 8px;
    }}

    .modal-thumbnails {{
      display: flex;
      gap: 0.45rem;
      padding: 0.65rem 1rem;
      overflow-x: auto;
      flex-shrink: 0;
    }}

    .modal-thumbnails:empty {{ display: none; }}

    .thumb {{
      width: 58px;
      height: 58px;
      object-fit: cover;
      border-radius: 6px;
      cursor: pointer;
      border: 2px solid transparent;
      flex-shrink: 0;
      transition: border-color 0.2s;
    }}

    .thumb.active, .thumb:hover {{ border-color: var(--gold); }}

    .modal-info {{
      padding: 1.5rem 1.5rem 1.5rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }}

    .modal-cat {{
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: var(--gold);
      text-transform: uppercase;
    }}

    .modal-nombre {{
      font-family: 'Playfair Display', serif;
      font-size: 1.35rem;
      line-height: 1.3;
    }}

    .modal-precio {{
      font-family: 'Playfair Display', serif;
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--gold);
    }}

    /* ── STOCK BAR ── */
    .stock-section {{ display: flex; flex-direction: column; gap: 0.3rem; }}

    .stock-bar-bg {{
      background: #ebebeb;
      border-radius: 4px;
      height: 6px;
      overflow: hidden;
    }}

    .stock-bar-fill {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.5s ease;
      width: 100%;
    }}

    .stock-msg {{
      font-size: 0.78rem;
      font-weight: 600;
    }}

    /* ── TALLAS ── */
    .tallas-section {{ display: flex; flex-direction: column; gap: 0.5rem; }}

    .tallas-label-txt {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--gray);
    }}

    .tallas-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
    }}

    .chip {{
      min-width: 46px;
      padding: 0.4rem 0.7rem;
      border: 2px solid #ddd;
      border-radius: 8px;
      background: var(--white);
      font-family: 'Inter', sans-serif;
      font-size: 0.88rem;
      font-weight: 600;
      cursor: pointer;
      transition: border-color 0.15s, background 0.15s, color 0.15s;
      text-align: center;
    }}

    .chip:hover:not(.agotada):not(.selected) {{ border-color: var(--black); }}

    .chip.selected {{
      border-color: var(--black);
      background: var(--black);
      color: var(--white);
    }}

    .chip.agotada {{
      color: #c0c0c0;
      border-color: #ebebeb;
      background: #fafafa;
      text-decoration: line-through;
      cursor: not-allowed;
    }}

    .no-tallas {{ font-size: 0.85rem; color: var(--gray); font-style: italic; }}

    /* ── CTA BUTTON ── */
    .btn-cta {{
      width: 100%;
      padding: 0.9rem;
      background: var(--black);
      color: var(--white);
      border: none;
      border-radius: 10px;
      font-family: 'Inter', sans-serif;
      font-size: 0.95rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
      margin-top: auto;
    }}

    .btn-cta:hover:not(:disabled) {{ background: var(--gold); }}

    .btn-cta:disabled {{
      background: #e0e0e0;
      color: #aaa;
      cursor: not-allowed;
    }}

    /* ── CART OVERLAY ── */
    #cart-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 300;
      align-items: flex-start;
      justify-content: flex-end;
    }}

    #cart-overlay.open {{ display: flex; }}

    #cart-panel {{
      background: var(--white);
      width: min(420px, 100vw);
      height: 100vh;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      animation: slideIn 0.25s ease;
    }}

    @keyframes slideIn {{
      from {{ transform: translateX(100%); }}
      to   {{ transform: translateX(0); }}
    }}

    .cart-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.5rem;
    }}

    .cart-header h2 {{
      font-family: 'Playfair Display', serif;
      font-size: 1.3rem;
    }}

    .close-cart {{
      background: none;
      border: none;
      font-size: 1.6rem;
      cursor: pointer;
      line-height: 1;
      color: var(--gray);
      transition: color 0.2s;
    }}

    .close-cart:hover {{ color: var(--black); }}

    #cart-items {{ flex: 1; }}

    .cart-empty {{
      text-align: center;
      color: var(--gray);
      padding: 3rem 0;
      font-size: 0.95rem;
    }}

    .cart-item {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 0;
      border-bottom: 1px solid #f0f0f0;
    }}

    .cart-item-name {{
      flex: 1;
      font-size: 0.85rem;
      font-weight: 500;
      line-height: 1.3;
    }}

    .cart-item-price {{
      font-size: 0.85rem;
      color: var(--gold);
      font-weight: 600;
      white-space: nowrap;
    }}

    .qty-ctrl {{
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}

    .qty-btn {{
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 1.5px solid #ddd;
      background: none;
      cursor: pointer;
      font-size: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: border-color 0.2s, background 0.2s;
    }}

    .qty-btn:hover {{ border-color: var(--gold); background: var(--gold); color: var(--white); }}

    .qty-num {{
      font-weight: 600;
      font-size: 0.9rem;
      min-width: 20px;
      text-align: center;
    }}

    .cart-footer {{
      border-top: 2px solid var(--black);
      padding-top: 1.2rem;
      margin-top: 1rem;
    }}

    .cart-total {{
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      font-size: 1.1rem;
      margin-bottom: 1.2rem;
    }}

    .cart-total span:last-child {{
      font-family: 'Playfair Display', serif;
      color: var(--gold);
    }}

    .btn-whatsapp {{
      width: 100%;
      padding: 1rem;
      background: #25D366;
      color: var(--white);
      border: none;
      border-radius: 10px;
      font-family: 'Inter', sans-serif;
      font-weight: 700;
      font-size: 1rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: background 0.2s, transform 0.1s;
    }}

    .btn-whatsapp:hover {{ background: #1ebe5d; transform: scale(1.01); }}

    /* ── FOOTER ── */
    footer {{
      text-align: center;
      padding: 1.5rem;
      font-size: 0.78rem;
      color: var(--gray);
      border-top: 1px solid #eee;
    }}

    /* ── TOAST ── */
    #toast {{
      position: fixed;
      bottom: 2rem;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: var(--black);
      color: var(--white);
      padding: 0.7rem 1.4rem;
      border-radius: 50px;
      font-size: 0.85rem;
      font-weight: 500;
      opacity: 0;
      transition: opacity 0.3s, transform 0.3s;
      pointer-events: none;
      z-index: 400;
    }}

    #toast.show {{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }}
  </style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="logo">Aura <span>Sole</span></div>
  <button class="cart-btn" onclick="abrirCarrito()" aria-label="Abrir carrito">
    🛒 Carrito
    <span class="cart-count" id="cart-count">0</span>
  </button>
</header>

<!-- HERO -->
<div class="hero">
  <h1>Calzado <span>Femenino</span></h1>
  <p>Estilo y comodidad para cada paso</p>
  <div class="search-wrap">
    <input type="search" id="buscador" placeholder="Buscar producto..." oninput="filtrar(this.value)" />
  </div>
</div>

<!-- CATÁLOGO -->
<main>
  <h2 class="section-title">
    Nuestro catálogo
    <span>{total_productos} productos</span>
  </h2>
  <div id="catalogo">
    {cards_html}
  </div>
</main>

<!-- PRODUCT MODAL -->
<div id="product-modal" onclick="cerrarSiModal(event)" aria-modal="true" role="dialog">
  <div id="product-panel">
    <button class="close-modal" onclick="cerrarModal()" aria-label="Cerrar">×</button>
    <div class="modal-gallery">
      <div class="modal-main-img-wrap">
        <img id="modal-img-main" src="" alt="" />
      </div>
      <div class="modal-thumbnails" id="modal-thumbs"></div>
    </div>
    <div class="modal-info">
      <span class="modal-cat" id="modal-cat"></span>
      <h2 class="modal-nombre" id="modal-nombre"></h2>
      <p class="modal-precio" id="modal-precio"></p>
      <div class="stock-section">
        <div class="stock-bar-bg">
          <div class="stock-bar-fill" id="stock-fill"></div>
        </div>
        <p class="stock-msg" id="stock-msg"></p>
      </div>
      <div class="tallas-section">
        <p class="tallas-label-txt">Talla</p>
        <div class="tallas-chips" id="tallas-chips"></div>
      </div>
      <button class="btn-cta" id="btn-cta" disabled onclick="agregarDesdeModal()">
        Selecciona una talla
      </button>
    </div>
  </div>
</div>

<!-- CARRITO OVERLAY -->
<div id="cart-overlay" onclick="cerrarSiOverlay(event)">
  <div id="cart-panel" role="dialog" aria-modal="true" aria-label="Carrito de compras">
    <div class="cart-header">
      <h2>Tu carrito 🛒</h2>
      <button class="close-cart" onclick="cerrarCarrito()" aria-label="Cerrar carrito">×</button>
    </div>
    <div id="cart-items">
      <p class="cart-empty">Tu carrito está vacío</p>
    </div>
    <div class="cart-footer">
      <div class="cart-total">
        <span>Total estimado</span>
        <span id="cart-total-val">$0</span>
      </div>
      <button class="btn-whatsapp" onclick="pedirPorWhatsApp()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
        </svg>
        PEDIR POR WHATSAPP
      </button>
    </div>
  </div>
</div>

<!-- TOAST -->
<div id="toast"></div>

<!-- FOOTER -->
<footer>
  <strong>{NOMBRE_TIENDA}</strong> &nbsp;|&nbsp; Precios actualizados: {fecha_display}
  <br>Los precios pueden variar. Confirma disponibilidad por WhatsApp.
</footer>

<script>
  const WHATSAPP = '{WHATSAPP_NUMBER}';
  const carrito = {{}};

  let modalProducto = null;
  let tallaSeleccionada = null;

  /* ── UTILS ── */
  function escHtml(s) {{
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }}

  function escAttr(s) {{
    return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }}

  /* ── COOKIES ── */
  function getCookie(name) {{
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m[2]) : null;
  }}

  function setCookie(name, value, days) {{
    const exp = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + ';expires=' + exp + ';path=/;SameSite=Lax';
  }}

  /* ── STOCK BAR ── */
  function initStockBar(productId) {{
    const key = 'aura_stock_' + productId;
    const stored = getCookie(key);
    let count = stored !== null ? parseInt(stored, 10) : 5;
    setCookie(key, Math.max(1, count - 1), 1);

    const pct = (count / 5) * 100;
    const fill = document.getElementById('stock-fill');
    const msg = document.getElementById('stock-msg');
    fill.style.width = pct + '%';

    if (count >= 4) {{
      fill.style.background = '#22c55e';
      msg.textContent = count + ' pares disponibles';
      msg.style.color = '#16a34a';
    }} else if (count >= 2) {{
      fill.style.background = '#f97316';
      msg.textContent = 'Solo ' + count + ' pares disponibles';
      msg.style.color = '#ea580c';
    }} else {{
      fill.style.background = '#ef4444';
      msg.textContent = '¡Último par!';
      msg.style.color = '#dc2626';
    }}
  }}

  /* ── PRODUCT MODAL ── */
  function abrirProducto(id) {{
    fetch('/api/productos/' + id)
      .then(function(r) {{
        if (!r.ok) throw new Error('not found');
        return r.json();
      }})
      .then(function(p) {{
        modalProducto = p;
        tallaSeleccionada = null;
        renderModal(p);
        document.getElementById('product-modal').classList.add('open');
        document.body.style.overflow = 'hidden';
      }})
      .catch(function() {{
        mostrarToast('Error al cargar el producto');
      }});
  }}

  function cerrarModal() {{
    document.getElementById('product-modal').classList.remove('open');
    document.body.style.overflow = '';
    modalProducto = null;
    tallaSeleccionada = null;
  }}

  function cerrarSiModal(e) {{
    if (e.target === document.getElementById('product-modal')) cerrarModal();
  }}

  function renderModal(p) {{
    const imgs = (p.imagenes && p.imagenes.length) ? p.imagenes : (p.imagen ? [p.imagen] : []);
    const mainImg = document.getElementById('modal-img-main');
    mainImg.src = imgs[0] || '';
    mainImg.alt = p.nombre || '';

    const thumbsEl = document.getElementById('modal-thumbs');
    if (imgs.length > 1) {{
      thumbsEl.innerHTML = imgs.map(function(url, i) {{
        return '<img src="' + escAttr(url) + '" class="thumb' + (i === 0 ? ' active' : '') + '" onclick="cambiarImg(\'' + escAttr(url) + '\', this)" alt="" />';
      }}).join('');
    }} else {{
      thumbsEl.innerHTML = '';
    }}

    document.getElementById('modal-cat').textContent = p.categoria || '';
    document.getElementById('modal-nombre').textContent = p.nombre || '';
    const precio = p.precio || p.precio_min || 0;
    document.getElementById('modal-precio').textContent = '$' + precio.toLocaleString('es-MX');

    initStockBar(p.id || p.nombre || 'prod');
    renderTallas(p.tallas || []);

    const btn = document.getElementById('btn-cta');
    btn.disabled = true;
    btn.textContent = 'Selecciona una talla';
  }}

  function cambiarImg(url, el) {{
    document.getElementById('modal-img-main').src = url;
    document.querySelectorAll('.thumb').forEach(function(t) {{ t.classList.remove('active'); }});
    el.classList.add('active');
  }}

  function renderTallas(tallas) {{
    const el = document.getElementById('tallas-chips');
    if (!tallas || !tallas.length) {{
      el.innerHTML = '<span class="no-tallas">Tallas no especificadas — consultar por WhatsApp</span>';
      return;
    }}
    el.innerHTML = tallas.map(function(t) {{
      if (t.disponible) {{
        return '<button class="chip" onclick="seleccionarTalla(\'' + escAttr(t.numero) + '\', this)">' + escHtml(t.numero) + '</button>';
      }} else {{
        return '<button class="chip agotada" disabled>' + escHtml(t.numero) + '</button>';
      }}
    }}).join('');
  }}

  function seleccionarTalla(numero, el) {{
    document.querySelectorAll('#tallas-chips .chip').forEach(function(c) {{ c.classList.remove('selected'); }});
    el.classList.add('selected');
    tallaSeleccionada = numero;
    const btn = document.getElementById('btn-cta');
    btn.disabled = false;
    btn.textContent = 'Agregar al carrito — Talla ' + numero;
  }}

  function agregarDesdeModal() {{
    if (!modalProducto || !tallaSeleccionada) return;
    const p = modalProducto;
    const cid = (p.id || p.nombre) + '_' + tallaSeleccionada;
    const precio = p.precio || p.precio_min || 0;
    const nombre = p.nombre + ' (T. ' + tallaSeleccionada + ')';
    agregarCarrito(cid, nombre, precio);
    cerrarModal();
  }}

  /* ── CARRITO ── */
  function agregarCarrito(cid, nombre, precio) {{
    if (carrito[cid]) {{
      carrito[cid].qty += 1;
    }} else {{
      carrito[cid] = {{ nombre: nombre, precio: precio, qty: 1 }};
    }}
    actualizarUI();
    mostrarToast('✓ ' + nombre.split(' ').slice(0, 4).join(' ') + ' agregado');
  }}

  function cambiarCantidadBtn(el, delta) {{
    cambiarCantidad(el.getAttribute('data-cid'), delta);
  }}

  function cambiarCantidad(cid, delta) {{
    if (!carrito[cid]) return;
    carrito[cid].qty += delta;
    if (carrito[cid].qty <= 0) delete carrito[cid];
    actualizarUI();
    renderCarrito();
  }}

  function actualizarUI() {{
    const total = Object.values(carrito).reduce(function(s, i) {{ return s + i.qty; }}, 0);
    document.getElementById('cart-count').textContent = total;
    renderCarrito();
  }}

  function renderCarrito() {{
    const el = document.getElementById('cart-items');
    const keys = Object.keys(carrito);

    if (!keys.length) {{
      el.innerHTML = '<p class="cart-empty">Tu carrito está vacío</p>';
      document.getElementById('cart-total-val').textContent = '$0';
      return;
    }}

    let totalVal = 0;
    let html = '';
    keys.forEach(function(cid) {{
      const item = carrito[cid];
      const subtotal = item.precio * item.qty;
      totalVal += subtotal;
      html += '<div class="cart-item">'
        + '<div class="cart-item-name">' + escHtml(item.nombre) + '</div>'
        + '<div class="qty-ctrl">'
        + '<button class="qty-btn" data-cid="' + escAttr(cid) + '" onclick="cambiarCantidadBtn(this, -1)">−</button>'
        + '<span class="qty-num">' + item.qty + '</span>'
        + '<button class="qty-btn" data-cid="' + escAttr(cid) + '" onclick="cambiarCantidadBtn(this, 1)">+</button>'
        + '</div>'
        + '<div class="cart-item-price">$' + subtotal.toLocaleString('es-MX') + '</div>'
        + '</div>';
    }});

    el.innerHTML = html;
    document.getElementById('cart-total-val').textContent = '$' + totalVal.toLocaleString('es-MX');
  }}

  /* ── WHATSAPP ── */
  function pedirPorWhatsApp() {{
    const keys = Object.keys(carrito);
    if (!keys.length) {{
      mostrarToast('Agrega productos al carrito primero');
      return;
    }}

    const lineas = keys.map(function(cid) {{
      const i = carrito[cid];
      return '🛍️ ' + i.nombre + ' x' + i.qty + ' — $' + i.precio.toLocaleString('es-MX') + ' c/u';
    }}).join('\\n');

    const total = keys.reduce(function(s, cid) {{ return s + carrito[cid].precio * carrito[cid].qty; }}, 0);
    const msg = 'Hola! Me interesa hacer un pedido en {NOMBRE_TIENDA}:\\n\\n' + lineas + '\\n\\n💰 Total estimado: $' + total.toLocaleString('es-MX') + '\\n\\nPor favor indíquenme disponibilidad.';
    window.open('https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(msg), '_blank');
  }}

  /* ── BUSCADOR ── */
  function filtrar(q) {{
    const t = q.toLowerCase().trim();
    document.querySelectorAll('.product-card').forEach(function(card) {{
      card.style.display = (card.dataset.nombre || '').includes(t) ? '' : 'none';
    }});
  }}

  /* ── PANEL CARRITO ── */
  function abrirCarrito() {{
    document.getElementById('cart-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
  }}

  function cerrarCarrito() {{
    document.getElementById('cart-overlay').classList.remove('open');
    document.body.style.overflow = '';
  }}

  function cerrarSiOverlay(e) {{
    if (e.target === document.getElementById('cart-overlay')) cerrarCarrito();
  }}

  /* ── TOAST ── */
  let toastTimer;
  function mostrarToast(msg) {{
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function() {{ t.classList.remove('show'); }}, 2200);
  }}
</script>
</body>
</html>
"""


def main():
    productos, actualizado = cargar_productos()
    html = generar_html(productos, actualizado)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"index.html generado con {len(productos)} productos.")
    print("Abrir index.html en el navegador para validar.")


if __name__ == "__main__":
    main()
