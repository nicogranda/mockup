<?php
// index.php — Formulario para generar mockups de portfolio
// Vive en /Applications/MAMP/htdocs/mockup/index.php
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Generador de Mockups — EcommJuice</title>
<style>
    * { box-sizing: border-box; }
    body {
        font-family: -apple-system, 'Inter', sans-serif;
        background: #f4f4f4;
        margin: 0;
        padding: 40px 20px;
        color: #222;
    }
    .card {
        max-width: 520px;
        margin: 0 auto;
        background: #fff;
        border-radius: 10px;
        padding: 32px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    h1 { font-size: 1.4rem; margin: 0 0 24px; }
    label { display: block; font-weight: 600; font-size: 0.9rem; margin: 18px 0 6px; }
    input[type=text], input[type=url], input[type=file] {
        width: 100%;
        padding: 10px 12px;
        border: 1px solid #ccc;
        border-radius: 6px;
        font-size: 0.95rem;
    }
    .tabs { display: flex; gap: 8px; margin-bottom: 8px; }
    .tab-btn {
        flex: 1;
        padding: 8px;
        border: 1px solid #ccc;
        background: #f8f8f8;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.85rem;
        text-align: center;
    }
    .tab-btn.active { background: #9CE000; color: #111; border-color: #9CE000; }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .checkbox-row { display: flex; align-items: center; gap: 8px; margin-top: 20px; }
    .checkbox-row input { width: auto; }
    button[type=submit] {
        margin-top: 28px;
        width: 100%;
        padding: 13px;
        background: #9CE000;
        color: #111;
        border: none;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
    }
    button[type=submit]:hover { filter: brightness(1.08); }
    .hint { font-size: 0.78rem; color: #888; margin-top: 4px; }
</style>
</head>
<body>

<div class="card">
    <h1>Generador de Mockups</h1>

    <form action="procesar.php" method="POST" enctype="multipart/form-data" id="mockupForm">

        <label for="cliente">Nombre del cliente</label>
        <input type="text" name="cliente" id="cliente" required>
        <div class="hint">Se usará para el nombre de la carpeta de resultados.</div>

        <label>Logo del cliente</label>
        <div class="tabs">
            <div class="tab-btn active" data-tab="archivo" onclick="cambiarTab('archivo')">Subir archivo</div>
            <div class="tab-btn" data-tab="url" onclick="cambiarTab('url')">Desde URL</div>
        </div>
        <div class="tab-content active" id="tab-archivo">
            <input type="file" name="logo_archivo" accept=".png,.jpg,.jpeg,.svg">
            <div class="hint">PNG, JPG o SVG.</div>
        </div>
        <div class="tab-content" id="tab-url">
            <input type="url" name="logo_url">
        </div>

        <label for="url">URL del sitio a mockupear</label>
        <input type="url" name="url" id="url" required>

        <div class="checkbox-row">
            <input type="checkbox" name="seo" id="seo" value="1">
            <label for="seo" style="margin:0;">Se hizo trabajo de SEO (usar gráfico de SEO en la pantalla del laptop)</label>
        </div>

        <button type="submit">Generar mockup</button>
    </form>
</div>

<script>
function cambiarTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
}
</script>

</body>
</html>
