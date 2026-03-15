#!/bin/sh
set -e

if [ ! -f .env ]; then
  cp .env.example .env
  [ -n "$DB_HOST" ] && sed -i "s|DB_HOST=.*|DB_HOST=$DB_HOST|" .env
  [ -n "$DB_PORT" ] && sed -i "s|DB_PORT=.*|DB_PORT=$DB_PORT|" .env
  [ -n "$DB_DATABASE" ] && sed -i "s|DB_DATABASE=.*|DB_DATABASE=$DB_DATABASE|" .env
  [ -n "$DB_USERNAME" ] && sed -i "s|DB_USERNAME=.*|DB_USERNAME=$DB_USERNAME|" .env
  [ -n "$DB_PASSWORD" ] && sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|" .env
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

php artisan key:generate --force
# Migrations + seeders (incl. CardSeeder con URLs correctas de assets.tcgdex.net para imágenes)
php artisan migrate --seed --force

exec "$@"
