# Prueba de funcionamiento del modelo AI en Docker.
# Requiere: backend + MySQL levantados (docker compose up -d). Usuario seller/password debe existir (seed).
# Ejecutar desde la raiz: .\scripts\test-ai-docker.ps1

$ErrorActionPreference = 'Stop'
$BaseUrl = $env:API_URL
if (-not $BaseUrl) { $BaseUrl = 'http://localhost:8000' }
$Api = "$BaseUrl/api"

Write-Host "API base: $Api"

# Login
$loginBody = @{ username = 'seller'; password = 'password' } | ConvertTo-Json
try {
    $loginResp = Invoke-RestMethod -Uri "$Api/login" -Method Post -Body $loginBody -ContentType 'application/json'
} catch {
    Write-Error "Login fallido: $_"
    exit 1
}
$token = $loginResp.data.token
if (-not $token) {
    Write-Error "Login no devolvio token. Respuesta: $($loginResp | ConvertTo-Json -Depth 2)"
    exit 1
}
Write-Host "Login OK, token obtenido."

# AI Chat
$chatBody = @{ question = 'Que reglas aplican?' } | ConvertTo-Json
$headers = @{
    'Authorization' = "Bearer $token"
    'Content-Type'  = 'application/json'
}
try {
    $chatResp = Invoke-RestMethod -Uri "$Api/ai/chat" -Method Post -Body $chatBody -Headers $headers
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    $body = $null
    if ($_.ErrorDetails.Message) { $body = $_.ErrorDetails.Message }
    Write-Error "AI chat fallo (HTTP $statusCode): $body"
    exit 1
}

# Verificar estructura de respuesta
$data = $chatResp.data
if (-not $data) {
    Write-Error "Respuesta sin .data: $($chatResp | ConvertTo-Json -Depth 3)"
    exit 1
}
$hasPayload = ($null -ne $data.rules) -or ($null -ne $data.collectionSummary) -or ($null -ne $data.recommendations) -or ($null -ne $data.intent)
if (-not $hasPayload) {
    Write-Host "Advertencia: respuesta sin bloques esperados (rules/collectionSummary/recommendations/intent)."
    Write-Host "Payload: $($data | ConvertTo-Json -Depth 2 -Compress)"
}

Write-Host "AI chat OK. message=$($chatResp.message)."
if ($data.rules -and $data.rules.Count -gt 0) {
    Write-Host "rules: $($data.rules.Count) regla(s)."
}
if ($data.collectionSummary) {
    Write-Host "collectionSummary presente."
}
Write-Host "Prueba de AI en Docker completada."
