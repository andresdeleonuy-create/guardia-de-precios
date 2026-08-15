# Guardia de Precios

Rastrea precios de ~70 productos en una tienda uruguaya varias veces al día,
guarda el histórico en un CSV versionado, y detecta cuándo un "% OFF" no es
un descuento real.

## Cómo funciona

1. `scraper/build_product_list.py` corrió una vez el 15/8/2026 y armó
   `config/productos.json`: 74 productos elegidos automáticamente en
   [AMV Store](https://amvstore.com.uy) (electro/tecnología, Uruguay),
   distribuidos en categorías de alta, media y baja volatilidad, priorizando
   los que ya mostraban un descuento activo al momento de la selección.
2. `scraper/capture_snapshot.py` corre cada 5 horas via GitHub Actions
   (`.github/workflows/captura.yml`), visita cada URL fija, y appendea una
   fila por producto a `data/precios.csv` con timestamp UTC.
3. Cada corrida que agrega datos queda commiteada por el propio workflow:
   el historial de commits es la prueba pública de que el sistema corre solo.

## Por qué AMV Store y no MercadoLibre

La propuesta original priorizaba la API pública de MercadoLibre. Se descartó
el 15/8 tras confirmar en vivo que ML bloquea todo acceso anónimo automatizado
—tanto la API como el HTML— con un muro de verificación de cuenta, tanto desde
una IP residencial de Uruguay como desde un runner limpio de GitHub Actions.
AMV Store es una tienda uruguaya real con catálogo equivalente (auriculares,
parlantes, smartwatch, airfryer, cafeteras, teclados, monitores, accesorios de
celular, herramientas, secadores de pelo) y `robots.txt` completamente
abierto.

## Estructura

```
config/categorias.json   categorías objetivo y parámetros de scraping
config/productos.json    los 74 productos fijos que se trackean siempre
scraper/common.py        extracción de precios (compartida)
scraper/build_product_list.py   selección inicial (corre una sola vez)
scraper/capture_snapshot.py     captura periódica (corre en cron)
data/precios.csv         histórico acumulado, una fila por producto por corrida
```

## Detección (en progreso)

- Variación % vs. ayer / semana pasada
- Mínimo histórico
- Descuento falso: precio de lista actual ≤ un precio de venta ya visto antes
- Precio estancado (para descartar productos que no aportan a la demo)
