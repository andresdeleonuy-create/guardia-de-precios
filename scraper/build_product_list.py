"""
Corre UNA sola vez (o cuando se quiera renovar la muestra) para construir
la lista fija de productos a trackear. A partir de ahi, capture_snapshot.py
siempre lee config/productos.json y sigue esos mismos productos.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import cargar_config, delay_cortes, extraer_productos_de_pagina, PRODUCTOS_PATH


def elegir_productos_de_categoria(page, config, categoria):
    url = config["sitio_base"] + categoria["path"]
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(1000)
    pool = extraer_productos_de_pagina(page)

    # priorizar los que ya tienen descuento activo (precio_original seteado):
    # son los mejores candidatos a "descuento falso"
    pool.sort(key=lambda p: p["precio_original"] is not None, reverse=True)

    elegidos = pool[: categoria["cupo"]]
    for p in elegidos:
        p["categoria"] = categoria["nombre"]
        p["volatilidad"] = categoria["volatilidad"]
        p["vendedor"] = "AMV Store"
    return elegidos


def main():
    config = cargar_config()
    seleccion = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=config["user_agent"],
            viewport={"width": 1366, "height": 900},
            locale="es-UY",
        )
        page = ctx.new_page()

        for categoria in config["categorias"]:
            print(f"-> {categoria['nombre']} ({categoria['path']})")
            try:
                elegidos = elegir_productos_de_categoria(page, config, categoria)
                print(f"   {len(elegidos)} productos elegidos "
                      f"({sum(1 for e in elegidos if e['precio_original'])} con descuento activo)")
                seleccion.extend(elegidos)
            except Exception as e:
                print(f"   ERROR en {categoria['nombre']}: {e}")
            delay_cortes(config)

        browser.close()

    # dedup por id, por si dos categorias del sitio devuelven el mismo producto
    vistos = set()
    seleccion_final = []
    for p in seleccion:
        if p["id"] not in vistos:
            vistos.add(p["id"])
            seleccion_final.append(p)

    PRODUCTOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PRODUCTOS_PATH, "w", encoding="utf-8") as f:
        json.dump(seleccion_final, f, ensure_ascii=False, indent=2)

    print(f"\nTotal seleccionado: {len(seleccion_final)} productos -> {PRODUCTOS_PATH}")
    con_desc = sum(1 for p in seleccion_final if p["precio_original"])
    print(f"Con descuento activo al momento de la seleccion: {con_desc}")


if __name__ == "__main__":
    main()
