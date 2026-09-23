# Generador de Mockup Multi-Dispositivo

Genera una imagen con tu web mostrada en Desktop, Laptop, Tablet y Móvil, usando el frame que subiste.

## Instalación (una sola vez)

```bash
pip install playwright pillow
playwright install chromium
```

## Uso

Deja `generar_mockup.py` y `mockup_base.png` en la misma carpeta, luego:

```bash
python generar_mockup.py https://tuweb.com
```

Esto genera `mockup_resultado.png` en la misma carpeta.

### Opciones útiles

```bash
# Cambiar el nombre de salida
python generar_mockup.py https://tuweb.com --output cliente_polita.png

# Si la web tarda en cargar animaciones/imágenes, dale más margen (ms)
python generar_mockup.py https://tuweb.com --wait 3000

# Usar otra imagen base (otro frame de mockup)
python generar_mockup.py https://tuweb.com --base otro_frame.png
```

## Cómo funciona por dentro

1. Abre la URL con Chromium headless (Playwright) a 4 resoluciones:
   - Desktop: 1920×1080
   - Laptop: 1440×900
   - Tablet: 768×1024
   - Móvil: 375×667
2. Toma un screenshot del viewport visible (no de toda la página, para que se vea "above the fold" tal cual entraría un visitante).
3. Recorta cada captura para que encaje sin deformarse en la pantalla correspondiente del frame.
4. Pega las 4 capturas sobre `mockup_base.png` en las coordenadas exactas de cada pantalla (ya calculadas por análisis de píxeles sobre tu imagen).

## Si quieres usarlo con otra imagen de mockup

Las coordenadas de las 4 pantallas están al principio del script, en `SCREEN_BOXES`. Si cambias de imagen base, hay que recalcularlas (dime y te ayudo a detectar las nuevas coordenadas automáticamente).

## Nota sobre full_page vs viewport

Por defecto se captura solo lo visible en pantalla (sin scroll). Si prefieres capturar la página completa (long-scroll) y luego recortar la parte superior, es un cambio de una línea (`full_page=True`) — avísame si lo quieres así.
