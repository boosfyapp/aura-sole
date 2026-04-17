URL_BASE = "https://cocoa-store.com"
URL_CATEGORIA = "https://cocoa-store.com/categoria-producto/damas/"
DESCUENTO = 50
INCREMENTO = 200
WHATSAPP_NUMBER = "5213418862783"
NOMBRE_TIENDA = "Aura Sole Calzado"

# precio_final = precio_cocoa - DESCUENTO + INCREMENTO
def aplicar_precio(precio_cocoa: float) -> int:
    return int(precio_cocoa - DESCUENTO + INCREMENTO)
