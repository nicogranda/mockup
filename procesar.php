<?php
// procesar.php — Recibe el formulario, guarda todo en /clientes/{slug}/ y corre generar_portfolio.py
// Vive en /Applications/MAMP/htdocs/mockup/procesar.php

set_time_limit(180); // Playwright + 4 capturas puede tardar un rato

$script_dir  = __DIR__;
$venv_python = $script_dir . '/venv/bin/python3';
$script_path = $script_dir . '/generar_portfolio.py';

function error_page(string $mensaje, string $detalle = ''): void {
    http_response_code(400);
    echo "<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'><title>Error</title>
    <style>body{font-family:sans-serif;max-width:600px;margin:60px auto;padding:0 20px;}
    .err{background:#fee;border:1px solid #f99;border-radius:8px;padding:20px;}
    pre{white-space:pre-wrap;background:#111;color:#0f0;padding:14px;border-radius:6px;font-size:0.8rem;overflow:auto;}
    a{color:#FF2400;}</style></head><body>";
    echo "<div class='err'><strong>❌ " . htmlspecialchars($mensaje) . "</strong></div>";
    if ($detalle) echo "<pre>" . htmlspecialchars($detalle) . "</pre>";
    echo "<p><a href='index.php'>← Volver al formulario</a></p></body></html>";
    exit;
}

// ── Validaciones básicas ─────────────────────────────────────────────
$cliente = trim($_POST['cliente'] ?? '');
$url     = trim($_POST['url'] ?? '');
$seo     = isset($_POST['seo']) && $_POST['seo'] === '1';

if ($cliente === '') error_page('Falta el nombre del cliente.');
if ($url === '' || !filter_var($url, FILTER_VALIDATE_URL)) error_page('La URL del sitio no es válida.');

// Slug seguro para nombre de carpeta
$slug = strtolower(trim(preg_replace('/[^a-zA-Z0-9]+/', '-', $cliente), '-'));
if ($slug === '') error_page('El nombre del cliente no genera un nombre de carpeta válido.');

// ── Carpeta de destino ───────────────────────────────────────────────
$carpeta_clientes = $script_dir . '/clientes';
if (!is_dir($carpeta_clientes)) mkdir($carpeta_clientes, 0775, true);

$carpeta = $carpeta_clientes . '/' . $slug;
if (!is_dir($carpeta)) {
    mkdir($carpeta, 0775, true);
} else {
    // Si ya existe, versiona con fecha para no pisar un mockup anterior
    $carpeta = $carpeta_clientes . '/' . $slug . '-' . date('Ymd-His');
    mkdir($carpeta, 0775, true);
}

// ── Logo: archivo subido o URL ───────────────────────────────────────
$logo_path = null;
$extensiones_validas = ['png', 'jpg', 'jpeg', 'svg'];

if (!empty($_FILES['logo_archivo']['name'])) {
    $ext = strtolower(pathinfo($_FILES['logo_archivo']['name'], PATHINFO_EXTENSION));
    if (!in_array($ext, $extensiones_validas)) {
        error_page("Formato de logo no soportado: .$ext (usa PNG, JPG o SVG).");
    }
    if ($_FILES['logo_archivo']['error'] !== UPLOAD_ERR_OK) {
        error_page('Error al subir el archivo del logo.');
    }
    $logo_path = $carpeta . '/logo.' . $ext;
    if (!move_uploaded_file($_FILES['logo_archivo']['tmp_name'], $logo_path)) {
        error_page('No se pudo guardar el logo subido.');
    }
} elseif (!empty($_POST['logo_url'])) {
    $logo_url = trim($_POST['logo_url']);
    if (!filter_var($logo_url, FILTER_VALIDATE_URL)) {
        error_page('La URL del logo no es válida.');
    }
    $ext = strtolower(pathinfo(parse_url($logo_url, PHP_URL_PATH), PATHINFO_EXTENSION));
    if (!in_array($ext, $extensiones_validas)) {
        error_page("Formato de logo no soportado desde la URL: .$ext");
    }
    $contexto = stream_context_create(['http' => ['header' => "User-Agent: Mozilla/5.0\r\n", 'timeout' => 15]]);
    $datos = @file_get_contents($logo_url, false, $contexto);
    if ($datos === false) {
        error_page('No se pudo descargar el logo desde la URL proporcionada.');
    }
    $logo_path = $carpeta . '/logo.' . $ext;
    file_put_contents($logo_path, $datos);
} else {
    error_page('Debes subir un logo o indicar una URL de logo.');
}

// ── Armar y ejecutar el comando ──────────────────────────────────────
$output_path = $carpeta . '/portfolio_resultado.png';
$flag_seo    = $seo ? '--seo' : '--no-seo';

$cmd = escapeshellarg($venv_python) . ' ' . escapeshellarg($script_path)
     . ' --url '    . escapeshellarg($url)
     . ' --logo '   . escapeshellarg($logo_path)
     . ' '          . $flag_seo
     . ' --output ' . escapeshellarg($output_path)
     . ' 2>&1';

exec($cmd, $salida_lineas, $codigo_salida);
$salida_texto = implode("\n", $salida_lineas);

if ($codigo_salida !== 0 || !file_exists($output_path)) {
    error_page('El script de generación falló.', $salida_texto);
}

// ── Resultado ─────────────────────────────────────────────────────────
$rel_carpeta = 'clientes/' . basename($carpeta);
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Mockup generado — <?= htmlspecialchars($cliente) ?></title>
<style>
    body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #222; }
    img { max-width: 100%; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
    .meta { color: #666; font-size: 0.85rem; margin: 10px 0 24px; }
    a.btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #FF2400; color: #fff; text-decoration: none; border-radius: 6px; }
    pre { background: #111; color: #0f0; padding: 14px; border-radius: 6px; font-size: 0.78rem; overflow: auto; }
</style>
</head>
<body>
    <h1>✅ Mockup de <?= htmlspecialchars($cliente) ?></h1>
    <p class="meta">Guardado en: <code><?= htmlspecialchars($rel_carpeta) ?></code></p>
    <img src="<?= htmlspecialchars($rel_carpeta) ?>/portfolio_resultado.png" alt="Mockup de <?= htmlspecialchars($cliente) ?>">
    <div>
        <a class="btn" href="<?= htmlspecialchars($rel_carpeta) ?>/portfolio_resultado.png" download>Descargar PNG</a>
        <a class="btn" style="background:#333;" href="index.php">Generar otro</a>
    </div>
    <?php if ($salida_texto): ?>
        <p class="meta" style="margin-top:30px;">Registro del proceso:</p>
        <pre><?= htmlspecialchars($salida_texto) ?></pre>
    <?php endif; ?>
</body>
</html>
