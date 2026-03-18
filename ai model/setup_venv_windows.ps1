# Crea un venv en "ai model/.venv-windows" e instala dependencias del chatbot.
# Asi PHP usa siempre el mismo Python con numpy, mysql-connector, etc.
# Ejecutar desde la raiz del proyecto: .\ai model\setup_venv_windows.ps1

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$aiModelDir = Join-Path $projectRoot "ai model"
$venvDir = Join-Path $aiModelDir ".venv-windows"
$requirementsPath = Join-Path $aiModelDir "requirements.txt"

if (-not (Test-Path $aiModelDir)) {
    Write-Error "No se encuentra la carpeta ai model en $projectRoot"
    exit 1
}

$py = $null
foreach ($candidate in @("py -3", "python")) {
    try {
        $py = Get-Command $candidate -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source
        if ($py) { break }
    } catch {}
}
if (-not $py) {
    $py = "C:\Users\josec\AppData\Local\Microsoft\WindowsApps\python.exe"
    if (-not (Test-Path $py)) {
        Write-Error "No se encontro Python. Instala Python 3 o ejecuta desde una terminal donde 'python' funcione."
        exit 1
    }
}

Write-Host "Usando Python: $py"
Write-Host "Creando venv en: $venvDir"

if (Test-Path $venvDir) {
    Write-Host "El venv ya existe. Reinstalando dependencias..."
} else {
    & $py -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Fallo al crear el venv."
        exit 1
    }
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "No se creo python.exe en el venv."
    exit 1
}

Write-Host "Instalando dependencias desde requirements.txt..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirementsPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Fallo al instalar dependencias."
    exit 1
}

Write-Host ""
Write-Host "Listo. El chat usara: $venvPython"
Write-Host "Reinicia el backend (php artisan serve) y prueba el asistente en el frontend."
