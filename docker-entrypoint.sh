#!/bin/sh
set -e

# Directorios que Laravel necesita para logs, cache, sesiones
mkdir -p storage/framework/{sessions,views,cache} storage/logs bootstrap/cache
chmod -R 775 storage bootstrap/cache 2>/dev/null || true

if [ ! -f .env ]; then
  cp .env.example .env
  [ -n "$DB_HOST" ] && sed -i "s|^DB_HOST=.*|DB_HOST=${DB_HOST}|" .env
  [ -n "$DB_PORT" ] && sed -i "s|^DB_PORT=.*|DB_PORT=${DB_PORT}|" .env
  [ -n "$DB_DATABASE" ] && sed -i "s|^DB_DATABASE=.*|DB_DATABASE=${DB_DATABASE}|" .env
  [ -n "$DB_USERNAME" ] && sed -i "s|^DB_USERNAME=.*|DB_USERNAME=${DB_USERNAME}|" .env
  [ -n "$DB_PASSWORD" ] && sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD}|" .env
  [ -n "$APP_URL" ] && sed -i "s|^APP_URL=.*|APP_URL=${APP_URL}|" .env
  [ -n "$TCGDEX_SSL_VERIFY" ] && sed -i "s|^#\?TCGDEX_SSL_VERIFY=.*|TCGDEX_SSL_VERIFY=${TCGDEX_SSL_VERIFY}|" .env || true
fi

# Wait for MySQL
until php -r "
  \$h = getenv('DB_HOST') ?: 'mysql';
  \$p = getenv('DB_PORT') ?: '3306';
  \$d = getenv('DB_DATABASE') ?: 'subasta_pokemon';
  \$u = getenv('DB_USERNAME') ?: 'root';
  \$w = getenv('DB_PASSWORD') ?: '';
  try {
    new PDO(\"mysql:host=\$h;port=\$p;dbname=\$d\", \$u, \$w);
    exit(0);
  } catch (Exception \$e) {
    exit(1);
  }
" 2>/dev/null; do
  echo "Waiting for MySQL..."
  sleep 2
done

php artisan key:generate --force 2>/dev/null || true
php artisan config:clear
php artisan migrate --force
# Seed (pon ARTISAN_SEED=0 en docker-compose para no ejecutar en cada arranque)
if [ "${ARTISAN_SEED:-1}" = "1" ]; then
  php artisan db:seed --force 2>/dev/null || true
fi

exec "$@"
