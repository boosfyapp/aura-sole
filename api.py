import json
import os
import time
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

_cache: dict = {"productos": [], "by_id": {}, "by_slug": {}, "mtime": 0.0}
_JSON_PATH = "productos.json"


def _slug(url: str) -> str:
    return urlparse(url).path.strip("/").split("/")[-1] if url else ""


def _refresh_cache() -> None:
    try:
        mtime = os.path.getmtime(_JSON_PATH)
    except OSError:
        return
    if mtime == _cache["mtime"]:
        return
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            datos = json.load(f)
        productos = datos.get("productos", [])
        by_id: dict = {}
        by_slug: dict = {}
        for p in productos:
            pid = p.get("id")
            if pid:
                by_id[pid] = p
            slug = _slug(p.get("url", ""))
            if slug and slug not in by_slug:
                by_slug[slug] = p
        _cache["productos"] = productos
        _cache["by_id"] = by_id
        _cache["by_slug"] = by_slug
        _cache["mtime"] = mtime
    except (json.JSONDecodeError, OSError):
        pass


def cargar_productos() -> list:
    _refresh_cache()
    return _cache["productos"]


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/productos")
def get_productos():
    return jsonify(cargar_productos())


@app.route("/api/productos/<prod_id>")
def get_producto(prod_id):
    _refresh_cache()
    p = _cache["by_id"].get(prod_id) or _cache["by_slug"].get(prod_id)
    if p:
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
