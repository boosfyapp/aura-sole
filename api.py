import json
from flask import Flask, jsonify
from flask_cors import CORS
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app, origins=[
    "https://aurasole.com.mx",
    "http://aurasole.com.mx",
    "http://localhost",
    "http://localhost:80",
    "http://localhost:5500",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
])


def cargar_productos() -> list:
    try:
        with open("productos.json", "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos.get("productos", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/productos")
def get_productos():
    return jsonify(cargar_productos())


def _slug(url: str) -> str:
    return urlparse(url).path.strip("/").split("/")[-1] if url else ""


@app.route("/api/productos/<prod_id>")
def get_producto(prod_id):
    for p in cargar_productos():
        if p.get("id") == prod_id:
            return jsonify(p)
        # Fallback: match by URL slug for products without id field
        if _slug(p.get("url", "")) == prod_id:
            producto = dict(p)
            producto.setdefault("id", prod_id)
            producto.setdefault("imagenes", [p["imagen"]] if p.get("imagen") else [])
            producto.setdefault("tallas", [])
            producto.setdefault("sku", "")
            return jsonify(producto)
    return jsonify({"error": "Producto no encontrado"}), 404


@app.route("/api/categorias")
def get_categorias():
    productos = cargar_productos()
    cats = sorted({p.get("categoria", "") for p in productos if p.get("categoria")})
    return jsonify(cats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
