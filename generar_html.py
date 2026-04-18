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
    for a, b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ä","a"),("ë","e"),("ï","i"),("ö","o"),("ü","u")]:
        nombre = nombre.replace(a, b)
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

        imagenes = p.get("imagenes", [])
        imagen = imagenes[0] if imagenes else p.get("imagen", "")

        precio_num = p.get("precio", p.get("precio_min", 0))
        precio_max = p.get("precio_max", precio_num)
        precio_display = (
            f"${precio_num:,} – ${precio_max:,}"
            if precio_num != precio_max
            else f"${precio_num:,}"
        )
        cat = p.get("categoria", "DAMAS")

        card = f"""
        <div class="product-card"
             data-nombre="{nombre_esc.lower()}"
             data-categoria="{cat}"
             data-id="{prod_id}"
             data-imagen="{imagen}"
             data-precio-num="{precio_num}"
             onclick="abrirProducto(this)">
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
            <button class="btn-agregar" onclick="event.stopPropagation(); abrirProducto(this.closest('.product-card'))">
              Ver producto
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
    .hero p {{ color: #ccc; margin-bottom: 1.5rem; font-size: 0.95rem; }}
    .search-wrap {{ max-width: 500px; margin: 0 auto; }}
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

    /* ── CATEGORÍAS ── */
    .categories-section {{
      background: var(--white);
      border-bottom: 1px solid #eee;
      padding: 0.7rem 1rem;
      position: sticky;
      top: 64px;
      z-index: 90;
    }}
    .categories-scroll {{
      display: flex;
      gap: 0.5rem;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: none;
      padding-bottom: 2px;
    }}
    .categories-scroll::-webkit-scrollbar {{ display: none; }}
    .cat-chip {{
      flex-shrink: 0;
      padding: 0.38rem 1rem;
      border-radius: 50px;
      border: 1.5px solid #ddd;
      background: var(--white);
      font-family: 'Inter', sans-serif;
      font-size: 0.78rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      color: var(--gray);
    }}
    .cat-chip:hover {{ border-color: var(--gold); color: var(--black); }}
    .cat-chip.active {{
      background: var(--black);
      border-color: var(--black);
      color: var(--white);
    }}
    @media (min-width: 1024px) {{
      .categories-scroll {{ flex-wrap: wrap; overflow-x: visible; }}
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
    @media (min-width: 600px) {{ #catalogo {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (min-width: 1024px) {{ #catalogo {{ grid-template-columns: repeat(4, 1fr); gap: 1.4rem; }} }}

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
    .product-card:hover {{ transform: translateY(-4px); box-shadow: var(--shadow-hover); }}
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
    .product-card:hover .card-img-wrap img {{ transform: scale(1.05); }}
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

    /* ── PRODUCT OVERLAY (full-screen) ── */
    #producto-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      z-index: 200;
      background: var(--white);
      flex-direction: column;
    }}
    #producto-overlay.open {{
      display: flex;
      animation: slideUp 0.26s ease;
    }}
    @keyframes slideUp {{
      from {{ transform: translateY(30px); opacity: 0; }}
      to   {{ transform: translateY(0);    opacity: 1; }}
    }}

    .producto-header {{
      flex-shrink: 0;
      background: rgba(255,255,255,0.96);
      backdrop-filter: blur(8px);
      padding: 0.8rem 1rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      border-bottom: 1px solid #eee;
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    .btn-back {{
      background: none;
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0.2rem 0.6rem;
      border-radius: 8px;
      transition: background 0.2s;
      line-height: 1;
    }}
    .btn-back:hover {{ background: var(--gray-light); }}
    .producto-header-title {{
      font-family: 'Playfair Display', serif;
      font-size: 0.95rem;
      font-weight: 700;
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .producto-scroll {{
      flex: 1;
      overflow-y: auto;
      -webkit-overflow-scrolling: touch;
    }}

    /* Gallery */
    .prod-gallery {{ background: var(--gray-light); }}
    .prod-main-img-wrap {{
      width: 100%;
      aspect-ratio: 1 / 1;
      max-height: 52vh;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .prod-main-img-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .prod-thumbs {{
      display: flex;
      gap: 0.45rem;
      padding: 0.6rem 1rem;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .prod-thumbs::-webkit-scrollbar {{ display: none; }}
    .prod-thumbs:empty {{ display: none; }}
    .prod-thumb {{
      width: 56px;
      height: 56px;
      object-fit: cover;
      border-radius: 6px;
      border: 2px solid transparent;
      flex-shrink: 0;
      cursor: pointer;
      transition: border-color 0.15s;
    }}
    .prod-thumb.active, .prod-thumb:hover {{ border-color: var(--gold); }}

    /* Product body */
    .producto-body {{
      padding: 1.25rem 1.25rem 1rem;
      max-width: 680px;
      margin: 0 auto;
      width: 100%;
    }}
    .producto-categoria-badge {{
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      color: var(--gold);
      text-transform: uppercase;
      margin-bottom: 0.4rem;
    }}
    .producto-nombre {{
      font-family: 'Playfair Display', serif;
      font-size: 1.45rem;
      font-weight: 700;
      line-height: 1.3;
      margin-bottom: 0.6rem;
    }}
    .producto-precio-grande {{
      font-family: 'Playfair Display', serif;
      font-size: 1.7rem;
      font-weight: 700;
      color: var(--gold);
      margin-bottom: 1rem;
    }}

    /* Stock bar */
    .stock-wrap {{ margin-bottom: 1rem; }}
    .stock-label {{
      font-size: 0.82rem;
      font-weight: 600;
      margin-bottom: 0.45rem;
    }}
    .stock-label.bueno   {{ color: #2f855a; }}
    .stock-label.medio   {{ color: #c05621; }}
    .stock-label.urgente {{ color: #c53030; }}
    @keyframes parpadeo {{
      0%, 100% {{ opacity: 1; }}
      50%       {{ opacity: 0.35; }}
    }}
    .parpadeo {{ animation: parpadeo 0.9s ease-in-out infinite; }}
    .stock-bar-bg {{
      height: 8px;
      background: #eee;
      border-radius: 50px;
      overflow: hidden;
    }}
    .stock-bar-fill {{
      height: 100%;
      border-radius: 50px;
      width: 0%;
      transition: width 0.7s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .stock-bar-fill.bueno   {{ background: #38a169; }}
    .stock-bar-fill.medio   {{ background: #dd6b20; }}
    .stock-bar-fill.urgente {{ background: #e53e3e; }}

    /* Tallas */
    .tallas-section {{ margin-bottom: 1rem; }}
    .tallas-section-label {{
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--gray);
      margin-bottom: 0.6rem;
    }}
    .size-chips {{ display: flex; flex-wrap: wrap; gap: 0.45rem; }}
    .size-chip {{
      min-width: 48px;
      padding: 0.42rem 0.75rem;
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
    .size-chip:hover:not(.agotada):not(.selected) {{ border-color: var(--black); }}
    .size-chip.selected {{
      border-color: var(--black);
      background: var(--black);
      color: var(--white);
    }}
    .size-chip.agotada {{
      color: #c0c0c0;
      border-color: #ebebeb;
      background: #fafafa;
      text-decoration: line-through;
      cursor: not-allowed;
    }}
    .tallas-nota {{
      font-size: 0.8rem;
      color: var(--gray);
      font-style: italic;
    }}
    .tallas-loading {{
      font-size: 0.82rem;
      color: var(--gray);
    }}

    /* CTA footer */
    .producto-cta {{
      flex-shrink: 0;
      background: var(--white);
      border-top: 1px solid #eee;
      padding: 0.9rem 1rem;
      display: flex;
      gap: 0.75rem;
      box-shadow: 0 -4px 16px rgba(0,0,0,0.08);
    }}
    .btn-cta-main {{
      flex: 1;
      padding: 0.9rem;
      background: var(--black);
      color: var(--white);
      border: none;
      border-radius: 10px;
      font-family: 'Inter', sans-serif;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      transition: background 0.2s;
    }}
    .btn-cta-main:hover:not(:disabled) {{ background: var(--gold); }}
    .btn-cta-main:disabled {{
      background: #e0e0e0;
      color: #aaa;
      cursor: not-allowed;
    }}
    .btn-cta-secondary {{
      padding: 0.9rem 1.1rem;
      background: none;
      border: 2px solid var(--black);
      border-radius: 10px;
      font-family: 'Inter', sans-serif;
      font-weight: 700;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .btn-cta-secondary:hover {{ background: var(--black); color: var(--white); }}

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
    .cart-item-name {{ flex: 1; font-size: 0.85rem; font-weight: 500; line-height: 1.3; }}
    .cart-item-price {{ font-size: 0.85rem; color: var(--gold); font-weight: 600; white-space: nowrap; }}
    .qty-ctrl {{ display: flex; align-items: center; gap: 0.4rem; }}
    .qty-btn {{
      width: 26px; height: 26px;
      border-radius: 50%;
      border: 1.5px solid #ddd;
      background: none;
      cursor: pointer;
      font-size: 1rem;
      display: flex; align-items: center; justify-content: center;
      transition: border-color 0.2s, background 0.2s;
    }}
    .qty-btn:hover {{ border-color: var(--gold); background: var(--gold); color: var(--white); }}
    .qty-num {{ font-weight: 600; font-size: 0.9rem; min-width: 20px; text-align: center; }}
    .cart-footer {{ border-top: 2px solid var(--black); padding-top: 1.2rem; margin-top: 1rem; }}
    .cart-total {{
      display: flex; justify-content: space-between;
      font-weight: 700; font-size: 1.1rem; margin-bottom: 1.2rem;
    }}
    .cart-total span:last-child {{ font-family: 'Playfair Display', serif; color: var(--gold); }}
    .btn-whatsapp {{
      width: 100%; padding: 1rem;
      background: #25D366; color: var(--white);
      border: none; border-radius: 10px;
      font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1rem;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 0.5rem;
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
    #toast.show {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
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

<!-- CATEGORÍAS -->
<div class="categories-section">
  <div class="categories-scroll" id="categories-scroll">
    <button class="cat-chip active" data-cat="todos" onclick="filtrarCategoria('todos')">👟 Todos</button>
  </div>
</div>

<!-- CATÁLOGO -->
<main>
  <h2 class="section-title">
    Nuestro catálogo
    <span id="prod-count">{total_productos} productos</span>
  </h2>
  <div id="catalogo">
    {cards_html}
  </div>
</main>

<!-- PRODUCT OVERLAY -->
<div id="producto-overlay" role="dialog" aria-modal="true">
  <div class="producto-header">
    <button class="btn-back" onclick="cerrarProducto()" aria-label="Volver">←</button>
    <span class="producto-header-title" id="prod-header-title"></span>
  </div>
  <div class="producto-scroll">
    <div class="prod-gallery">
      <div class="prod-main-img-wrap">
        <img id="prod-img-main" src="" alt="" />
      </div>
      <div class="prod-thumbs" id="prod-thumbs"></div>
    </div>
    <div class="producto-body">
      <p class="producto-categoria-badge" id="prod-categoria"></p>
      <h1 class="producto-nombre" id="prod-nombre"></h1>
      <p class="producto-precio-grande" id="prod-precio"></p>
      <div id="prod-stock-wrap"></div>
      <div class="tallas-section" id="prod-tallas-section">
        <p class="tallas-section-label">Talla</p>
        <div class="size-chips" id="prod-tallas-chips">
          <span class="tallas-loading">Cargando tallas...</span>
        </div>
      </div>
    </div>
  </div>
  <div class="producto-cta">
    <button class="btn-cta-main" id="btn-cta-main" onclick="agregarDesdeDetalle()">
      🛒 Agregar al carrito
    </button>
    <button class="btn-cta-secondary" onclick="comprarAhora()">Comprar ahora</button>
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

  const CAT_ICONOS = {{
    'ALPARGATAS':'🌿','BOTA ALTA':'👢','BOTA/BOTIN 2025':'🥾',
    'BOTAS Y PANTUFLA UGG':'🧸','COWBOY BOOTS':'🤠',
    'MULES, FLATS Y MOCASINES':'👞','SANDALIAS':'👡',
    'TACONES':'👠','TACONES EN OFERTA':'🏷️','TENIS DAMA':'👟',
  }};

  let termBusqueda = '';
  let categoriaActiva = 'todos';
  let productoActual = null;
  let tallaSeleccionada = null;
  let _closingFromButton = false;

  /* ── UTILS ── */
  function escHtml(s) {{
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }}
  function escAttr(s) {{
    return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
  }}

  /* ── COOKIES ── */
  function getCookie(name) {{
    const m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }}
  function setCookie(name, value, hours) {{
    const exp = new Date(Date.now() + hours * 3600000).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + exp + '; path=/';
  }}

  /* ── CATEGORÍAS ── */
  function initCategorias() {{
    const seen = new Set();
    document.querySelectorAll('.card-categoria').forEach(function(el) {{
      const cat = (el.textContent || '').trim();
      if (cat) seen.add(cat);
    }});
    const scroll = document.getElementById('categories-scroll');
    Array.from(seen).sort().forEach(function(cat) {{
      const btn = document.createElement('button');
      btn.className = 'cat-chip';
      btn.dataset.cat = cat;
      btn.textContent = (CAT_ICONOS[cat] || '👠') + ' ' + cat;
      btn.onclick = function() {{ filtrarCategoria(cat); }};
      scroll.appendChild(btn);
    }});
  }}

  function filtrarCategoria(cat) {{
    categoriaActiva = cat;
    document.querySelectorAll('.cat-chip').forEach(function(chip) {{
      chip.classList.toggle('active', chip.dataset.cat === cat);
    }});
    const active = document.querySelector('.cat-chip.active');
    if (active) active.scrollIntoView({{ behavior:'smooth', block:'nearest', inline:'center' }});
    aplicarFiltros();
  }}

  /* ── BUSCADOR ── */
  function filtrar(q) {{
    termBusqueda = q.toLowerCase().trim();
    aplicarFiltros();
  }}

  function aplicarFiltros() {{
    let visibles = 0;
    document.querySelectorAll('.product-card').forEach(function(card) {{
      const nombre = card.dataset.nombre || '';
      const cat = (card.dataset.categoria || '').trim();
      const matchSearch = !termBusqueda || nombre.includes(termBusqueda);
      const matchCat = categoriaActiva === 'todos' || cat === categoriaActiva;
      card.style.display = (matchSearch && matchCat) ? '' : 'none';
      if (matchSearch && matchCat) visibles++;
    }});
    const span = document.getElementById('prod-count');
    if (span) span.textContent = visibles + ' productos';
  }}

  /* ── PRODUCT OVERLAY ── */
  function abrirProducto(cardEl) {{
    const id        = cardEl.dataset.id || '';
    const nombre    = cardEl.querySelector('.card-nombre').textContent.trim();
    const imagen    = cardEl.dataset.imagen || cardEl.querySelector('img').src || '';
    const precioTxt = cardEl.querySelector('.card-precio').textContent.trim();
    const precioNum = parseInt(cardEl.dataset.precioNum || '0', 10);
    const categoria = (cardEl.dataset.categoria || '').trim();

    productoActual  = {{ id, nombre, imagen, precio: precioTxt, precioNum, categoria, tallas: null }};
    tallaSeleccionada = null;

    // Populate overlay immediately with embedded card data
    document.getElementById('prod-img-main').src = imagen;
    document.getElementById('prod-img-main').alt = nombre;
    document.getElementById('prod-thumbs').innerHTML = '';
    document.getElementById('prod-header-title').textContent = nombre;
    document.getElementById('prod-categoria').textContent = categoria;
    document.getElementById('prod-nombre').textContent = nombre;
    document.getElementById('prod-precio').textContent = precioTxt;

    // Stock: cookie-based while we wait for API
    initStockBarCookie(id || nombre);

    // Tallas: show loading spinner
    document.getElementById('prod-tallas-section').style.display = '';
    document.getElementById('prod-tallas-chips').innerHTML = '<span class="tallas-loading">Cargando tallas...</span>';

    // CTA: enabled without talla requirement while loading
    setCTA(null);

    document.getElementById('producto-overlay').classList.add('open');
    document.body.style.overflow = 'hidden';
    history.pushState({{ producto: id }}, '', '?producto=' + encodeURIComponent(id));

    // Enrich with API data (tallas + full images)
    if (id) {{
      var _ctrl = new AbortController();
      var _tid = setTimeout(function() {{ _ctrl.abort(); }}, 5000);
      fetch('/api/productos/' + encodeURIComponent(id), {{ signal: _ctrl.signal }})
        .then(function(r) {{ clearTimeout(_tid); return r.ok ? r.json() : null; }})
        .then(function(p) {{
          if (!p || !document.getElementById('producto-overlay').classList.contains('open')) return;
          if (p.id !== productoActual.id && p.id !== id) return; // stale response

          productoActual.tallas = p.tallas || [];
          productoActual.imagenes = p.imagenes || [];

          // Update gallery with full images
          const imgs = p.imagenes && p.imagenes.length ? p.imagenes : [imagen];
          document.getElementById('prod-img-main').src = imgs[0];
          renderThumbs(imgs);

          // Update stock bar with real talla data
          if (productoActual.tallas.length > 0) {{
            initStockBarReal(productoActual.tallas);
          }}

          // Render talla chips
          renderTallas(productoActual.tallas);
        }})
        .catch(function() {{
          // API unavailable — show "ask on WhatsApp" note
          document.getElementById('prod-tallas-chips').innerHTML =
            '<span class="tallas-nota">Consulta tallas disponibles por WhatsApp</span>';
        }});
    }} else {{
      document.getElementById('prod-tallas-chips').innerHTML =
        '<span class="tallas-nota">Consulta tallas disponibles por WhatsApp</span>';
    }}
  }}

  function renderThumbs(imgs) {{
    const el = document.getElementById('prod-thumbs');
    if (imgs.length <= 1) {{ el.innerHTML = ''; return; }}
    el.innerHTML = imgs.map(function(url, i) {{
      return '<img src="' + escAttr(url) + '" class="prod-thumb' + (i===0?' active':'') + '" onclick="cambiarImgProd(\\'' + escAttr(url) + '\\', this)" alt="" />';
    }}).join('');
  }}

  function cambiarImgProd(url, el) {{
    document.getElementById('prod-img-main').src = url;
    document.querySelectorAll('.prod-thumb').forEach(function(t) {{ t.classList.remove('active'); }});
    el.classList.add('active');
  }}

  function renderTallas(tallas) {{
    const el = document.getElementById('prod-tallas-chips');
    tallaSeleccionada = null;

    if (!tallas || tallas.length === 0) {{
      el.innerHTML = '<span class="tallas-nota">Consulta tallas disponibles por WhatsApp</span>';
      setCTA(null);
      return;
    }}

    el.innerHTML = tallas.map(function(t) {{
      if (t.disponible) {{
        return '<button class="size-chip" onclick="seleccionarTalla(\\'' + escAttr(t.numero) + '\\', this)">' + escHtml(t.numero) + '</button>';
      }} else {{
        return '<button class="size-chip agotada" disabled>' + escHtml(t.numero) + '</button>';
      }}
    }}).join('');

    const hayDisponibles = tallas.some(function(t) {{ return t.disponible; }});
    setCTA(hayDisponibles ? 'pending' : 'none');
  }}

  function seleccionarTalla(numero, el) {{
    document.querySelectorAll('.size-chip').forEach(function(c) {{ c.classList.remove('selected'); }});
    el.classList.add('selected');
    tallaSeleccionada = numero;
    setCTA('selected');
  }}

  function setCTA(state) {{
    const btn = document.getElementById('btn-cta-main');
    if (state === 'selected') {{
      btn.disabled = false;
      btn.textContent = '🛒 Agregar — Talla ' + tallaSeleccionada;
    }} else if (state === 'pending') {{
      btn.disabled = false;
      btn.textContent = '👆 Selecciona una talla';
    }} else if (state === 'none') {{
      btn.disabled = false;
      btn.textContent = '🛒 Agregar al carrito';
    }} else {{
      btn.disabled = false;
      btn.textContent = '🛒 Agregar al carrito';
    }}
  }}

  function cerrarProducto() {{
    if (!document.getElementById('producto-overlay').classList.contains('open')) return;
    _closingFromButton = true;
    document.getElementById('producto-overlay').classList.remove('open');
    document.body.style.overflow = '';
    productoActual = null;
    tallaSeleccionada = null;
    if (history.state && history.state.producto !== undefined) history.back();
  }}

  window.addEventListener('popstate', function() {{
    if (_closingFromButton) {{ _closingFromButton = false; return; }}
    const overlay = document.getElementById('producto-overlay');
    if (overlay.classList.contains('open')) {{
      overlay.classList.remove('open');
      document.body.style.overflow = '';
      productoActual = null;
      tallaSeleccionada = null;
    }}
  }});

  function agregarDesdeDetalle() {{
    if (!productoActual) return;

    // If tallas loaded and none selected, prompt
    if (productoActual.tallas && productoActual.tallas.length > 0 && !tallaSeleccionada) {{
      mostrarToast('👆 Selecciona una talla primero');
      document.getElementById('prod-tallas-chips').scrollIntoView({{ behavior:'smooth' }});
      return;
    }}

    const cid = tallaSeleccionada
      ? productoActual.id + '_' + tallaSeleccionada
      : productoActual.id || productoActual.nombre;
    const nombre = tallaSeleccionada
      ? productoActual.nombre + ' (T. ' + tallaSeleccionada + ')'
      : productoActual.nombre;

    agregarCarrito(cid, nombre, productoActual.precioNum);
    cerrarProducto();
  }}

  function comprarAhora() {{
    if (!productoActual) return;

    if (productoActual.tallas && productoActual.tallas.length > 0 && !tallaSeleccionada) {{
      mostrarToast('👆 Selecciona una talla primero');
      document.getElementById('prod-tallas-chips').scrollIntoView({{ behavior:'smooth' }});
      return;
    }}

    const cid = tallaSeleccionada
      ? productoActual.id + '_' + tallaSeleccionada
      : productoActual.id || productoActual.nombre;
    const nombre = tallaSeleccionada
      ? productoActual.nombre + ' (T. ' + tallaSeleccionada + ')'
      : productoActual.nombre;

    agregarCarrito(cid, nombre, productoActual.precioNum);
    cerrarProducto();
    setTimeout(abrirCarrito, 320);
  }}

  /* ── STOCK BAR ── */
  function initStockBarCookie(prodId) {{
    const MAX = 5;
    const key = 'aura_stock_' + prodId;
    const existing = getCookie(key);
    let stock;
    if (existing === null) {{
      stock = MAX;
      setCookie(key, MAX - 1, 24);
    }} else {{
      stock = Math.max(1, parseInt(existing, 10));
      setCookie(key, Math.max(1, stock - 1), 24);
    }}
    renderStockBar(stock, MAX);
  }}

  function initStockBarReal(tallas) {{
    const disponibles = tallas.filter(function(t) {{ return t.disponible; }}).length;
    const total = tallas.length;
    renderStockBar(disponibles, total);
  }}

  function renderStockBar(valor, maximo) {{
    const pct = Math.round((valor / maximo) * 100);
    let nivel, texto, blink = false;
    if (valor === 0) {{
      nivel = 'urgente'; texto = '🔴 Sin tallas disponibles';
    }} else if (valor === 1) {{
      nivel = 'urgente'; texto = '🔴 ¡Última talla disponible!'; blink = true;
    }} else if (valor <= 3) {{
      nivel = 'medio'; texto = '⚠️ Solo ' + valor + ' tallas disponibles';
    }} else {{
      nivel = 'bueno'; texto = '✅ ' + valor + ' tallas disponibles';
    }}
    document.getElementById('prod-stock-wrap').innerHTML =
      '<div class="stock-wrap">' +
        '<div class="stock-label ' + nivel + (blink ? ' parpadeo' : '') + '">' + texto + '</div>' +
        '<div class="stock-bar-bg"><div class="stock-bar-fill ' + nivel + '" id="stock-bar-fill" style="width:0%"></div></div>' +
      '</div>';
    setTimeout(function() {{
      const fill = document.getElementById('stock-bar-fill');
      if (fill) fill.style.width = pct + '%';
    }}, 80);
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
    const total = Object.values(carrito).reduce(function(s,i){{return s+i.qty;}},0);
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
    let totalVal = 0, html = '';
    keys.forEach(function(cid) {{
      const item = carrito[cid];
      const subtotal = item.precio * item.qty;
      totalVal += subtotal;
      html += '<div class="cart-item">'
        + '<div class="cart-item-name">' + escHtml(item.nombre) + '</div>'
        + '<div class="qty-ctrl">'
        + '<button class="qty-btn" data-cid="' + escAttr(cid) + '" onclick="cambiarCantidadBtn(this,-1)">−</button>'
        + '<span class="qty-num">' + item.qty + '</span>'
        + '<button class="qty-btn" data-cid="' + escAttr(cid) + '" onclick="cambiarCantidadBtn(this,1)">+</button>'
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
    if (!keys.length) {{ mostrarToast('Agrega productos al carrito primero'); return; }}
    const lineas = keys.map(function(cid) {{
      const i = carrito[cid];
      return '🛍️ ' + i.nombre + ' x' + i.qty + ' — $' + i.precio.toLocaleString('es-MX') + ' c/u';
    }}).join('\\n');
    const total = keys.reduce(function(s,cid){{return s+carrito[cid].precio*carrito[cid].qty;}},0);
    const msg = 'Hola! Me interesa hacer un pedido en {NOMBRE_TIENDA}:\\n\\n' + lineas + '\\n\\n💰 Total estimado: $' + total.toLocaleString('es-MX') + '\\n\\nPor favor indíquenme disponibilidad.';
    window.open('https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(msg), '_blank');
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
    toastTimer = setTimeout(function(){{ t.classList.remove('show'); }}, 2200);
  }}

  /* ── INIT ── */
  initCategorias();
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


if __name__ == "__main__":
    main()
