import json
from datetime import datetime
from config import NOMBRE_TIENDA, WHATSAPP_NUMBER


def cargar_productos() -> tuple[list, str]:
    try:
        with open("productos.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos.get("productos", []), datos.get("actualizado", "")
    except FileNotFoundError:
        print("AVISO: productos.json no encontrado. Generando HTML con catálogo vacío.")
        return [], datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def generar_cards(productos: list) -> str:
    if not productos:
        return '<p class="empty-catalog">No hay productos disponibles en este momento.</p>'

    cards = []
    for i, p in enumerate(productos):
        nombre_esc = p["nombre"].replace('"', "&quot;")
        precio_display = (
            f"${p['precio_min']:,} – ${p['precio_max']:,}"
            if p["precio_min"] != p["precio_max"]
            else f"${p['precio_min']:,}"
        )
        precio_js = p["precio_min"]

        card = f"""
        <div class="product-card" data-nombre="{nombre_esc.lower()}">
          <div class="card-img-wrap">
            <img
              src="{p['imagen']}"
              alt="{nombre_esc}"
              loading="lazy"
              onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22300%22%3E%3Crect width=%22300%22 height=%22300%22 fill=%22%23f5f5f5%22/%3E%3Ctext x=%22150%22 y=%22155%22 text-anchor=%22middle%22 fill=%22%23bbb%22 font-size=%2214%22%3ESin imagen%3C/text%3E%3C/svg%3E'"
            />
          </div>
          <div class="card-body">
            <p class="card-categoria">{p.get('categoria', 'DAMAS')}</p>
            <h3 class="card-nombre">{p['nombre']}</h3>
            <p class="card-precio">{precio_display}</p>
            <button
              class="btn-agregar"
              onclick="agregarCarrito({i}, '{nombre_esc}', {precio_js})"
            >Agregar al carrito</button>
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

    /* ── HERO / SEARCH BAR ── */
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

    /* ── CART OVERLAY ── */
    #cart-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.5);
      z-index: 200;
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
      z-index: 300;
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
  <br>Los precios pueden variar. Confirma disponibilidad y tallas por WhatsApp.
</footer>

<script>
  const WHATSAPP = '{WHATSAPP_NUMBER}';
  let carrito = {{}};

  /* ── CARRITO ── */
  function agregarCarrito(id, nombre, precio) {{
    if (carrito[id]) {{
      carrito[id].qty += 1;
    }} else {{
      carrito[id] = {{ nombre, precio, qty: 1 }};
    }}
    actualizarUI();
    mostrarToast('✓ ' + nombre.split(' ').slice(0, 3).join(' ') + ' agregado');
  }}

  function cambiarCantidad(id, delta) {{
    if (!carrito[id]) return;
    carrito[id].qty += delta;
    if (carrito[id].qty <= 0) delete carrito[id];
    actualizarUI();
    renderCarrito();
  }}

  function actualizarUI() {{
    const total = Object.values(carrito).reduce((s, i) => s + i.qty, 0);
    document.getElementById('cart-count').textContent = total;
    renderCarrito();
  }}

  function renderCarrito() {{
    const el = document.getElementById('cart-items');
    const items = Object.entries(carrito);

    if (!items.length) {{
      el.innerHTML = '<p class="cart-empty">Tu carrito está vacío</p>';
      document.getElementById('cart-total-val').textContent = '$0';
      return;
    }}

    let totalVal = 0;
    let html = '';
    items.forEach(([id, item]) => {{
      const subtotal = item.precio * item.qty;
      totalVal += subtotal;
      html += `
        <div class="cart-item">
          <div class="cart-item-name">${{item.nombre}}</div>
          <div class="qty-ctrl">
            <button class="qty-btn" onclick="cambiarCantidad(${{id}}, -1)">−</button>
            <span class="qty-num">${{item.qty}}</span>
            <button class="qty-btn" onclick="cambiarCantidad(${{id}}, 1)">+</button>
          </div>
          <div class="cart-item-price">$${{subtotal.toLocaleString('es-MX')}}</div>
        </div>`;
    }});

    el.innerHTML = html;
    document.getElementById('cart-total-val').textContent = '$' + totalVal.toLocaleString('es-MX');
  }}

  /* ── WHATSAPP ── */
  function pedirPorWhatsApp() {{
    const items = Object.values(carrito);
    if (!items.length) {{
      mostrarToast('Agrega productos al carrito primero');
      return;
    }}

    let lineas = items.map(i =>
      `🛍️ ${{i.nombre}} x${{i.qty}} — $${{i.precio.toLocaleString('es-MX')}} c/u`
    ).join('\\n');

    const total = items.reduce((s, i) => s + i.precio * i.qty, 0);

    const mensaje = `Hola! Me interesa hacer un pedido en {NOMBRE_TIENDA}:\\n\\n${{lineas}}\\n\\n💰 Total estimado: $${{total.toLocaleString('es-MX')}}\\n\\nPor favor indíquenme disponibilidad y tallas.`;

    const url = `https://wa.me/${{WHATSAPP}}?text=${{encodeURIComponent(mensaje)}}`;
    window.open(url, '_blank');
  }}

  /* ── BUSCADOR ── */
  function filtrar(q) {{
    const termino = q.toLowerCase().trim();
    document.querySelectorAll('.product-card').forEach(card => {{
      const nombre = card.dataset.nombre || '';
      card.style.display = nombre.includes(termino) ? '' : 'none';
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
    toastTimer = setTimeout(() => t.classList.remove('show'), 2200);
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
