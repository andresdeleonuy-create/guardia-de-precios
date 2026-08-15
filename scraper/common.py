import json
import random
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_PATH = RAIZ / "config" / "categorias.json"
PRODUCTOS_PATH = RAIZ / "config" / "productos.json"
CSV_PATH = RAIZ / "data" / "precios.csv"


def cargar_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def delay_cortes(config):
    time.sleep(random.uniform(config["delay_min_segundos"], config["delay_max_segundos"]))


_EXTRACTOR_JS = """
() => {
    const tarjetas = document.querySelectorAll('#catalogoProductos .it[data-codprod], .articleList .it[data-codprod]');
    const num = (txt) => {
        if (!txt) return null;
        const limpio = txt.replace(/\\./g, '').replace(',', '.').replace(/[^0-9.]/g, '');
        return limpio ? parseFloat(limpio) : null;
    };
    return [...tarjetas].map(el => {
        const link = el.querySelector('a.tit');
        const ventaEl = el.querySelector('.precio.venta .monto');
        const listaEl = el.querySelector('.precio.lista .monto');
        const simEl = el.querySelector('.precio.venta .sim');
        return {
            id: el.dataset.codprod + '_' + el.dataset.codvar,
            titulo: link ? link.getAttribute('title') : null,
            url: link ? link.href : null,
            precio: num(ventaEl ? ventaEl.textContent : null),
            precio_original: num(listaEl ? listaEl.textContent : null),
            moneda: simEl ? simEl.textContent.trim() : null,
        };
    });
}
"""


def extraer_productos_de_pagina(page):
    """Lee las tarjetas de producto de una pagina de categoria de AMV Store.
    El precio de lista tachado (.precio.lista) solo aparece cuando el
    producto tiene un descuento activo.
    """
    crudos = page.evaluate(_EXTRACTOR_JS)
    return [p for p in crudos if p["id"] and p["titulo"] and p["precio"] is not None]


_PRECIO_DETALLE_JS = """
() => {
    const num = (txt) => {
        if (!txt) return null;
        const limpio = txt.replace(/\\./g, '').replace(',', '.').replace(/[^0-9.]/g, '');
        return limpio ? parseFloat(limpio) : null;
    };
    const bloque = document.querySelector('.precios');
    if (!bloque) return null;
    const ventaEl = bloque.querySelector('.precio.venta .monto');
    const listaEl = bloque.querySelector('.precio.lista .monto');
    const simEl = bloque.querySelector('.precio.venta .sim');
    return {
        precio: num(ventaEl ? ventaEl.textContent : null),
        precio_original: num(listaEl ? listaEl.textContent : null),
        moneda: simEl ? simEl.textContent.trim() : null,
    };
}
"""


def extraer_precio_de_producto(page):
    """Lee el precio actual (y el de lista, si hay descuento) de una pagina
    de detalle de producto individual."""
    return page.evaluate(_PRECIO_DETALLE_JS)
