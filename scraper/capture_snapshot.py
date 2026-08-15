"""
Corre cada 4-6 horas (via GitHub Actions). Visita cada producto de
config/productos.json en su URL fija y appendea una fila a data/precios.csv
con el precio de ese momento.
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import cargar_config, delay_cortes, extraer_precio_de_producto, CSV_PATH, PRODUCTOS_PATH

CAMPOS = ["timestamp", "producto_id", "titulo", "precio", "precio_original", "vendedor", "categoria", "url"]


def cargar_productos():
    with open(PRODUCTOS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def capturar_producto(page, producto):
    page.goto(producto["url"], wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    return extraer_precio_de_producto(page)


def main():
    config = cargar_config()
    productos = cargar_productos()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    existe = CSV_PATH.exists() and CSV_PATH.stat().st_size > 0

    filas = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=config["user_agent"],
            viewport={"width": 1366, "height": 900},
            locale="es-UY",
        )
        page = ctx.new_page()

        for i, prod in enumerate(productos, 1):
            try:
                lectura = capturar_producto(page, prod)
                if lectura is None or lectura["precio"] is None:
                    print(f"[{i}/{len(productos)}] {prod['titulo'][:50]}: SIN PRECIO (pagina cambio?)")
                else:
                    filas.append(
                        {
                            "timestamp": timestamp,
                            "producto_id": prod["id"],
                            "titulo": prod["titulo"],
                            "precio": lectura["precio"],
                            "precio_original": lectura["precio_original"] or "",
                            "vendedor": prod["vendedor"],
                            "categoria": prod["categoria"],
                            "url": prod["url"],
                        }
                    )
                    print(f"[{i}/{len(productos)}] {prod['titulo'][:50]}: {lectura['precio']}")
            except Exception as e:
                print(f"[{i}/{len(productos)}] {prod['titulo'][:50]}: ERROR {e}")
            delay_cortes(config)

        browser.close()

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS)
        if not existe:
            writer.writeheader()
        writer.writerows(filas)

    print(f"\n{len(filas)}/{len(productos)} productos capturados -> {CSV_PATH}")


if __name__ == "__main__":
    main()
