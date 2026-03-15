# Deploy frontend + backend + MySQL. Si FrontPKMNTCG no tiene codigo fuente, lo clona del repo.
# Ejecutar desde la raiz: .\scripts\deploy-docker.ps1
# Opcional: $env:VITE_API_URL = "https://api.ejemplo.com/api"; $env:FRONTEND_REPO = "https://github.com/otro/front.git"; .\scripts\deploy-docker.ps1

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RootDir

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Docker no encontrado. Instala Docker Desktop (o Docker + Docker Compose) y vuelve a intentar.'
    exit 1
}

$frontDir = Join-Path $RootDir 'FrontPKMNTCG'
$frontSrc = Join-Path $frontDir 'src\main.js'
$frontRepo = $env:FRONTEND_REPO
if (-not $frontRepo) { $frontRepo = 'https://github.com/jose22uwu/FrontEnd-TCG-Center.git' }

if (-not (Test-Path $frontSrc)) {
    Write-Host 'FrontPKMNTCG sin codigo fuente. Clonando frontend...'
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error 'Git no encontrado. Instala Git o copia el codigo del front en FrontPKMNTCG y vuelve a ejecutar.'
        exit 1
    }
    $cloneDir = Join-Path $RootDir 'FrontPKMNTCG_clone'
    if (Test-Path $cloneDir) { Remove-Item -Recurse -Force $cloneDir }
    git clone --depth 1 $frontRepo $cloneDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'No se pudo clonar el repositorio del frontend. Comprueba FRONTEND_REPO o la red.'
        exit 1
    }
    if (-not (Test-Path $frontDir)) { New-Item -ItemType Directory -Path $frontDir | Out-Null }
    $toCopy = @('src', 'index.html', 'package.json', 'package-lock.json', 'vite.config.js', 'vite.config.ts', 'public', 'favicon.svg')
    foreach ($item in $toCopy) {
        $srcPath = Join-Path $cloneDir $item
        if (Test-Path $srcPath) {
            Copy-Item -Path $srcPath -Destination $frontDir -Recurse -Force
        }
    }
    Remove-Item -Recurse -Force $cloneDir
    Write-Host 'Frontend clonado en FrontPKMNTCG.'
}

Write-Host 'Construyendo y levantando servicios (mysql, backend, frontend)...'
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Error 'docker compose up fallo.'
    exit 1
}

Write-Host ''
Write-Host 'Despliegue listo.'
Write-Host '  Frontend: http://localhost:8080'
Write-Host '  Backend API: http://localhost:8000'
Write-Host '  Parar: docker compose down'
