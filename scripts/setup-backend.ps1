# Backend setup from scratch. Run from project root or from scripts/:
#   .\scripts\setup-backend.ps1
# Or: pwsh -File scripts\setup-backend.ps1

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RootDir

if (-not (Get-Command php -ErrorAction SilentlyContinue)) {
    Write-Error 'PHP not found. Install PHP 8.2+ and try again.'
    exit 1
}

if (-not (Get-Command composer -ErrorAction SilentlyContinue)) {
    Write-Error 'Composer not found. Install Composer and try again.'
    exit 1
}

& php (Join-Path $ScriptDir 'setup-backend.php')
exit $LASTEXITCODE
