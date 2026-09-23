#!/usr/bin/env python3
"""
generar_portfolio.py
---------------------
Genera una pieza de portfolio estandarizada: mockup de dispositivos con tu web real,
logo del cliente en un área fija, y (opcional) la pantalla del laptop reemplazada por
un gráfico de SEO en vez del sitio real.

Requisitos (instalar una vez):
    pip install playwright pillow cairosvg
    playwright install chromium

Uso INTERACTIVO (recomendado, te va preguntando todo en orden: logo → SEO → URL):
    python generar_portfolio.py

Uso con argumentos (para automatizar / scripts):
    python generar_portfolio.py --url https://ejemplo.com --logo logo_cliente.png --seo
    python generar_portfolio.py --url https://ejemplo.com --logo https://site.com/logo.png --no-seo

El logo puede ser:
    - una ruta local:  logos/eliveli.png  o  logos/eliveli.svg
    - una URL:         https://ejemplo.com/logo.png  o  .../logo.svg
    Formatos soportados: PNG, JPG, SVG (el SVG se convierte automáticamente).

Salida:
    portfolio_resultado.png (o el nombre que indiques con --output)
"""

import argparse
import sys
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from playwright.sync_api import sync_playwright

# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LA PLANTILLA (ajustable)
# ────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BASE_IMAGE_PATH = SCRIPT_DIR / "mockup_base.png"
SEO_IMAGE_PATH = SCRIPT_DIR / "SEO1.png"
SEO_LAPTOP_BOX = (500, 300, 1050, 675)  # Portátil SEO completo, incluida la lupa

# Coordenadas (x0, y0, x1, y1) de cada pantalla dentro de mockup_base.png
SCREEN_BOXES = {
    "desktop": (185, 145, 681, 454),
    "laptop":  (549, 392, 895, 608),
    "tablet":  (96, 367, 259, 585),
    "phone":   (246, 506, 314, 609),
}

# Viewports (ancho x alto) ajustados a la proporción real de cada pantalla del frame
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1196},
    "laptop":  {"width": 1440, "height": 899},
    "tablet":  {"width": 768,  "height": 1027},
    "phone":   {"width": 390,  "height": 591},
}

# Lienzo final = el mismo frame de dispositivos (no se agrega columna en blanco aparte).
# El logo se pega directamente sobre el fondo vacío del frame: a la derecha del monitor
# y por encima del laptop.
LOGO_BOX = (725, 33, 1178, 282)


# ────────────────────────────────────────────────────────────────────────────
# ENTRADA INTERACTIVA
# ────────────────────────────────────────────────────────────────────────────

def preguntar_datos(args):
    """Completa los datos faltantes preguntando por consola."""
    logo = args.logo
    if not logo:
        logo = input("Logo del cliente — ruta local o URL (PNG o SVG): ").strip()

    if args.seo is None:
        resp = input("¿Se hizo trabajo de SEO para este cliente? (s/n): ").strip().lower()
        incluye_seo = resp.startswith("s")
    else:
        incluye_seo = args.seo

    url = args.url or input("URL del sitio a mockupear: ").strip()

    output = args.output
    if not output:
        sugerido = "portfolio_resultado.png"
        resp = input(f"Nombre del archivo de salida [{sugerido}]: ").strip()
        output = resp or sugerido

    return url, logo, incluye_seo, output


# ────────────────────────────────────────────────────────────────────────────
# CAPTURA Y COMPOSICIÓN DE DISPOSITIVOS (igual que generar_mockup.py)
# ────────────────────────────────────────────────────────────────────────────

def forzar_carga_lazy(page):
    page.evaluate("""
        () => new Promise((resolve) => {
            let total = 0;
            const step = 400;
            const timer = setInterval(() => {
                window.scrollBy(0, step);
                total += step;
                if (total >= document.body.scrollHeight) {
                    clearInterval(timer);
                    window.scrollTo(0, 0);
                    resolve();
                }
            }, 80);
        })
    """)


def capturar_screenshot(page, url: str, viewport: dict, wait_ms: int = 1500) -> Image.Image:
    page.set_viewport_size(viewport)
    try:
        page.goto(url, wait_until="load", timeout=45000)
    except Exception:
        # Fallback: si ni siquiera "load" dispara a tiempo (sitio muy pesado
        # o con recursos que cuelgan), seguimos con lo que haya cargado ya.
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    forzar_carga_lazy(page)
    page.wait_for_timeout(max(wait_ms, 500))
    screenshot_bytes = page.screenshot(full_page=False)
    return Image.open(BytesIO(screenshot_bytes)).convert("RGB")


def ajustar_a_pantalla(shot: Image.Image, box: tuple) -> Image.Image:
    """Recorta/escala una imagen para llenar exactamente el rectángulo 'box' (cover, sin deformar)."""
    x0, y0, x1, y1 = box
    target_w, target_h = x1 - x0, y1 - y0
    target_ratio = target_w / target_h
    src_ratio = shot.width / shot.height

    if src_ratio > target_ratio:
        new_width = int(shot.height * target_ratio)
        left = (shot.width - new_width) // 2
        shot = shot.crop((left, 0, left + new_width, shot.height))
    else:
        new_height = int(shot.width / target_ratio)
        top = min(0, shot.height - new_height)
        shot = shot.crop((0, top, shot.width, top + new_height))

    return shot.resize((target_w, target_h), Image.LANCZOS)


def construir_mockup_dispositivos(url: str, incluye_seo: bool) -> Image.Image:
    """Genera el frame de 4 dispositivos con el sitio real (y SEO en el laptop si aplica)."""
    base = Image.open(BASE_IMAGE_PATH).convert("RGB")
    if incluye_seo:
        # Retira el portátil anterior del frame antes de colocar el PNG completo.
        # Conserva la parte visible del monitor y su soporte a la izquierda.
        from PIL import ImageDraw
        ImageDraw.Draw(base).rectangle((520, 455, 955, 670), fill=base.getpixel((0, 0)))

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for nombre, box in SCREEN_BOXES.items():
            if nombre == "laptop" and incluye_seo:
                continue
            print(f"→ Capturando versión '{nombre}'...")
            shot = capturar_screenshot(page, url, VIEWPORTS[nombre])
            shot_ajustado = ajustar_a_pantalla(shot, box)

            mask_path = SCRIPT_DIR / f"mask_{nombre}.png"
            if mask_path.exists():
                mask = Image.open(mask_path).convert("L")
                base.paste(shot_ajustado, (box[0], box[1]), mask=mask)
            else:
                base.paste(shot_ajustado, (box[0], box[1]))

        browser.close()

    if incluye_seo:
        print("→ Colocando portátil SEO...")
        laptop = Image.open(SEO_IMAGE_PATH).convert("RGBA")
        laptop = laptop.crop(laptop.getchannel("A").getbbox())
        x0, y0, x1, y1 = SEO_LAPTOP_BOX
        laptop = laptop.resize((x1 - x0, y1 - y0), Image.LANCZOS)
        base.paste(laptop, (x0, y0), laptop)

    return base


# ────────────────────────────────────────────────────────────────────────────
# LOGO
# ────────────────────────────────────────────────────────────────────────────

def _es_svg(data_o_path) -> bool:
    """Detecta si es SVG por extensión de archivo o por contenido (bytes)."""
    if isinstance(data_o_path, (bytes, bytearray)):
        return b"<svg" in data_o_path[:1000].lower()
    return str(data_o_path).lower().endswith(".svg")


def _svg_a_imagen(svg_bytes: bytes, ancho_objetivo: int = 800) -> Image.Image:
    """Convierte bytes SVG a una imagen PIL RGBA usando cairosvg."""
    try:
        import cairosvg
    except ImportError:
        raise RuntimeError(
            "El logo es SVG pero falta la librería 'cairosvg'.\n"
            "Instálala con:  pip install cairosvg"
        )
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=ancho_objetivo)
    return Image.open(BytesIO(png_bytes)).convert("RGBA")


def cargar_logo(logo_ref: str) -> Image.Image:
    """Carga el logo desde una ruta local o una URL. Soporta PNG, JPG y SVG."""
    if logo_ref.lower().startswith("http://") or logo_ref.lower().startswith("https://"):
        print(f"→ Descargando logo desde {logo_ref} ...")
        req = urllib.request.Request(logo_ref, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if _es_svg(logo_ref) or _es_svg(data):
            return _svg_a_imagen(data)
        return Image.open(BytesIO(data)).convert("RGBA")
    else:
        path = Path(logo_ref)
        if not path.exists():
            raise FileNotFoundError(f"No se encontró el logo en: {path}")
        if _es_svg(path):
            return _svg_a_imagen(path.read_bytes())
        return Image.open(path).convert("RGBA")


def colocar_logo(canvas: Image.Image, logo: Image.Image, box: tuple):
    """Escala el logo (sin deformar) para que quepa dentro de 'box' y lo centra ahí."""
    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0

    logo_fit = ImageOps.contain(logo, (box_w, box_h))
    px = x0 + (box_w - logo_fit.width) // 2
    py = y0 + (box_h - logo_fit.height) // 2
    canvas.paste(logo_fit, (px, py), logo_fit)


# ────────────────────────────────────────────────────────────────────────────
# COMPOSICIÓN FINAL
# ────────────────────────────────────────────────────────────────────────────

def generar_portfolio(url: str, logo_ref: str, incluye_seo: bool, output_path: str):
    devices = construir_mockup_dispositivos(url, incluye_seo).convert("RGBA")
    logo = cargar_logo(logo_ref)

    # El logo se pega directo sobre el fondo vacío del frame (junto al monitor, arriba del laptop)
    colocar_logo(devices, logo, LOGO_BOX)

    devices.convert("RGB").save(output_path)
    print(f"\nPortfolio guardado en: {output_path}")


# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Genera una pieza de portfolio estandarizada.")
    parser.add_argument("--url", help="URL del sitio a mockupear")
    parser.add_argument("--logo", help="Ruta local o URL del logo del cliente")
    seo_group = parser.add_mutually_exclusive_group()
    seo_group.add_argument("--seo", dest="seo", action="store_true", help="Incluir panel de SEO en el laptop")
    seo_group.add_argument("--no-seo", dest="seo", action="store_false", help="No incluir panel de SEO")
    parser.set_defaults(seo=None)
    parser.add_argument("--output", help="Nombre del archivo de salida")
    args = parser.parse_args()

    if not BASE_IMAGE_PATH.exists():
        print(f"Falta {BASE_IMAGE_PATH.name} en la carpeta del script.")
        sys.exit(1)

    url, logo, incluye_seo, output = preguntar_datos(args)

    if incluye_seo and not SEO_IMAGE_PATH.exists():
        print(f"Falta {SEO_IMAGE_PATH.name} en la carpeta del script (necesario para --seo).")
        sys.exit(1)

    generar_portfolio(url, logo, incluye_seo, output)


if __name__ == "__main__":
    main()
