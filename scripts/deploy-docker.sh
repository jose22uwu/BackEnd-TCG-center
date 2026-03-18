#!/usr/bin/env bash
# Deploy frontend + backend + MySQL. Si FrontPKMNTCG no tiene codigo fuente, lo clona del repo.
# Ejecutar desde la raiz: ./scripts/deploy-docker.sh
# Opcional: VITE_API_URL=... FRONTEND_REPO=https://github.com/otro/front.git ./scripts/deploy-docker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
    echo 'Docker no encontrado. Instala Docker y Docker Compose e inténtalo de nuevo.' >&2
    exit 1
fi

FRONT_DIR="$ROOT_DIR/FrontPKMNTCG"
FRONT_SRC="$FRONT_DIR/src/main.js"
FRONTEND_REPO="${FRONTEND_REPO:-https://github.com/jose22uwu/FrontEnd-TCG-Center.git}"

if [ ! -f "$FRONT_SRC" ]; then
    echo 'FrontPKMNTCG sin codigo fuente. Clonando frontend...'
    if ! command -v git >/dev/null 2>&1; then
        echo 'Git no encontrado. Instala Git o copia el codigo del front en FrontPKMNTCG.' >&2
        exit 1
    fi
    CLONE_DIR="$ROOT_DIR/FrontPKMNTCG_clone"
    rm -rf "$CLONE_DIR"
    git clone --depth 1 "$FRONTEND_REPO" "$CLONE_DIR"
    mkdir -p "$FRONT_DIR"
    for item in src index.html package.json package-lock.json vite.config.js vite.config.ts nginx.conf public favicon.svg; do
        [ -e "$CLONE_DIR/$item" ] && cp -R "$CLONE_DIR/$item" "$FRONT_DIR/"
    done
    rm -rf "$CLONE_DIR"
    echo 'Frontend clonado en FrontPKMNTCG.'
fi

echo 'Construyendo y levantando servicios (mysql, backend, frontend)...'
docker compose up -d --build

echo ''
echo 'Despliegue listo.'
echo '  Frontend: http://localhost:8080'
echo '  Backend API: http://localhost:8000'
echo '  Parar: docker compose down'
