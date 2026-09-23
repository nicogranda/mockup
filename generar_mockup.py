#!/usr/bin/env python3
"""
generar_mockup.py
------------------
Genera un mockup responsive (desktop, laptop, tablet, móvil) a partir de una URL,
usando la imagen base "mockup_base.png" (el frame con los 4 dispositivos).

Requisitos (instalar una vez):
    pip install playwright pillow
    playwright install chromium

Uso:
    python generar_mockup.py https://ejemplo.com
    python generar_mockup.py https://ejemplo.com --output mi_mockup.png
    python generar_mockup.py https://ejemplo.com --wait 2000   # espera 2s tras cargar (animaciones, lazy-load, etc.)

Salida:
    mockup_resultado.png (o el nombre que indiques con --output)
"""

import argparse
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

# Coordenadas (x0, y0, x1, y1) de cada pantalla dentro de mockup_base.png
# Calculadas por análisis de píxeles sobre la imagen original.
SCREEN_BOXES = {
    "desktop": (185, 145, 681, 454),
    "laptop":  (549, 392, 895, 608),
    "tablet":  (96, 367, 259, 585),
    "phone":   (246, 506, 314, 609),
}

# Viewport con el que se captura cada dispositivo (ancho x alto lógico del navegador).
# Las alturas se calculan para que coincidan EXACTAMENTE con la proporción de cada
# pantalla del frame (SCREEN_BOXES), así se evita recortar el contenido a la fuerza.
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1196},
    "laptop":  {"width": 1440, "height": 899},
    "tablet":  {"width": 768,  "height": 1027},
    "phone":   {"width": 390,  "height": 591},
}

BASE_IMAGE_NAME = "mockup_base.png"


def forzar_carga_lazy(page):
    """Baja y sube la página para disparar imágenes con lazy-load antes de capturar."""
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


def capturar_screenshot(page, url: str, viewport: dict, wait_ms: int) -> Image.Image:
    """Navega a la URL con el viewport dado y devuelve un objeto PIL.Image con el screenshot."""
    page.set_viewport_size(viewport)
    try:
        page.goto(url, wait_until="load", timeout=45000)
    except Exception:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    forzar_carga_lazy(page)
    page.wait_for_timeout(max(wait_ms, 500))
    # Screenshot solo del viewport visible (no full_page) para que
    # coincida 1:1 con lo que se ve "arriba del scroll" en cada dispositivo.
    screenshot_bytes = page.screenshot(full_page=False)
    from io import BytesIO
    return Image.open(BytesIO(screenshot_bytes)).convert("RGB")


def ajustar_a_pantalla(shot: Image.Image, box: tuple) -> Image.Image:
    """Recorta/escala el screenshot para llenar exactamente el rectángulo 'box' (cover, sin deformar)."""
    x0, y0, x1, y1 = box
    target_w, target_h = x1 - x0, y1 - y0
    target_ratio = target_w / target_h
    src_ratio = shot.width / shot.height

    if src_ratio > target_ratio:
        # el screenshot es más ancho -> recortar a los lados
        new_width = int(shot.height * target_ratio)
        left = (shot.width - new_width) // 2
        shot = shot.crop((left, 0, left + new_width, shot.height))
    else:
        # el screenshot es más alto -> recortar arriba/abajo
        new_height = int(shot.width / target_ratio)
        top = 0  # priorizamos la parte superior de la página (más relevante visualmente)
        top = min(top, shot.height - new_height)
        shot = shot.crop((0, top, shot.width, top + new_height))

    return shot.resize((target_w, target_h), Image.LANCZOS)


def generar_mockup(url: str, output_path: str, wait_ms: int, base_image_path: str):
    base = Image.open(base_image_path).convert("RGB")
    base_dir = Path(base_image_path).parent

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for nombre, box in SCREEN_BOXES.items():
            print(f"→ Capturando versión '{nombre}'...")
            viewport = VIEWPORTS[nombre]
            shot = capturar_screenshot(page, url, viewport, wait_ms)
            shot_ajustado = ajustar_a_pantalla(shot, box)

            mask_path = base_dir / f"mask_{nombre}.png"
            if mask_path.exists():
                # Máscara precisa (polígono real de la pantalla, respetando qué
                # partes están tapadas por otros dispositivos del frame).
                mask = Image.open(mask_path).convert("L")
                target_w, target_h = box[2] - box[0], box[3] - box[1]
                if mask.size != (target_w, target_h):
                    mask = mask.resize((target_w, target_h), Image.LANCZOS)
                base.paste(shot_ajustado, (box[0], box[1]), mask=mask)
            else:
                # Fallback: rectángulo simple si no existe la máscara.
                base.paste(shot_ajustado, (box[0], box[1]))

        browser.close()

    base.save(output_path)
    print(f"\n✅ Mockup guardado en: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Genera un mockup multi-dispositivo a partir de una URL.")
    parser.add_argument("url", help="URL de la web a capturar (ej: https://ejemplo.com)")
    parser.add_argument("--output", default="mockup_resultado.png", help="Nombre del archivo de salida")
    parser.add_argument("--wait", type=int, default=1000, help="Milisegundos de espera extra tras cargar la página")
    parser.add_argument(
        "--base",
        default=str(Path(__file__).parent / BASE_IMAGE_NAME),
        help="Ruta a la imagen base del mockup (por defecto usa mockup_base.png en la misma carpeta)",
    )
    args = parser.parse_args()

    if not Path(args.base).exists():
        print(f"❌ No se encontró la imagen base en: {args.base}")
        print("   Asegúrate de tener 'mockup_base.png' en la misma carpeta que este script.")
        sys.exit(1)

    generar_mockup(args.url, args.output, args.wait, args.base)


if __name__ == "__main__":
    main()
