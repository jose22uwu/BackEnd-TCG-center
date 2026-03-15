# Deploy frontend + backend + MySQL con Docker Compose.
# Ejecutar desde la raíz del proyecto: .\scripts\deploy-docker.ps1
# Opcional: $env:VITE_API_URL = "https://api.ejemplo.com/api"; .\scripts\deploy-docker.ps1

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RootDir

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Docker no encontrado. Instala Docker Desktop (o Docker + Docker Compose) y vuelve a intentar.'
    exit 1
}

Write-Host 'Construyendo y levantando servicios (mysql, backend, frontend)...'
docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Error 'docker compose up falló.'
    exit $LASTEXITCODE
}

Write-Host ''
Write-Host 'Despliegue listo.'
Write-Host '  Frontend: http://localhost:8080'
Write-Host '  Backend API: http://localhost:8000'
Write-Host '  Parar: docker compose down'
