#!/usr/bin/env bash
# Deploy frontend + backend + MySQL con Docker Compose.
# Ejecutar desde la raíz del proyecto: ./scripts/deploy-docker.sh
# Opcional: VITE_API_URL=https://api.ejemplo.com/api ./scripts/deploy-docker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
    echo 'Docker no encontrado. Instala Docker y Docker Compose e inténtalo de nuevo.' >&2
    exit 1
fi

echo 'Construyendo y levantando servicios (mysql, backend, frontend)...'
docker compose up -d --build

echo ''
echo 'Despliegue listo.'
echo '  Frontend: http://localhost:8080'
echo '  Backend API: http://localhost:8000'
echo '  Parar: docker compose down'
